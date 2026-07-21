from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.repository_hygiene import (
    label_findings,
    metadata_findings,
    readme_findings,
    validate_policy_files,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy" / "repository-hygiene.json"
PROJECTION_PATH = ROOT / "policy" / "public-repository-classifications.json"


class RepositoryHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_repository_policy_matches_current_public_projection(self) -> None:
        self.assertEqual([], validate_policy_files(POLICY_PATH, PROJECTION_PATH))

    def test_standard_readme_contract_accepts_reference_shape(self) -> None:
        text = """<div align=\"center\">\n  <img src=\"https://raw.githubusercontent.com/AtlasReaper311/AtlasReaper311/main/atlas-icon-dark-256.png\" width=\"88\" alt=\"Atlas Systems\"/>\n</div>\n\n# demo-repo\n\n```\n┌─────────────────────────────────────────────┐\n│  ATLAS SYSTEMS // demo-repo                 │\n│  demo                                       │\n└─────────────────────────────────────────────┘\n```\n\n![A](https://img.shields.io/badge/a-a-f5a623?style=flat-square&labelColor=0a0a0f)\n![B](https://img.shields.io/badge/b-b-4ade80?style=flat-square&labelColor=0a0a0f)\n![C](https://img.shields.io/badge/c-c-aaa9a0?style=flat-square&labelColor=0a0a0f)\n![D](https://img.shields.io/badge/d-d-aaa9a0?style=flat-square&labelColor=0a0a0f)\n\nDescription.\n\n## How it fits into Atlas Systems\n\nText.\n\n---\n\nPart of [atlas-systems.uk](https://atlas-systems.uk)\n"""
        self.assertEqual(
            [],
            readme_findings(
                "AtlasReaper311/demo-repo",
                text,
                self.policy,
                has_license=False,
            ),
        )

    def test_standard_readme_contract_rejects_missing_structure(self) -> None:
        findings = readme_findings(
            "AtlasReaper311/demo-repo",
            "# Wrong\n",
            self.policy,
            has_license=False,
        )
        rules = {finding.rule_id for finding in findings}
        self.assertTrue(
            {
                "icon",
                "h1",
                "ascii-banner",
                "atlas-fit-heading",
                "footer",
                "badge-style",
                "badge-count",
            }.issubset(rules)
        )

    def test_metadata_contract_accepts_atlas_homepage_and_topic(self) -> None:
        findings = metadata_findings(
            "AtlasReaper311/demo-repo",
            {
                "visibility": "public",
                "default_branch": "main",
                "description": "Demo repository for Atlas Systems",
                "homepage": "https://demo.atlas-systems.uk/docs",
                "topics": ["atlas-systems", "demo"],
                "archived": False,
            },
            {"lifecycle": "active"},
            self.policy,
        )
        self.assertEqual([], findings)

    def test_metadata_contract_rejects_empty_portfolio_metadata(self) -> None:
        findings = metadata_findings(
            "AtlasReaper311/demo-repo",
            {
                "visibility": "public",
                "default_branch": "main",
                "description": "",
                "homepage": None,
                "topics": [],
                "archived": False,
            },
            {"lifecycle": "active"},
            self.policy,
        )
        rules = {finding.rule_id for finding in findings}
        self.assertEqual({"description", "homepage", "topic"}, rules)

    def test_archived_lifecycle_requires_github_archive_state(self) -> None:
        findings = metadata_findings(
            "AtlasReaper311/demo-repo",
            {
                "visibility": "public",
                "default_branch": "main",
                "description": "Demo repository for Atlas Systems",
                "homepage": "https://atlas-systems.uk",
                "topics": ["atlas-systems"],
                "archived": False,
            },
            {"lifecycle": "archived"},
            self.policy,
        )
        self.assertEqual(["archive-state"], [finding.rule_id for finding in findings])

    def test_required_labels_match_exact_color_and_description(self) -> None:
        labels = [dict(label) for label in self.policy["pull_request_labels"]]
        self.assertEqual([], label_findings("AtlasReaper311/demo-repo", labels, self.policy))
        labels[0]["color"] = "000000"
        findings = label_findings("AtlasReaper311/demo-repo", labels, self.policy)
        self.assertEqual(["label-color"], [finding.rule_id for finding in findings])

    def test_policy_rejects_profile_outside_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
            policy["readme"]["profile_repository"] = "AtlasReaper311/not-public"
            policy_path = tmp_path / "policy.json"
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            errors = validate_policy_files(policy_path, PROJECTION_PATH)
            self.assertIn(
                "readme.profile_repository must exist in the public repository projection",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
