#!/usr/bin/env python3
"""Validate the accepted Public Interface System v2 footer extension."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "atlas-control-plane/public-interface-footer-extension/v1"
VERSION = "1.1.0"
SLOTS = {"identity", "context", "evidence", "sequence", "estate_escape"}
VARIANTS = {"estate", "product", "tool", "editorial"}
CLASSIC_WRITING_SERIES = {"W-01", "W-02", "W-03", "W-04", "W-05", "W-06", "W-07"}
CLASSIC_WRITING_REPOSITORIES = {
    "AtlasReaper311/atlas-article-gen",
    "AtlasReaper311/atlas-scheduler",
    "AtlasReaper311/atlas-systems",
}
CLASSIC_WRITING_FORBIDDEN_STRUCTURE = {
    ".atlas-footer",
    ".atlas-footer--editorial",
    ".atlas-footer__identity",
    ".atlas-footer__context",
    ".atlas-footer__sequence",
    ".atlas-footer__estate-escape",
}
REQUIRED_EXCLUSIONS = {
    "interface-kit-source-changes",
    "interface-kit-release-publication",
    "consumer-source-changes",
    "generated-article-output-edits",
    "scheduler-production-execution",
    "publication-execution",
    "workflow-dispatch",
    "deployment",
    "provider-settings",
    "secrets",
    "runtime-routing",
    "content-rewriting",
    "global-navigation-redesign",
    "phase-6b",
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


def validate_footer_extension(doc: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []

    require(doc.get("schema_version") == SCHEMA_VERSION, "invalid footer extension schema", errors)
    require(doc.get("version") == VERSION, "footer extension version must be 1.1.0", errors)
    require(doc.get("status") == "accepted", "footer extension must be accepted", errors)

    authority = doc.get("authority", {})
    require(
        authority.get("decision") == "docs/adrs/ADR-0008-public-interface-system-v2.md",
        "ADR-0008 must remain the base decision authority",
        errors,
    )
    require(
        authority.get("exception_decision") == "docs/adrs/ADR-0009-classic-writing-footer-exception.md",
        "ADR-0009 must remain the classic Writing exception authority",
        errors,
    )
    require(
        authority.get("phase_record") == "docs/public-interface-phase-6-footer-authority.md",
        "Phase 6 authority record must remain explicit",
        errors,
    )
    require(
        authority.get("base_policy") == "policy/public-interface-system-v2.json",
        "base Public Interface System v2 policy must remain explicit",
        errors,
    )
    require(
        authority.get("shell_contract") == "policy/public-interface-contract.json",
        "shell contract must remain explicit",
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

    evidence = doc.get("evidence_basis", {})
    require(
        evidence.get("phase_5_closeout") == "docs/public-interface-phase-5-closeout.md",
        "Phase 5 closeout reference is invalid",
        errors,
    )
    require(
        set(evidence.get("observed_families", [])) == VARIANTS,
        "observed footer families must be estate, product, tool, and editorial",
        errors,
    )
    require(
        evidence.get("blocking_findings") == {"p0": 0, "p1": 0},
        "Phase 6 authority must keep an empty P0/P1 backlog",
        errors,
    )

    component = doc.get("component", {})
    require(component.get("role") == "footer", "footer component role is invalid", errors)
    require(component.get("selector") == ".atlas-footer", "footer selector drifted", errors)
    require(component.get("semantic_element") == "footer", "footer semantic element must be footer", errors)
    require(component.get("single_primary_footer_required") is True, "one primary footer must be required", errors)
    require(
        component.get("accessible_name_required_when_multiple") is True,
        "multiple footer landmarks require accessible names",
        errors,
    )
    require(component.get("empty_footer_forbidden") is True, "empty footers must remain forbidden", errors)
    require(component.get("empty_slots_forbidden") is True, "empty slots must remain forbidden", errors)

    slots = doc.get("slots", {})
    require(set(slots) == SLOTS, "footer slot contract is incomplete", errors)
    require(slots.get("identity", {}).get("required") is True, "identity slot must be required", errors)
    require(slots.get("estate_escape", {}).get("required") is True, "estate escape slot must be required", errors)
    require(slots.get("sequence", {}).get("required") is False, "sequence slot must remain optional globally", errors)
    require(
        slots.get("sequence", {}).get("article_owner") == "AtlasReaper311/atlas-scheduler",
        "article sequence ownership must remain with atlas-scheduler",
        errors,
    )

    variants = doc.get("variants", {})
    require(set(variants) == VARIANTS, "footer variant contract is incomplete", errors)
    expected = {
        "estate": ({"identity", "estate_escape"}, {"context", "evidence"}, {"sequence"}),
        "product": ({"identity", "estate_escape"}, {"context", "evidence"}, {"sequence"}),
        "tool": ({"identity", "context", "estate_escape"}, {"evidence"}, {"sequence"}),
        "editorial": ({"identity", "sequence", "estate_escape"}, {"context", "evidence"}, set()),
    }
    for name, (required, optional, forbidden) in expected.items():
        variant = variants.get(name, {})
        required_slots = set(variant.get("required_slots", []))
        optional_slots = set(variant.get("optional_slots", []))
        forbidden_slots = set(variant.get("forbidden_slots", []))
        require(required_slots == required, f"{name} required slots drifted", errors)
        require(optional_slots == optional, f"{name} optional slots drifted", errors)
        require(forbidden_slots == forbidden, f"{name} forbidden slots drifted", errors)
        require(
            not (required_slots & optional_slots or required_slots & forbidden_slots or optional_slots & forbidden_slots),
            f"{name} slot groups must not overlap",
            errors,
        )
        require(required_slots | optional_slots | forbidden_slots == SLOTS, f"{name} must classify every slot", errors)

    differences = doc.get("intentional_differences", {})
    require(
        set(differences) == {"classic_writing_articles"},
        "only the classic Writing article difference is accepted",
        errors,
    )
    classic = differences.get("classic_writing_articles", {})
    require(classic.get("status") == "accepted", "classic Writing difference must be accepted", errors)
    require(
        classic.get("decision") == "docs/adrs/ADR-0009-classic-writing-footer-exception.md",
        "classic Writing difference must cite ADR-0009",
        errors,
    )
    require(
        classic.get("profile") == "classic-writing-article-footer",
        "classic Writing profile drifted",
        errors,
    )
    scope = classic.get("scope", {})
    require(scope.get("surface") == "published Writing article pages", "classic Writing surface drifted", errors)
    require(
        set(scope.get("repositories", [])) == CLASSIC_WRITING_REPOSITORIES,
        "classic Writing repository scope drifted",
        errors,
    )
    require(
        set(scope.get("permanent_series", [])) == CLASSIC_WRITING_SERIES,
        "classic Writing permanent series scope drifted",
        errors,
    )
    require(
        scope.get("current_generator_output_until") == "Phase 10 editorial surface review",
        "classic Writing generator review gate drifted",
        errors,
    )
    structure = classic.get("required_structure", {})
    require(structure.get("container_element") == "div", "classic Writing container must remain div", errors)
    require(
        structure.get("container_selector") == ".article-footer",
        "classic Writing selector must remain .article-footer",
        errors,
    )
    require(
        structure.get("single_scheduler_placeholder_required") is True,
        "classic Writing shell must retain one scheduler placeholder",
        errors,
    )
    require(
        structure.get("published_content")
        == "scheduler-owned previous and next article links, or Latest article",
        "classic Writing published content drifted",
        errors,
    )
    require(
        set(classic.get("forbidden_structure", [])) == CLASSIC_WRITING_FORBIDDEN_STRUCTURE,
        "classic Writing forbidden structure drifted",
        errors,
    )
    classic_ownership = classic.get("ownership", {})
    require(
        classic_ownership.get("shell") == "AtlasReaper311/atlas-article-gen",
        "classic Writing shell ownership drifted",
        errors,
    )
    require(
        classic_ownership.get("sequence") == "AtlasReaper311/atlas-scheduler",
        "classic Writing sequence ownership drifted",
        errors,
    )
    require(
        classic_ownership.get("publication") == "AtlasReaper311/atlas-scheduler",
        "classic Writing publication ownership drifted",
        errors,
    )
    require(classic.get("non_transferable") is True, "classic Writing difference must remain non-transferable", errors)
    require(
        classic.get("interface_kit_variant_created") is False,
        "classic Writing difference must not create an interface-kit variant",
        errors,
    )

    behaviour = doc.get("behaviour", {})
    required_true = (
        "global_navigation_duplication_forbidden",
        "purpose_specific_labels_required",
        "atlas_owned_html_same_tab_required",
        "external_links_new_tab_required",
        "visible_focus_required",
        "mobile_wrap_required",
        "fixed_bottom_navigation_clearance_required",
        "reduced_motion_required",
        "remote_runtime_dependency_forbidden",
        "shared_runtime_javascript_forbidden",
    )
    for key in required_true:
        require(behaviour.get(key) is True, f"{key} must remain true", errors)
    require(behaviour.get("external_links_rel") == "noopener noreferrer", "external rel contract drifted", errors)
    require(behaviour.get("minimum_touch_target_px") == 44, "footer touch target must remain 44px", errors)

    ownership = doc.get("ownership", {})
    require(
        ownership.get("generator", {}).get("repository") == "AtlasReaper311/atlas-article-gen",
        "article generator ownership drifted",
        errors,
    )
    require(
        ownership.get("publisher", {}).get("repository") == "AtlasReaper311/atlas-scheduler",
        "scheduler ownership drifted",
        errors,
    )
    require(
        "only write path into atlas-systems" in ownership.get("publisher", {}).get("owns", []),
        "scheduler must remain the only publication write path",
        errors,
    )
    require(
        ownership.get("publisher", {}).get("production_execution_requires_separate_approval") is True,
        "scheduler production execution must remain separately approval-gated",
        errors,
    )
    consumers = ownership.get("consumers", {})
    for key in (
        "adoption_requires_separate_pull_request",
        "rollout_requires_separate_approval",
        "visual_merge_approval_required",
    ):
        require(consumers.get(key) is True, f"{key} must remain true", errors)

    distribution = doc.get("distribution", {})
    require(
        distribution.get("intended_interface_kit_release") == "0.4.0",
        "intended interface-kit release must be 0.4.0",
        errors,
    )
    for key in (
        "repository_local_assets_required",
        "fingerprint_verification_required",
        "consumer_adoption_after_immutable_release_only",
    ):
        require(distribution.get(key) is True, f"{key} must remain true", errors)

    exclusions = set(doc.get("excluded", []))
    require(REQUIRED_EXCLUSIONS.issubset(exclusions), "Phase 6 exclusions are incomplete", errors)

    return ValidationResult(tuple(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    policy_path = args.root / "policy/public-interface-footer-extension-v1.json"
    result = validate_footer_extension(load_json(policy_path))

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "schema_version": "atlas-control-plane/public-interface-footer-extension-report/v1",
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

    print("Public interface footer extension validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
