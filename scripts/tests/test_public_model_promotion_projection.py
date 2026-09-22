from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import control_plane_contracts as contracts  # noqa: E402
import model_promotion_public_projection as projection  # noqa: E402


class PublicModelPromotionProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = contracts.load_json(
            ROOT / "contracts" / "v1" / "public-model-promotion-projection.schema.json"
        )
        cls.rules = contracts.load_json(ROOT / "contracts" / "v1" / "fingerprint-rules.json")
        cls.fixture = contracts.load_json(
            ROOT / "contracts" / "v1" / "fixtures" / "valid" / "public-model-promotion-projection.json"
        )

    def candidate(self) -> dict:
        return copy.deepcopy(self.fixture)

    def refresh_fingerprint(self, candidate: dict) -> None:
        candidate["projection_fingerprint"] = contracts.calculate_fingerprint(
            "public-model-promotion-projection", candidate, self.rules
        )

    def validate(self, candidate: dict) -> list[str]:
        return projection.validate_projection(candidate, ROOT)

    def assert_valid(self, candidate: dict) -> None:
        self.refresh_fingerprint(candidate)
        self.assertEqual([], self.validate(candidate))

    def test_policy_and_canonical_fixture_pass(self) -> None:
        policy = projection.load_policy(ROOT)
        self.assertEqual(
            ["qwen3.5-mtp", "qwen3:14b", "synthetic-model-1b", "synthetic-model-2b"],
            policy["allowed_model_identifiers"],
        )
        self.assertFalse(policy["public_boundary"]["production_artifact_registered"])
        self.assertEqual(
            "deferred-until-artifact-exists",
            policy["public_boundary"]["target_registration"],
        )
        self.assertEqual([], projection.validate_policy(ROOT))
        self.assertEqual([], self.validate(self.candidate()))

    def test_allowlisted_qwen_identity_is_contract_valid_without_registration(self) -> None:
        for model_id in ("qwen3.5-mtp", "qwen3:14b"):
            with self.subTest(model_id=model_id):
                candidate = self.candidate()
                candidate["model"]["public_id"] = model_id
                self.assert_valid(candidate)

    def test_synthetic_model_ids_remain_contract_valid_for_fixtures(self) -> None:
        for model_id in ("synthetic-model-1b", "synthetic-model-2b"):
            with self.subTest(model_id=model_id):
                candidate = self.candidate()
                candidate["model"]["public_id"] = model_id
                self.assert_valid(candidate)

    def test_projection_fingerprint_sorts_set_like_arrays(self) -> None:
        candidate = self.candidate()
        candidate["evaluation"]["categories"].reverse()
        candidate["gaps"].reverse()
        self.assertEqual([], self.validate(candidate))
        self.assertEqual(self.fixture["projection_fingerprint"], candidate["projection_fingerprint"])

    def test_review_pending_is_distinct_from_failed_evaluation(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "review-pending"
        candidate["human_review"] = {"state": "pending", "reviewed_at": None}
        candidate["promotion"] = {
            "state": "not-approved",
            "approved_at": None,
            "supersedes_projection_fingerprint": None,
            "superseded_by_projection_fingerprint": None,
        }
        candidate["gaps"].append("human-review-pending")
        candidate["gaps"].append("promotion-not-observed")
        self.assert_valid(candidate)

    def test_stale_evidence_is_not_runtime_staleness(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "stale-evidence"
        candidate["freshness"] = {
            "state": "stale",
            "evidence_observed_at": "2026-08-01T13:30:00Z",
            "max_age_days": 30,
        }
        candidate["gaps"].append("stale-evidence")
        self.assert_valid(candidate)

    def test_superseded_projection_requires_a_public_successor_identity(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "superseded-promotion"
        candidate["promotion"]["state"] = "superseded"
        candidate["promotion"]["superseded_by_projection_fingerprint"] = "sha256:" + "2" * 64
        candidate["freshness"] = {
            "state": "superseded",
            "evidence_observed_at": None,
            "max_age_days": None,
        }
        candidate["gaps"].append("superseded-promotion")
        self.assert_valid(candidate)

    def test_unknown_is_explicit_and_not_failed(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "unknown-not-observed"
        candidate["model"]["public_id"] = None
        candidate["evaluation"] = {
            "state": "unknown-not-observed",
            "suite": None,
            "prepared_at": None,
            "evaluated_at": None,
            "categories": [],
            "known_regressions": {
                "vocabulary_version": "atlas-control-plane/model-promotion-regression-vocabulary/v1",
                "state": "unknown-not-observed",
                "categories": [],
            },
            "result": None,
        }
        candidate["human_review"] = {"state": "unknown-not-observed", "reviewed_at": None}
        candidate["promotion"] = {
            "state": "unknown-not-observed",
            "approved_at": None,
            "supersedes_projection_fingerprint": None,
            "superseded_by_projection_fingerprint": None,
        }
        candidate["freshness"] = {"state": "unknown", "evidence_observed_at": None, "max_age_days": None}
        candidate["current_model_observation"] = {
            "subject": "runtime-model-identity",
            "state": "unknown-not-observed",
            "observed_model_id": None,
            "observed_at": None,
        }
        candidate["gaps"] = [
            "deployment-not-applicable",
            "promotion-not-observed",
            "runtime-model-not-represented",
            "unknown-evidence",
        ]
        self.assert_valid(candidate)
        self.assertNotEqual("evaluated-failed", candidate["state"])

    def test_no_accepted_evaluation_can_omit_model_identity(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "no-accepted-evaluation"
        candidate["model"]["public_id"] = None
        candidate["evaluation"] = {
            "state": "no-accepted-evaluation",
            "suite": None,
            "prepared_at": None,
            "evaluated_at": None,
            "categories": [],
            "known_regressions": {
                "vocabulary_version": "atlas-control-plane/model-promotion-regression-vocabulary/v1",
                "state": "not-applicable",
                "categories": [],
            },
            "result": None,
        }
        candidate["human_review"] = {"state": "not-required", "reviewed_at": None}
        candidate["promotion"] = {
            "state": "not-approved",
            "approved_at": None,
            "supersedes_projection_fingerprint": None,
            "superseded_by_projection_fingerprint": None,
        }
        candidate["freshness"] = {"state": "unknown", "evidence_observed_at": None, "max_age_days": None}
        candidate["current_model_observation"] = {
            "subject": "runtime-model-identity",
            "state": "not-represented",
            "observed_model_id": None,
            "observed_at": None,
        }
        candidate["gaps"] = [
            "deployment-not-applicable",
            "no-accepted-evaluation",
            "promotion-not-observed",
            "runtime-model-not-represented",
        ]
        self.assert_valid(candidate)

    def test_promoted_current_model_mismatch_is_a_separate_observation(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "promoted-current-model-mismatch"
        candidate["current_model_observation"] = {
            "subject": "runtime-model-identity",
            "state": "observed-mismatch",
            "observed_model_id": "synthetic-model-2b",
            "observed_at": "2026-09-15T13:45:00Z",
        }
        candidate["gaps"].append("promoted-current-model-mismatch")
        self.assert_valid(candidate)

    def test_pass_rate_without_case_count_is_rejected(self) -> None:
        candidate = self.candidate()
        candidate["evaluation"]["result"].pop("case_count")
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("case_count" in error for error in errors), errors)

    def test_pass_rate_without_threshold_is_rejected(self) -> None:
        candidate = self.candidate()
        candidate["evaluation"]["result"].pop("minimum_pass_rate")
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("minimum_pass_rate" in error for error in errors), errors)

    def test_private_and_runtime_fields_are_not_allowlisted(self) -> None:
        for field in (
            "prompt",
            "reasoning",
            "raw_answer",
            "windows_path",
            "unix_path",
            "endpoint",
            "ip_address",
            "hostname",
            "private_evidence_uri",
            "runtime_configuration",
            "api_token",
        ):
            with self.subTest(field=field):
                candidate = self.candidate()
                candidate[field] = "synthetic-forbidden-value"
                self.refresh_fingerprint(candidate)
                errors = self.validate(candidate)
                self.assertTrue(
                    any("additional property" in error or "secret-bearing property" in error for error in errors),
                    errors,
                )

    def test_capability_and_model_must_be_policy_allowlisted(self) -> None:
        candidate = self.candidate()
        candidate["capability"]["id"] = "unclassified-capability"
        candidate["model"]["public_id"] = "arbitrary-model-name"
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("capability is not in the public allowlist" in error for error in errors), errors)
        self.assertTrue(any("model identifier is not in the public allowlist" in error for error in errors), errors)

    def test_invalid_state_and_malformed_fingerprint_fail(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "deployed"
        candidate["projection_fingerprint"] = "not-a-fingerprint"
        errors = self.validate(candidate)
        self.assertTrue(any("must be one of" in error for error in errors), errors)
        self.assertTrue(any("does not match required pattern" in error for error in errors), errors)

    def test_promotion_cannot_claim_deployment_or_live_verification(self) -> None:
        candidate = self.candidate()
        candidate["deployment_boundary"]["deployed"] = "deployed"
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("must equal 'not-applicable'" in error for error in errors), errors)

    def test_unknown_cannot_be_collapsed_into_failed(self) -> None:
        candidate = self.candidate()
        candidate["state"] = "evaluated-failed"
        candidate["evaluation"]["state"] = "unknown-not-observed"
        candidate["evaluation"]["suite"] = None
        candidate["evaluation"]["prepared_at"] = None
        candidate["evaluation"]["evaluated_at"] = None
        candidate["evaluation"]["result"] = None
        candidate["human_review"] = {"state": "unknown-not-observed", "reviewed_at": None}
        candidate["promotion"]["state"] = "unknown-not-observed"
        candidate["promotion"]["approved_at"] = None
        candidate["freshness"] = {"state": "unknown", "evidence_observed_at": None, "max_age_days": None}
        candidate["current_model_observation"]["state"] = "unknown-not-observed"
        candidate["gaps"] = [
            "deployment-not-applicable",
            "promotion-not-observed",
            "runtime-model-not-represented",
            "unknown-evidence",
        ]
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("expected 'unknown-not-observed'" in error for error in errors), errors)

    def test_inconsistent_supersession_fails_closed(self) -> None:
        candidate = self.candidate()
        candidate["promotion"]["state"] = "superseded"
        candidate["freshness"] = {"state": "superseded", "evidence_observed_at": None, "max_age_days": None}
        candidate["state"] = "superseded-promotion"
        candidate["gaps"].append("superseded-promotion")
        self.refresh_fingerprint(candidate)
        errors = self.validate(candidate)
        self.assertTrue(any("requires a successor" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
