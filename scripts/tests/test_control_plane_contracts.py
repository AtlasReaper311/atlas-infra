from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts as contracts


class ControlPlaneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_root = ROOT / "contracts" / "v1"
        cls.rules = contracts.load_json(cls.contract_root / "fingerprint-rules.json")

    def fixture(self, relative: str) -> dict:
        return contracts.load_json(self.contract_root / "fixtures" / relative)

    def schema(self, name: str) -> dict:
        return contracts.load_json(self.contract_root / name)

    def test_complete_repository_passes(self) -> None:
        report = contracts.validate_repository(ROOT)
        self.assertEqual([], report["errors"])
        self.assertEqual(8, report["schemas_checked"])
        self.assertEqual(8, report["positive_fixtures"])
        self.assertEqual(8, report["negative_fixtures"])

    def test_finding_fingerprint_is_order_independent(self) -> None:
        finding = self.fixture("valid/finding.json")
        reversed_finding = dict(reversed(list(finding.items())))
        expected = finding["fingerprint"]
        self.assertEqual(
            expected,
            contracts.calculate_fingerprint("finding", finding, self.rules),
        )
        self.assertEqual(
            expected,
            contracts.calculate_fingerprint(
                "finding", reversed_finding, self.rules
            ),
        )

    def test_proposal_file_order_does_not_change_identity(self) -> None:
        proposal = self.fixture("valid/remediation-proposal.json")
        proposal["files_affected"] = ["README.md", ".gitignore"]
        first = contracts.calculate_fingerprint(
            "remediation-proposal", proposal, self.rules
        )
        proposal["files_affected"].reverse()
        second = contracts.calculate_fingerprint(
            "remediation-proposal", proposal, self.rules
        )
        self.assertEqual(first, second)

    def test_inline_evidence_digest_mismatch_is_rejected(self) -> None:
        envelope = self.fixture("valid/evidence-envelope.json")
        envelope["payload"]["status"] = "failed"
        errors = contracts.semantic_errors(
            "evidence-envelope.schema.json", envelope, self.rules
        )
        self.assertTrue(any("deterministic evidence-envelope" in item for item in errors))

    def test_reference_evidence_digest_is_not_recomputed_without_content(self) -> None:
        envelope = self.fixture("valid/evidence-envelope.json")
        envelope.pop("payload")
        envelope["reference"] = {
            "uri": "https://github.com/AtlasReaper311/atlas-infra/actions/runs/100",
            "content_type": "application/json",
        }
        errors = contracts.semantic_errors(
            "evidence-envelope.schema.json", envelope, self.rules
        )
        self.assertEqual([], errors)

    def test_secret_bearing_payload_property_is_rejected(self) -> None:
        envelope = self.fixture("valid/evidence-envelope.json")
        envelope["payload"]["token"] = "fixture-value"
        errors = contracts.semantic_errors(
            "evidence-envelope.schema.json", envelope, self.rules
        )
        self.assertTrue(any("secret-bearing property" in item for item in errors))

    def test_compound_secret_bearing_property_is_rejected(self) -> None:
        envelope = self.fixture("valid/evidence-envelope.json")
        envelope["payload"]["access_token"] = "fixture-value"
        errors = contracts.semantic_errors(
            "evidence-envelope.schema.json", envelope, self.rules
        )
        self.assertTrue(any("secret-bearing property" in item for item in errors))

    def test_simple_proxy_cannot_own_routes(self) -> None:
        service = self.fixture("valid/service-contract.json")
        service["control_plane_policy"]["route_ownership"] = True
        errors = contracts.validate_instance(
            service, self.schema("service-contract.schema.json")
        )
        self.assertTrue(any("must equal False" in item for item in errors))

    def test_current_internal_service_can_declare_root_metadata_route(self) -> None:
        service = self.fixture("valid/service-contract.json")
        service.update(
            {
                "service_id": "atlas-infra",
                "display_name": "atlas-infra",
                "source_repository": "AtlasReaper311/atlas-infra",
                "classification": {
                    "lifecycle": "active",
                    "scope": "internal",
                    "provenance": "original",
                },
                "registry_visibility": "current",
                "runtime": {
                    "kind": "tool",
                    "deployment_target": "github-actions",
                    "release_identity_supported": False,
                },
                "routes": [
                    {"path": "/health", "methods": ["GET"], "visibility": "internal"}
                ],
                "metadata_route": "/_meta",
                "control_plane_policy": {
                    "new_features": True,
                    "route_ownership": True,
                    "default_assurance": True,
                    "gardener_remediation": True,
                    "deployment_orchestration": False,
                },
            }
        )
        self.assertEqual(
            [],
            contracts.validate_instance(
                service, self.schema("service-contract.schema.json")
            ),
        )

    def test_service_contract_accepts_openapi_route_template(self) -> None:
        service = self.fixture("valid/service-contract.json")
        service.update(
            {
                "service_id": "atlas-api-public",
                "display_name": "Atlas public API",
                "source_repository": "AtlasReaper311/atlas-api-public",
                "classification": {
                    "lifecycle": "production",
                    "scope": "public",
                    "provenance": "original",
                },
                "registry_visibility": "current",
                "control_plane_policy": {
                    "new_features": True,
                    "route_ownership": True,
                    "default_assurance": True,
                    "gardener_remediation": True,
                    "deployment_orchestration": True,
                },
            }
        )
        service["routes"] = [
            {
                "path": "/v1/control-plane/tools/services/{service_id}",
                "methods": ["GET"],
                "visibility": "authenticated",
            }
        ]
        self.assertEqual(
            [],
            contracts.validate_instance(
                service, self.schema("service-contract.schema.json")
            ),
        )

        service["routes"][0]["path"] = "/v1/services/{Invalid-parameter}"
        errors = contracts.validate_instance(
            service, self.schema("service-contract.schema.json")
        )
        self.assertTrue(any("pattern" in error for error in errors), errors)

    def test_invalid_release_timestamp_fails_without_crashing_semantics(self) -> None:
        release = self.fixture("valid/release-evidence.json")
        release["completed_at"] = "not-a-timestamp"
        schema_errors = contracts.validate_instance(
            release, self.schema("release-evidence.schema.json")
        )
        semantic_errors = contracts.semantic_errors(
            "release-evidence.schema.json", release, self.rules
        )
        self.assertTrue(any("UTC RFC 3339" in item for item in schema_errors))
        self.assertEqual([], semantic_errors)

    def test_release_evidence_accepts_phase3_optional_identity_fields(self) -> None:
        release = self.fixture("valid/release-evidence.json")
        self.assertEqual("atlas-infra", release["service_id"])
        self.assertEqual("github-actions", release["deployment_target"])
        self.assertEqual(
            [],
            contracts.validate_instance(
                release, self.schema("release-evidence.schema.json")
            ),
        )

    def test_backup_evidence_accepts_phase8_optional_audit_fields(self) -> None:
        evidence = self.fixture("valid/backup-evidence.json")
        self.assertEqual("atlas-blackbox", evidence["service_id"])
        self.assertEqual("fresh", evidence["freshness_state"])
        self.assertEqual("passed", evidence["restore_drill_state"])
        self.assertEqual("met", evidence["retention_state"])
        self.assertEqual(
            [],
            contracts.validate_instance(
                evidence, self.schema("backup-evidence.schema.json")
            ),
        )

    def test_optional_property_addition_is_minor_compatible(self) -> None:
        previous = {
            "type": "object",
            "required": ["schema_version"],
            "properties": {"schema_version": {"const": "example/v1"}},
        }
        current = copy.deepcopy(previous)
        current["properties"]["note"] = {"type": "string"}
        self.assertEqual([], contracts.classify_schema_change(previous, current))

    def test_required_property_addition_is_breaking(self) -> None:
        previous = {
            "type": "object",
            "required": ["schema_version"],
            "properties": {"schema_version": {"const": "example/v1"}},
        }
        current = copy.deepcopy(previous)
        current["required"].append("owner")
        current["properties"]["owner"] = {"type": "string"}
        self.assertEqual(
            ["required field added: owner"],
            contracts.classify_schema_change(previous, current),
        )

    def test_vocabulary_removal_is_breaking(self) -> None:
        previous = {
            "properties": {"state": {"type": "string", "enum": ["a", "b"]}}
        }
        current = {
            "properties": {"state": {"type": "string", "enum": ["a"]}}
        }
        self.assertEqual(
            ["enum values removed from state: ['b']"],
            contracts.classify_schema_change(previous, current),
        )

    def test_fingerprint_rule_change_is_breaking(self) -> None:
        changed = copy.deepcopy(self.rules)
        changed["rules"]["finding"]["fields"].append("severity")
        self.assertEqual(
            ["fingerprint rule changed: finding"],
            contracts.fingerprint_rule_change(self.rules, changed),
        )

    def test_cli_report_is_byte_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            command = [
                sys.executable,
                str(SCRIPTS / "validate_control_plane_contracts.py"),
                "--root",
                str(ROOT),
                "--report",
                str(report_path),
                "--quiet",
            ]
            subprocess.run(command, check=True)
            first = report_path.read_bytes()
            subprocess.run(command, check=True)
            second = report_path.read_bytes()
            self.assertEqual(first, second)
            self.assertTrue(json.loads(second)["idempotent"])


if __name__ == "__main__":
    unittest.main()
