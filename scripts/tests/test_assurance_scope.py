import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import assurance_scope


class AssuranceScopeTests(unittest.TestCase):
    def test_default_assurance_exclusion_removes_repository(self):
        registry = {
            "repositories": [
                {
                    "repository": "AtlasReaper311/example-default-excluded",
                    "exclusions": ["default-assurance", "new-features"],
                },
                {
                    "repository": "AtlasReaper311/atlas-infra",
                    "exclusions": [],
                },
            ]
        }

        filtered = assurance_scope.filter_default_assurance(registry)

        self.assertEqual(
            ["AtlasReaper311/atlas-infra"],
            [item["repository"] for item in filtered["repositories"]],
        )
        self.assertEqual(2, len(registry["repositories"]))

    def test_unrelated_exclusions_do_not_remove_repository(self):
        registry = {
            "repositories": [
                {
                    "repository": "AtlasReaper311/example-unrelated-exclusion",
                    "exclusions": ["deployment-orchestration"],
                }
            ]
        }

        filtered = assurance_scope.filter_default_assurance(registry)

        self.assertEqual(registry, filtered)
        self.assertIsNot(registry, filtered)

    def test_missing_exclusions_remains_in_scope(self):
        registry = {
            "repositories": [
                {"repository": "AtlasReaper311/status"},
            ]
        }

        filtered = assurance_scope.filter_default_assurance(registry)

        self.assertEqual(registry, filtered)

    def test_invalid_repository_collection_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "repositories must be a list"):
            assurance_scope.filter_default_assurance({"repositories": {}})


if __name__ == "__main__":
    unittest.main()
