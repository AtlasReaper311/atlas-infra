from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts
import estate_drift
import public_repository_classifications


GENERATED_AT = "2026-09-07T12:00:00Z"
SOURCE_COMMIT = "b" * 40
FIXTURES = ROOT / "tests/fixtures/estate-drift"


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


class EstateDriftTests(unittest.TestCase):
    def schema(self) -> dict:
        return json.loads((ROOT / "policy/estate-drift.schema.json").read_text(encoding="utf-8"))

    def report(self, **kwargs) -> dict:
        registry = kwargs.get(
            "registry",
            make_registry(make_runtime_entry("AtlasReaper311/status")),
        )
        supplement = kwargs.get(
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
        built = public_repository_classifications.build_projection(registry, supplement)
        committed_text = kwargs.get(
            "committed_projection_text",
            public_repository_classifications.render_json(built),
        )
        return estate_drift.build_report(
            registry=registry,
            supplement=supplement,
            committed_projection_text=committed_text,
            github_repositories=kwargs.get("github_repositories"),
            github_route=kwargs.get(
                "github_route", "github_rest:/user/repos?affiliation=owner&visibility=all"
            ),
            github_source=kwargs.get("github_source", "UNKNOWN / NOT OBSERVED"),
            presentation=kwargs.get("presentation"),
            presentation_source=kwargs.get(
                "presentation_source", "UNKNOWN / NOT OBSERVED"
            ),
            generated_at=kwargs.get("generated_at", GENERATED_AT),
            source_commit=kwargs.get("source_commit", SOURCE_COMMIT),
        )

    def kinds(self, report: dict) -> list[str]:
        return [item["kind"] for item in report["findings"]]

    def test_current_policy_is_schema_valid_and_keeps_missing_observation_unknown(self) -> None:
        report = estate_drift.build_from_paths(
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
        self.assertEqual([], control_plane_contracts.validate_instance(report, self.schema()))
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            report["classes"]["owned-public-missing-classification"]["status"],
        )
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            report["classes"]["presentation-conflicts-with-classification"]["status"],
        )
        self.assertEqual("agree", report["classes"]["projection-differs-from-authority"]["status"])
        self.assertEqual(
            "agree", report["classes"]["hand-maintained-current-truth-conflict"]["status"]
        )
        self.assertEqual("agree", report["classes"]["duplicate-or-ambiguous-ownership"]["status"])
        self.assertFalse(report["summary"]["blocking"])
        self.assertEqual("SOURCE", report["evidence_boundary"]["delivery_stage_claimed"])
        self.assertTrue(report["observation"]["snapshot_content_fingerprint"].startswith("sha256:"))

    def test_report_is_deterministic_apart_from_generated_at(self) -> None:
        first = self.report()
        second = self.report(generated_at="2026-09-07T13:00:00Z")
        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(first["content_fingerprint"], second["content_fingerprint"])
        self.assertNotEqual(
            first["observation"]["generated_at"], second["observation"]["generated_at"]
        )
        self.assertEqual(
            estate_drift.deterministic_payload(first),
            estate_drift.deterministic_payload(second),
        )

    def test_markdown_is_generated_from_the_same_model_as_json(self) -> None:
        report = self.report()
        markdown = estate_drift.render_markdown(report)
        self.assertIn("UNKNOWN / NOT OBSERVED", markdown)
        self.assertIn(report["content_fingerprint"], markdown)
        self.assertEqual(
            markdown,
            estate_drift.render_markdown(json.loads(estate_drift.render_json(report))),
        )

    def test_owned_public_repository_missing_classification_from_github_fixture(self) -> None:
        observation = json.loads(
            (FIXTURES / "github-unclassified-public.json").read_text(encoding="utf-8")
        )
        github = {
            item["repository"]: item for item in observation["repositories"]
        }
        report = self.report(github_repositories=github, github_source=observation["route"])
        missing = [
            item
            for item in report["findings"]
            if item["kind"] == "owned-public-missing-classification"
        ]
        self.assertEqual(["AtlasReaper311/unclassified-public"], [item["subject"] for item in missing])
        self.assertEqual("observation-derived-drift", missing[0]["result_class"])
        self.assertTrue(report["summary"]["blocking"])
        self.assertNotIn(
            "AtlasReaper311/private-unclassified",
            [item["subject"] for item in missing],
        )

    def test_missing_github_observation_is_unknown_not_a_clean_pass(self) -> None:
        report = self.report(github_repositories=None)
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            report["classes"]["owned-public-missing-classification"]["status"],
        )
        self.assertFalse(report["summary"]["blocking"])

    def test_stale_projection_is_detected_with_owning_generator(self) -> None:
        registry = make_registry(make_runtime_entry("AtlasReaper311/status"))
        supplement = make_supplement(
            {
                "repository": "AtlasReaper311/atlas-infra",
                "lifecycle": "active",
                "scope": "public",
                "provenance": "original",
            }
        )
        built = public_repository_classifications.build_projection(registry, supplement)
        stale = json.loads(json.dumps(built))
        stale["repositories"][0]["lifecycle"] = "experimental"
        report = self.report(
            registry=registry,
            supplement=supplement,
            committed_projection_text=public_repository_classifications.render_json(stale),
        )
        self.assertIn("projection-differs-from-authority", self.kinds(report))
        self.assertEqual("disagree", report["classes"]["projection-differs-from-authority"]["status"])
        self.assertTrue(report["summary"]["blocking"])

    def test_presentation_fixture_conflicts_on_lifecycle_scope_and_provenance(self) -> None:
        presentation = json.loads(
            (FIXTURES / "presentation-classification-conflict.json").read_text(encoding="utf-8")
        )
        report = self.report(
            presentation=presentation,
            presentation_source="tests/fixtures/estate-drift/presentation-classification-conflict.json",
        )
        subjects = [
            item["subject"]
            for item in report["findings"]
            if item["kind"] == "presentation-conflicts-with-classification"
        ]
        self.assertIn("AtlasReaper311/atlas-infra:atlas-infra:lifecycle", subjects)
        self.assertIn("AtlasReaper311/atlas-infra:atlas-infra:scope", subjects)
        self.assertIn("AtlasReaper311/atlas-infra:atlas-infra:provenance", subjects)
        self.assertIn("AtlasReaper311/mystery:mystery", subjects)
        self.assertTrue(
            all(
                item["result_class"] == "observation-derived-drift"
                for item in report["findings"]
                if item["kind"] == "presentation-conflicts-with-classification"
            )
        )

    def test_missing_presentation_observation_is_unknown(self) -> None:
        report = self.report(presentation=None)
        self.assertEqual(
            "UNKNOWN / NOT OBSERVED",
            report["classes"]["presentation-conflicts-with-classification"]["status"],
        )

    def test_hand_maintained_registry_count_conflict(self) -> None:
        report = self.report(
            registry=make_registry(make_runtime_entry("AtlasReaper311/status"), approved=99)
        )
        self.assertIn("hand-maintained-current-truth-conflict", self.kinds(report))
        self.assertEqual(
            "disagree",
            report["classes"]["hand-maintained-current-truth-conflict"]["status"],
        )
        self.assertTrue(report["summary"]["blocking"])

    def test_planning_fixture_is_not_current_truth(self) -> None:
        relative = "tests/fixtures/estate-drift/planning-stale-count.md"
        self.assertTrue((ROOT / relative).is_file())
        self.assertIn("12 repositories", (ROOT / relative).read_text(encoding="utf-8"))
        self.assertFalse(estate_drift.is_current_truth_path(relative))
        self.assertFalse(estate_drift.is_current_truth_path("docs/2026-completion-roadmap.md"))
        self.assertTrue(estate_drift.is_current_truth_path("policy/estate-registry.json"))
        report = self.report()
        self.assertNotIn("hand-maintained-current-truth-conflict", self.kinds(report))

    def test_duplicate_authority_fails_closed_without_choosing_a_winner(self) -> None:
        report = estate_drift.build_report(
            registry=make_registry(make_runtime_entry("AtlasReaper311/status")),
            supplement=make_supplement(
                {
                    "repository": "AtlasReaper311/status",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                }
            ),
            committed_projection_text="{}",
            github_repositories=None,
            github_route="github_rest:/user/repos?affiliation=owner&visibility=all",
            github_source="UNKNOWN / NOT OBSERVED",
            presentation=None,
            presentation_source="UNKNOWN / NOT OBSERVED",
            generated_at=GENERATED_AT,
            source_commit=SOURCE_COMMIT,
        )
        self.assertIn("duplicate-or-ambiguous-ownership", self.kinds(report))
        self.assertTrue(report["summary"]["blocking"])
        self.assertEqual("disagree", report["classes"]["duplicate-or-ambiguous-ownership"]["status"])

    def test_casefold_duplicate_identities_fail_closed(self) -> None:
        report = self.report(
            registry=make_registry(make_runtime_entry("AtlasReaper311/status")),
            supplement=make_supplement(
                {
                    "repository": "AtlasReaper311/Status",
                    "lifecycle": "active",
                    "scope": "public",
                    "provenance": "original",
                }
            ),
        )
        self.assertIn("duplicate-or-ambiguous-ownership", self.kinds(report))
        self.assertTrue(report["summary"]["blocking"])

    def test_malformed_snapshot_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            registry.write_text("{not json", encoding="utf-8")
            self.assertEqual(
                2,
                estate_drift.main(
                    [
                        "--root",
                        str(root),
                        "--registry",
                        str(registry),
                        "--supplement",
                        str(ROOT / "policy/public-assurance-repositories.json"),
                        "--projection",
                        str(ROOT / "policy/public-repository-classifications.json"),
                        "--schema",
                        str(ROOT / "policy/estate-drift.schema.json"),
                        "--check",
                    ]
                ),
            )

    def test_check_cli_accepts_current_authority_without_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "estate-drift.json"
            markdown_out = Path(tmp) / "estate-drift.md"
            self.assertEqual(
                0,
                estate_drift.main(
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
            json_out = Path(tmp) / "estate-drift.json"
            markdown_out = Path(tmp) / "estate-drift.md"
            self.assertEqual(
                0,
                estate_drift.main(
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
                estate_drift.main(
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
                estate_drift.render_markdown(payload),
            )

    def test_supplied_github_fixture_cli_surfaces_observation_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "estate-drift.json"
            markdown_out = Path(tmp) / "estate-drift.md"
            status = estate_drift.main(
                [
                    "--root",
                    str(ROOT),
                    "--github-observation",
                    str(FIXTURES / "github-unclassified-public.json"),
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
            )
            self.assertEqual(2, status)

    def test_workflows_run_deterministic_drift_check(self) -> None:
        estate_policy = (ROOT / ".github/workflows/estate-policy.yml").read_text(encoding="utf-8")
        contract_ci = (
            ROOT / ".github/workflows/contract-registry-ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python3 -m py_compile scripts/estate_drift.py", estate_policy)
        self.assertIn("python3 scripts/estate_drift.py --check", estate_policy)
        self.assertIn("scripts/estate_drift.py", contract_ci)
        self.assertIn("policy/estate-drift.schema.json", contract_ci)
        self.assertIn("python3 scripts/estate_drift.py --check", contract_ci)


if __name__ == "__main__":
    unittest.main()
