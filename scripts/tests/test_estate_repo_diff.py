import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import estate_repo_diff


class EstateRepositoryDiffTests(unittest.TestCase):
    def test_reconciliation_separates_mismatches_and_matches(self):
        registry = {
            "reviewed_at": "2026-07-15T00:00:00Z",
            "repositories": [
                {
                    "repository": "AtlasReaper311/atlas-infra",
                    "lifecycle": "production",
                    "scope": "public",
                    "provenance": "original",
                    "runtime_service": False,
                },
                {
                    "repository": "AtlasReaper311/missing",
                    "lifecycle": "active",
                    "scope": "internal",
                    "provenance": "original",
                    "runtime_service": False,
                },
            ],
        }
        github = {
            "AtlasReaper311/atlas-infra": {
                "repository": "AtlasReaper311/atlas-infra",
                "default_branch": "main",
                "archived": False,
                "private": False,
                "visibility": "public",
                "id": 1,
            },
            "AtlasReaper311/unclassified": {
                "repository": "AtlasReaper311/unclassified",
                "default_branch": "main",
                "archived": False,
                "private": True,
                "visibility": "private",
                "id": 2,
            },
        }

        result = estate_repo_diff.reconcile(registry, github)

        self.assertEqual(result["github_only"], ["AtlasReaper311/unclassified"])
        self.assertEqual(result["registry_only"], ["AtlasReaper311/missing"])
        self.assertEqual(
            [item["repository"] for item in result["matches"]],
            ["AtlasReaper311/atlas-infra"],
        )
        self.assertEqual(len(result["reconciliation_digest"]), 64)

    def test_anonymous_owner_listing_is_refused(self):
        class Client:
            token = ""

        with self.assertRaisesRegex(RuntimeError, "authenticated token"):
            estate_repo_diff.list_owned_repositories(Client(), "AtlasReaper311")


if __name__ == "__main__":
    unittest.main()
