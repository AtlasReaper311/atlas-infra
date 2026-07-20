#!/usr/bin/env python3
"""Load, validate, and project the canonical reliability policy.

The canonical form is one objective file per measured service under
``policy/reliability/objectives/`` plus ``policy/reliability/evaluator-config.json``.
Everything else is a deterministic projection of those files:

- ``emit-policy-document`` renders the fingerprinted ``atlas-reliability-policy/v1``
  document that the publish workflow sends to atlas-api-public;
- ``emit-status-slo`` renders the ``status`` repository's ``slo.json`` so the
  presentation surface can never drift from approved policy.

Determinism rule: identical canonical files produce byte-identical output.
``generated_at`` derives from the newest objective approval, never wall time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from .control_plane_io import canonical_json, digest_json, load_json
except ImportError:  # direct script execution
    from control_plane_io import canonical_json, digest_json, load_json

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVES_DIR = ROOT / "policy/reliability/objectives"
EVALUATOR_CONFIG = ROOT / "policy/reliability/evaluator-config.json"
OBJECTIVE_SCHEMA = ROOT / "contracts/v1/reliability-objective.schema.json"
POLICY_SCHEMA = ROOT / "policy/schemas/reliability-policy.schema.json"
FINGERPRINT_RULES = ROOT / "contracts/v1/fingerprint-rules.json"
REGISTRY = ROOT / "policy/estate-registry.json"
SERVICE_CONTRACTS = ROOT / "policy/service-contracts"

EXCLUDED_LIFECYCLES = {"deprecated", "archived"}


def _contracts_module():
    try:
        from . import control_plane_contracts
    except ImportError:  # direct script execution
        import control_plane_contracts
    return control_plane_contracts


def load_objectives(root: Path = ROOT) -> list[dict[str, Any]]:
    """Load every objective file, sorted by service_id for determinism."""
    directory = root / "policy/reliability/objectives"
    objectives = []
    for path in sorted(directory.glob("*.json")):
        objectives.append(load_json(path))
    return objectives


def validate_policy(root: Path = ROOT) -> list[str]:
    """Validate objectives, config, and cross-references. Returns errors."""
    contracts = _contracts_module()
    errors: list[str] = []
    schema = load_json(root / "contracts/v1/reliability-objective.schema.json")
    rules = load_json(root / "contracts/v1/fingerprint-rules.json")
    registry = load_json(root / "policy/estate-registry.json")
    lifecycle_by_service: dict[str, str] = {}
    for repository in registry.get("repositories", []):
        for service_id in repository.get("service_ids", []):
            lifecycle_by_service[service_id] = repository.get("lifecycle", "unknown")

    seen_services: set[str] = set()
    seen_objectives: set[str] = set()
    for path in sorted((root / "policy/reliability/objectives").glob("*.json")):
        objective = load_json(path)
        for problem in contracts.validate_instance(objective, schema):
            errors.append(f"{path.name}: {problem}")
        errors.extend(
            f"{path.name}: {problem}"
            for problem in contracts.semantic_errors(
                "reliability-objective.schema.json", objective, rules
            )
        )
        service_id = objective.get("service_id")
        if path.stem != service_id:
            errors.append(
                f"{path.name}: file name must match service_id {service_id!r}"
            )
        if service_id in seen_services:
            errors.append(f"{path.name}: duplicate service_id {service_id!r}")
        seen_services.add(service_id)
        objective_id = objective.get("objective_id")
        if objective_id in seen_objectives:
            errors.append(f"{path.name}: duplicate objective_id {objective_id!r}")
        seen_objectives.add(objective_id)
        lifecycle = lifecycle_by_service.get(service_id)
        if lifecycle in EXCLUDED_LIFECYCLES:
            errors.append(
                f"{path.name}: {lifecycle} service {service_id!r} may not carry an objective"
            )
        contract_path = root / "policy/service-contracts" / f"{service_id}.json"
        expected_ref = f"policy/reliability/objectives/{service_id}.json"
        if not contract_path.exists():
            errors.append(f"{path.name}: no service contract exists for {service_id!r}")
        else:
            contract = load_json(contract_path)
            if expected_ref not in contract.get("slo_refs", []):
                errors.append(
                    f"{path.name}: service contract slo_refs must include {expected_ref!r}"
                )

    for contract_path in sorted((root / "policy/service-contracts").glob("*.json")):
        contract = load_json(contract_path)
        for ref in contract.get("slo_refs", []):
            if not (root / ref).exists():
                errors.append(f"{contract_path.name}: slo_refs target missing: {ref}")

    config = load_json(root / "policy/reliability/evaluator-config.json")
    if config.get("schema_version") != "atlas-reliability-evaluator-config/v1":
        errors.append("evaluator-config.json: unexpected schema_version")
    for field in (
        "expected_samples_per_day",
        "result_stale_after_seconds",
        "policy_stale_after_seconds",
        "minimum_evaluation_samples",
        "remaining_budget_at_risk_fraction",
        "coverage_confidence_floor",
        "notification_cooldown_seconds",
        "storm_suppression_threshold",
        "recovery_confirmation_passes",
        "percentile_reason",
    ):
        if field not in config:
            errors.append(f"evaluator-config.json: missing {field}")
    for window in ("fast_burn", "slow_burn"):
        block = config.get(window)
        if not isinstance(block, dict) or not {
            "bucket_days",
            "minimum_samples",
            "at_risk_threshold",
        }.issubset(block):
            errors.append(f"evaluator-config.json: incomplete {window} block")

    def integral_float_errors(value: Any, path: str) -> list[str]:
        """Integral values must be integers: Python renders 2.0 where
        JavaScript renders 2, which would split the canonical fingerprint
        across the two evaluator implementations."""
        found: list[str] = []
        if isinstance(value, float) and value.is_integer():
            found.append(
                f"evaluator-config.json: {path} must be written as an integer"
                " for cross-language canonical parity"
            )
        elif isinstance(value, dict):
            for key, child in value.items():
                found.extend(integral_float_errors(child, f"{path}.{key}"))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                found.extend(integral_float_errors(child, f"{path}[{index}]"))
        return found

    errors.extend(integral_float_errors(config, "$"))
    return sorted(errors)


def build_unmeasured(root: Path = ROOT) -> list[dict[str, str]]:
    """Runtime services without an approved objective, each with its reason."""
    registry = load_json(root / "policy/estate-registry.json")
    measured = {path.stem for path in (root / "policy/reliability/objectives").glob("*.json")}
    unmeasured = []
    for repository in registry.get("repositories", []):
        if not repository.get("runtime_service"):
            continue
        lifecycle = repository.get("lifecycle", "unknown")
        for service_id in repository.get("service_ids", []):
            if service_id in measured:
                continue
            if lifecycle in EXCLUDED_LIFECYCLES:
                reason = f"{lifecycle} lifecycle; excluded from reliability objectives"
            else:
                reason = "no approved objective; service remains explicitly unmeasured"
            unmeasured.append({"service_id": service_id, "reason": reason})
    return sorted(unmeasured, key=lambda item: item["service_id"])


def build_policy_document(root: Path = ROOT, commit: str | None = None) -> dict[str, Any]:
    """Render the deterministic published policy document."""
    objectives = load_objectives(root)
    config = load_json(root / "policy/reliability/evaluator-config.json")
    generated_at = max(
        objective["provenance"]["approved_at"] for objective in objectives
    )
    source: dict[str, Any] = {
        "repository": "AtlasReaper311/atlas-infra",
        "path": "policy/reliability",
    }
    if commit:
        source["commit"] = commit
    document: dict[str, Any] = {
        "schema": "atlas-reliability-policy/v1",
        "generated_at": generated_at,
        "source": source,
        "evaluator_config": config,
        "objectives": objectives,
        "unmeasured": build_unmeasured(root),
    }
    document["fingerprint"] = digest_json(document)
    return document


def build_status_slo(root: Path = ROOT) -> dict[str, Any]:
    """Render the status repository slo.json projection."""
    objectives = load_objectives(root)
    policy = build_policy_document(root)
    ordered = sorted(
        objectives,
        key=lambda item: (item["display"].get("order", 99), item["service_id"]),
    )
    window_days = {objective["window_days"] for objective in ordered}
    if len(window_days) != 1:
        raise ValueError("objectives disagree on window_days; slo.json needs one window")
    services = []
    for objective in ordered:
        service: dict[str, Any] = {
            "id": objective["service_id"],
            "component": objective["measurement_source"]["component"],
            "target_pct": objective["target_pct"],
            "sub": objective["display"]["label"],
            "domain": objective["display"]["domain"],
        }
        if "note" in objective["display"]:
            service["note"] = objective["display"]["note"]
        services.append(service)
    return {
        "window_days": window_days.pop(),
        "generated_from": "AtlasReaper311/atlas-infra:policy/reliability",
        "policy_fingerprint": policy["fingerprint"],
        "services": services,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("validate", "emit-policy-document", "emit-status-slo"),
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--commit", help="full commit SHA recorded in the published source block")
    args = parser.parse_args(argv)

    errors = validate_policy(args.root)
    if errors:
        for problem in errors:
            print(f"ERROR {problem}", file=sys.stderr)
        return 1
    if args.command == "validate":
        objectives = load_objectives(args.root)
        print(f"reliability policy: {len(objectives)} objectives valid")
        return 0

    if args.command == "emit-policy-document":
        document = build_policy_document(args.root, commit=args.commit)
        contracts = _contracts_module()
        schema = load_json(args.root / "policy/schemas/reliability-policy.schema.json")
        schema_errors = contracts.validate_instance(document, schema)
        if schema_errors:
            for problem in schema_errors:
                print(f"ERROR policy document: {problem}", file=sys.stderr)
            return 1
    else:
        document = build_status_slo(args.root)

    rendered = json.dumps(document, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
