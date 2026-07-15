import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import estate_policy


class FakeReader:
    def __init__(self, files):
        self.files = files

    def repo(self, _full_name):
        return {"default_branch": "main"}

    def tree(self, _full_name, _ref):
        return [{"path": path, "type": "blob"} for path in self.files]

    def text(self, _full_name, path, _ref):
        return self.files[path]


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

    def test_explicit_repository_exclusions_are_not_audited(self):
        manifest = {
            "repositories": [
                {"repository": "AtlasReaper311/atlas-infra"},
                {"repository": "AtlasReaper311/simple-proxy"},
            ]
        }
        self.assertEqual(
            ["AtlasReaper311/atlas-infra"],
            estate_policy.manifest_repositories(
                manifest,
                {"AtlasReaper311/simple-proxy"},
            ),
        )

    def test_explicit_url_exclusions_are_not_audited(self):
        manifest = {
            "repositories": [
                {"url": "https://github.com/AtlasReaper311/simple-proxy"},
                {"url": "https://github.com/AtlasReaper311/status"},
            ]
        }
        self.assertEqual(
            ["AtlasReaper311/status"],
            estate_policy.manifest_repositories(
                manifest,
                {"AtlasReaper311/simple-proxy"},
            ),
        )

    def test_warning_reduces_weighted_score(self):
        policy = {"rules": {}, "banned_words": []}
        files = {
            "README.md": "clean",
            ".gitignore": "*.pyc\n",
            "LICENSE": "MIT",
            ".github/workflows/ci.yml": (
                "permissions:\n  contents: read\n"
                "concurrency:\n  group: ci\n"
                "jobs:\n  test:\n    timeout-minutes: 10\n"
                "    steps:\n      - uses: actions/checkout@v4\n"
            ),
        }
        report = estate_policy.evaluate_repository(FakeReader(files), "owner/repo", policy)
        self.assertEqual("warning", report["status"])
        self.assertLess(report["score"], 100)
        self.assertGreater(report["score"], 70)

    def test_not_applicable_rules_leave_denominator(self):
        policy = {"rules": {}, "banned_words": []}
        files = {"README.md": "clean", ".gitignore": "*.pyc\n", "LICENSE": "MIT"}
        report = estate_policy.evaluate_repository(FakeReader(files), "owner/repo", policy)
        npm = next(rule for rule in report["rules"] if rule["rule"] == "npm-lock")
        self.assertEqual("not_applicable", npm["status"])
        self.assertEqual(100.0, report["score"])


    def test_reusable_caller_job_does_not_require_timeout(self):
        workflow = (
            "jobs:\n"
            "  deploy:\n"
            "    uses: owner/repo/.github/workflows/deploy.yml@main\n"
        )
        self.assertEqual(
            [],
            estate_policy.workflow_timeout_findings(
                "owner/repo",
                ".github/workflows/deploy.yml",
                workflow,
            ),
        )

    def test_each_runnable_job_requires_its_own_timeout(self):
        workflow = (
            "jobs:\n"
            "  bounded:\n"
            "    runs-on: ubuntu-latest\n"
            "    timeout-minutes: 10\n"
            "    steps: []\n"
            "  unbounded:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps: []\n"
        )
        findings = estate_policy.workflow_timeout_findings(
            "owner/repo",
            ".github/workflows/ci.yml",
            workflow,
        )
        self.assertEqual(1, len(findings))
        self.assertIn("unbounded", findings[0].message)


if __name__ == "__main__":
    unittest.main()
