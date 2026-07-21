#!/usr/bin/env python3
"""README-only governance for public and source-owned private Atlas repositories.

Public audits are allowlist-driven through the canonical public repository
classification projection. Private validation is source-local: the caller passes
only its own repository identity and checked-out README, so no private repository
inventory is introduced into the public control plane.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from .repository_hygiene import (
        Finding,
        GitHubClient,
        HygieneError,
        _decode_content,
        load_json,
        load_projection,
        readme_findings,
    )
except ImportError:
    from repository_hygiene import (
        Finding,
        GitHubClient,
        HygieneError,
        _decode_content,
        load_json,
        load_projection,
        readme_findings,
    )

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy" / "repository-hygiene.json"
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"


def order_findings(repository: str, text: str, policy: dict[str, Any]) -> list[Finding]:
    """Enforce the README section-order rules from the Atlas README style guide."""
    cfg = policy["readme"]
    if repository == cfg["profile_repository"]:
        return []

    findings: list[Finding] = []
    heading = cfg["required_heading"]
    footer_prefix = cfg["required_footer"]
    heading_match = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    footer_match = re.search(rf"(?m)^{re.escape(footer_prefix)}.*$", text)

    if heading_match and footer_match:
        if heading_match.start() > footer_match.start():
            findings.append(
                Finding(
                    repository,
                    "readme",
                    "section-order",
                    "The Atlas Systems integration section must appear before the footer.",
                )
            )
        else:
            between = text[heading_match.end() : footer_match.start()]
            if re.search(r"(?m)^##\s+", between):
                findings.append(
                    Finding(
                        repository,
                        "readme",
                        "atlas-fit-order",
                        "'How it fits into Atlas Systems' must be the final H2 section.",
                    )
                )

        if text[footer_match.end() :].strip():
            findings.append(
                Finding(
                    repository,
                    "readme",
                    "footer-order",
                    "The Atlas Systems footer must be the final non-empty README line.",
                )
            )

    return findings


def all_readme_findings(
    repository: str,
    text: str,
    policy: dict[str, Any],
    *,
    has_license: bool,
) -> list[Finding]:
    findings = readme_findings(repository, text, policy, has_license=has_license)
    findings.extend(order_findings(repository, text, policy))
    findings.sort(key=lambda item: (item.rule_id, item.message))
    return findings


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas Systems README contract audit",
        "",
        f"Mode: `{report['mode']}`",
        f"Repositories checked: **{report['summary']['repositories_checked']}**",
        f"Findings: **{report['summary']['finding_count']}**",
        "",
    ]
    if not report["findings"]:
        lines.extend(["All checked repositories satisfy the current README contract.", ""])
        return "\n".join(lines)

    lines.extend(["| Repository | Rule | Finding |", "|---|---|---|"])
    for finding in report["findings"]:
        message = finding["message"].replace("|", "\\|")
        lines.append(
            f"| `{finding['repository']}` | `{finding['rule_id']}` | {message} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check_local(
    *,
    repository: str,
    readme_path: Path,
    license_path: Path,
    policy_path: Path,
) -> int:
    policy = load_json(policy_path)
    if not isinstance(policy, dict):
        raise HygieneError("repository hygiene policy root must be an object")
    if not readme_path.is_file():
        raise HygieneError(f"README is missing: {readme_path}")
    text = readme_path.read_text(encoding="utf-8")
    findings = all_readme_findings(
        repository,
        text,
        policy,
        has_license=license_path.is_file(),
    )
    if findings:
        for finding in findings:
            print(f"ERROR [{finding.rule_id}] {finding.message}", file=sys.stderr)
        return 1
    print(f"README contract valid: {repository}")
    return 0


def audit_public(
    *,
    policy_path: Path,
    projection_path: Path,
    token: str | None,
    mode: str,
) -> tuple[dict[str, Any], int]:
    policy = load_json(policy_path)
    if not isinstance(policy, dict):
        raise HygieneError("repository hygiene policy root must be an object")
    repositories = load_projection(projection_path)
    client = GitHubClient(token)
    findings: list[Finding] = []

    for classification in repositories:
        repository = classification["repository"]
        owner, name = repository.split("/", 1)
        repo_path = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}"
        try:
            readme_document = client.get_optional_json(f"{repo_path}/contents/README.md")
            if readme_document is None:
                findings.append(
                    Finding(repository, "readme", "missing-readme", "README.md is missing.")
                )
                continue
            readme_text = _decode_content(readme_document, repository, "README.md")
            has_license = client.get_optional_json(f"{repo_path}/contents/LICENSE") is not None
            findings.extend(
                all_readme_findings(
                    repository,
                    readme_text,
                    policy,
                    has_license=has_license,
                )
            )
        except HygieneError as error:
            findings.append(
                Finding(repository, "audit", "provider-read-failed", str(error))
            )

    findings.sort(key=lambda item: (item.repository.lower(), item.rule_id, item.message))
    report = {
        "schema_version": "atlas-repository-readme-audit/report/v1",
        "mode": mode,
        "authority": policy["authority"],
        "repository_projection": policy["repository_projection"],
        "summary": {
            "repositories_checked": len(repositories),
            "finding_count": len(findings),
            "repositories_with_findings": len({item.repository for item in findings}),
        },
        "findings": [item.as_dict() for item in findings],
    }
    return report, 1 if mode == "enforce" and findings else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the Atlas README contract.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    local = subparsers.add_parser("check-local", help="Validate one checked-out repository README.")
    local.add_argument("--repository", required=True)
    local.add_argument("--readme", type=Path, default=Path("README.md"))
    local.add_argument("--license", dest="license_path", type=Path, default=Path("LICENSE"))
    local.add_argument("--policy", type=Path, default=DEFAULT_POLICY)

    public = subparsers.add_parser("audit-public", help="Audit README files for the approved public projection.")
    public.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    public.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    public.add_argument("--mode", choices=("advisory", "enforce"), default="advisory")
    public.add_argument("--json-out", type=Path, required=True)
    public.add_argument("--markdown-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check-local":
            return check_local(
                repository=args.repository,
                readme_path=args.readme,
                license_path=args.license_path,
                policy_path=args.policy,
            )

        report, status = audit_public(
            policy_path=args.policy,
            projection_path=args.projection,
            token=os.environ.get("GITHUB_TOKEN"),
            mode=args.mode,
        )
        write_json(args.json_out, report)
        write_text(args.markdown_out, render_markdown(report))
        print(
            f"checked {report['summary']['repositories_checked']} repositories; "
            f"found {report['summary']['finding_count']} README findings"
        )
        return status
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, HygieneError) as error:
        print(f"README contract validation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
