from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_public_interface import load_json, validate_system


ROOT = Path(__file__).resolve().parents[2]


class PublicInterfaceImplementationStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.system = load_json(ROOT / "policy/public-interface-system-v2.json")

    def test_interface_kit_is_active(self) -> None:
        implementation = self.system["authority"]["implementation_repository"]
        self.assertEqual("AtlasReaper311/atlas-interface-kit", implementation["repository"])
        self.assertEqual("active", implementation["state"])
        self.assertEqual("active", self.system["distribution"]["implementation_owner_state"])

    def test_migration_has_entered_implementation(self) -> None:
        self.assertEqual("implementation", self.system["migration"]["state"])
        self.assertTrue(self.system["migration"]["current_shell_contract_remains_active"])
        self.assertTrue(
            self.system["migration"]["production_rollout_requires_separate_approval"]
        )

    def test_committed_policy_remains_valid(self) -> None:
        self.assertTrue(validate_system(self.system).ok)


if __name__ == "__main__":
    unittest.main()
