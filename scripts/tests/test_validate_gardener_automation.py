import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import validate_gardener_automation


class GardenerAutomationAuthorityTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def policy(self) -> dict:
        return self.load("policy/gardener-automation.json")

    def coverage(self) -> dict:
        return self.load("policy/gardener-github-app-coverage.json")

    def test_committed_policy_is_valid_and_disabled(self):
        report = validate_gardener_automation.validate_policy(
            self.policy(), self.coverage()
        )
        self.assertEqual("valid", report["status"])
        self.assertEqual("disabled", report["default_mode"])
        self.assertEqual(20, report["coverage_count"])
        self.assertEqual(
            ["macos-metadata-ignore", "python-cache-ignore"],
            report["automatic_fixers"],
        )
        self.assertEqual(0, report["provider_mutations"])

    def test_unknown_mode_fails_closed(self):
        policy = self.policy()
        policy["allowed_modes"].append("unsafe")
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "exact ordered v1 mode set"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_default_write_mode_fails_closed(self):
        policy = self.policy()
        policy["default_mode"] = "automerge-low-risk"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "default source mode"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_workflow_fixer_cannot_gain_automatic_merge(self):
        policy = self.policy()
        policy["fixers"]["workflow-timeout"]["automatic_merge"] = True
        policy["fixers"]["workflow-timeout"]["risk_class"] = "low"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "must remain review-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_housekeeping_fixer_is_gitignore_only(self):
        policy = self.policy()
        policy["fixers"]["python-cache-ignore"]["automatic_merge_paths"] = [
            ".gitignore",
            "src/cache.py",
        ]
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "gitignore-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_unverified_coverage_fails_closed(self):
        coverage = self.coverage()
        coverage["batches"][0]["status"] = "planned"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "not verified"
        ):
            validate_gardener_automation.validate_policy(self.policy(), coverage)

    def test_permission_expansion_fails_closed(self):
        coverage = self.coverage()
        coverage["permissions"]["actions"] = "read"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "permission boundary changed"
        ):
            validate_gardener_automation.validate_policy(self.policy(), coverage)

    def test_long_approval_expiry_fails_closed(self):
        policy = self.policy()
        policy["approval_ttl_hours"] = 25
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "longer than 24 hours"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_missing_source_path_refusal_fails_closed(self):
        policy = self.policy()
        policy["forbidden_path_prefixes"].remove("src/")
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "required forbidden prefix"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_policy_digest_is_deterministic(self):
        policy = self.policy()
        reordered = copy.deepcopy(policy)
        reordered = dict(reversed(list(reordered.items())))
        self.assertEqual(
            validate_gardener_automation.digest_json(policy),
            validate_gardener_automation.digest_json(reordered),
        )


if __name__ == "__main__":
    unittest.main()
