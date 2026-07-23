from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate_gardener_target_readiness.py"
SPEC = importlib.util.spec_from_file_location("validate_gardener_target_readiness", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = Path(__file__).resolve().parents[2] / "policy" / "gardener-target-readiness.json"


class GardenerTargetReadinessPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_committed_policy_is_valid(self) -> None:
        report = VALIDATOR.validate_policy(self.policy)
        self.assertEqual("valid", report["status"])
        self.assertEqual(5, report["target_count"])
        self.assertEqual(0, report["provider_mutations"])

    def test_rejects_missing_barrier(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["barrier_check"] = ""
        with self.assertRaisesRegex(
            VALIDATOR.ReadinessPolicyError,
            "barrier",
        ):
            VALIDATOR.validate_policy(policy)

    def test_rejects_reordered_batch(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["targets"] = list(reversed(policy["targets"]))
        with self.assertRaisesRegex(
            VALIDATOR.ReadinessPolicyError,
            "ordered verified batch-one",
        ):
            VALIDATOR.validate_policy(policy)

    def test_rejects_auto_merge_enabled_at_rest(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["required_repository_settings"]["allow_auto_merge_at_rest"] = True
        with self.assertRaisesRegex(
            VALIDATOR.ReadinessPolicyError,
            "broader than approved",
        ):
            VALIDATOR.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
