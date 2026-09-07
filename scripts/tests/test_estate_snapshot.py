from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts
import estate_snapshot
import public_repository_classifications


GENERATED_AT = "2026-09-07T12:00:00Z"
SOURCE_COMMIT = "a" * 40


def make_runtime_entry(repository: str, lifecycle: str = "production") -> dict:
    return {
        "repository": repository,
        "local_directory": repository.split("/", 1)[1],
        "lifecycle": lifecycle,
        "scope": "public",
        "provenance": "original",
        "owner": "AtlasReaper311",
        "purpose": "fixture",
        "runtime_service": True,
        "contract_required": True,
        "public_surface": True,
        "service_ids": ["fixture"],
        "deployment_owner": repository,
        "evidence_owner": repository,
        "runbook_reference": "docs/runbooks/contract-registry-service-triage.md",
        "contract_exception": None,
        "notes": "fixture",
        "exclusions": [],
    }


def make_registry(*repositories: dict, approved: int | None = None) -> dict:
    items = list(repositories)
    return {
        "schema_version": "atlas-contract-registry/estate-registry/v1",
        "owner": "AtlasReaper311/atlas-infra",
        "reviewed_at": "2026-07-20T00:00:00Z",
        "approved_repository_count": len(items) if approved is None else approved,
        "classification_axes": {
            "lifecycle": ["active", "archived", "deprecated", "experimental", "production"],
            "scope": ["internal", "public"],
            "provenance": ["external-derived", "original"],
        },
        "repositories": items,
    }


def make_supplement(*repositories: dict) -> dict:
    return {
        "schema_version": "atlas-public-assurance/repositories/v2",
        "repositories": list(repositories),
    }


def github_item(
    repository: str,
    *,
    visibility: str = "public",
    private: bool = False,
    archived: bool = False,
) -> dict:
    return {
        "repository": repository,
        "default_branch": "main",
        "archived": archived,
        "private": private,
        "visibility": visibility,
    }


