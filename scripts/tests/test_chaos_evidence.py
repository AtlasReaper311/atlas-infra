import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chaos_evidence
import chaos_harness


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy" / "chaos-experiments.json"


class ChaosEvidenceTests(unittest.TestCase):
    def policy(self):
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_current_policy_and_target_capabilities_are_consistent(self):
        policy = self.policy()
        self.assertEqual([], chaos_harness.validate_policy(policy))
        self.assertEqual([], chaos_evidence.validate_capabilities(policy))

    def test_test_only_fault_cannot_enter_live_policy(self):
        policy = self.policy()
        experiment = copy.deepcopy(policy["experiments"][0])
        experiment["id"] = "specular-stale-test-v1"
        experiment["fault"] = "stale_response"
        policy["experiments"].append(experiment)

        errors = chaos_evidence.validate_capabilities(policy)
        self.assertTrue(any("test-only fault" in item for item in errors))

    def test_every_harness_fault_has_one_capability_class(self):
        policy = self.policy()
        contract = policy["target_capabilities"]["specular-edge"]
        declared = set(contract["live_faults"]) | set(contract["test_only_faults"])
        self.assertEqual(set(chaos_harness.ALLOWED_FAULTS), declared)
        self.assertFalse(set(contract["live_faults"]) & set(contract["test_only_faults"]))

    def test_simulation_report_is_stamped_with_policy_provenance(self):
        policy = self.policy()
        experiment = policy["experiments"][0]
        report = chaos_harness.run_experiment(experiment, "simulate", "")

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "chaos-report.json"
            markdown_path = Path(tmp) / "chaos-report.md"
            chaos_harness.write_reports([report], report_path, markdown_path)
            before = json.loads(report_path.read_text(encoding="utf-8"))["fingerprint"]

            document = chaos_evidence.stamp_report(
                policy,
                report_path,
                markdown_path,
            )
            stamped = document["experiments"][0]
            self.assertEqual(policy["version"], document["policy"]["version"])
            self.assertEqual(policy["version"], stamped["policy_version"])
            self.assertEqual("live", stamped["capability_class"])
            self.assertNotEqual(before, document["fingerprint"])
            self.assertEqual(document["fingerprint"], chaos_evidence.fingerprint(document))
            self.assertIn(
                f"Policy version: **{policy['version']}**",
                markdown_path.read_text(encoding="utf-8"),
            )

    def test_report_for_undeclared_experiment_is_rejected(self):
        policy = self.policy()
        experiment = copy.deepcopy(policy["experiments"][0])
        experiment["id"] = "undeclared-experiment-v1"
        report = chaos_harness.run_experiment(experiment, "simulate", "")

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "chaos-report.json"
            markdown_path = Path(tmp) / "chaos-report.md"
            chaos_harness.write_reports([report], report_path, markdown_path)
            with self.assertRaisesRegex(ValueError, "undeclared experiment"):
                chaos_evidence.stamp_report(policy, report_path, markdown_path)


if __name__ == "__main__":
    unittest.main()
