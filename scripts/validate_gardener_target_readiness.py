#!/usr/bin/env python3
"""Validate the committed Atlas Gardener target-readiness policy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy/gardener-target-readiness.json"
EXPECTED_REPOSITORIES = [
    "AtlasReaper311/atlas-doc-viewer",
    "AtlasReaper311/atlas-quota-watch",
    "AtlasReaper311/site-pulse",
    "AtlasReaper311/specular-sonify",
    "AtlasReaper311/status",
]


class ReadinessPolicyError(ValueError):
    """Raised when target-readiness authority is incomplete or unsafe."""


def load_policy(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReadinessPolicyError(f"cannot read valid readiness policy from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ReadinessPolicyError("target-readiness policy must be a JSON object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise ReadinessPolicyError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ReadinessPolicyError(f"{label} has unknown fields: {', '.join(unknown)}")


def validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(
        policy,
        {
            "schema_version",
            "authority",
            "batch_id",
            "default_branch",
            "gate_workflow_path",
            "expected_app_login",
            "target_variable",
            "disabled_value",
            "barrier_check",
            "required_repository_settings",
            "targets",
        },
        "target-readiness policy",
    )
    if policy["schema_version"] != "atlas-gardener/target-readiness-policy/v1":
        raise ReadinessPolicyError("unsupported target-readiness policy schema")
    if policy["authority"] != "AtlasReaper311/atlas-infra":
        raise ReadinessPolicyError("target-readiness authority must remain atlas-infra")
    if policy["batch_id"] != "public-runtime-low-blast-radius":
        raise ReadinessPolicyError("production readiness must begin with the verified low-blast-radius batch")
    if policy["default_branch"] != "main":
        raise ReadinessPolicyError("target-readiness default branch must remain main")
    if policy["gate_workflow_path"] != ".github/workflows/gardener-remediation-gate.yml":
        raise ReadinessPolicyError("unexpected target gate workflow path")
    if policy["expected_app_login"] != "atlas-gardener-w37-atlasreaper[bot]":
        raise ReadinessPolicyError("unexpected Gardener App identity")
    if policy["target_variable"] != "ATLAS_GARDENER_AUTOMERGE_ENABLED":
        raise ReadinessPolicyError("unexpected target auto-merge variable")
    if policy["disabled_value"] != "false":
        raise ReadinessPolicyError("target auto-merge variable must be disabled at rest")
    if policy["barrier_check"] != "Gardener native auto-merge barrier":
        raise ReadinessPolicyError("unexpected native auto-merge barrier check")
    if policy["required_repository_settings"] != {
        "allow_squash_merge": True,
        "allow_auto_merge_at_rest": False,
    }:
        raise ReadinessPolicyError("repository readiness settings are broader than approved")

    targets = policy["targets"]
    if not isinstance(targets, list):
        raise ReadinessPolicyError("target-readiness targets must be an array")
    repositories: list[str] = []
    required_checks: dict[str, list[str]] = {}
    for index, item in enumerate(targets):
        if not isinstance(item, dict):
            raise ReadinessPolicyError(f"target {index} must be an object")
        _require_exact_keys(item, {"repository", "required_checks"}, f"target {index}")
        repository = item["repository"]
        checks = item["required_checks"]
        if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
            raise ReadinessPolicyError(f"target {index} has an invalid repository identity")
        if not isinstance(checks, list) or not checks or not all(isinstance(value, str) and value for value in checks):
            raise ReadinessPolicyError(f"target {repository} requires one or more named checks")
        if checks != sorted(set(checks)):
            raise ReadinessPolicyError(f"target {repository} checks must be sorted and unique")
        repositories.append(repository)
        required_checks[repository] = checks

    if repositories != EXPECTED_REPOSITORIES:
        raise ReadinessPolicyError("target-readiness repositories must match the ordered verified batch-one set")
    if len(set(repositories)) != len(repositories):
        raise ReadinessPolicyError("target-readiness repositories must be unique")

    return {
        "schema_version": "atlas-gardener/target-readiness-policy-validation/v1",
        "status": "valid",
        "batch_id": policy["batch_id"],
        "target_count": len(repositories),
        "repositories": repositories,
        "required_checks": required_checks,
        "provider_mutations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    try:
        report = validate_policy(load_policy(args.policy))
    except ReadinessPolicyError as error:
        print(f"Gardener target-readiness policy invalid: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    if not args.quiet:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
