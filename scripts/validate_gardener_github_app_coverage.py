#!/usr/bin/env python3
"""Validate the public Atlas Gardener GitHub App coverage policy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_POLICY = Path("policy/gardener-github-app-coverage.json")
DEFAULT_REGISTRY = Path("policy/estate-registry.json")
POLICY_SCHEMA = "atlas-gardener/github-app-coverage/v1"
REGISTRY_SCHEMA = "atlas-contract-registry/estate-registry/v1"
REPORT_SCHEMA = "atlas-gardener/github-app-coverage-report/v1"
EXPECTED_AUTHORITY = "AtlasReaper311/atlas-infra"
EXPECTED_SOURCE = "policy/estate-registry.json"
EXPECTED_PERMISSIONS = {
    "metadata": "read",
    "contents": "write",
    "pull_requests": "write",
}
FORBIDDEN_LIFECYCLES = {"archived", "deprecated"}
ALLOWED_BATCH_STATUSES = {"verified", "ready", "planned", "separate-approval"}
ALLOWED_RISK_TIERS = {"low", "medium", "high"}


class CoveragePolicyError(ValueError):
    """Raised when the coverage policy or its authority is invalid."""


def load_object(path: Path) -> dict[str, Any]:
    """Load one UTF-8 JSON object."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CoveragePolicyError(f"cannot read valid JSON object: {path}") from error
    if not isinstance(value, dict):
        raise CoveragePolicyError(f"JSON object required: {path}")
    return value


def _eligible_registry_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise CoveragePolicyError("unsupported estate registry schema")
    values = registry.get("repositories")
    if not isinstance(values, list):
        raise CoveragePolicyError("estate registry repositories must be a list")

    entries: list[dict[str, Any]] = []
    identities: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            raise CoveragePolicyError("estate registry entry must be an object")
        repository = value.get("repository")
        lifecycle = value.get("lifecycle")
        scope = value.get("scope")
        provenance = value.get("provenance")
        runtime_service = value.get("runtime_service")
        if not isinstance(repository, str) or not repository.startswith(
            "AtlasReaper311/"
        ):
            raise CoveragePolicyError("estate registry repository identity is malformed")
        if repository in identities:
            raise CoveragePolicyError(f"duplicate estate registry repository: {repository}")
        identities.add(repository)
        if not all(
            isinstance(item, str) and item
            for item in (lifecycle, scope, provenance)
        ):
            raise CoveragePolicyError(
                f"estate registry classification is malformed for {repository}"
            )
        if runtime_service is not True:
            raise CoveragePolicyError(
                f"estate registry contains non-runtime repository: {repository}"
            )
        if lifecycle in FORBIDDEN_LIFECYCLES or provenance == "external-derived":
            continue
        entries.append(
            {
                "repository": repository,
                "lifecycle": lifecycle,
                "scope": scope,
                "provenance": provenance,
                "runtime_service": True,
            }
        )
    return sorted(entries, key=lambda item: item["repository"])


