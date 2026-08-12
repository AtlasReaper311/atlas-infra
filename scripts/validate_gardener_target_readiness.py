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
EXPECTED_BATCHES = [
    {
        "order": 1,
        "id": "public-runtime-low-blast-radius",
        "risk_tier": "low",
        "repositories": [
            "AtlasReaper311/atlas-doc-viewer",
            "AtlasReaper311/atlas-quota-watch",
            "AtlasReaper311/site-pulse",
            "AtlasReaper311/specular-sonify",
            "AtlasReaper311/status",
        ],
        "required_checks": {
            "AtlasReaper311/atlas-doc-viewer": ["Static document validation"],
            "AtlasReaper311/atlas-quota-watch": ["validate"],
            "AtlasReaper311/site-pulse": ["Worker validation"],
            "AtlasReaper311/specular-sonify": [
                "Worker configuration validation"
            ],
            "AtlasReaper311/status": ["Status site validation"],
        },
    },
    {
        "order": 2,
        "id": "public-runtime-observability",
        "risk_tier": "medium",
        "repositories": [
            "AtlasReaper311/atlas-api-index",
            "AtlasReaper311/atlas-blackbox",
            "AtlasReaper311/atlas-corpus",
            "AtlasReaper311/github-pulse",
            "AtlasReaper311/specular-telemetry",
        ],
        "required_checks": {
            "AtlasReaper311/atlas-api-index": ["build"],
            "AtlasReaper311/atlas-blackbox": ["Offline Worker validation"],
            "AtlasReaper311/atlas-corpus": ["build"],
            "AtlasReaper311/github-pulse": ["Worker validation"],
            "AtlasReaper311/specular-telemetry": ["build"],
        },
    },
    {
        "order": 3,
        "id": "gardener-canary-reset",
        "risk_tier": "medium",
        "repositories": [
            "AtlasReaper311/atlas-dora",
        ],
        "required_checks": {
            "AtlasReaper311/atlas-dora": ["check"],
        },
    },
    {
        "order": 4,
        "id": "public-runtime-operations",
        "risk_tier": "medium",
        "repositories": [
            "AtlasReaper311/atlas-daily-digest",
            "AtlasReaper311/atlas-notify",
            "AtlasReaper311/deploy-watch",
            "AtlasReaper311/ramone-edge",
            "AtlasReaper311/ramone-memory",
            "AtlasReaper311/ramone-voice-trigger",
            "AtlasReaper311/specular-sentinel",
        ],
        "required_checks": {
            "AtlasReaper311/atlas-daily-digest": ["Worker validation"],
            "AtlasReaper311/atlas-notify": ["Test (Vitest)"],
            "AtlasReaper311/deploy-watch": ["Worker validation"],
            "AtlasReaper311/ramone-edge": ["Worker validation"],
            "AtlasReaper311/ramone-memory": ["build"],
            "AtlasReaper311/ramone-voice-trigger": ["build"],
            "AtlasReaper311/specular-sentinel": ["build"],
        },
    },
    {
        "order": 5,
        "id": "primary-public-surfaces",
        "risk_tier": "high",
        "repositories": [
            "AtlasReaper311/atlas-api-public",
            "AtlasReaper311/atlas-systems",
        ],
        "required_checks": {
            "AtlasReaper311/atlas-api-public": ["Test (node --test)"],
            "AtlasReaper311/atlas-systems": ["Static site validation"],
        },
    },
]
EXPECTED_BATCH_IDS = [batch["id"] for batch in EXPECTED_BATCHES]


class ReadinessPolicyError(ValueError):
    """Raised when target-readiness authority is incomplete or unsafe."""


