from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts as contracts  # noqa: E402


class CostGuardPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads((ROOT / "policy" / "cost-guard.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "policy" / "cost-guard.schema.json").read_text(encoding="utf-8"))

    def test_policy_matches_declared_schema(self) -> None:
        self.assertEqual([], contracts.validate_instance(self.policy, self.schema))

    def test_malformed_policy_is_rejected(self) -> None:
        malformed = copy.deepcopy(self.policy)
        del malformed["services"][0]["provider"]
        errors = contracts.validate_instance(malformed, self.schema)
        self.assertTrue(any("provider" in error for error in errors))

    def test_thresholds_and_keys_are_deterministic(self) -> None:
        keys: set[tuple[str, str, str]] = set()
        for service in self.policy["services"]:
            key = (service["service_id"], service["provider"], service["quota_type"])
            self.assertNotIn(key, keys)
            keys.add(key)
            self.assertLess(service["warning_threshold_pct"], service["critical_threshold_pct"])

    def test_every_action_is_advisory_and_issue_creation_is_disabled(self) -> None:
        self.assertTrue(self.policy["defaults"]["advisory_only"])
        self.assertFalse(self.policy["defaults"]["issue_creation_allowed"])
        for service in self.policy["services"]:
            self.assertTrue(service["advisory_only"])
            self.assertFalse(service["issue_creation_allowed"])

    def test_public_policy_contains_only_active_assured_services(self) -> None:
        for service in self.policy["services"]:
            self.assertNotIn(service["classification"]["lifecycle"], {"deprecated", "archived"})
            self.assertNotEqual(service["classification"]["provenance"], "external-derived")
            self.assertTrue(service["assurance"]["enabled"])
            self.assertIsNone(service["assurance"]["exclusion_reason"])

    def test_phase_one_contract_references_exist(self) -> None:
        for field in ("finding_contract", "evidence_contract"):
            self.assertTrue((ROOT / self.policy[field]).is_file())

    def test_required_runbooks_exist(self) -> None:
        names = {
            "warning-threshold-exceeded",
            "critical-threshold-exceeded",
            "projected-exhaustion",
            "stale-data",
            "provider-unavailable",
            "malformed-snapshot",
            "noisy-or-duplicate-finding",
            "policy-owner-missing",
        }
        for name in names:
            with self.subTest(name=name):
                self.assertTrue((ROOT / "docs" / "runbooks" / f"cost-guard-{name}.md").is_file())


if __name__ == "__main__":
    unittest.main()
