from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts as base
import wave3_contracts as wave3


class Wave3ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT
        cls.contract_root = ROOT / "contracts" / "v1" / "wave3"
        cls.rules = wave3.load_rules(ROOT)

    def fixture(self, relative: str) -> dict:
        return base.load_json(self.contract_root / "fixtures" / relative)

    def schema(self, name: str) -> dict:
        return base.load_json(self.contract_root / name)

    def test_complete_wave3_contract_set_passes(self) -> None:
        report = wave3.validate_repository(ROOT)
        self.assertEqual([], report["errors"])
        self.assertEqual(3, report["schemas_checked"])
        self.assertEqual(3, report["positive_fixtures"])
        self.assertEqual(3, report["negative_fixtures"])

    def test_archived_retirement_fails_closed_on_unknown_evidence(self) -> None:
        instance = self.fixture("invalid/retirement-evidence.archived-with-unknown.json")
        errors = wave3.semantic_errors(
            "retirement-evidence.schema.json", instance, self.rules
        )
        self.assertTrue(
            any("archived retirement requires verified" in item for item in errors),
            errors,
        )

    def test_repository_and_service_retirement_identity_cannot_mix(self) -> None:
        instance = self.fixture("valid/retirement-evidence.json")
        instance["subject"]["repository"] = "AtlasReaper311/atlas-api-index"
        errors = wave3.semantic_errors(
            "retirement-evidence.schema.json", instance, self.rules
        )
        self.assertTrue(any("must not also declare repository" in item for item in errors))

    def test_model_promotion_below_threshold_is_rejected(self) -> None:
        instance = self.fixture("invalid/model-promotion.below-threshold.json")
        errors = wave3.semantic_errors(
            "model-promotion.schema.json", instance, self.rules
        )
        self.assertTrue(any("meet or exceed minimum_pass_rate" in item for item in errors))

    def test_adr_relationship_fingerprint_is_array_order_independent(self) -> None:
        instance = self.fixture("valid/adr-runtime-relationship.json")
        first = base.calculate_fingerprint(
            "adr-runtime-relationship", instance, self.rules
        )
        changed = copy.deepcopy(instance)
        changed["affects"]["repositories"].reverse()
        changed["affects"]["services"].reverse()
        second = base.calculate_fingerprint(
            "adr-runtime-relationship", changed, self.rules
        )
        self.assertEqual(first, second)
        self.assertEqual(instance["relationship_id"], first)


if __name__ == "__main__":
    unittest.main()