def source_fingerprint(entries: list[dict[str, Any]]) -> str:
    """Fingerprint the complete eligible public runtime classification set."""

    material = json.dumps(
        {"repositories": entries},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def validate_coverage(
    policy: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    """Validate complete, unique, phased public runtime coverage."""

    expected_keys = {
        "schema_version",
        "authority",
        "source_registry",
        "installation_mode",
        "permissions",
        "source_fingerprint",
        "coverage_count",
        "canary",
        "batches",
        "private_repository_policy",
    }
    if set(policy) != expected_keys:
        raise CoveragePolicyError("coverage policy contains missing or unexpected fields")
    if policy.get("schema_version") != POLICY_SCHEMA:
        raise CoveragePolicyError("unsupported Gardener coverage policy schema")
    if policy.get("authority") != EXPECTED_AUTHORITY:
        raise CoveragePolicyError("Gardener coverage authority must remain Atlas Infra")
    if policy.get("source_registry") != EXPECTED_SOURCE:
        raise CoveragePolicyError("Gardener coverage must use the public runtime registry")
    if policy.get("installation_mode") != "selected-repositories":
        raise CoveragePolicyError("GitHub App installation must use selected repositories")
    if policy.get("permissions") != EXPECTED_PERMISSIONS:
        raise CoveragePolicyError("GitHub App permission contract changed")
    if policy.get("private_repository_policy") != "source-owned-separate-approval":
        raise CoveragePolicyError("private repository coverage boundary changed")

    eligible_entries = _eligible_registry_entries(registry)
    eligible = {item["repository"] for item in eligible_entries}
    fingerprint = source_fingerprint(eligible_entries)
    if policy.get("source_fingerprint") != fingerprint:
        raise CoveragePolicyError(
            "coverage source fingerprint differs from the authoritative registry"
        )

    canary = policy.get("canary")
    if not isinstance(canary, dict) or set(canary) != {"repository", "status"}:
        raise CoveragePolicyError("coverage canary is malformed")
    if canary.get("status") != "verified":
        raise CoveragePolicyError("coverage canary must be verified before expansion")
    canary_repository = canary.get("repository")
    if not isinstance(canary_repository, str):
        raise CoveragePolicyError("coverage canary repository is malformed")

    batches = policy.get("batches")
    if not isinstance(batches, list) or not batches:
        raise CoveragePolicyError("at least one coverage batch is required")

    covered = [canary_repository]
    batch_ids: set[str] = set()
    orders: list[int] = []
    ready_count = 0
    non_verified_seen = False
    report_batches: list[dict[str, Any]] = []

    for batch in batches:
        if not isinstance(batch, dict) or set(batch) != {
            "order",
            "id",
            "status",
            "risk_tier",
            "repositories",
        }:
            raise CoveragePolicyError("coverage batch is malformed")
        order = batch.get("order")
        batch_id = batch.get("id")
        status = batch.get("status")
        risk_tier = batch.get("risk_tier")
        repositories = batch.get("repositories")
        if not isinstance(order, int) or order < 1:
            raise CoveragePolicyError("coverage batch order is malformed")
        if not isinstance(batch_id, str) or not batch_id:
            raise CoveragePolicyError("coverage batch ID is malformed")
        if batch_id in batch_ids:
            raise CoveragePolicyError(f"duplicate coverage batch ID: {batch_id}")
        batch_ids.add(batch_id)
        orders.append(order)
        if status not in ALLOWED_BATCH_STATUSES:
            raise CoveragePolicyError(f"invalid coverage batch status: {batch_id}")
        if risk_tier not in ALLOWED_RISK_TIERS:
            raise CoveragePolicyError(f"invalid coverage batch risk tier: {batch_id}")
        if not isinstance(repositories, list) or not repositories:
            raise CoveragePolicyError(f"coverage batch is empty: {batch_id}")
        if not all(isinstance(repository, str) for repository in repositories):
            raise CoveragePolicyError(
                f"coverage batch contains malformed repository identity: {batch_id}"
            )
        if repositories != sorted(repositories):
            raise CoveragePolicyError(
                f"coverage batch repositories must be sorted: {batch_id}"
            )
        if len(repositories) != len(set(repositories)):
            raise CoveragePolicyError(
                f"coverage batch contains duplicate repositories: {batch_id}"
            )
        if status == "ready":
            ready_count += 1
        if status != "verified":
            non_verified_seen = True
        elif non_verified_seen:
            raise CoveragePolicyError(
                "verified coverage batches must precede unverified batches"
            )
        covered.extend(repositories)
        report_batches.append(
            {
                "order": order,
                "id": batch_id,
                "status": status,
                "risk_tier": risk_tier,
                "repository_count": len(repositories),
            }
        )

    if orders != list(range(1, len(batches) + 1)):
        raise CoveragePolicyError("coverage batch order must be contiguous and canonical")
    if ready_count > 1:
        raise CoveragePolicyError("only one coverage batch may be ready at a time")
    if len(covered) != len(set(covered)):
        raise CoveragePolicyError("coverage policy contains duplicate repository identities")
    coverage_count = policy.get("coverage_count")
    if coverage_count != len(covered):
        raise CoveragePolicyError("coverage count does not match the phased repository set")

    actual = set(covered)
    missing = sorted(eligible - actual)
    unexpected = sorted(actual - eligible)
    if missing:
        raise CoveragePolicyError(
            "eligible public runtime repositories missing from coverage: "
            + ", ".join(missing)
        )
    if unexpected:
        raise CoveragePolicyError(
            "coverage contains repositories outside public runtime authority: "
            + ", ".join(unexpected)
        )

    return {
        "schema_version": REPORT_SCHEMA,
        "status": "valid",
        "authority": EXPECTED_AUTHORITY,
        "installation_mode": "selected-repositories",
        "permissions": EXPECTED_PERMISSIONS,
        "source_fingerprint": fingerprint,
        "coverage_count": len(covered),
        "canary": canary,
        "batches": report_batches,
        "ready_batch_count": ready_count,
        "private_repository_policy": "source-owned-separate-approval",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate phased public coverage for the Atlas Gardener GitHub App."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = validate_coverage(load_object(args.policy), load_object(args.registry))
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    if not args.quiet:
        print(
            "Gardener GitHub App coverage verified: "
            f"{report['coverage_count']} public runtime repositories, "
            f"{report['ready_batch_count']} ready batch"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
