from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.repository_metadata import (
    findings_for_repository,
    load_private_governance,
    topic_findings,
    validate_metadata_policy,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy" / "repository-hygiene.json"


class RepositoryMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_metadata_policy_is_valid(self) -> None:
        self.assertEqual([], validate_metadata_policy(self.policy))

    def test_controlled_topics_accept_atlas_vocabulary(self) -> None:
        findings = topic_findings(
            "AtlasReaper311/demo-repo",
            {"topics": ["atlas-systems", "python", "cloudflare-workers"]},
            self.policy,
        )
        self.assertEqual([], findings)

    def test_controlled_topics_reject_unknown_and_excess_topics(self) -> None:
        findings = topic_findings(
            "AtlasReaper311/demo-repo",
            {
                "topics": [
                    "atlas-systems",
                    "api",
                    "automation",
                    "cloudflare",
                    "devops",
                    "github-actions",
                    "python",
                    "security",
                    "not-approved",
                ]
            },
            self.policy,
        )
        self.assertEqual(
            {"topic-count", "topic-vocabulary"},
            {finding.rule_id for finding in findings},
        )

    def test_private_metadata_uses_private_visibility(self) -> None:
        findings = findings_for_repository(
            "AtlasReaper311/demo-private",
            {
                "visibility": "private",
                "default_branch": "main",
                "description": "Private Atlas Systems demo repository",
                "homepage": "https://atlas-systems.uk",
                "topics": ["atlas-systems", "automation"],
                "archived": False,
            },
            {"lifecycle": "active"},
            self.policy,
            expected_visibility="private",
        )
        self.assertEqual([], findings)

    def test_private_governance_must_match_caller_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "governance.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "atlas-repository-governance/v1",
                        "repository": "AtlasReaper311/private-repo",
                        "visibility": "private",
                        "lifecycle": "active",
                        "public_projection": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(Exception, "does not match"):
                load_private_governance(path, "AtlasReaper311/other-repo")


if __name__ == "__main__":
    unittest.main()
