#!/usr/bin/env python3
"""Check runtime model call inventory against Atlas promotion coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_INVENTORY = Path("policy/runtime-model-call-inventory.json")
DEFAULT_COVERAGE = Path("policy/model-promotion-coverage.json")
GENERATION_CLASSIFICATIONS = {
    "interactive-live",
    "async-summary",
    "batch-draft",
    "background-warmup",
}
CAPABILITY_OPTIONAL = {
    "embedding-only",
    "telemetry-only",
    "runtime-evidence-only",
    "unknown",
}


class InventoryError(ValueError):
    """The runtime model inventory is malformed."""


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InventoryError(f"{path} must contain a JSON object")
    return payload


def validate_inventory(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema_version") != "atlas-runtime-model-call-inventory/v1":
        raise InventoryError("unsupported runtime model inventory schema_version")
    allowed = set(payload.get("classification_values", []))
    expected = GENERATION_CLASSIFICATIONS | CAPABILITY_OPTIONAL
    missing = sorted(expected - allowed)
    if missing:
        raise InventoryError("classification_values missing: " + ", ".join(missing))
    call_sites = payload.get("call_sites")
    if not isinstance(call_sites, list):
        raise InventoryError("call_sites must be a list")
    seen: set[str] = set()
    for call_site in call_sites:
        if not isinstance(call_site, dict):
            raise InventoryError("every call site must be an object")
        call_id = str(call_site.get("id", ""))
        if not call_id:
            raise InventoryError("call site missing id")
        if call_id in seen:
            raise InventoryError(f"duplicate call site id: {call_id}")
        seen.add(call_id)
        classification = str(call_site.get("classification", ""))
        if classification not in allowed:
            raise InventoryError(f"{call_id} has unknown classification {classification!r}")
        for key, value in call_site.items():
            if isinstance(value, str) and value.strip() == "<present>":
                raise InventoryError(f"{call_id} includes a masked secret value in {key}")
    return call_sites


def capabilities_by_id(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    capabilities = coverage.get("capabilities")
    if not isinstance(capabilities, list):
        raise InventoryError("model promotion coverage capabilities must be a list")
    result: dict[str, dict[str, Any]] = {}
    for capability in capabilities:
        if not isinstance(capability, dict) or not capability.get("id"):
            raise InventoryError("coverage capability missing id")
        result[str(capability["id"])] = capability
    return result


def path_exists(root: Path | None, relative_path: str) -> bool | None:
    if root is None:
        return None
    return (root / relative_path).is_file()


def issue(
    severity: str,
    code: str,
    call_site: dict[str, Any],
    message: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "call_site": str(call_site.get("id", "")),
        "classification": str(call_site.get("classification", "")),
        "capability_id": str(call_site.get("capability_id") or ""),
        "message": message,
    }


def analyse(
    call_sites: list[dict[str, Any]],
    coverage: dict[str, Any],
    *,
    harness_root: Path | None = None,
) -> list[dict[str, str]]:
    capabilities = capabilities_by_id(coverage)
    issues: list[dict[str, str]] = []
    for call_site in call_sites:
        classification = str(call_site["classification"])
        capability_id = call_site.get("capability_id")
        if classification in CAPABILITY_OPTIONAL:
            continue
        if not capability_id:
            issues.append(
                issue(
                    "warning",
                    "generation-without-capability",
                    call_site,
                    "generation-capable call site has no capability_id",
                )
            )
            continue
        capability = capabilities.get(str(capability_id))
        if capability is None:
            issues.append(
                issue(
                    "failure",
                    "capability-missing-from-coverage",
                    call_site,
                    "call site capability is absent from model-promotion-coverage.json",
                )
            )
            continue
        if classification == "interactive-live" and capability.get("coverage_override"):
            issues.append(
                issue(
                    "failure",
                    "interactive-live-covered-by-override",
                    call_site,
                    "interactive-live call site must not rely on a low-risk coverage override",
                )
            )
        eval_paths = list(capability.get("eval_case_paths", []))
        promotion_paths = list(capability.get("promotion_record_paths", []))
        if classification == "interactive-live" and not eval_paths:
            issues.append(
                issue(
                    "failure",
                    "interactive-live-without-eval-case",
                    call_site,
                    "interactive-live call site has no eval case path in promotion coverage",
                )
            )
        if classification == "interactive-live" and not promotion_paths:
            issues.append(
                issue(
                    "warning",
                    "interactive-live-without-promotion-path",
                    call_site,
                    "interactive-live call site has no promotion record path in promotion coverage",
                )
            )
        if harness_root is not None:
            for eval_path in eval_paths:
                if path_exists(harness_root, str(eval_path)) is False:
                    issues.append(
                        issue(
                            "failure",
                            "eval-case-path-missing",
                            call_site,
                            f"eval case path missing from harness: {eval_path}",
                        )
                    )
            for promotion_path in promotion_paths:
                if path_exists(harness_root, str(promotion_path)) is False:
                    issues.append(
                        issue(
                            "warning",
                            "promotion-record-path-missing",
                            call_site,
                            f"promotion record path missing from harness: {promotion_path}",
                        )
                    )
    return issues


def build_report(
    inventory_path: Path,
    coverage_path: Path,
    *,
    harness_root: Path | None,
) -> dict[str, Any]:
    inventory = load_json(inventory_path)
    coverage = load_json(coverage_path)
    call_sites = validate_inventory(inventory)
    issues = analyse(call_sites, coverage, harness_root=harness_root)
    failures = [item for item in issues if item["severity"] == "failure"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "schema_version": "atlas-runtime-model-call-inventory-report/v1",
        "inventory": str(inventory_path),
        "coverage": str(coverage_path),
        "harness_root": str(harness_root) if harness_root else None,
        "summary": {
            "call_sites": len(call_sites),
            "issues": len(issues),
            "failures": len(failures),
            "warnings": len(warnings),
        },
        "issues": issues,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--harness-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(
        args.inventory,
        args.coverage,
        harness_root=args.harness_root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.strict and report["summary"]["failures"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
