import json
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_public_non_runtime_classification_is_preserved(self):
        registry = {
            "repositories": [
                {
                    "repository": "AtlasReaper311/status",
                    "lifecycle": "production",
                    "scope": "public",
                    "provenance": "original",
                    "runtime_service": True,
                }
            ]
        }
        supplement = {
            "schema_version": "atlas-public-assurance/repositories/v2",
            "repositories": [
                {
                    "repository": "AtlasReaper311/example-public-tooling",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public-assurance-repositories.json"
            path.write_text(json.dumps(supplement), encoding="utf-8")
            merged = assurance_scope.add_public_assurance_repositories(registry, path)

        entry = next(
            item
            for item in merged["repositories"]
            if item["repository"] == "AtlasReaper311/example-public-tooling"
        )
        self.assertEqual("active", entry["lifecycle"])
        self.assertEqual("public", entry["scope"])
        self.assertEqual("original", entry["provenance"])
        self.assertFalse(entry["runtime_service"])

    def test_public_non_runtime_overlap_fails_closed(self):
        registry = {"repositories": [{"repository": "AtlasReaper311/status"}]}
        supplement = {
            "schema_version": "atlas-public-assurance/repositories/v2",
            "repositories": [
                {
                    "repository": "AtlasReaper311/status",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public-assurance-repositories.json"
            path.write_text(json.dumps(supplement), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "overlaps runtime registry"):
                assurance_scope.add_public_assurance_repositories(registry, path)

    def test_public_non_runtime_internal_scope_fails_closed(self):
        registry = {"repositories": []}
        supplement = {
            "schema_version": "atlas-public-assurance/repositories/v2",
            "repositories": [
                {
                    "repository": "AtlasReaper311/example-public-tooling",
                    "lifecycle": "active",
                    "scope": "internal",
                    "provenance": "original",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public-assurance-repositories.json"
            path.write_text(json.dumps(supplement), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must have public scope"):
                assurance_scope.add_public_assurance_repositories(registry, path)


if __name__ == "__main__":
    unittest.main()
