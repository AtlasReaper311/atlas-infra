from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import public_boundary_audit  # noqa: E402


class FakeGitHubClient:
    def __init__(
        self,
        *,
        private_repositories=None,
        repository_metadata=None,
        contents=None,
    ):
        self.private_repositories = private_repositories or []
        self.repository_metadata = repository_metadata or {}
        self.contents = contents or {}
        self.paths: list[str] = []

    def paginate(self, path):
        self.paths.append(path)
        return list(self.private_repositories)

    def get(self, path):
        self.paths.append(path)
        if not path.startswith("/repos/"):
            raise AssertionError(f"unexpected fake GitHub path: {path}")

        remainder = path.removeprefix("/repos/")
        if "/contents/" in remainder:
            repository, source_path = remainder.split("/contents/", 1)
            key = (repository, source_path)
            if key not in self.contents:
                raise RuntimeError("missing fake projection content")
            text = self.contents[key]
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            }

        return self.repository_metadata.get(remainder, {"private": False})


class PublicBoundaryAuditTests(unittest.TestCase):
    def test_local_scan_finds_identity_without_echoing_or_hashing_it(self):
        protected = "private-example"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                f"This selected source names {protected}.\n",
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
            hashlib.sha256(protected.encode("utf-8")).hexdigest(),
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

    def test_projection_policy_requires_sorted_unique_public_coordinates(self):
        document = {
            "schema_version": public_boundary_audit.PROJECTION_POLICY_SCHEMA,
            "owner": "AtlasReaper311",
            "targets": [
                {
                    "repository": "AtlasReaper311/atlas-api-public",
                    "path": "data/estate.manifest.json",
                },
                {
                    "repository": "AtlasReaper311/atlas-infra",
                    "path": "policy/estate-registry.json",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            targets = public_boundary_audit.load_projection_targets(
                path,
                "AtlasReaper311",
            )

        self.assertEqual(document["targets"], targets)

    def test_projection_policy_rejects_unsorted_targets(self):
        document = {
            "schema_version": public_boundary_audit.PROJECTION_POLICY_SCHEMA,
            "owner": "AtlasReaper311",
            "targets": [
                {
                    "repository": "AtlasReaper311/atlas-infra",
                    "path": "policy/estate-registry.json",
                },
                {
                    "repository": "AtlasReaper311/atlas-api-public",
                    "path": "data/estate.manifest.json",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                public_boundary_audit.BoundaryAuditError,
                "must be sorted",
            ):
                public_boundary_audit.load_projection_targets(
                    path,
                    "AtlasReaper311",
                )

    def test_github_projection_audit_detects_identity_without_disclosing_it(self):
        identity = "private-example"
        target = {
            "repository": "AtlasReaper311/public-example",
            "path": "data/projection.json",
        }
        client = FakeGitHubClient(
            repository_metadata={"AtlasReaper311/public-example": {"private": False}},
            contents={
                ("AtlasReaper311/public-example", "data/projection.json"):
                    '{"repository":"private-example"}\n'
            },
        )

        report = public_boundary_audit.audit_github_public_projections(
            client,
            "AtlasReaper311",
            [identity],
            [target],
        )

        self.assertEqual("failed", report["status"])
        self.assertEqual(1, len(report["findings"]))
        self.assertEqual(target["repository"], report["findings"][0]["repository"])
        self.assertEqual(target["path"], report["findings"][0]["path"])
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn(identity, serialized)
        self.assertNotIn(
            hashlib.sha256(identity.encode("utf-8")).hexdigest(),
            serialized,
        )
        self.assertNotIn("protected_identity_count", report)

    def test_github_projection_audit_does_not_search_unscoped_source(self):
        target = {
            "repository": "AtlasReaper311/public-example",
            "path": "data/projection.json",
        }
        client = FakeGitHubClient(
            repository_metadata={"AtlasReaper311/public-example": {"private": False}},
            contents={
                ("AtlasReaper311/public-example", "data/projection.json"):
                    '{"repositories":[]}\n'
            },
        )

        report = public_boundary_audit.audit_github_public_projections(
            client,
            "AtlasReaper311",
            ["private-example"],
            [target],
        )

        self.assertEqual("passed", report["status"])
        self.assertFalse(any(path.startswith("/search/code") for path in client.paths))
        self.assertEqual(1, report["projection_targets_checked"])

    def test_github_projection_audit_refuses_private_target_repository(self):
        target = {
            "repository": "AtlasReaper311/not-public",
            "path": "data/projection.json",
        }
        client = FakeGitHubClient(
            repository_metadata={"AtlasReaper311/not-public": {"private": True}},
        )

        report = public_boundary_audit.audit_github_public_projections(
            client,
            "AtlasReaper311",
            ["private-example"],
            [target],
        )

        self.assertEqual("failed", report["status"])
        self.assertEqual([], report["findings"])
        self.assertEqual(1, len(report["errors"]))
        self.assertIn("not public", report["errors"][0])

    def test_committed_projection_policy_covers_only_projection_surfaces(self):
        path = REPO_ROOT / "policy" / "public-boundary-projections.json"
        targets = public_boundary_audit.load_projection_targets(path, "AtlasReaper311")
        coordinates = {(item["repository"], item["path"]) for item in targets}

        self.assertEqual(6, len(coordinates))
        self.assertIn(
            ("AtlasReaper311/atlas-infra", "policy/estate-registry.json"),
            coordinates,
        )
        self.assertIn(
            (
                "AtlasReaper311/atlas-infra",
                "policy/public-repository-classifications.json",
            ),
            coordinates,
        )
        self.assertIn(
            ("AtlasReaper311/atlas-api-public", "data/estate.manifest.json"),
            coordinates,
        )
        self.assertIn(
            ("AtlasReaper311/atlas-systems", "lab/speculum/topology.js"),
            coordinates,
        )
        for _, source_path in coordinates:
            self.assertFalse(source_path.startswith("docs/adrs/"))
            self.assertNotIn("/tests/", f"/{source_path}/")
            self.assertFalse(source_path.endswith(".css"))

    def test_markdown_contains_only_public_coordinates_and_finding_fingerprint(self):
        protected = "private-example"
        report = {
            "schema_version": public_boundary_audit.SCHEMA_VERSION,
            "mode": "github-public-projections",
            "projection_targets_checked": 1,
            "findings": [
                public_boundary_audit._redacted_finding(
                    "AtlasReaper311/public-example",
                    "data/projection.json",
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
        self.assertIn("Governed public projections checked", markdown)
        self.assertIn("AtlasReaper311/public-example", markdown)


if __name__ == "__main__":
    unittest.main()
