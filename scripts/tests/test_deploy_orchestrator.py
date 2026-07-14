from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import deploy_orchestrator  # noqa: E402


class DeployOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "contracts", self.root / "contracts")
        shutil.copytree(ROOT / "docs" / "runbooks", self.root / "docs" / "runbooks")
        (self.root / "policy").mkdir()
        for name in (
            "deploy-orchestrator.json",
            "deploy-orchestrator.schema.json",
            "deploy-plan.schema.json",
            "estate-registry.json",
            "estate-registry.schema.json",
        ):
            shutil.copy2(ROOT / "policy" / name, self.root / "policy" / name)
        shutil.copytree(
            ROOT / "policy" / "service-contracts",
            self.root / "policy" / "service-contracts",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def policy_path(self) -> Path:
        return self.root / "policy" / "deploy-orchestrator.json"

    @property
    def registry_path(self) -> Path:
        return self.root / "policy" / "estate-registry.json"

    @property
    def contracts_dir(self) -> Path:
        return self.root / "policy" / "service-contracts"

    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, path: Path, value: dict) -> None:
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def policy(self) -> dict:
        return self.load(self.policy_path)

    def registry(self) -> dict:
        return self.load(self.registry_path)

    def contract(self, service_id: str) -> dict:
        return self.load(self.contracts_dir / f"{service_id}.json")

    def write_contract(self, service_id: str, value: dict) -> None:
        self.write(self.contracts_dir / f"{service_id}.json", value)

    def target(self, policy: dict, service_id: str = "atlas-api-public") -> dict:
        return next(
            target for target in policy["targets"] if target["service_id"] == service_id
        )

    def registry_entry(self, registry: dict, repository: str) -> dict:
        return next(
            entry
            for entry in registry["repositories"]
            if entry["repository"] == repository
        )

    def validate(self) -> dict:
        return deploy_orchestrator.validate_deploy_policy(
            root=self.root,
            policy_path=self.policy_path,
            registry_path=self.registry_path,
            contracts_dir=self.contracts_dir,
        )

    def plan(
        self,
        service: str = "atlas-api-public",
        environment: str = "production",
        *,
        execute: bool = False,
        commit: str | None = None,
    ) -> dict:
        return deploy_orchestrator.build_plan(
            root=self.root,
            policy_path=self.policy_path,
            registry_path=self.registry_path,
            contracts_dir=self.contracts_dir,
            requested_services=[service],
            environment=environment,
            execute=execute,
            commit=commit,
        )

    def rules(self, report: dict) -> set[str]:
        return {finding["rule_id"] for finding in report["findings"]}

    def add_index_dependency(self) -> None:
        policy = self.policy()
        public = self.target(policy)
        index = copy.deepcopy(public)
        index["service_id"] = "atlas-api-index"
        index["repository"] = "AtlasReaper311/atlas-api-index"
        index["owner"] = "github:AtlasReaper311"
        index["post_deploy_release_watch"]["journey_target"] = "api-contract"
        public["dependencies"] = ["atlas-api-index"]
        policy["targets"].append(index)
        policy["targets"].sort(
            key=lambda target: (target["service_id"], target["environment"])
        )
        self.write(self.policy_path, policy)

    def change_classification(self, field: str, value: str) -> None:
        repository = "AtlasReaper311/atlas-api-public"
        registry = self.registry()
        self.registry_entry(registry, repository)[field] = value
        self.write(self.registry_path, registry)
        contract = self.contract("atlas-api-public")
        contract["classification"][field] = value
        self.write_contract("atlas-api-public", contract)

    def test_valid_deployment_plan(self) -> None:
        report = self.plan(commit="1" * 40)
        self.assertEqual("ready", report["status"])
        self.assertEqual(["atlas-api-public"], report["order"])
        self.assertEqual([], report["findings"])
        self.assertEqual([], report["plan_schema_errors"])

    def test_dependency_ordering(self) -> None:
        self.add_index_dependency()
        report = self.plan()
        self.assertEqual("ready", report["status"])
        self.assertEqual(["atlas-api-index", "atlas-api-public"], report["order"])

    def test_cycle_detection(self) -> None:
        self.add_index_dependency()
        policy = self.policy()
        self.target(policy, "atlas-api-index")["dependencies"] = ["atlas-api-public"]
        self.write(self.policy_path, policy)
        self.assertIn("dependency-cycle", self.rules(self.validate()))

    def test_missing_dependency(self) -> None:
        policy = self.policy()
        self.target(policy)["dependencies"] = ["missing-service"]
        self.write(self.policy_path, policy)
        self.assertIn("missing-dependency", self.rules(self.validate()))

    def test_disabled_service_refusal(self) -> None:
        policy = self.policy()
        self.target(policy)["disabled"] = True
        self.write(self.policy_path, policy)
        report = self.plan()
        self.assertEqual("invalid", report["status"])
        self.assertIn("disabled-service-requested", self.rules(report))

    def test_simple_proxy_exclusion(self) -> None:
        policy = self.policy()
        proxy = copy.deepcopy(self.target(policy))
        proxy["service_id"] = "simple-proxy"
        proxy["repository"] = "AtlasReaper311/simple-proxy"
        proxy["disabled"] = False
        policy["targets"].append(proxy)
        policy["targets"].sort(
            key=lambda target: (target["service_id"], target["environment"])
        )
        self.write(self.policy_path, policy)
        report = self.plan("simple-proxy")
        self.assertIn("service-excluded", self.rules(report))

    def test_deprecated_repository_refusal(self) -> None:
        self.change_classification("lifecycle", "deprecated")
        self.assertIn("deprecated-service-ineligible", self.rules(self.plan()))

    def test_archived_repository_refusal(self) -> None:
        self.change_classification("lifecycle", "archived")
        self.assertIn("archived-service-ineligible", self.rules(self.plan()))

    def test_external_derived_default_refusal(self) -> None:
        self.change_classification("provenance", "external-derived")
        self.assertIn("external-derived-ineligible", self.rules(self.plan()))

    def test_missing_deploy_workflow(self) -> None:
        policy = self.policy()
        self.target(policy)["dispatch"].pop("workflow")
        self.write(self.policy_path, policy)
        self.assertIn("missing-deploy-workflow", self.rules(self.validate()))

    def test_missing_owner(self) -> None:
        policy = self.policy()
        self.target(policy).pop("owner")
        self.write(self.policy_path, policy)
        self.assertIn("missing-owner", self.rules(self.validate()))

    def test_missing_rollback_runbook(self) -> None:
        policy = self.policy()
        self.target(policy).pop("rollback_runbook")
        self.write(self.policy_path, policy)
        self.assertIn("missing-rollback-runbook", self.rules(self.validate()))

    def test_dry_run_is_default(self) -> None:
        report = self.plan()
        self.assertEqual("dry-run", report["mode"])
        self.assertFalse(report["execution"]["requested"])
        self.assertFalse(report["execution"]["allowed"])
        self.assertEqual("noop", report["execution"]["executor"])

    def test_execute_refusal_by_default(self) -> None:
        report = self.plan(execute=True)
        self.assertEqual("invalid", report["status"])
        self.assertIn("dispatch-execution-disabled", self.rules(report))
        self.assertIn("production-approval-missing", self.rules(report))

    def test_approval_required_for_production(self) -> None:
        report = self.plan()
        self.assertTrue(report["approval"]["required"])
        self.assertEqual("missing", report["approval"]["status"])
        self.assertEqual(
            ["owner", "production-environment"], report["approval"]["gates"]
        )
        self.assertFalse(report["approval"]["protected_environment"]["bypass_allowed"])
        self.assertFalse(report["approval"]["two_owner_fallback"]["implemented"])

    def test_post_deploy_release_watch_plan_is_included(self) -> None:
        report = self.plan(commit="2" * 40)
        release = report["dispatches"][0]["post_deploy_release_watch"]
        self.assertEqual(
            "https://api.atlas-systems.uk/v1/_meta", release["metadata_endpoint"]
        )
        self.assertEqual("release-watch.yml", release["dispatch"]["workflow"])
        self.assertEqual("api-contract", release["journey_target"])
        self.assertEqual("2" * 40, release["expected_commit"])
        self.assertIn("gh workflow run release-watch.yml", release["command"])
        self.assertFalse(release["registry_eligible"])

    def test_finding_schema_validation(self) -> None:
        policy = self.policy()
        self.target(policy)["disabled"] = True
        self.write(self.policy_path, policy)
        report = self.plan()
        self.assertTrue(report["findings"])
        self.assertEqual([], report["finding_schema_errors"])

    def test_deterministic_output(self) -> None:
        first = self.plan(commit="3" * 40)
        second = self.plan(commit="3" * 40)
        self.assertEqual(first, second)
        self.assertEqual(
            sorted(first["dispatches"], key=deploy_orchestrator.canonical_json),
            first["dispatches"],
        )

    def test_aggregate_release_evidence_reference_is_planned(self) -> None:
        evidence = self.plan()["aggregate_release_evidence"]
        self.assertEqual("planned", evidence["status"])
        self.assertEqual(
            "contracts/v1/release-evidence.schema.json",
            evidence["release_evidence_contract"],
        )
        self.assertEqual("not-created", evidence["records"][0]["status"])

    def test_policy_validation_is_idempotent(self) -> None:
        self.assertEqual(self.validate(), self.validate())

    def test_cli_generates_markdown_and_json_reports(self) -> None:
        output = self.root / "output"
        command = [
            sys.executable,
            str(SCRIPTS / "deploy_orchestrator.py"),
            "plan",
            "--root",
            str(self.root),
            "--service",
            "atlas-api-public",
            "--environment",
            "production",
            "--output",
            str(output / "plan.json"),
            "--markdown",
            str(output / "plan.md"),
            "--quiet",
        ]
        subprocess.run(command, check=True)
        report = self.load(output / "plan.json")
        self.assertEqual("ready", report["status"])
        self.assertTrue(report["idempotent"])
        self.assertIn(
            "Dependency-resolved order",
            (output / "plan.md").read_text(encoding="utf-8"),
        )

    def test_cli_output_is_byte_idempotent(self) -> None:
        report_path = self.root / "plan.json"
        command = [
            sys.executable,
            str(SCRIPTS / "deploy_orchestrator.py"),
            "plan",
            "--root",
            str(self.root),
            "--service",
            "atlas-api-public",
            "--environment",
            "production",
            "--output",
            str(report_path),
            "--quiet",
        ]
        subprocess.run(command, check=True)
        first = report_path.read_bytes()
        subprocess.run(command, check=True)
        self.assertEqual(first, report_path.read_bytes())

    def test_cli_execute_is_refused(self) -> None:
        command = [
            sys.executable,
            str(SCRIPTS / "deploy_orchestrator.py"),
            "plan",
            "--root",
            str(self.root),
            "--service",
            "atlas-api-public",
            "--environment",
            "production",
            "--execute",
            "--quiet",
        ]
        result = subprocess.run(command, check=False)
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
