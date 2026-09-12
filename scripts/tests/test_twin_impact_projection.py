from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import control_plane_contracts as contracts  # noqa: E402


class TwinImpactProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        contract_root = ROOT / "contracts" / "v1"
        cls.schema = contracts.load_json(
            contract_root / "twin-impact-projection.schema.json"
        )
        cls.rules = contracts.load_json(contract_root / "fingerprint-rules.json")
        cls.projection = contracts.load_json(
            contract_root / "fixtures" / "valid" / "twin-impact-projection.json"
        )
        classification = contracts.load_json(
            ROOT / "policy" / "public-repository-classifications.json"
        )
        cls.public_repositories = contracts._public_repository_set(ROOT)
        cls.internal_repositories = {
            item["repository"]
            for item in classification["repositories"]
            if item.get("scope") == "internal"
        }
        cls.internal_repository = "AtlasReaper311/atlas-notify"
        if cls.internal_repository not in cls.internal_repositories:
            raise AssertionError(
                "regression fixture must use a currently classified internal repository"
            )
        if cls.internal_repository in cls.public_repositories:
            raise AssertionError(
                "internal repository must not be included in the public repository set"
            )

    def validate(self, projection: dict) -> list[str]:
        errors = contracts.validate_instance(projection, self.schema)
        errors.extend(
            contracts.semantic_errors(
                "twin-impact-projection.schema.json",
                projection,
                self.rules,
                public_repositories=self.public_repositories,
            )
        )
        return errors

    def test_canonical_public_fixture_passes(self) -> None:
        self.assertEqual([], self.validate(self.projection))

    def test_fingerprint_is_independent_of_relationship_order(self) -> None:
        first = contracts.calculate_fingerprint(
            "twin-impact-projection", self.projection, self.rules
        )
        second_projection = copy.deepcopy(self.projection)
        second_projection["impact"]["relationships"].reverse()
        second_projection["limitations"].reverse()
        second = contracts.calculate_fingerprint(
            "twin-impact-projection", second_projection, self.rules
        )
        self.assertEqual(first, second)

    def test_private_subject_is_explicit_unknown_without_inference(self) -> None:
        candidate = copy.deepcopy(self.projection)
        candidate["subject"] = {
            "visibility": "private-or-unknown",
            "repository": None,
            "base_oid": None,
            "head_oid": None,
        }
        candidate["impact"]["coverage"] = "unknown"
        candidate["impact"]["relationships"] = []
        candidate["impact"]["unknowns"] = ["private-or-unknown-subject"]
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "twin-impact-projection", candidate, self.rules
        )
        self.assertEqual([], self.validate(candidate))

    def test_private_repository_relationship_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.projection)
        candidate["impact"]["relationships"][0]["id"] = (
            "AtlasReaper311/atlas-twin"
        )
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "twin-impact-projection", candidate, self.rules
        )
        errors = self.validate(candidate)
        self.assertTrue(
            any("not in current public classification" in error for error in errors),
            errors,
        )

    def test_internal_repository_cannot_be_public_subject(self) -> None:
        candidate = copy.deepcopy(self.projection)
        candidate["subject"]["repository"] = self.internal_repository
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "twin-impact-projection", candidate, self.rules
        )
        errors = self.validate(candidate)
        self.assertTrue(
            any(
                "$.subject.repository: public identity is not in current public classification"
                in error
                for error in errors
            ),
            errors,
        )

    def test_internal_repository_cannot_be_relationship_identifier(self) -> None:
        candidate = copy.deepcopy(self.projection)
        candidate["impact"]["relationships"][0]["id"] = (
            self.internal_repository
        )
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "twin-impact-projection", candidate, self.rules
        )
        errors = self.validate(candidate)
        self.assertTrue(
            any(
                "$.impact.relationships[0].id: public identity is not in current public classification"
                in error
                for error in errors
            ),
            errors,
        )

    def test_component_and_service_use_explicit_topology_proof_authority(self) -> None:
        self.assertEqual(
            "atlas-api-public-topology-exporter",
            self.projection["impact"]["relationships"][1]["identity_authority"],
        )
        self.assertEqual(
            "atlas-api-public-topology-exporter",
            self.projection["impact"]["relationships"][2]["identity_authority"],
        )
        self.assertEqual([], self.validate(self.projection))

    def test_component_cannot_claim_infra_classification_as_identity_proof(self) -> None:
        candidate = copy.deepcopy(self.projection)
        candidate["impact"]["relationships"][1]["identity_authority"] = (
            "atlas-infra-public-classification"
        )
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "twin-impact-projection", candidate, self.rules
        )
        errors = self.validate(candidate)
        self.assertTrue(
            any(
                "component identity must name atlas-api-public-topology-exporter"
                in error
                for error in errors
            ),
            errors,
        )
