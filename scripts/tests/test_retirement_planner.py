from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import retirement_planner


class RetirementPlannerTests(unittest.TestCase):
    def test_current_public_service_is_blocked_by_live_declarations(self) -> None:
        plan = retirement_planner.build_plan(
            ROOT,
            kind="service",
            identifier="atlas-api-index",
        )
        self.assertFalse(plan["eligible_for_owner_retirement_review"])
        self.assertEqual("none", plan["execution_authority"])
        self.assertEqual("failed", plan["evidence"]["routes_clear"])
        self.assertEqual("failed", plan["evidence"]["manifest_clear"])
        self.assertEqual("failed", plan["evidence"]["worker_allowlist_clear"])
        self.assertTrue(plan["blockers"]["routes_clear"])

    def test_current_repository_plan_aggregates_service_blockers(self) -> None:
        plan = retirement_planner.build_plan(
            ROOT,
            kind="repository",
            identifier="AtlasReaper311/atlas-api-public",
        )
        self.assertEqual(
            {"kind": "repository", "repository": "AtlasReaper311/atlas-api-public"},
            plan["subject"],
        )
        self.assertFalse(plan["eligible_for_owner_retirement_review"])
        self.assertEqual("failed", plan["evidence"]["manifest_clear"])
        self.assertEqual("failed", plan["evidence"]["worker_allowlist_clear"])

    def test_unknown_subject_fails_closed(self) -> None:
        with self.assertRaisesRegex(retirement_planner.RetirementPlanError, "unknown service_id"):
            retirement_planner.build_plan(
                ROOT,
                kind="service",
                identifier="does-not-exist",
            )

    def test_external_evidence_cannot_override_current_public_allowlist(self) -> None:
        payload = {
            "schema_version": "atlas-retirement-external-evidence/v1",
            "subject": {"kind": "service", "service_id": "atlas-api-index"},
            "worker_allowlist_clear": "verified",
            "production_prs_clear": "verified",
            "historical_evidence_preserved": "verified",
            "recovery_handled": "not-applicable",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                retirement_planner.RetirementPlanError,
                "cannot clear worker_allowlist_clear",
            ):
                retirement_planner.build_plan(
                    ROOT,
                    kind="service",
                    identifier="atlas-api-index",
                    external_evidence=path,
                )

    def test_external_evidence_subject_must_match(self) -> None:
        payload = {
            "schema_version": "atlas-retirement-external-evidence/v1",
            "subject": {"kind": "service", "service_id": "wrong-service"},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                retirement_planner.RetirementPlanError,
                "subject does not match",
            ):
                retirement_planner.build_plan(
                    ROOT,
                    kind="service",
                    identifier="atlas-api-index",
                    external_evidence=path,
                )

    def test_markdown_never_claims_execution_authority(self) -> None:
        plan = retirement_planner.build_plan(
            ROOT,
            kind="service",
            identifier="atlas-api-index",
        )
        markdown = retirement_planner.render_markdown(plan)
        self.assertIn("Execution authority: **none**", markdown)
        self.assertIn("cannot archive, delete, deploy", markdown)


if __name__ == "__main__":
    unittest.main()
