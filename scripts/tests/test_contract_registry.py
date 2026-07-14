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

import contract_registry  # noqa: E402
import control_plane_contracts  # noqa: E402


class ContractRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "contracts", self.root / "contracts")
        shutil.copytree(ROOT / "docs" / "runbooks", self.root / "docs" / "runbooks")
        (self.root / "policy").mkdir()
        shutil.copy2(
            ROOT / "policy" / "estate-registry.schema.json",
            self.root / "policy" / "estate-registry.schema.json",
        )
        shutil.copy2(
            ROOT / "policy" / "estate-registry.json",
            self.root / "policy" / "estate-registry.json",
        )
        shutil.copytree(
            ROOT / "policy" / "service-contracts",
            self.root / "policy" / "service-contracts",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

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
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def registry(self) -> dict:
        return self.load(self.registry_path)

    def contract(self, service_id: str) -> dict:
        return self.load(self.contracts_dir / f"{service_id}.json")

    def write_contract(self, service_id: str, value: dict) -> None:
        self.write(self.contracts_dir / f"{service_id}.json", value)

    def entry(self, registry: dict, repository: str) -> dict:
        return next(
            item
            for item in registry["repositories"]
            if item["repository"] == repository
        )

    def validate(self) -> dict:
        return contract_registry.validate_contract_registry(
            root=self.root,
            registry_path=self.registry_path,
            contracts_dir=self.contracts_dir,
        )

    def rules(self, report: dict) -> set[str]:
        return {finding["rule_id"] for finding in report["findings"]}

    def test_canonical_registry_contains_all_34_repositories(self) -> None:
        report = self.validate()
        self.assertEqual("passed", report["status"])
        self.assertEqual(34, report["repositories_checked"])
        self.assertEqual(
            set(contract_registry.EXPECTED_REPOSITORIES),
            {item["repository"] for item in self.registry()["repositories"]},
        )

    def test_classification_axes_are_valid_and_independent(self) -> None:
        registry = self.registry()
        normalized = {
            key: sorted(value) for key, value in registry["classification_axes"].items()
        }
        self.assertEqual(contract_registry.CLASSIFICATION_AXES, normalized)
        for entry in registry["repositories"]:
            self.assertIn(entry["lifecycle"], normalized["lifecycle"])
            self.assertIn(entry["scope"], normalized["scope"])
            self.assertIn(entry["provenance"], normalized["provenance"])

    def test_simple_proxy_classification_and_exclusions(self) -> None:
        entry = self.entry(self.registry(), "AtlasReaper311/simple-proxy")
        self.assertEqual("deprecated", entry["lifecycle"])
        self.assertEqual("internal", entry["scope"])
        self.assertEqual("external-derived", entry["provenance"])
        self.assertFalse(entry["public_surface"])
        self.assertTrue(
            contract_registry.SIMPLE_PROXY_EXCLUSIONS.issubset(entry["exclusions"])
        )
        contract = self.contract("simple-proxy")
        self.assertEqual([], contract["routes"])
        self.assertTrue(not any(contract["control_plane_policy"].values()))

    def test_valid_service_contract_conforms_to_v1_schema(self) -> None:
        contract = self.contract("atlas-api-public")
        schema = self.load(
            self.root / "contracts" / "v1" / "service-contract.schema.json"
        )
        rules = self.load(self.root / "contracts" / "v1" / "fingerprint-rules.json")
        errors = control_plane_contracts.validate_instance(contract, schema)
        errors.extend(
            control_plane_contracts.semantic_errors(
                "service-contract.schema.json", contract, rules
            )
        )
        self.assertEqual([], errors)

    def test_malformed_service_contract_is_rejected(self) -> None:
        contract = self.contract("atlas-api-index")
        contract.pop("runtime")
        self.write_contract("atlas-api-index", contract)
        self.assertIn("contract-schema-invalid", self.rules(self.validate()))

    def test_duplicate_route_owner_is_rejected(self) -> None:
        contract = self.contract("atlas-api-public")
        contract["routes"].append(
            copy.deepcopy(self.contract("atlas-api-index")["routes"][0])
        )
        contract["routes"].sort(
            key=lambda route: (
                route["origin"],
                route["path"],
                control_plane_contracts.canonical_json(route["methods"]),
                route["visibility"],
            )
        )
        self.write_contract("atlas-api-public", contract)
        self.assertIn("duplicate-route-owner", self.rules(self.validate()))

    def test_missing_service_owner_is_rejected(self) -> None:
        contract = self.contract("atlas-api-index")
        contract["owner"] = {}
        self.write_contract("atlas-api-index", contract)
        self.assertIn("missing-service-owner", self.rules(self.validate()))

    def test_runtime_service_missing_contract_is_rejected(self) -> None:
        (self.contracts_dir / "atlas-api-index.json").unlink()
        self.assertIn("missing-service-contract", self.rules(self.validate()))

    def test_contract_for_non_runtime_repository_requires_exception(self) -> None:
        registry = self.registry()
        entry = self.entry(registry, "AtlasReaper311/atlas-api-index")
        entry["runtime_service"] = False
        self.write(self.registry_path, registry)
        self.assertIn("non-runtime-contract", self.rules(self.validate()))

    def test_missing_runbook_for_production_runtime_is_rejected(self) -> None:
        registry = self.registry()
        self.entry(registry, "AtlasReaper311/atlas-api-index")["runbook_reference"] = (
            None
        )
        self.write(self.registry_path, registry)
        contract = self.contract("atlas-api-index")
        contract["runbooks"] = []
        self.write_contract("atlas-api-index", contract)
        self.assertIn("missing-production-runbook", self.rules(self.validate()))

    def test_deprecated_repository_cannot_claim_route(self) -> None:
        contract = self.contract("simple-proxy")
        contract["routes"] = [
            {
                "origin": "https://proxy.invalid",
                "path": "/proxy",
                "methods": ["GET"],
                "visibility": "authenticated",
            }
        ]
        self.write_contract("simple-proxy", contract)
        self.assertIn("deprecated-route-owner", self.rules(self.validate()))

    def test_archived_repository_cannot_claim_route(self) -> None:
        registry = self.registry()
        self.entry(registry, "AtlasReaper311/atlas-api-index")["lifecycle"] = "archived"
        self.write(self.registry_path, registry)
        contract = self.contract("atlas-api-index")
        contract["classification"]["lifecycle"] = "archived"
        self.write_contract("atlas-api-index", contract)
        self.assertIn("archived-route-owner", self.rules(self.validate()))

    def test_external_derived_repository_cannot_enable_active_features(self) -> None:
        contract = self.contract("simple-proxy")
        contract["control_plane_policy"]["new_features"] = True
        self.write_contract("simple-proxy", contract)
        self.assertIn("external-derived-active-feature", self.rules(self.validate()))

    def test_public_route_on_internal_service_requires_exception(self) -> None:
        registry = self.registry()
        self.entry(registry, "AtlasReaper311/atlas-api-index")["scope"] = "internal"
        self.write(self.registry_path, registry)
        contract = self.contract("atlas-api-index")
        contract["classification"]["scope"] = "internal"
        self.write_contract("atlas-api-index", contract)
        self.assertIn("public-internal-mismatch", self.rules(self.validate()))

    def test_unknown_service_id_is_rejected(self) -> None:
        contract = self.contract("atlas-api-index")
        contract["dependencies"] = ["unknown-service"]
        self.write_contract("atlas-api-index", contract)
        self.assertIn("unknown-service-id", self.rules(self.validate()))

    def test_missing_metadata_endpoint_is_rejected_for_release_watch(self) -> None:
        contract = self.contract("atlas-api-index")
        contract["release_watch_eligible"] = True
        contract["metadata_route"] = None
        contract["metadata_endpoint"] = {
            "state": "unknown",
            "origin": None,
            "path": None,
            "expected_shape": "unknown",
        }
        self.write_contract("atlas-api-index", contract)
        self.assertIn("missing-metadata-endpoint", self.rules(self.validate()))

    def test_registry_lifecycle_mismatch_is_rejected(self) -> None:
        contract = self.contract("atlas-api-index")
        contract["classification"]["scope"] = "internal"
        self.write_contract("atlas-api-index", contract)
        self.assertIn("lifecycle-conflict", self.rules(self.validate()))

    def test_stale_registry_entry_is_rejected(self) -> None:
        registry = self.registry()
        extra = copy.deepcopy(registry["repositories"][0])
        extra["repository"] = "AtlasReaper311/stale-example"
        extra["local_directory"] = "stale-example"
        registry["repositories"].append(extra)
        registry["repositories"].sort(key=lambda entry: entry["repository"])
        self.write(self.registry_path, registry)
        self.assertIn("stale-registry-entry", self.rules(self.validate()))

    def test_emitted_findings_validate_against_finding_schema(self) -> None:
        contract = self.contract("atlas-api-index")
        contract["dependencies"] = ["unknown-service"]
        self.write_contract("atlas-api-index", contract)
        report = self.validate()
        self.assertTrue(report["findings"])
        self.assertEqual([], report["finding_schema_errors"])

    def test_dependency_graph_and_service_catalog_are_deterministic(self) -> None:
        first = self.validate()
        second = self.validate()
        self.assertEqual(first, second)
        self.assertEqual(
            sorted(node["service_id"] for node in first["dependency_graph"]["nodes"]),
            [node["service_id"] for node in first["dependency_graph"]["nodes"]],
        )
        self.assertEqual(24, len(first["service_catalog"]))

    def test_cli_generates_json_markdown_graph_and_catalog(self) -> None:
        output = self.root / "output"
        command = [
            sys.executable,
            str(SCRIPTS / "validate_contract_registry.py"),
            "--root",
            str(self.root),
            "--report",
            str(output / "report.json"),
            "--markdown",
            str(output / "report.md"),
            "--graph",
            str(output / "graph.json"),
            "--catalog",
            str(output / "catalog.json"),
            "--quiet",
        ]
        subprocess.run(command, check=True)
        report = self.load(output / "report.json")
        self.assertEqual("passed", report["status"])
        self.assertTrue(report["idempotent"])
        self.assertIn("No registry findings.", (output / "report.md").read_text())
        self.assertEqual(
            "atlas-contract-registry/dependency-graph/v1",
            self.load(output / "graph.json")["schema_version"],
        )
        self.assertEqual(
            "atlas-contract-registry/service-catalog/v1",
            self.load(output / "catalog.json")["schema_version"],
        )

    def test_cli_output_is_byte_idempotent(self) -> None:
        report_path = self.root / "report.json"
        command = [
            sys.executable,
            str(SCRIPTS / "validate_contract_registry.py"),
            "--root",
            str(self.root),
            "--report",
            str(report_path),
            "--quiet",
        ]
        subprocess.run(command, check=True)
        first = report_path.read_bytes()
        subprocess.run(command, check=True)
        self.assertEqual(first, report_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
