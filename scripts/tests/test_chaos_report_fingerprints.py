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
POLICY = ROOT / "policy" / "chaos-experiments.json"


class ChaosReportFingerprintTests(unittest.TestCase):
    def test_policy_change_changes_stamped_report_fingerprint(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        report = chaos_harness.run_experiment(policy["experiments"][0], "simulate", "")

        with tempfile.TemporaryDirectory() as tmp:
            first_path = Path(tmp) / "first.json"
            second_path = Path(tmp) / "second.json"
            first_md = Path(tmp) / "first.md"
            second_md = Path(tmp) / "second.md"
            chaos_harness.write_reports([copy.deepcopy(report)], first_path, first_md)
            chaos_harness.write_reports([copy.deepcopy(report)], second_path, second_md)

            first = chaos_evidence.stamp_report(policy, first_path, first_md)
            changed = copy.deepcopy(policy)
            changed["version"] = "1.1.1-test"
            second = chaos_evidence.stamp_report(changed, second_path, second_md)

            self.assertNotEqual(first["fingerprint"], second["fingerprint"])
            self.assertNotEqual(
                first["experiments"][0]["fingerprint"],
                second["experiments"][0]["fingerprint"],
            )


if __name__ == "__main__":
    unittest.main()