class EstateSnapshotTests(unittest.TestCase):
    def schema(self) -> dict:
        return json.loads((ROOT / "policy/estate-snapshot.schema.json").read_text(encoding="utf-8"))

    def snapshot(self, **kwargs) -> dict:
        payload = kwargs.get(
            "registry",
            make_registry(make_runtime_entry("AtlasReaper311/status")),
        )
        extra = kwargs.get(
            "supplement",
            make_supplement(
                {
                    "repository": "AtlasReaper311/atlas-infra",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                }
            ),
        )
        projection = kwargs.get(
            "projection",
            public_repository_classifications.build_projection(payload, extra),
        )
        return estate_snapshot.build_snapshot(
            registry=payload,
            supplement=extra,
            projection=projection,
            github_repositories=kwargs.get("github_repositories"),
            github_route=kwargs.get(
                "github_route", "github_rest:/user/repos?affiliation=owner&visibility=all"
            ),
            presentation=kwargs.get("presentation"),
            presentation_source=kwargs.get("presentation_source", "UNKNOWN / NOT OBSERVED"),
            generated_at=kwargs.get("generated_at", GENERATED_AT),
            source_commit=kwargs.get("source_commit", SOURCE_COMMIT),
        )

    def test_current_policy_snapshot_is_schema_valid_and_uses_projection(self) -> None:
        projection = public_repository_classifications.build_projection(
            json.loads((ROOT / "policy/estate-registry.json").read_text(encoding="utf-8")),
            json.loads(
                (ROOT / "policy/public-assurance-repositories.json").read_text(encoding="utf-8")
            ),
        )
        snapshot = estate_snapshot.build_from_paths(
            root=ROOT,
            registry_path=ROOT / "policy/estate-registry.json",
            supplement_path=ROOT / "policy/public-assurance-repositories.json",
            projection_path=ROOT / "policy/public-repository-classifications.json",
            github_observation=None,
            discover_github=False,
            token_env="ATLAS_ESTATE_READ_TOKEN",
            presentation_path=None,
            generated_at=GENERATED_AT,
            source_commit=SOURCE_COMMIT,
        )
        self.assertEqual([], control_plane_contracts.validate_instance(snapshot, self.schema()))
        self.assertEqual(
            projection["repository_count"],
            snapshot["estate"]["classified_repository_count"],
        )
        self.assertEqual(
            [item["repository"] for item in projection["repositories"]],
            [item["repository"] for item in snapshot["estate"]["repositories"]],
        )
        self.assertEqual("UNKNOWN / NOT OBSERVED", snapshot["observation"]["github"]["status"])
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            snapshot["estate"]["github_observed_repository_count"],
        )
        self.assertEqual("SOURCE", snapshot["estate"]["evidence_boundary"]["delivery_stage_claimed"])
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            snapshot["estate"]["evidence_boundary"]["later_stage_observation"],
        )

    def test_snapshot_is_deterministic_apart_from_generated_at(self) -> None:
        first = self.snapshot()
        second = self.snapshot(generated_at="2026-09-07T13:00:00Z")
        self.assertEqual(first["estate"], second["estate"])
        self.assertEqual(first["content_fingerprint"], second["content_fingerprint"])
        self.assertNotEqual(first["observation"]["generated_at"], second["observation"]["generated_at"])
        self.assertEqual(
            estate_snapshot.deterministic_payload(first),
            estate_snapshot.deterministic_payload(second),
        )

    def test_markdown_is_generated_from_the_same_model_as_json(self) -> None:
        snapshot = self.snapshot()
        markdown = estate_snapshot.render_markdown(snapshot)
        self.assertIn("AtlasReaper311/status", markdown)
        self.assertIn(snapshot["content_fingerprint"], markdown)
        self.assertIn("UNKNOWN / NOT OBSERVED", markdown)
        self.assertEqual(markdown, estate_snapshot.render_markdown(json.loads(estate_snapshot.render_json(snapshot))))

    def test_github_owned_repository_without_classification_is_missing_authority(self) -> None:
        snapshot = self.snapshot(
            github_repositories={
                "AtlasReaper311/status": github_item("AtlasReaper311/status"),
                "AtlasReaper311/atlas-infra": github_item("AtlasReaper311/atlas-infra"),
                "AtlasReaper311/unclassified": github_item("AtlasReaper311/unclassified"),
            }
        )
        self.assertEqual(3, snapshot["estate"]["github_observed_repository_count"])
        kinds = [item["kind"] for item in snapshot["estate"]["missing_authority"]]
        self.assertEqual(["github-without-classification"], kinds)
        self.assertEqual(
            "AtlasReaper311/unclassified",
            snapshot["estate"]["missing_authority"][0]["subject"],
        )
        classified = {
            item["repository"]: item for item in snapshot["estate"]["repositories"]
        }
        self.assertEqual("observed", classified["AtlasReaper311/status"]["github"]["observation"])
        self.assertEqual("production", classified["AtlasReaper311/status"]["lifecycle"])

    def test_classified_repository_missing_from_github_is_missing_authority(self) -> None:
        snapshot = self.snapshot(
            github_repositories={
                "AtlasReaper311/status": github_item("AtlasReaper311/status"),
            }
        )
        subjects = [item["subject"] for item in snapshot["estate"]["missing_authority"]]
        self.assertIn("AtlasReaper311/atlas-infra", subjects)

    def test_presentation_lifecycle_is_not_used_as_classification(self) -> None:
        snapshot = self.snapshot(
            presentation={
                "components": [
                    {
                        "name": "atlas-infra",
                        "kind": "docs",
                        "layer": "infra",
                        "lifecycle": "production",
                        "repo": "https://github.com/AtlasReaper311/atlas-infra",
                        "public_surface": "https://github.com/AtlasReaper311/atlas-infra",
                    },
                    {
                        "name": "ollama",
                        "kind": "local-service",
                        "layer": "local-ai",
                        "lifecycle": "production",
                        "repo": None,
                        "public_surface": "no direct public surface",
                    },
                ]
            },
            presentation_source="estate.manifest.json",
        )
        classified = {
            item["repository"]: item for item in snapshot["estate"]["repositories"]
        }
        self.assertEqual("active", classified["AtlasReaper311/atlas-infra"]["lifecycle"])
        self.assertEqual(
            ["presentation-lifecycle-mismatch"],
            [item["kind"] for item in snapshot["estate"]["contradictory_authority"]],
        )
        self.assertEqual(
            "NOT APPLICABLE",
            snapshot["estate"]["repository_less_topology"][0]["classification"],
        )
        self.assertEqual(
            "NOT APPLICABLE",
            classified["AtlasReaper311/status"]["topology"]["observation"],
        )

    def test_presentation_repo_without_classification_is_missing_authority(self) -> None:
        snapshot = self.snapshot(
            presentation={
                "components": [
                    {
                        "name": "mystery",
                        "kind": "tool",
                        "layer": "infra",
                        "lifecycle": "active",
                        "repo": "https://github.com/AtlasReaper311/mystery",
                        "public_surface": "GitHub",
                    }
                ]
            },
            presentation_source="estate.manifest.json",
        )
        self.assertEqual(
            "presentation-repo-without-classification",
            snapshot["estate"]["missing_authority"][0]["kind"],
        )

    def test_stale_projection_fails_closed(self) -> None:
        extra = make_supplement(
            {
                "repository": "AtlasReaper311/atlas-infra",
                "lifecycle": "active",
                "scope": "public",
                "provenance": "original",
            }
        )
        built = public_repository_classifications.build_projection(
            make_registry(make_runtime_entry("AtlasReaper311/status")),
            extra,
        )
        stale = json.loads(json.dumps(built))
        stale["repositories"][0]["lifecycle"] = "experimental"
        with self.assertRaisesRegex(estate_snapshot.EstateSnapshotError, "projection differs"):
            self.snapshot(projection=stale)

    def test_classification_overlap_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            public_repository_classifications.ClassificationProjectionError,
            "classification authority overlap",
        ):
            public_repository_classifications.build_projection(
                make_registry(make_runtime_entry("AtlasReaper311/status")),
                make_supplement(
                    {
                        "repository": "AtlasReaper311/status",
                        "lifecycle": "active",
                        "scope": "public",
                        "provenance": "original",
                    }
                ),
            )

    def test_registry_count_mismatch_is_reported_not_used_as_truth(self) -> None:
        snapshot = self.snapshot(
            registry=make_registry(make_runtime_entry("AtlasReaper311/status"), approved=99)
        )
        self.assertEqual(2, snapshot["estate"]["classified_repository_count"])
        self.assertEqual(
            "registry-count-mismatch",
            snapshot["estate"]["contradictory_authority"][0]["kind"],
        )

    def test_private_github_public_scope_is_contradictory(self) -> None:
        snapshot = self.snapshot(
            github_repositories={
                "AtlasReaper311/status": github_item(
                    "AtlasReaper311/status", visibility="private", private=True
                ),
                "AtlasReaper311/atlas-infra": github_item("AtlasReaper311/atlas-infra"),
            }
        )
        self.assertEqual(
            "github-private-public-scope",
            snapshot["estate"]["contradictory_authority"][0]["kind"],
        )

    def test_anonymous_github_discovery_is_refused(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "authenticated token"):
            estate_snapshot.discover_github("")

    def test_github_full_name_requires_github_host_not_substring(self) -> None:
        self.assertEqual(
            "AtlasReaper311/atlas-infra",
            estate_snapshot.github_full_name(
                "https://github.com/AtlasReaper311/atlas-infra.git"
            ),
        )
        self.assertEqual(
            "AtlasReaper311/atlas-infra",
            estate_snapshot.github_full_name("AtlasReaper311/atlas-infra"),
        )
        self.assertEqual(
            "AtlasReaper311/atlas-infra",
            estate_snapshot.github_full_name("github.com/AtlasReaper311/atlas-infra"),
        )
        self.assertIsNone(
            estate_snapshot.github_full_name(
                "https://evil.example/github.com/AtlasReaper311/atlas-infra"
            )
        )
        self.assertIsNone(
            estate_snapshot.github_full_name(
                "https://github.com.evil.example/AtlasReaper311/atlas-infra"
            )
        )
        self.assertIsNone(
            estate_snapshot.github_full_name("https://github.com/other/atlas-infra")
        )

    def test_discover_github_flag_calls_owned_listing_not_boolean(self) -> None:
        observed = {
            "AtlasReaper311/status": github_item("AtlasReaper311/status"),
            "AtlasReaper311/atlas-infra": github_item("AtlasReaper311/atlas-infra"),
        }
        with patch.object(
            estate_snapshot,
            "list_owned_github_repositories",
            return_value=observed,
        ) as mocked:
            snapshot = estate_snapshot.build_from_paths(
                root=ROOT,
                registry_path=ROOT / "policy/estate-registry.json",
                supplement_path=ROOT / "policy/public-assurance-repositories.json",
                projection_path=ROOT / "policy/public-repository-classifications.json",
                github_observation=None,
                discover_github=True,
                token_env="ATLAS_ESTATE_READ_TOKEN",
                presentation_path=None,
                generated_at=GENERATED_AT,
                source_commit=SOURCE_COMMIT,
            )
        mocked.assert_called_once()
        self.assertEqual("observed", snapshot["observation"]["github"]["status"])
        self.assertEqual(
            2,
            snapshot["estate"]["github_observed_repository_count"],
        )

    def test_check_cli_validates_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "estate-snapshot.json"
            markdown_out = Path(tmp) / "estate-snapshot.md"
            self.assertEqual(
                0,
                estate_snapshot.main(
                    [
                        "--root",
                        str(ROOT),
                        "--json-out",
                        str(json_out),
                        "--markdown-out",
                        str(markdown_out),
                        "--generated-at",
                        GENERATED_AT,
                        "--source-commit",
                        SOURCE_COMMIT,
                        "--check",
                    ]
                ),
            )
            self.assertFalse(json_out.exists())

    def test_write_and_check_agree_on_generated_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "estate-snapshot.json"
            markdown_out = Path(tmp) / "estate-snapshot.md"
            self.assertEqual(
                0,
                estate_snapshot.main(
                    [
                        "--root",
                        str(ROOT),
                        "--json-out",
                        str(json_out),
                        "--markdown-out",
                        str(markdown_out),
                        "--generated-at",
                        GENERATED_AT,
                        "--source-commit",
                        SOURCE_COMMIT,
                    ]
                ),
            )
            self.assertEqual(
                0,
                estate_snapshot.main(
                    [
                        "--root",
                        str(ROOT),
                        "--json-out",
                        str(json_out),
                        "--markdown-out",
                        str(markdown_out),
                        "--generated-at",
                        "2026-09-07T13:00:00Z",
                        "--source-commit",
                        SOURCE_COMMIT,
                        "--check",
                    ]
                ),
            )
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertEqual(
                markdown_out.read_text(encoding="utf-8"),
                estate_snapshot.render_markdown(payload),
            )


if __name__ == "__main__":
    unittest.main()
