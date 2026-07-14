from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts as contracts  # noqa: E402


class SecretWatchPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (ROOT / "policy" / "secret-watch.json").read_text(encoding="utf-8")
        )
        cls.schema = json.loads(
            (ROOT / "policy" / "secret-watch.schema.json").read_text(encoding="utf-8")
        )

    def test_policy_matches_declared_schema(self) -> None:
        self.assertEqual([], contracts.validate_instance(self.policy, self.schema))

    def test_every_referenced_name_has_metadata(self) -> None:
        definitions = self.policy["secret_definitions"]
        for repository in self.policy["repositories"]:
            for scope in repository["scopes"]:
                for field in (
                    "required_secret_names",
                    "optional_secret_names",
                    "deprecated_secret_names",
                ):
                    for name in scope[field]:
                        with self.subTest(
                            repository=repository["repository"], name=name
                        ):
                            self.assertIn(name, definitions)
                            self.assertTrue(definitions[name]["owner"])
                            self.assertTrue(definitions[name]["purpose"])

    def test_simple_proxy_is_explicitly_excluded(self) -> None:
        declaration = next(
            item
            for item in self.policy["repositories"]
            if item["repository"] == "AtlasReaper311/simple-proxy"
        )
        self.assertEqual(
            {
                "lifecycle": "deprecated",
                "scope": "internal",
                "provenance": "external-derived",
            },
            declaration["classification"],
        )
        self.assertFalse(declaration["assurance"]["enabled"])
        self.assertTrue(declaration["assurance"]["exclusion_reason"])

    def test_policy_contains_names_not_values(self) -> None:
        rendered = json.dumps(self.policy, sort_keys=True)
        self.assertNotIn("BEGIN PRIVATE KEY", rendered)
        self.assertNotRegex(rendered, r"gh[pousr]_[A-Za-z0-9]{20,}")
        self.assertNotRegex(rendered, r"AKIA[0-9A-Z]{16}")


if __name__ == "__main__":
    unittest.main()
