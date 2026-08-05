from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_interface_evidence_mode_extension import load_json, validate_extension


class PublicInterfaceEvidenceModeExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_json(ROOT / "policy/public-interface-evidence-mode-extension-v1.json")

    def assert_error_contains(self, policy: dict, fragment: str) -> None:
        errors = validate_extension(policy).errors
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected an error containing {fragment!r}, got {errors!r}",
        )

    def test_committed_extension_is_valid(self) -> None:
        self.assertEqual((), validate_extension(self.policy).errors)

    def test_runtime_state_maturity_and_evidence_mode_remain_separate(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["taxonomies"]["runtime_state_is_separate_from_evidence_mode"] = False
        policy["taxonomies"]["maturity_is_separate_from_evidence_mode"] = False
        self.assert_error_contains(policy, "runtime state and evidence mode must remain separate")
        self.assert_error_contains(policy, "maturity and evidence mode must remain separate")

    def test_generated_output_does_not_become_evidence(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["taxonomies"]["generated_output_is_evidence"] = True
        self.assert_error_contains(policy, "generated product output must not become evidence")

    def test_unknown_unavailable_and_unscored_cannot_render_as_zero(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["presentation"]["zero_may_not_represent"] = ["unknown"]
        policy["mode_contracts"]["unavailable"]["numeral_treatment"] = "zero"
        self.assert_error_contains(policy, "zero must not represent unavailable, unknown, or unscored evidence")
        self.assert_error_contains(policy, "unavailable evidence must render an em dash instead of zero")

    def test_simulated_and_replayed_evidence_remain_neutral(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["mode_contracts"]["simulated"]["semantic_runtime_hue_permitted"] = True
        policy["presentation"]["semantic_runtime_hue_modes"].append("recorded-replay")
        self.assert_error_contains(policy, "simulated semantic runtime hue permission is invalid")
        self.assert_error_contains(policy, "semantic runtime hue must remain limited to measured evidence")

    def test_fallback_mode_is_persistent_and_not_colour_only(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["presentation"]["fallback_mode_must_remain_visible_across_primary_state_metrics_tables_and_charts"] = False
        policy["presentation"]["colour_must_not_be_the_only_signal"] = False
        self.assert_error_contains(
            policy,
            "fallback_mode_must_remain_visible_across_primary_state_metrics_tables_and_charts must remain true",
        )
        self.assert_error_contains(policy, "colour_must_not_be_the_only_signal must remain true")

    def test_directory_and_destination_vocabulary_must_agree(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["presentation"]["directory_and_destination_vocabulary_must_agree"] = False
        self.assert_error_contains(policy, "directory_and_destination_vocabulary_must_agree must remain true")

    def test_consumer_adoption_and_rollout_remain_separate(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["distribution"]["consumer_adoption_requires_separate_pull_request"] = False
        policy["distribution"]["consumer_rollout_requires_separate_approval"] = False
        self.assert_error_contains(policy, "consumer_adoption_requires_separate_pull_request must remain true")
        self.assert_error_contains(policy, "consumer_rollout_requires_separate_approval must remain true")

    def test_policy_and_schema_parse_as_json(self) -> None:
        schema = json.loads(
            (
                ROOT
                / "contracts/v1/public-interface/public-interface-evidence-mode-extension.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "https://atlas-systems.uk/contracts/v1/public-interface/public-interface-evidence-mode-extension.schema.json",
            schema["$id"],
        )


if __name__ == "__main__":
    unittest.main()
