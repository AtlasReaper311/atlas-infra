import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chaos_evidence


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "policy" / "chaos-experiments.json"


class ChaosPolicySelectionTests(unittest.TestCase):
    def test_all_declared_experiments_use_live_capabilities(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        contract = policy["target_capabilities"]["specular-edge"]
        live = set(contract["live_faults"])
        test_only = set(contract["test_only_faults"])
        for experiment in policy["experiments"]:
            self.assertIn(experiment["fault"], live)
            self.assertNotIn(experiment["fault"], test_only)

    def test_validator_rejects_missing_single_lease_contract(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        policy["target_capabilities"]["specular-edge"]["single_active_lease"] = False
        errors = chaos_evidence.validate_capabilities(policy)
        self.assertTrue(any("single_active_lease" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
