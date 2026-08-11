import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import github_conformance_scoreboard


class FakeClient:
    def __init__(self, values):
        self.values = values

    def get(self, path):
        if path not in self.values:
            raise AssertionError(f"unexpected GET {path}")
        return copy.deepcopy(self.values[path])

    def get_optional(self, path):
        if path not in self.values:
            return None
        return copy.deepcopy(self.values[path])


class GitHubConformanceScoreboardTests(unittest.TestCase):
    def load_projection(self):
        return json.loads((ROOT / "policy/public-repository-classifications.json").read_text(encoding="utf-8"))

    def test_projection_contains_public_github_defaults_repository(self):
        projection = self.load_projection()
        repositories = {item["repository"] for item in projection["repositories"]}
        self.assertIn("AtlasReaper311/.github", repositories)
        self.assertEqual(34, projection["repository_count"])

    def test_scoreboard_uses_global_security_default_without_private_discovery(self):
        projection = {
            "schema_version": "atlas-public-repository-classifications/projection/v1",
            "authority": "AtlasReaper311/atlas-infra",
            "source_fingerprint": "sha256:" + "0" * 64,
            "repository_count": 1,
            "repositories": [
                {
                    "repository": "AtlasReaper311/example",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                    "runtime_service": False,
                }
            ],
        }
        values = {
            "/repos/AtlasReaper311/.github/contents/SECURITY.md?ref=main": {"name": "SECURITY.md"},
            "/repos/AtlasReaper311/example": {
                "description": "Example repo",
                "default_branch": "main",
                "license": {"spdx_id": "MIT"},
                "topics": ["atlas-systems"],
                "visibility": "public",
            },
            "/repos/AtlasReaper311/example/contents/.github/dependabot.yml?ref=main": {"name": "dependabot.yml"},
            "/repos/AtlasReaper311/example/contents/.github/workflows/codeql.yml?ref=main": {"name": "codeql.yml"},
            "/repos/AtlasReaper311/example/contents/.github/workflows/scorecard.yml?ref=main": {"name": "scorecard.yml"},
            "/repos/AtlasReaper311/example/contents/.github/workflows/release.yml?ref=main": {"name": "release.yml"},
            "/repos/AtlasReaper311/example/releases?per_page=1": [],
            "/repos/AtlasReaper311/example/tags?per_page=1": [{"name": "v1.0.0"}],
            "/repos/AtlasReaper311/example/rulesets": [
                {
                    "name": "Atlas default branch PR guard",
                    "target": "branch",
                    "enforcement": "active",
                    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
                }
            ],
            "/repos/AtlasReaper311/example/branches/main/protection": None,
        }
        report = github_conformance_scoreboard.build_scoreboard(FakeClient(values), projection)
        self.assertEqual(1, report["summary"]["repositories_checked"])
        self.assertEqual(10, report["summary"]["checks_passed"])
        self.assertEqual(0, report["summary"]["checks_failed"])

    def test_markdown_contains_failed_and_unknown_columns(self):
        report = {
            "source_fingerprint": "sha256:" + "0" * 64,
            "summary": {
                "repositories_checked": 1,
                "checks_passed": 1,
                "checks_failed": 1,
                "checks_unknown": 1,
            },
            "repositories": [
                {
                    "repository": "AtlasReaper311/example",
                    "lifecycle": "active",
                    "scope": "public",
                    "score": 50,
                    "checks": [
                        {"label": "Description", "status": "passed"},
                        {"label": "CodeQL workflow", "status": "failed"},
                        {"label": "Default branch PR guard", "status": "unknown"},
                    ],
                }
            ],
        }
        markdown = github_conformance_scoreboard.render_markdown(report)
        self.assertIn("CodeQL workflow", markdown)
        self.assertIn("Default branch PR guard", markdown)

    def test_ruleset_summary_detail_link_is_followed_for_branch_guard(self):
        values = {
            "/repos/AtlasReaper311/example/rulesets": [
                {
                    "name": "Atlas default branch PR guard",
                    "target": "branch",
                    "enforcement": "active",
                    "_links": {
                        "self": {
                            "href": "https://api.github.com/repos/AtlasReaper311/example/rulesets/1"
                        }
                    },
                }
            ],
            "https://api.github.com/repos/AtlasReaper311/example/rulesets/1": {
                "name": "Atlas default branch PR guard",
                "target": "branch",
                "enforcement": "active",
                "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
                "rules": [
                    {"type": "deletion"},
                    {"type": "non_fast_forward"},
                    {"type": "pull_request"},
                ],
            },
        }
        result = github_conformance_scoreboard.has_default_branch_guard(
            FakeClient(values), "AtlasReaper311/example", "main"
        )
        self.assertEqual("passed", result.status)

    def test_cli_writes_outputs_with_fake_projection_validation(self):
        projection = self.load_projection()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "projection.json"
            path.write_text(json.dumps(projection), encoding="utf-8")
            loaded = github_conformance_scoreboard.load_projection(path)
        self.assertEqual(projection["repository_count"], loaded["repository_count"])


if __name__ == "__main__":
    unittest.main()
