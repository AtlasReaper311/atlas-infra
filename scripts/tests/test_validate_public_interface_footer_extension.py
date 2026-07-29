from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_public_interface_footer_extension import (
    REQUIRED_EXCLUSIONS,
    load_json,
    validate_footer_extension,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy/public-interface-footer-extension-v1.json"


class FooterExtensionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_json(POLICY_PATH)

    def test_committed_policy_is_valid(self) -> None:
        self.assertTrue(validate_footer_extension(self.policy).ok)

    def test_rejects_missing_estate_escape(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["variants"]["product"]["required_slots"].remove("estate_escape")
        candidate["variants"]["product"]["optional_slots"].append("estate_escape")
        result = validate_footer_extension(candidate)
        self.assertIn("product required slots drifted", result.errors)

    def test_rejects_scheduler_ownership_drift(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["slots"]["sequence"]["article_owner"] = "AtlasReaper311/atlas-interface-kit"
        result = validate_footer_extension(candidate)
        self.assertIn("article sequence ownership must remain with atlas-scheduler", result.errors)

    def test_rejects_remote_runtime_dependency(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["behaviour"]["remote_runtime_dependency_forbidden"] = False
        result = validate_footer_extension(candidate)
        self.assertIn("remote_runtime_dependency_forbidden must remain true", result.errors)

    def test_rejects_incomplete_phase_exclusions(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["excluded"] = sorted(REQUIRED_EXCLUSIONS - {"deployment"})
        result = validate_footer_extension(candidate)
        self.assertIn("Phase 6A exclusions are incomplete", result.errors)

    def test_schema_is_valid_json_and_targets_policy(self) -> None:
        schema_path = (
            ROOT
            / "contracts/v1/public-interface/public-interface-footer-extension.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            self.policy["schema_version"],
        )
        self.assertEqual(schema["properties"]["version"]["const"], self.policy["version"])


if __name__ == "__main__":
    unittest.main()
