#!/usr/bin/env python3
"""Validate the fail-closed Atlas Gardener automatic-remediation authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy/gardener-automation.json"
DEFAULT_COVERAGE = ROOT / "policy/gardener-github-app-coverage.json"
EXPECTED_MODES = ["disabled", "observe", "pr-only", "automerge-low-risk"]
EXPECTED_FIXERS = {
    "action-pin-plan",
    "macos-metadata-ignore",
    "python-cache-ignore",
    "workflow-permissions",
    "workflow-timeout",
}
AUTO_FIXERS = {"macos-metadata-ignore", "python-cache-ignore"}
EXPECTED_PERMISSIONS = {
    "metadata": "read",
    "contents": "write",
    "pull_requests": "write",
}


class PolicyError(ValueError):
    """Raised when automatic-remediation authority is incomplete or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PolicyError(f"cannot read valid JSON object from {path}: {error}") from error
    if not isinstance(value, dict):
        raise PolicyError(f"{path} must contain a JSON object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise PolicyError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise PolicyError(f"{label} has unknown fields: {', '.join(unknown)}")


def validate_policy(policy: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(
        policy,
        {
            "schema_version",
            "authority",
            "default_mode",
            "allowed_modes",
            "write_gate_variable",
            "write_gate_enabled_value",
            "mode_variable",
            "public_coverage_policy",
            "public_coverage_source_fingerprint",
            "finding_bundle",
            "repository_eligibility",
            "fixers",
            "automatic_merge_limits",
            "forbidden_path_prefixes",
            "forbidden_exact_paths",
            "approval_ttl_hours",
            "evidence_retention_days",
            "notification_cooldown_hours",
            "scheduling",
        },
        "automation policy",
    )
    if policy["schema_version"] != "atlas-gardener/automation-policy/v1":
        raise PolicyError("unsupported automation policy schema")
    if policy["authority"] != "AtlasReaper311/atlas-infra":
        raise PolicyError("automation authority must remain AtlasReaper311/atlas-infra")
    if policy["default_mode"] != "disabled":
        raise PolicyError("default source mode must be disabled")
    if policy["allowed_modes"] != EXPECTED_MODES:
        raise PolicyError("allowed modes must be the exact ordered v1 mode set")
    if policy["mode_variable"] != "ATLAS_GARDENER_MODE":
        raise PolicyError("unexpected controller mode variable")
    if policy["write_gate_variable"] != "ATLAS_GARDENER_WRITE_GATE":
        raise PolicyError("unexpected write-gate variable")
    if policy["write_gate_enabled_value"] != "enabled":
        raise PolicyError("write gate must require the exact value 'enabled'")

    bundle = policy["finding_bundle"]
    _require_exact_keys(
        bundle,
        {
            "producer",
            "workflow",
            "maximum_age_hours",
            "public_only",
            "require_attestation",
            "maximum_findings",
        },
        "finding bundle policy",
    )
    if bundle["producer"] != "AtlasReaper311/atlas-dep-audit":
        raise PolicyError("finding producer must remain atlas-dep-audit")
    if bundle["workflow"] != ".github/workflows/audit.yml":
        raise PolicyError("finding workflow must remain the scheduled audit workflow")
    if bundle["public_only"] is not True or bundle["require_attestation"] is not True:
        raise PolicyError("public finding handoff must be public-only and attested")
    if not isinstance(bundle["maximum_age_hours"], int) or not 1 <= bundle["maximum_age_hours"] <= 168:
        raise PolicyError("finding bundle maximum age is outside the bounded range")
    if not isinstance(bundle["maximum_findings"], int) or not 1 <= bundle["maximum_findings"] <= 1000:
        raise PolicyError("finding bundle count is outside the bounded range")

    repository_policy = policy["repository_eligibility"]
    if repository_policy != {
        "lifecycles": ["active", "production"],
        "scopes": ["internal", "public"],
        "provenance": ["original"],
        "require_verified_public_coverage": True,
        "private_repository_policy": "source-owned-separate-approval",
    }:
        raise PolicyError("repository eligibility is broader than the approved public v1 boundary")

    fixers = policy["fixers"]
    if set(fixers) != EXPECTED_FIXERS:
        raise PolicyError("fixer policy must cover exactly the five allowlisted fixers")
    for fixer_id, fixer in fixers.items():
        _require_exact_keys(
            fixer,
            {
                "risk_class",
                "minimum_mode",
                "automatic_merge",
                "automatic_merge_paths",
                "automatic_merge_added_lines",
            },
            f"fixer {fixer_id}",
        )
        if fixer_id in AUTO_FIXERS:
            if fixer["risk_class"] != "low" or fixer["automatic_merge"] is not True:
                raise PolicyError(f"{fixer_id} must be the only low-risk automatic fixer class")
            if fixer["automatic_merge_paths"] != [".gitignore"]:
                raise PolicyError(f"{fixer_id} automatic merge must be .gitignore-only")
            if not fixer["automatic_merge_added_lines"]:
                raise PolicyError(f"{fixer_id} requires an exact added-line allowlist")
        else:
            if fixer["risk_class"] != "review-required" or fixer["automatic_merge"] is not False:
                raise PolicyError(f"{fixer_id} must remain review-only")
            if fixer["automatic_merge_paths"] or fixer["automatic_merge_added_lines"]:
                raise PolicyError(f"{fixer_id} cannot declare automatic-merge output")

    limits = policy["automatic_merge_limits"]
    if limits["maximum_changed_files"] != 1:
        raise PolicyError("automatic merge must change exactly one file at most")
    if not isinstance(limits["maximum_changed_lines"], int) or not 1 <= limits["maximum_changed_lines"] <= 2:
        raise PolicyError("automatic merge line limit must be one or two")
    for required_true in (
        "additions_only",
        "forbid_binary",
        "forbid_symlink",
        "forbid_generated_output",
        "require_exact_base_sha",
        "require_exact_head_sha",
        "require_unchanged_patch_digest",
        "require_required_checks",
        "delete_gardener_branch",
    ):
        if limits.get(required_true) is not True:
            raise PolicyError(f"automatic merge must require {required_true}")
    if limits.get("allowed_file_modes") != ["100644"]:
        raise PolicyError("automatic merge must allow only normal non-executable files")
    if limits.get("merge_method") != "squash":
        raise PolicyError("automatic merge method must remain squash")

    forbidden_prefixes = policy["forbidden_path_prefixes"]
    forbidden_paths = policy["forbidden_exact_paths"]
    if forbidden_prefixes != sorted(set(forbidden_prefixes)):
        raise PolicyError("forbidden path prefixes must be sorted and unique")
    if forbidden_paths != sorted(set(forbidden_paths)):
        raise PolicyError("forbidden exact paths must be sorted and unique")
    for required in (".github/workflows/", "src/", "migrations/", "dist/"):
        if required not in forbidden_prefixes:
            raise PolicyError(f"required forbidden prefix is missing: {required}")
    for required in ("package.json", "package-lock.json", "wrangler.toml", "pyproject.toml"):
        if required not in forbidden_paths:
            raise PolicyError(f"required forbidden path is missing: {required}")

    if policy["approval_ttl_hours"] > 24:
        raise PolicyError("automation approvals cannot live longer than 24 hours")
    if not 1 <= policy["evidence_retention_days"] <= 30:
        raise PolicyError("controller evidence retention must be between one and 30 days")
    if not 1 <= policy["notification_cooldown_hours"] <= 168:
        raise PolicyError("notification cooldown is outside the bounded range")
    if policy["scheduling"] != {
        "controller_cron": "15 10 * * *",
        "audit_cron": "41 8 * * 1",
        "monday_ingest": True,
        "daily_reconciliation": True,
    }:
        raise PolicyError("automation scheduling no longer matches the approved audit cadence")

    if coverage.get("schema_version") != "atlas-gardener/github-app-coverage/v1":
        raise PolicyError("unsupported GitHub App coverage policy")
    if coverage.get("installation_mode") != "selected-repositories":
        raise PolicyError("GitHub App must remain in selected-repository mode")
    if coverage.get("permissions") != EXPECTED_PERMISSIONS:
        raise PolicyError("GitHub App permission boundary changed")
    if coverage.get("coverage_count") != 20:
        raise PolicyError("public runtime coverage must contain exactly 20 repositories")
    repositories: list[str] = [coverage["canary"]["repository"]]
    if coverage["canary"].get("status") != "verified":
        raise PolicyError("Gardener canary coverage is not verified")
    for batch in coverage.get("batches", []):
        if batch.get("status") != "verified":
            raise PolicyError(f"coverage batch is not verified: {batch.get('id', 'unknown')}")
        repositories.extend(batch.get("repositories", []))
    if len(repositories) != 20 or len(set(repositories)) != 20:
        raise PolicyError("coverage repository identities are incomplete or duplicated")
    if policy["public_coverage_source_fingerprint"] != coverage.get("source_fingerprint"):
        raise PolicyError("automation policy is not bound to the current coverage source fingerprint")

    return {
        "schema_version": "atlas-gardener/automation-policy-validation/v1",
        "status": "valid",
        "policy_digest": digest_json(policy),
        "coverage_digest": digest_json(coverage),
        "coverage_count": len(repositories),
        "automatic_fixers": sorted(AUTO_FIXERS),
        "review_only_fixers": sorted(EXPECTED_FIXERS - AUTO_FIXERS),
        "default_mode": policy["default_mode"],
        "provider_mutations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    try:
        report = validate_policy(load_object(args.policy), load_object(args.coverage))
    except PolicyError as error:
        print(f"Gardener automation authority invalid: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    if not args.quiet:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
