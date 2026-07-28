from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_interface_foundation_extension import load_json, validate_extension


class PublicInterfaceFoundationExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_json(ROOT / "policy/public-interface-foundation-extension-v1.json")

    def assert_error_contains(self, policy: dict, fragment: str) -> None:
        errors = validate_extension(policy).errors
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected an error containing {fragment!r}, got {errors!r}",
        )

    def test_committed_extension_is_valid(self) -> None:
        self.assertEqual((), validate_extension(self.policy).errors)

    def test_breadcrumbs_remain_optional_and_exclude_machine_surfaces(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["components"]["breadcrumb_navigation"]["required"] = True
        policy["components"]["breadcrumb_navigation"]["machine_surfaces_excluded"] = False
        self.assert_error_contains(policy, "breadcrumbs must remain optional")
        self.assert_error_contains(policy, "machine surfaces must remain excluded")

    def test_routine_status_polling_remains_silent(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["components"]["status_announcement"]["silent_on"] = ["unchanged-poll"]
        self.assert_error_contains(policy, "routine polling must remain silent")

    def test_global_header_does_not_become_a_live_region(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["components"]["status_announcement"]["global_header_status_remains_aria_live_off"] = False
        self.assert_error_contains(policy, "global header status must remain aria-live off")

    def test_dense_data_regions_are_focusable_only_when_overflowing(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["components"]["dense_data_overflow"]["when_not_overflowing"] = {
            "unnecessary_tab_stop_forbidden": False
        }
        self.assert_error_contains(policy, "must not add unnecessary tab stops")

    def test_1920_remains_reporting_only(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["evidence"]["reporting_only_is_breakpoint"] = True
        policy["evidence"]["reporting_only_is_budget"] = True
        self.assert_error_contains(policy, "reporting_only_is_breakpoint must remain false")
        self.assert_error_contains(policy, "reporting_only_is_budget must remain false")

    def test_consumer_rollout_remains_separate(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["distribution"]["consumer_rollout_requires_separate_approval"] = False
        self.assert_error_contains(policy, "consumer_rollout_requires_separate_approval must remain true")

    def test_policy_and_schema_parse_as_json(self) -> None:
        schema = json.loads(
            (
                ROOT
                / "contracts/v1/public-interface/public-interface-foundation-extension.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "https://atlas-systems.uk/contracts/v1/public-interface/public-interface-foundation-extension.schema.json",
            schema["$id"],
        )


if __name__ == "__main__":
    unittest.main()
