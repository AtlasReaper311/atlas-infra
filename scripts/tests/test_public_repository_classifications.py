import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts
import public_repository_classifications


class PublicRepositoryClassificationTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def projection(self) -> dict:
        return public_repository_classifications.build_projection(
            self.load("policy/estate-registry.json"),
            self.load("policy/public-assurance-repositories.json"),
        )

    def test_public_non_runtime_source_conforms_to_schema(self):
        schema = self.load("policy/public-assurance-repositories.schema.json")
        self.assertEqual(
            [],
            control_plane_contracts.validate_instance(
                self.load("policy/public-assurance-repositories.json"), schema
            ),
        )

    def test_committed_projection_matches_authoritative_sources(self):
        expected = public_repository_classifications.render_json(self.projection())
        actual = (ROOT / "policy/public-repository-classifications.json").read_text(
            encoding="utf-8"
        )
        self.assertEqual(expected, actual)

    def test_projection_conforms_to_public_contract(self):
        schema = self.load(
            "contracts/v1/public-repository-classifications.schema.json"
        )
        self.assertEqual(
            [],
            control_plane_contracts.validate_instance(self.projection(), schema),
        )

    def test_projection_is_sorted_unique_and_complete(self):
        projection = self.projection()
        repositories = [item["repository"] for item in projection["repositories"]]
        self.assertEqual(sorted(repositories), repositories)
        self.assertEqual(len(repositories), len(set(repositories)))
        self.assertEqual(31, projection["repository_count"])
        self.assertEqual(31, len(repositories))

    def test_known_runtime_lifecycle_drift_is_resolved_at_authority(self):
        projection = self.projection()
        by_repository = {
            item["repository"]: item for item in projection["repositories"]
        }
        self.assertEqual(
            "active", by_repository["AtlasReaper311/atlas-doc-viewer"]["lifecycle"]
        )
        self.assertEqual(
            "active", by_repository["AtlasReaper311/ramone-memory"]["lifecycle"]
        )
        self.assertTrue(
            by_repository["AtlasReaper311/atlas-doc-viewer"]["runtime_service"]
        )

    def test_public_non_runtime_repository_has_explicit_classification(self):
        projection = self.projection()
        entry = next(
            item
            for item in projection["repositories"]
            if item["repository"] == "AtlasReaper311/atlas-gardener"
        )
        self.assertEqual("active", entry["lifecycle"])
        self.assertEqual("public", entry["scope"])
        self.assertEqual("original", entry["provenance"])
        self.assertFalse(entry["runtime_service"])

    def test_runtime_and_non_runtime_sources_must_not_overlap(self):
        registry = self.load("policy/estate-registry.json")
        supplement = copy.deepcopy(
            self.load("policy/public-assurance-repositories.json")
        )
        supplement["repositories"].append(
            {
                "repository": "AtlasReaper311/status",
                "lifecycle": "active",
                "scope": "public",
                "provenance": "original",
            }
        )
        with self.assertRaisesRegex(
            public_repository_classifications.ClassificationProjectionError,
            "classification authority overlap",
        ):
            public_repository_classifications.build_projection(registry, supplement)

    def test_projection_is_deterministic(self):
        first = self.projection()
        second = self.projection()
        self.assertEqual(first, second)
        self.assertEqual(
            public_repository_classifications.render_json(first),
            public_repository_classifications.render_json(second),
        )

    def test_source_fingerprint_changes_when_classification_changes(self):
        registry = self.load("policy/estate-registry.json")
        supplement = self.load("policy/public-assurance-repositories.json")
        before = public_repository_classifications.build_projection(registry, supplement)
        changed = copy.deepcopy(supplement)
        changed["repositories"][0]["lifecycle"] = "experimental"
        after = public_repository_classifications.build_projection(registry, changed)
        self.assertNotEqual(before["source_fingerprint"], after["source_fingerprint"])


if __name__ == "__main__":
    unittest.main()
