import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import estate_policy


class EstatePolicyTests(unittest.TestCase):
    def test_full_sha_is_accepted(self):
        workflow = "steps:\n  - uses: owner/action@0123456789012345678901234567890123456789\n"
        findings = estate_policy.action_ref_findings("owner/repo", "ci.yml", workflow)
        self.assertEqual([], findings)

    def test_tag_is_warning(self):
        workflow = "steps:\n  - uses: actions/checkout@v4\n"
        findings = estate_policy.action_ref_findings("owner/repo", "ci.yml", workflow)
        self.assertEqual(1, len(findings))
        self.assertEqual("actions-pin", findings[0].rule)

    def test_canonical_registry_repository_names_are_supported(self):
        manifest = {
            "repositories": [
                {"repository": "AtlasReaper311/status"},
                {"repository": "AtlasReaper311/atlas-infra"},
            ]
        }
        self.assertEqual(
            ["AtlasReaper311/atlas-infra", "AtlasReaper311/status"],
            estate_policy.manifest_repositories(manifest),
        )

    def test_legacy_manifest_urls_remain_supported(self):
        manifest = {
            "repositories": [
                {"url": "https://github.com/AtlasReaper311/status"},
            ]
        }
        self.assertEqual(
            ["AtlasReaper311/status"],
            estate_policy.manifest_repositories(manifest),
        )


if __name__ == "__main__":
    unittest.main()
