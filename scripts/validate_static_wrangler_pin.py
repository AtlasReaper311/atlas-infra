#!/usr/bin/env python3
"""Validate that validate-static.yml pins Wrangler immutably for Pages deploy.

Historical defect (atlas-infra#101): floating `wrangler@4` resolved to a release
whose Miniflare alpha dependency was unavailable, so validation passed but the
Pages deploy failed. The invariant is exact, immutable Wrangler resolution —
not a permanent freeze to one specific patch unless source declares it.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / ".github" / "workflows" / "validate-static.yml"

EXACT_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ENV_ASSIGN_RE = re.compile(
    r'^(?P<indent>\s*)WRANGLER_VERSION:\s*(?P<value>["\']?)(?P<version>[^"\'#\s]+)'
    r'(?P=value)\s*(?:#.*)?$'
)
DEPLOY_INVOCATION_RE = re.compile(
    r'npx\s+--yes\s+"wrangler@\$\{WRANGLER_VERSION\}"\s+pages\s+deploy\b'
)
FLOATING_MAJOR_RE = re.compile(r"^wrangler@[0-9]+$")
MUTABLE_SELECTORS = (
    "wrangler@latest",
    "wrangler@next",
    "wrangler@canary",
)


class WranglerPinValidationError(ValueError):
    """Raised when the static Pages Wrangler pin is missing or mutable."""


@dataclass(frozen=True)
class WranglerPin:
    version: str
    line: int


def strip_yaml_scalar(value: str) -> str:
    text = value.split("#", 1)[0].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def parse_wrangler_pin(text: str) -> WranglerPin:
    """Extract the deploy-step WRANGLER_VERSION from workflow text."""
    lines = text.splitlines()
    in_deploy_step = False
    in_env = False
    deploy_indent: int | None = None
    env_indent: int | None = None
    pin: WranglerPin | None = None
    run_block: list[str] = []
    in_run = False
    run_indent: int | None = None

    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))

        if stripped.startswith("- name:") or stripped.startswith("- uses:"):
            name = strip_yaml_scalar(stripped.split(":", 1)[1]) if ":" in stripped else ""
            in_deploy_step = name == "Deploy with wrangler"
            deploy_indent = indent if in_deploy_step else None
            in_env = False
            env_indent = None
            in_run = False
            run_indent = None
            continue

        if not in_deploy_step or deploy_indent is None:
            continue

        if indent <= deploy_indent and not stripped.startswith("-"):
            # Left the deploy step.
            in_deploy_step = False
            in_env = False
            in_run = False
            continue

        if re.match(r"^\s*env:\s*$", raw):
            in_env = True
            env_indent = indent
            in_run = False
            continue

        if re.match(r"^\s*run:\s*\|", raw):
            in_run = True
            run_indent = indent
            in_env = False
            continue

        if in_env and env_indent is not None:
            if indent <= env_indent:
                in_env = False
            else:
                match = ENV_ASSIGN_RE.match(raw)
                if match:
                    if pin is not None:
                        raise WranglerPinValidationError(
                            "multiple WRANGLER_VERSION declarations in deploy step"
                        )
                    pin = WranglerPin(
                        version=match.group("version"),
                        line=index + 1,
                    )
                continue

        if in_run and run_indent is not None:
            if indent <= run_indent and stripped and not raw.startswith(" " * (run_indent + 1)):
                in_run = False
            else:
                run_block.append(raw)

    if pin is None:
        raise WranglerPinValidationError(
            "deploy step is missing an explicit WRANGLER_VERSION declaration"
        )

    run_text = "\n".join(run_block)
    if not DEPLOY_INVOCATION_RE.search(run_text):
        raise WranglerPinValidationError(
            "deploy command must consume wrangler@${WRANGLER_VERSION} via "
            'npx --yes "wrangler@${WRANGLER_VERSION}" pages deploy'
        )

    return pin


def assert_exact_immutable_version(version: str) -> None:
    if version in {"4", "latest", "next", "canary"} or version.startswith("^") or version.startswith("~"):
        raise WranglerPinValidationError(
            f"WRANGLER_VERSION must be an exact x.y.z pin, observed {version!r}"
        )
    if FLOATING_MAJOR_RE.fullmatch(f"wrangler@{version}"):
        raise WranglerPinValidationError(
            f"WRANGLER_VERSION must not be a floating major, observed {version!r}"
        )
    if not EXACT_VERSION_RE.fullmatch(version):
        raise WranglerPinValidationError(
            f"WRANGLER_VERSION must be an exact x.y.z pin, observed {version!r}"
        )


def assert_rejects_mutable_selectors(text: str) -> None:
    """Fail closed if the deploy invocation uses a known mutable selector."""
    # Inspect the deploy run block only after structural parse succeeded.
    pin = parse_wrangler_pin(text)
    assert_exact_immutable_version(pin.version)

    lowered = text.lower()
    for selector in MUTABLE_SELECTORS:
        # Permit mentions in comments describing the historical failure, but
        # reject an actual npx invocation of a mutable selector.
        pattern = re.compile(
            rf'npx\s+(?:--yes\s+)?["\']?{re.escape(selector)}["\']?',
            re.IGNORECASE,
        )
        if pattern.search(text):
            raise WranglerPinValidationError(
                f"deploy must not invoke mutable selector {selector}"
            )

    if re.search(r'npx\s+(?:--yes\s+)?["\']?wrangler["\']?\s+pages\s+deploy\b', text):
        raise WranglerPinValidationError(
            "deploy must not invoke unversioned wrangler for pages deploy"
        )

    if re.search(r'npx\s+(?:--yes\s+)?["\']?wrangler@[0-9]+["\']?', text):
        raise WranglerPinValidationError(
            "deploy must not invoke floating major wrangler@N"
        )

    # Keep linters calm about unused lowered when comments-only.
    del lowered


def validate_workflow_text(text: str) -> WranglerPin:
    pin = parse_wrangler_pin(text)
    assert_exact_immutable_version(pin.version)
    assert_rejects_mutable_selectors(text)
    return pin


def validate_workflow(path: Path) -> WranglerPin:
    if not path.is_file():
        raise WranglerPinValidationError(f"workflow not found: {path}")
    return validate_workflow_text(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow",
        type=Path,
        default=DEFAULT_WORKFLOW,
        help="Path to validate-static.yml",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        pin = validate_workflow(args.workflow.resolve())
    except WranglerPinValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"validated immutable Wrangler pin {pin.version} "
        f"at {args.workflow}:{pin.line}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
