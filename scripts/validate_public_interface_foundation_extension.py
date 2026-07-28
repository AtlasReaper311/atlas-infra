#!/usr/bin/env python3
"""Validate the measured Public Interface System v2 foundation extension."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "atlas-control-plane/public-interface-foundation-extension/v1"
VERSION = "1.0.0"
BLOCKING_VIEWPORTS = [320, 375, 768, 1024, 1440]
REPORTING_VIEWPORTS = [1920]
REQUIRED_EXCLUSIONS = {
    "footer-slots-and-variants",
    "consumer-touch-target-remediation",
    "colour-token-changes",
    "spacing-token-changes",
    "typography-token-changes",
    "breakpoint-token-changes",
    "consumer-source-changes",
    "provider-settings",
    "secrets",
    "runtime-routing",
    "model-or-inference-behaviour",
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

    require(doc.get("schema_version") == SCHEMA_VERSION, "invalid extension schema", errors)
    require(doc.get("version") == VERSION, "extension version must be 1.0.0", errors)
    require(doc.get("status") == "accepted", "extension must be accepted", errors)

    authority = doc.get("authority", {})
    require(
        authority.get("decision") == "docs/adrs/ADR-0008-public-interface-system-v2.md",
        "ADR-0008 must remain the decision authority",
        errors,
    )
    require(
        authority.get("base_policy") == "policy/public-interface-system-v2.json",
        "base Public Interface System v2 policy must remain explicit",
        errors,
    )
    require(
        authority.get("implementation_repository") == "AtlasReaper311/atlas-interface-kit",
        "interface-kit must remain the implementation owner",
        errors,
    )

    evidence_basis = doc.get("evidence_basis", {})
    blocking = evidence_basis.get("blocking_findings", {})
    require(blocking == {"p0": 0, "p1": 0}, "Phase 4 must start with an empty P0/P1 backlog", errors)
    require(
        evidence_basis.get("atlas_systems_phase_2_pull_request") == "AtlasReaper311/atlas-systems#168",
        "Phase 2 evidence reference is invalid",
        errors,
    )
    require(
        evidence_basis.get("phase_3_closeout") == "docs/public-interface-phase-3-closeout.md",
        "Phase 3 closeout reference is invalid",
        errors,
    )

    components = doc.get("components", {})
    breadcrumbs = components.get("breadcrumb_navigation", {})
    require(breadcrumbs.get("role") == "breadcrumb-navigation", "breadcrumb role is invalid", errors)
    require(breadcrumbs.get("required") is False, "breadcrumbs must remain optional", errors)
    require(breadcrumbs.get("landmark") == "nav", "breadcrumbs require a nav landmark", errors)
    require(breadcrumbs.get("accessible_name_required") is True, "breadcrumbs require an accessible name", errors)
    require(breadcrumbs.get("ordered_list_required") is True, "breadcrumbs require an ordered list", errors)
    require(breadcrumbs.get("homepage_forbidden") is True, "homepage breadcrumbs must remain forbidden", errors)
    require(
        breadcrumbs.get("machine_surfaces_excluded") is True,
        "machine surfaces must remain excluded from breadcrumbs",
        errors,
    )

    announcement = components.get("status_announcement", {})
    require(announcement.get("role") == "status-announcement", "status announcement role is invalid", errors)
    require(announcement.get("required") is False, "status announcements must remain optional", errors)
    require(
        announcement.get("default_semantics")
        == {"role": "status", "aria_live": "polite", "aria_atomic": "true"},
        "default status-announcement semantics drifted",
        errors,
    )
    require(
        announcement.get("blocking_failure_semantics")
        == {"role": "alert", "use": "immediate-blocking-failure-only"},
        "alert semantics must remain bounded to immediate blocking failures",
        errors,
    )
    require(
        announcement.get("silent_on") == ["initial-poll", "unchanged-poll", "routine-refresh"],
        "routine polling must remain silent",
        errors,
    )
    require(
        announcement.get("shared_runtime_javascript_forbidden") is True,
        "shared runtime JavaScript must remain forbidden",
        errors,
    )
    require(
        announcement.get("global_header_status_remains_aria_live_off") is True,
        "global header status must remain aria-live off",
        errors,
    )

    overflow = components.get("dense_data_overflow", {})
    require(overflow.get("extends_role") == "table-wrapper", "dense overflow must extend table-wrapper", errors)
    require(
        overflow.get("when_overflowing")
        == {
            "accessible_name_required": True,
            "keyboard_focus_required": True,
            "visible_focus_required": True,
            "local_horizontal_scroll_required": True,
        },
        "overflow semantics drifted",
        errors,
    )
    require(
        overflow.get("when_not_overflowing") == {"unnecessary_tab_stop_forbidden": True},
        "non-overflowing regions must not add unnecessary tab stops",
        errors,
    )

    evidence = doc.get("evidence", {})
    require(evidence.get("blocking_viewports_px") == BLOCKING_VIEWPORTS, "blocking viewport matrix drifted", errors)
    require(
        evidence.get("reporting_only_viewports_px") == REPORTING_VIEWPORTS,
        "1920 must remain the only reporting-only viewport",
        errors,
    )
    for key in (
        "reporting_only_is_breakpoint",
        "reporting_only_is_budget",
        "reporting_only_changes_content_width",
        "reporting_only_changes_layout_tokens",
    ):
        require(evidence.get(key) is False, f"{key} must remain false", errors)

    distribution = doc.get("distribution", {})
    require(
        distribution.get("intended_interface_kit_release") == "0.3.0",
        "intended interface-kit release must be 0.3.0",
        errors,
    )
    for key in (
        "repository_local_assets_required",
        "remote_runtime_dependency_forbidden",
        "consumer_adoption_requires_separate_pull_request",
        "consumer_rollout_requires_separate_approval",
        "visual_merge_approval_required",
    ):
        require(distribution.get(key) is True, f"{key} must remain true", errors)

    exclusions = set(doc.get("excluded", []))
    require(REQUIRED_EXCLUSIONS.issubset(exclusions), "Phase 4 exclusions are incomplete", errors)

    return ValidationResult(tuple(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    policy_path = args.root / "policy/public-interface-foundation-extension-v1.json"
    result = validate_extension(load_json(policy_path))

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "schema_version": "atlas-control-plane/public-interface-foundation-extension-report/v1",
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

    print("Public interface foundation extension validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
