#!/usr/bin/env python3
"""Validate the Public Interface System v2 evidence-mode extension."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "atlas-control-plane/public-interface-evidence-mode-extension/v1"
VERSION = "1.0.0"
BASELINE_COMMIT = "3971669be15d2cc26f7ba0dd0a644716578ef88d"
EVIDENCE_MODES = [
    "measured",
    "stale-measured",
    "recorded-replay",
    "simulated",
    "unavailable",
    "unknown",
    "not-applicable-unscored",
]
DIRECTORY_DATA_MODES = ["Live", "Replay", "Generated", "Simulated"]
SEMANTIC_HUE_MODES = ["measured", "stale-measured"]
NEUTRAL_MODES = [
    "recorded-replay",
    "simulated",
    "unavailable",
    "unknown",
    "not-applicable-unscored",
]
ZERO_FORBIDDEN_MODES = ["unavailable", "unknown", "not-applicable-unscored"]
EXPECTED_LABELS = {
    "measured": "Measured",
    "stale-measured": "Stale measured",
    "recorded-replay": "Recorded replay",
    "simulated": "Simulated",
    "unavailable": "Unavailable",
    "unknown": "Unknown",
    "not-applicable-unscored": "Not applicable / unscored",
}
REQUIRED_EXCLUSIONS = {
    "consumer-source-changes",
    "consumer-deployment",
    "provider-settings",
    "secrets",
    "runtime-routing",
    "endpoint-contract-changes",
    "anomaly-calculation-changes",
    "conformance-calculation-changes",
    "generated-product-output-reclassification",
    "system-symphony-scenario-palette-changes",
    "maturity-taxonomy-changes",
    "runtime-state-taxonomy-changes",
    "directory-layout-changes",
    "global-navigation-redesign",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path}")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_extension(doc: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []

    require(doc.get("schema_version") == SCHEMA_VERSION, "invalid evidence-mode extension schema", errors)
    require(doc.get("version") == VERSION, "evidence-mode extension version must be 1.0.0", errors)
    require(doc.get("status") == "accepted", "evidence-mode extension must be accepted", errors)

    authority = doc.get("authority", {})
    require(
        authority.get("decision") == "docs/adrs/ADR-0008-public-interface-system-v2.md",
        "ADR-0008 must remain the decision authority",
        errors,
    )
    require(
        authority.get("measured_extension_record")
        == "docs/public-interface-successor-evidence-mode-authority.md",
        "evidence-mode measured extension record is invalid",
        errors,
    )
    require(
        authority.get("base_policy") == "policy/public-interface-system-v2.json",
        "base Public Interface System v2 policy must remain explicit",
        errors,
    )
    require(
        authority.get("governance_repository") == "AtlasReaper311/atlas-infra",
        "atlas-infra must remain the governance owner",
        errors,
    )
    require(
        authority.get("implementation_repository") == "AtlasReaper311/atlas-interface-kit",
        "atlas-interface-kit must remain the implementation owner",
        errors,
    )

    evidence_basis = doc.get("evidence_basis", {})
    require(
        evidence_basis.get("atlas_systems_baseline_commit") == BASELINE_COMMIT,
        "evidence-mode baseline commit is invalid",
        errors,
    )
    require(
        evidence_basis.get("source_confirmed_findings") == ["LAB-007a", "LAB-007b"],
        "source-confirmed finding set must remain LAB-007a and LAB-007b",
        errors,
    )
    require(
        set(evidence_basis.get("inspected_surfaces", []))
        == {"Estate Conformance", "Shape Detector", "Lab directory", "Systems directory"},
        "inspected evidence-mode surface set is incomplete",
        errors,
    )
    require(
        len(evidence_basis.get("confirmed_failures", [])) == 3,
        "evidence basis must retain the three confirmed failures",
        errors,
    )

    taxonomies = doc.get("taxonomies", {})
    require(taxonomies.get("evidence_modes") == EVIDENCE_MODES, "evidence-mode order or values drifted", errors)
    require(
        taxonomies.get("directory_data_modes") == DIRECTORY_DATA_MODES,
        "directory data modes must remain Live, Replay, Generated, Simulated",
        errors,
    )
    require(
        taxonomies.get("generated_output_is_evidence") is False,
        "generated product output must not become evidence",
        errors,
    )
    require(
        taxonomies.get("runtime_state_is_separate_from_evidence_mode") is True,
        "runtime state and evidence mode must remain separate",
        errors,
    )
    require(
        taxonomies.get("maturity_is_separate_from_evidence_mode") is True,
        "maturity and evidence mode must remain separate",
        errors,
    )

    contracts = doc.get("mode_contracts", {})
    require(list(contracts) == EVIDENCE_MODES, "mode contracts must match the evidence-mode order", errors)
    for mode in EVIDENCE_MODES:
        contract = contracts.get(mode, {})
        require(contract.get("label") == EXPECTED_LABELS[mode], f"{mode} label is invalid", errors)
        require(bool(contract.get("definition")), f"{mode} definition is required", errors)
        require(
            contract.get("semantic_runtime_hue_permitted") is (mode in SEMANTIC_HUE_MODES),
            f"{mode} semantic runtime hue permission is invalid",
            errors,
        )
        require(
            contract.get("source_and_age_required")
            is (mode in {"measured", "stale-measured", "recorded-replay"}),
            f"{mode} source and age requirement is invalid",
            errors,
        )

    require(
        contracts.get("unavailable", {}).get("numeral_treatment") == "em-dash",
        "unavailable evidence must render an em dash instead of zero",
        errors,
    )
    require(
        contracts.get("unknown", {}).get("numeral_treatment") == "em-dash",
        "unknown evidence must render an em dash instead of zero",
        errors,
    )
    require(
        contracts.get("not-applicable-unscored", {}).get("numeral_treatment")
        == "not-applicable-or-unscored-label",
        "not-applicable or unscored evidence requires an explicit label",
        errors,
    )

    presentation = doc.get("presentation", {})
    require(
        presentation.get("evidence_bearing_operational_surfaces_only") is True,
        "strict evidence-mode presentation must remain scoped to evidence-bearing operational surfaces",
        errors,
    )
    require(presentation.get("mode_attribute") == "data-evidence-mode", "evidence mode attribute is invalid", errors)
    require(
        presentation.get("runtime_state_attribute") == "data-runtime-state",
        "runtime state attribute is invalid",
        errors,
    )
    for key in (
        "visible_mode_label_required",
        "machine_readable_mode_required",
        "fallback_mode_must_remain_visible_across_primary_state_metrics_tables_and_charts",
        "generated_product_output_may_retain_product_specific_palette",
        "directory_and_destination_vocabulary_must_agree",
        "colour_must_not_be_the_only_signal",
    ):
        require(presentation.get(key) is True, f"{key} must remain true", errors)
    require(
        presentation.get("redundant_signals")
        == ["visible-text-label", "surface-treatment", "numeral-convention"],
        "evidence modes require visible text, surface treatment, and numeral conventions",
        errors,
    )
    require(
        presentation.get("semantic_runtime_hue_modes") == SEMANTIC_HUE_MODES,
        "semantic runtime hue must remain limited to measured evidence",
        errors,
    )
    require(
        presentation.get("neutral_surface_modes") == NEUTRAL_MODES,
        "neutral evidence-mode surface set drifted",
        errors,
    )
    require(
        presentation.get("zero_may_not_represent") == ZERO_FORBIDDEN_MODES,
        "zero must not represent unavailable, unknown, or unscored evidence",
        errors,
    )

    distribution = doc.get("distribution", {})
    require(
        distribution.get("intended_interface_kit_release") == "0.5.0",
        "intended interface-kit release must be 0.5.0",
        errors,
    )
    for key in (
        "repository_local_assets_required",
        "fingerprint_verification_required",
        "consumer_adoption_requires_separate_pull_request",
        "consumer_rollout_requires_separate_approval",
        "visual_merge_approval_required",
        "shared_runtime_javascript_forbidden",
    ):
        require(distribution.get(key) is True, f"{key} must remain true", errors)

    exclusions = set(doc.get("excluded", []))
    require(REQUIRED_EXCLUSIONS.issubset(exclusions), "evidence-mode exclusions are incomplete", errors)

    return ValidationResult(tuple(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    policy_path = args.root / "policy/public-interface-evidence-mode-extension-v1.json"
    result = validate_extension(load_json(policy_path))

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "schema_version": "atlas-control-plane/public-interface-evidence-mode-extension-report/v1",
                    "valid": result.ok,
                    "errors": list(result.errors),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1

    print("Public interface evidence-mode extension validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