def load_policy(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReadinessPolicyError(
            f"cannot read valid readiness policy from {path}: {error}"
        ) from error
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


def _validate_target(
    item: dict[str, Any],
    *,
    index: int,
) -> tuple[str, list[str]]:
    _require_exact_keys(item, {"repository", "required_checks"}, f"target {index}")
    repository = item["repository"]
    checks = item["required_checks"]
    if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
        raise ReadinessPolicyError(f"target {index} has an invalid repository identity")
    if (
        not isinstance(checks, list)
        or not checks
        or not all(isinstance(value, str) and value for value in checks)
    ):
        raise ReadinessPolicyError(
            f"target {repository} requires one or more named checks"
        )
    if checks != sorted(set(checks)):
        raise ReadinessPolicyError(f"target {repository} checks must be sorted and unique")
    return repository, checks


def _validate_batch(
    batch: dict[str, Any],
    *,
    index: int,
    expected: dict[str, Any],
) -> tuple[list[str], dict[str, list[str]]]:
    _require_exact_keys(batch, {"order", "id", "risk_tier", "targets"}, f"batch {index}")
    if batch["order"] != expected["order"]:
        raise ReadinessPolicyError("target-readiness batches must match the approved order")
    if batch["id"] != expected["id"]:
        raise ReadinessPolicyError("target-readiness batches must match the approved ids")
    if batch["risk_tier"] != expected["risk_tier"]:
        raise ReadinessPolicyError(
            f"target-readiness batch {batch['id']} has an unexpected risk tier"
        )

    targets = batch["targets"]
    if not isinstance(targets, list):
        raise ReadinessPolicyError(f"target-readiness batch {batch['id']} targets must be an array")

    repositories: list[str] = []
    required_checks: dict[str, list[str]] = {}
    for target_index, item in enumerate(targets):
        if not isinstance(item, dict):
            raise ReadinessPolicyError(f"batch {batch['id']} target {target_index} must be an object")
        repository, checks = _validate_target(item, index=target_index)
        repositories.append(repository)
        required_checks[repository] = checks

    if repositories != expected["repositories"]:
        raise ReadinessPolicyError(
            f"target-readiness batch {batch['id']} must match the ordered verified batch"
        )
    if required_checks != expected["required_checks"]:
        raise ReadinessPolicyError(
            f"target-readiness batch {batch['id']} required checks changed"
        )
    return repositories, required_checks


def validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(
        policy,
        {
            "schema_version",
            "authority",
            "default_branch",
            "gate_workflow_path",
            "expected_app_login",
            "target_variable",
            "disabled_value",
            "barrier_check",
            "required_repository_settings",
            "active_batch_ids",
            "future_scope",
            "batches",
        },
        "target-readiness policy",
    )
    if policy["schema_version"] != "atlas-gardener/target-readiness-policy/v2":
        raise ReadinessPolicyError("unsupported target-readiness policy schema")
    if policy["authority"] != "AtlasReaper311/atlas-infra":
        raise ReadinessPolicyError("target-readiness authority must remain atlas-infra")
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
    if policy["active_batch_ids"] != EXPECTED_BATCH_IDS:
        raise ReadinessPolicyError(
            "active Gardener batches must match the approved batch set"
        )
    if not isinstance(policy["future_scope"], str) or not policy["future_scope"].strip():
        raise ReadinessPolicyError("future_scope must describe the expansion rule")

    batches = policy["batches"]
    if not isinstance(batches, list):
        raise ReadinessPolicyError("target-readiness batches must be an array")
    if len(batches) != len(EXPECTED_BATCHES):
        raise ReadinessPolicyError(
            "target-readiness batches must match the approved batch count"
        )

    repositories: list[str] = []
    required_checks: dict[str, list[str]] = {}
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            raise ReadinessPolicyError(f"batch {index} must be an object")
        batch_repositories, batch_checks = _validate_batch(
            batch,
            index=index,
            expected=EXPECTED_BATCHES[index],
        )
        repositories.extend(batch_repositories)
        required_checks.update(batch_checks)

    if len(set(repositories)) != len(repositories):
        raise ReadinessPolicyError("target-readiness repositories must be unique")

    return {
        "schema_version": "atlas-gardener/target-readiness-policy-validation/v2",
        "status": "valid",
        "batch_count": len(batches),
        "active_batch_ids": policy["active_batch_ids"],
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
