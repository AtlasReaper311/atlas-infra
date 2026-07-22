import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts
import validate_gardener_github_app_coverage


class GardenerGitHubAppCoverageTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def policy(self) -> dict:
        return self.load("policy/gardener-github-app-coverage.json")

    def registry(self) -> dict:
        return self.load("policy/estate-registry.json")

    def test_policy_conforms_to_schema(self):
        schema = self.load("policy/gardener-github-app-coverage.schema.json")
        self.assertEqual(
            [],
            control_plane_contracts.validate_instance(self.policy(), schema),
        )

    def test_committed_policy_is_complete_and_valid(self):
        report = validate_gardener_github_app_coverage.validate_coverage(
            self.policy(), self.registry()
        )
        self.assertEqual("valid", report["status"])
        self.assertEqual(20, report["coverage_count"])
        self.assertEqual(1, report["ready_batch_count"])
        self.assertEqual(
            "AtlasReaper311/atlas-dora", report["canary"]["repository"]
        )
        self.assertEqual(
            "sha256:96654dd254875030d59f461b70339c7f01e13ddf3eb22e34aa3c9dec88529cd5",
            report["source_fingerprint"],
        )

    def test_missing_eligible_repository_fails_closed(self):
        policy = self.policy()
        policy["batches"][0]["repositories"].pop()
        policy["coverage_count"] -= 1
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "missing from coverage",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )

    def test_duplicate_repository_fails_closed(self):
        policy = self.policy()
        policy["batches"][0]["repositories"].append(
            "AtlasReaper311/atlas-dora"
        )
        policy["batches"][0]["repositories"].sort()
        policy["coverage_count"] += 1
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "duplicate repository identities",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )

    def test_repository_outside_public_runtime_authority_is_refused(self):
        policy = self.policy()
        policy["batches"][0]["repositories"].append(
            "AtlasReaper311/atlas-watch"
        )
        policy["batches"][0]["repositories"].sort()
        policy["coverage_count"] += 1
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "outside public runtime authority",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )

    def test_permission_drift_is_refused(self):
        policy = self.policy()
        policy["permissions"]["actions"] = "read"
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "permission contract changed",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )

    def test_registry_classification_drift_invalidates_fingerprint(self):
        registry = copy.deepcopy(self.registry())
        registry["repositories"][0]["lifecycle"] = "deprecated"
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "source fingerprint differs",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                self.policy(), registry
            )

    def test_only_one_batch_may_be_ready(self):
        policy = self.policy()
        policy["batches"][1]["status"] = "ready"
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "only one coverage batch may be ready",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )

    def test_verified_batches_must_precede_pending_batches(self):
        policy = self.policy()
        policy["batches"][1]["status"] = "verified"
        with self.assertRaisesRegex(
            validate_gardener_github_app_coverage.CoveragePolicyError,
            "verified coverage batches must precede",
        ):
            validate_gardener_github_app_coverage.validate_coverage(
                policy, self.registry()
            )


if __name__ == "__main__":
    unittest.main()
