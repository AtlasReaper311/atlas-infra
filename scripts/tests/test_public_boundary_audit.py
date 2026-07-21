from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import public_boundary_audit  # noqa: E402


class FakeGitHubClient:
    def __init__(self, private_repositories=None, search_items=None):
        self.private_repositories = private_repositories or []
        self.search_items = search_items or {}
        self.paths: list[str] = []

    def paginate(self, path):
        self.paths.append(path)
        return list(self.private_repositories)

    def get(self, path):
        self.paths.append(path)
        for identity, items in self.search_items.items():
            encoded = identity.replace("/", "%2F")
            if identity in path or encoded in path:
                return {"total_count": len(items), "items": list(items)}
        return {"total_count": 0, "items": []}


class PublicBoundaryAuditTests(unittest.TestCase):
    def test_local_scan_finds_identity_without_echoing_or_hashing_it(self):
        protected = "private-example"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                f"This stale public text names {protected}.\n",
                encoding="utf-8",
            )

            report = public_boundary_audit.audit_local_tree(
                root,
                [protected],
                repository="AtlasReaper311/public-example",
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["findings"]))
        self.assertEqual("README.md", report["findings"][0]["path"])
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn(protected, serialized)
        self.assertNotIn(
            __import__("hashlib").sha256(protected.encode("utf-8")).hexdigest(),
            serialized,
        )
        self.assertIn("sha256:", report["findings"][0]["fingerprint"])
        self.assertNotIn("protected_identity_count", report)

    def test_multiple_protected_identities_on_one_line_emit_one_public_coordinate(self):
        protected = ["private-example-one", "private-example-two"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "references " + " and ".join(protected) + "\n",
                encoding="utf-8",
            )

            report = public_boundary_audit.audit_local_tree(root, protected)

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["findings"]))
        serialized = json.dumps(report, sort_keys=True)
        for identity in protected:
            self.assertNotIn(identity, serialized)

    def test_local_scan_ignores_binary_and_explicit_exclusion(self):
        protected = "private-example"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ignored.txt").write_text(protected + "\n", encoding="utf-8")
            (root / "image.png").write_bytes(protected.encode("utf-8"))
            (root / "safe.md").write_text("public text\n", encoding="utf-8")

            report = public_boundary_audit.audit_local_tree(
                root,
                [protected],
                excluded_paths=["ignored.txt"],
            )

        self.assertEqual("passed", report["status"])
        self.assertEqual([], report["findings"])
        self.assertEqual([], report["errors"])

    def test_oversized_text_fails_closed(self):
        protected = "private-example"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.txt").write_text(
                "x" * (public_boundary_audit.MAX_LOCAL_FILE_BYTES + 1),
                encoding="utf-8",
            )

            report = public_boundary_audit.audit_local_tree(root, [protected])

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["errors"]))
        self.assertIn("size bound", report["errors"][0])
        self.assertNotIn(protected, json.dumps(report))

    def test_private_identity_discovery_returns_name_and_full_name_in_memory(self):
        client = FakeGitHubClient(
            private_repositories=[
                {
                    "name": "private-example",
                    "full_name": "AtlasReaper311/private-example",
                    "private": True,
                    "owner": {"login": "AtlasReaper311"},
                },
                {
                    "name": "other-owner-private",
                    "full_name": "someone/other-owner-private",
                    "private": True,
                    "owner": {"login": "someone"},
                },
            ]
        )

        identities = public_boundary_audit.discover_private_identities(
            client,
            "AtlasReaper311",
        )

        self.assertEqual(
            ["AtlasReaper311/private-example", "private-example"],
            identities,
        )

    def test_private_identity_discovery_fails_when_authenticated_context_is_empty(self):
        with self.assertRaisesRegex(
            public_boundary_audit.BoundaryAuditError,
            "returned no protected repository identities",
        ):
            public_boundary_audit.discover_private_identities(
                FakeGitHubClient(),
                "AtlasReaper311",
            )

    def test_github_audit_keeps_only_public_matches_and_redacts_identity(self):
        identity = "private-example"
        client = FakeGitHubClient(
            search_items={
                identity: [
                    {
                        "path": "README.md",
                        "repository": {
                            "full_name": "AtlasReaper311/public-example",
                            "private": False,
                            "owner": {"login": "AtlasReaper311"},
                        },
                    },
                    {
                        "path": "private.md",
                        "repository": {
                            "full_name": "AtlasReaper311/private-example",
                            "private": True,
                            "owner": {"login": "AtlasReaper311"},
                        },
                    },
                ]
            }
        )

        report = public_boundary_audit.audit_github_public_source(
            client,
            "AtlasReaper311",
            [identity],
        )

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["findings"]))
        self.assertEqual(
            "AtlasReaper311/public-example",
            report["findings"][0]["repository"],
        )
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn(identity, serialized)
        self.assertNotIn("protected_identity_count", report)
        self.assertNotIn("searches_performed", report)

    def test_markdown_contains_only_public_coordinates_and_finding_fingerprint(self):
        protected = "private-example"
        report = {
            "schema_version": public_boundary_audit.SCHEMA_VERSION,
            "mode": "local",
            "files_checked": 1,
            "findings": [
                public_boundary_audit._redacted_finding(
                    "AtlasReaper311/public-example",
                    "README.md",
                    line=4,
                )
            ],
            "errors": [],
            "status": "failed",
        }

        markdown = public_boundary_audit.render_markdown(report)

        self.assertNotIn(protected, markdown)
        self.assertNotIn("Protected identity fingerprint", markdown)
        self.assertNotIn("Protected identities evaluated", markdown)
        self.assertIn("Finding fingerprint", markdown)
        self.assertIn("AtlasReaper311/public-example", markdown)


if __name__ == "__main__":
    unittest.main()
