from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import public_boundary_audit as base  # noqa: E402
import public_boundary_policy_audit as policy_audit  # noqa: E402


class FakeGitHubClient:
    def __init__(self, text: str):
        self.text = text

    def get(self, path: str):
        if "/contents/" in path:
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(self.text.encode("utf-8")).decode("ascii"),
            }
        return {"private": False}


class PublicBoundaryPolicyAuditTests(unittest.TestCase):
    owner = "AtlasReaper311"
    target = {
        "repository": "AtlasReaper311/atlas-api-public",
        "path": "data/twin-impact-projection.json",
    }
    identities = ["AtlasReaper311/atlas-twin", "atlas-twin"]
    approval = {
        "authority": "ADR-0017",
        "json_pointer": "/provenance/producer_id",
        "path": "data/twin-impact-projection.json",
        "repository": "AtlasReaper311/atlas-api-public",
        "value": "atlas-twin",
    }

    def test_exact_reviewed_capability_literal_passes(self):
        client = FakeGitHubClient(
            json.dumps({"provenance": {"producer_id": "atlas-twin"}})
        )

        report = policy_audit.audit_github_public_projections(
            client,
            self.owner,
            self.identities,
            [self.target],
            [self.approval],
        )

        self.assertEqual("passed", report["status"])
        self.assertEqual([], report["findings"])
        self.assertEqual([], report["errors"])

    def test_same_literal_at_another_pointer_fails_closed(self):
        client = FakeGitHubClient(
            json.dumps(
                {
                    "provenance": {"producer_id": "atlas-twin"},
                    "source_repository": "atlas-twin",
                }
            )
        )

        report = policy_audit.audit_github_public_projections(
            client,
            self.owner,
            self.identities,
            [self.target],
            [self.approval],
        )

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["findings"]))
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn("atlas-twin", serialized)

    def test_full_private_repository_identity_remains_protected(self):
        client = FakeGitHubClient(
            json.dumps(
                {
                    "provenance": {"producer_id": "atlas-twin"},
                    "source_repository": "AtlasReaper311/atlas-twin",
                }
            )
        )

        report = policy_audit.audit_github_public_projections(
            client,
            self.owner,
            self.identities,
            [self.target],
            [self.approval],
        )

        self.assertEqual("failed", report["status"])
        self.assertGreaterEqual(len(report["findings"]), 1)
        self.assertNotIn("AtlasReaper311/atlas-twin", json.dumps(report, sort_keys=True))

    def test_stale_approval_fails_closed_when_pointer_is_absent(self):
        client = FakeGitHubClient(json.dumps({"provenance": {"producer_id": "other"}}))

        report = policy_audit.audit_github_public_projections(
            client,
            self.owner,
            self.identities,
            [self.target],
            [self.approval],
        )

        self.assertEqual("failed", report["status"])
        self.assertTrue(
            any("absent from its reviewed JSON pointer" in error for error in report["errors"])
        )

    def test_committed_policy_binds_one_adr0017_literal(self):
        policy_path = REPO_ROOT / "policy" / "public-boundary-projections.json"
        targets = base.load_projection_targets(policy_path, self.owner)
        approvals = policy_audit._load_approved_literals(
            policy_path,
            self.owner,
            targets,
        )

        self.assertEqual([self.approval], approvals)


if __name__ == "__main__":
    unittest.main()
