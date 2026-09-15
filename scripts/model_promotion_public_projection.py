#!/usr/bin/env python3
"""Validate the public-safe Model Promotion projection and its policy.

The JSON Schema is the field allowlist. This module adds only cross-field
rules that the repository's dependency-free schema subset cannot express, such
as lifecycle consistency, count arithmetic, freshness, and supersession.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import control_plane_contracts as base


SCHEMA_NAME = "public-model-promotion-projection.schema.json"
POLICY_PATH = Path("policy/model-promotion-public-projection.json")
POLICY_SCHEMA_PATH = Path("policy/model-promotion-public-projection.schema.json")
POLICY_SCHEMA_VERSION = "atlas-model-promotion/public-projection-policy/v1"
REGRESSION_VOCABULARY_VERSION = (
    "atlas-control-plane/model-promotion-regression-vocabulary/v1"
)


def load_policy(root: Path) -> dict[str, Any]:
    """Load the public projection policy."""

    value = base.load_json(root / POLICY_PATH)
    if not isinstance(value, dict):
        raise ValueError("public Model Promotion policy must be an object")
    return value


def validate_policy(root: Path) -> list[str]:
    """Validate policy shape and deterministic ordering."""

    errors: list[str] = []
    try:
        policy = load_policy(root)
        schema = base.load_json(root / POLICY_SCHEMA_PATH)
    except (OSError, json.JSONDecodeError) as error:
        return [f"public Model Promotion policy cannot be loaded: {error}"]

    errors.extend(base.validate_instance(policy, schema))
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        errors.append("public Model Promotion policy schema_version is unsupported")

    for key in (
        "allowed_capability_ids",
        "allowed_model_identifiers",
        "allowed_suite_versions",
    ):
        values = policy.get(key)
        if isinstance(values, list) and values != sorted(values):
            errors.append(f"policy.{key} must be sorted")

    vocabulary = policy.get("regression_vocabulary")
    if isinstance(vocabulary, dict):
        categories = vocabulary.get("categories")
        if isinstance(categories, list) and categories != sorted(categories):
            errors.append("policy.regression_vocabulary.categories must be sorted")

    if policy.get("lifecycle_authority") != ["ADR-0013", "ADR-0014"]:
        errors.append("policy.lifecycle_authority must preserve ADR-0013 and ADR-0014")
    return errors


def _timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        errors.append(f"{path}: timestamp cannot be parsed")
        return None


def _require_gap(instance: dict[str, Any], gap: str, errors: list[str]) -> None:
    if gap not in instance.get("gaps", []):
        errors.append(f"$.gaps: missing required gap {gap!r}")


def semantic_errors(instance: dict[str, Any], *, root: Path) -> list[str]:
    """Apply public projection rules that need more than JSON Schema."""

    errors: list[str] = []
    try:
        policy = load_policy(root)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"public Model Promotion policy cannot be loaded: {error}"]

    capability = instance.get("capability", {})
    model = instance.get("model", {})
    evaluation = instance.get("evaluation", {})
    human_review = instance.get("human_review", {})
    promotion = instance.get("promotion", {})
    freshness = instance.get("freshness", {})
    current_observation = instance.get("current_model_observation", {})
    projection_state = instance.get("state")
    evaluation_state = evaluation.get("state")
    promotion_state = promotion.get("state")
    observation_state = current_observation.get("state")

    allowed_capabilities = policy.get("allowed_capability_ids", [])
    if capability.get("id") not in allowed_capabilities:
        errors.append("$.capability.id: capability is not in the public allowlist")

    allowed_models = policy.get("allowed_model_identifiers", [])
    public_model = model.get("public_id")
    if public_model is None:
        if evaluation_state not in {
            "no-accepted-evaluation",
            "exempt-not-applicable",
            "unknown-not-observed",
        }:
            errors.append("$.model.public_id: evaluated states require a public model identifier")
    elif public_model not in allowed_models:
        errors.append("$.model.public_id: model identifier is not in the public allowlist")

    observed_model = current_observation.get("observed_model_id")
    if observed_model is not None and observed_model not in allowed_models:
        errors.append(
            "$.current_model_observation.observed_model_id: model identifier is not in the public allowlist"
        )

    suite = evaluation.get("suite")
    result = evaluation.get("result")
    if isinstance(suite, dict) and suite.get("version") not in policy.get(
        "allowed_suite_versions", []
    ):
        errors.append("$.evaluation.suite.version: suite version is not in the public allowlist")

    regressions = evaluation.get("known_regressions", {})
    vocabulary = policy.get("regression_vocabulary", {})
    if regressions.get("vocabulary_version") != REGRESSION_VOCABULARY_VERSION:
        errors.append("$.evaluation.known_regressions.vocabulary_version: unsupported vocabulary")
    allowed_regressions = vocabulary.get("categories", [])
    if any(category not in allowed_regressions for category in regressions.get("categories", [])):
        errors.append("$.evaluation.known_regressions.categories: category is not in the public vocabulary")

    regression_state = regressions.get("state")
    regression_categories = regressions.get("categories", [])
    if regression_state == "none" and regression_categories:
        errors.append("$.evaluation.known_regressions.categories: none cannot list regressions")
    if regression_state == "known" and not regression_categories:
        errors.append("$.evaluation.known_regressions.categories: known requires a bounded category")
    if regression_state in {"unknown-not-observed", "not-applicable"} and regression_categories:
        errors.append("$.evaluation.known_regressions.categories: unknown or not-applicable must be empty")

    if evaluation_state in {"prepared", "evaluated-passed", "evaluated-failed"}:
        if not isinstance(suite, dict):
            errors.append("$.evaluation.suite: evaluated evidence requires a public suite identity")
        if not isinstance(evaluation.get("prepared_at"), str):
            errors.append("$.evaluation.prepared_at: evaluated evidence requires a prepared timestamp")
    else:
        if suite is not None:
            errors.append("$.evaluation.suite: non-evaluated states must not expose a suite")
        if evaluation.get("prepared_at") is not None or evaluation.get("evaluated_at") is not None:
            errors.append("$.evaluation: non-evaluated states must not expose evaluation timestamps")

    if evaluation_state in {"evaluated-passed", "evaluated-failed"}:
        if not isinstance(result, dict):
            errors.append("$.evaluation.result: evaluated evidence requires aggregate result context")
        else:
            case_count = result.get("case_count")
            passed_count = result.get("passed_count")
            failed_count = result.get("failed_count")
            pass_rate = result.get("pass_rate")
            minimum = result.get("minimum_pass_rate")
            if all(isinstance(value, int) and not isinstance(value, bool) for value in (case_count, passed_count, failed_count)) and case_count != passed_count + failed_count:
                errors.append("$.evaluation.result: passed_count plus failed_count must equal case_count")
            if isinstance(case_count, int) and case_count > 0 and isinstance(pass_rate, (int, float)):
                expected_rate = passed_count / case_count
                if abs(pass_rate - expected_rate) > 1e-9:
                    errors.append("$.evaluation.result.pass_rate: rate must equal passed_count / case_count")
            if isinstance(pass_rate, (int, float)) and not isinstance(pass_rate, bool) and isinstance(minimum, (int, float)) and not isinstance(minimum, bool):
                if evaluation_state == "evaluated-passed" and pass_rate < minimum:
                    errors.append("$.evaluation.state: passed requires pass_rate to meet minimum_pass_rate")
                if evaluation_state == "evaluated-failed" and pass_rate >= minimum:
                    errors.append("$.evaluation.state: failed requires pass_rate below minimum_pass_rate")
    elif result is not None:
        errors.append("$.evaluation.result: non-evaluated states must not expose aggregate results")

    generated_at = _timestamp(instance.get("generated_at"), "$.generated_at", errors)
    prepared_at = _timestamp(evaluation.get("prepared_at"), "$.evaluation.prepared_at", errors)
    evaluated_at = _timestamp(evaluation.get("evaluated_at"), "$.evaluation.evaluated_at", errors)
    reviewed_at = _timestamp(human_review.get("reviewed_at"), "$.human_review.reviewed_at", errors)
    approved_at = _timestamp(promotion.get("approved_at"), "$.promotion.approved_at", errors)
    observed_at = _timestamp(current_observation.get("observed_at"), "$.current_model_observation.observed_at", errors)
    evidence_observed_at = _timestamp(
        freshness.get("evidence_observed_at"),
        "$.freshness.evidence_observed_at",
        errors,
    )
    timestamps = [
        item for item in (prepared_at, evaluated_at, reviewed_at, approved_at, observed_at) if item
    ]
    if generated_at and any(item > generated_at for item in timestamps):
        errors.append("$.generated_at: generated_at must not precede a contained observation timestamp")
    if prepared_at and evaluated_at and evaluated_at < prepared_at:
        errors.append("$.evaluation.evaluated_at: must not precede prepared_at")
    if generated_at and evidence_observed_at and evidence_observed_at > generated_at:
        errors.append("$.freshness.evidence_observed_at: must not follow generated_at")

    review_state = human_review.get("state")
    if review_state == "reviewed" and reviewed_at is None:
        errors.append("$.human_review.reviewed_at: reviewed state requires a timestamp")
    if review_state != "reviewed" and human_review.get("reviewed_at") is not None:
        errors.append("$.human_review.reviewed_at: only reviewed state may carry a timestamp")

    if promotion_state in {"approved", "superseded"} and approved_at is None:
        errors.append("$.promotion.approved_at: approved or superseded state requires a timestamp")
    if promotion_state not in {"approved", "superseded"} and promotion.get("approved_at") is not None:
        errors.append("$.promotion.approved_at: unapproved states must not carry an approval timestamp")
    if promotion_state in {"approved", "superseded"}:
        if evaluation_state != "evaluated-passed":
            errors.append("$.promotion.state: promotion approval requires an evaluated-passed result")
        if human_review.get("state") != "reviewed":
            errors.append("$.promotion.state: promotion approval requires human review")
    if review_state in {"pending", "reviewed"} and evaluation_state != "evaluated-passed":
        errors.append("$.human_review.state: human review requires an evaluated-passed result")
    supersedes = promotion.get("supersedes_projection_fingerprint")
    superseded_by = promotion.get("superseded_by_projection_fingerprint")
    if promotion_state == "superseded":
        if not superseded_by:
            errors.append("$.promotion.superseded_by_projection_fingerprint: superseded state requires a successor")
        if supersedes is not None:
            errors.append("$.promotion.supersedes_projection_fingerprint: superseded record cannot also replace another record")
    elif superseded_by is not None:
        errors.append("$.promotion.superseded_by_projection_fingerprint: only superseded state may carry a successor")
    if supersedes == instance.get("projection_fingerprint") or superseded_by == instance.get("projection_fingerprint"):
        errors.append("$.promotion: supersession must not point to the current projection")
    if supersedes is not None and promotion_state != "approved":
        errors.append("$.promotion.supersedes_projection_fingerprint: only an approved projection may replace another")

    freshness_state = freshness.get("state")
    if freshness_state in {"current", "stale"}:
        if evidence_observed_at is None or freshness.get("max_age_days") is None:
            errors.append("$.freshness: current or stale evidence requires observation time and max_age_days")
        elif generated_at is not None:
            age_days = (generated_at - evidence_observed_at).total_seconds() / 86400
            max_age_days = freshness["max_age_days"]
            if freshness_state == "current" and age_days > max_age_days:
                errors.append("$.freshness.state: current evidence exceeds max_age_days")
            if freshness_state == "stale" and age_days <= max_age_days:
                errors.append("$.freshness.state: stale evidence is within max_age_days")
    else:
        if freshness.get("evidence_observed_at") is not None or freshness.get("max_age_days") is not None:
            errors.append("$.freshness: unknown or superseded evidence must not claim an age window")
    if freshness_state == "superseded" and promotion_state != "superseded":
        errors.append("$.freshness.state: superseded freshness requires superseded promotion state")
    if promotion_state == "superseded" and freshness_state != "superseded":
        errors.append("$.promotion.state: superseded promotion requires superseded freshness state")

    if observation_state == "not-represented":
        if observed_model is not None or current_observation.get("observed_at") is not None:
            errors.append("$.current_model_observation: not-represented must not carry runtime identity")
    elif observation_state in {"observed-match", "observed-mismatch"}:
        if observed_model is None or observed_at is None:
            errors.append("$.current_model_observation: an observed state requires model identity and time")
        elif observation_state == "observed-match" and observed_model != model.get("public_id"):
            errors.append("$.current_model_observation: observed-match must equal the promoted public model")
        elif observation_state == "observed-mismatch" and observed_model == model.get("public_id"):
            errors.append("$.current_model_observation: observed-mismatch must differ from the promoted public model")
        if observation_state == "observed-mismatch" and promotion_state != "approved":
            errors.append("$.current_model_observation: mismatch requires an approved promotion record")
    elif current_observation.get("observed_model_id") is not None or current_observation.get("observed_at") is not None:
        errors.append("$.current_model_observation: unknown observation must not carry runtime identity")

    expected_state = None
    if promotion_state == "superseded":
        expected_state = "superseded-promotion"
    elif freshness_state == "stale":
        expected_state = "stale-evidence"
    elif observation_state == "observed-mismatch":
        expected_state = "promoted-current-model-mismatch"
    elif review_state == "pending":
        expected_state = "review-pending"
    elif promotion_state == "approved":
        expected_state = "promotion-approved"
    elif evaluation_state == "evaluated-failed":
        expected_state = "evaluated-failed"
    elif evaluation_state == "evaluated-passed":
        expected_state = "evaluated-passed"
    elif evaluation_state == "prepared":
        expected_state = "evaluation-prepared"
    elif evaluation_state == "no-accepted-evaluation":
        expected_state = "no-accepted-evaluation"
    elif evaluation_state == "exempt-not-applicable":
        expected_state = "exempt-not-applicable"
    elif evaluation_state == "unknown-not-observed":
        expected_state = "unknown-not-observed"
    if expected_state and projection_state != expected_state:
        errors.append(f"$.state: expected {expected_state!r} for the declared lifecycle axes")

    for required_gap in ("deployment-not-applicable",):
        _require_gap(instance, required_gap, errors)
    implied_gaps = {
        "prepared": "evaluation-not-observed",
        "evaluated-failed": "evaluation-failed",
        "no-accepted-evaluation": "no-accepted-evaluation",
        "exempt-not-applicable": "exempt-not-applicable",
        "unknown-not-observed": "unknown-evidence",
    }
    if evaluation_state in implied_gaps:
        _require_gap(instance, implied_gaps[evaluation_state], errors)
    if review_state == "pending":
        _require_gap(instance, "human-review-pending", errors)
    if promotion_state in {"not-approved", "unknown-not-observed"}:
        _require_gap(instance, "promotion-not-observed", errors)
    if freshness_state == "stale":
        _require_gap(instance, "stale-evidence", errors)
    if promotion_state == "superseded":
        _require_gap(instance, "superseded-promotion", errors)
    if observation_state == "observed-mismatch":
        _require_gap(instance, "promoted-current-model-mismatch", errors)
    if observation_state == "not-represented":
        _require_gap(instance, "runtime-model-not-represented", errors)

    return errors


def validate_projection(instance: dict[str, Any], root: Path) -> list[str]:
    """Validate schema, canonical identity, and public semantic rules."""

    try:
        schema = base.load_json(root / "contracts" / "v1" / SCHEMA_NAME)
        rules = base.load_json(root / "contracts" / "v1" / "fingerprint-rules.json")
    except (OSError, json.JSONDecodeError) as error:
        return [f"public Model Promotion contract cannot be loaded: {error}"]
    errors = base.validate_instance(instance, schema)
    errors.extend(base._sensitive_key_errors(instance))
    expected = base.calculate_fingerprint(
        "public-model-promotion-projection", instance, rules
    )
    if instance.get("projection_fingerprint") != expected:
        errors.append(
            "$.projection_fingerprint: deterministic public-model-promotion-projection value does not match canonical input"
        )
    errors.extend(semantic_errors(instance, root=root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = validate_policy(root)
    report = base.validate_repository(root)
    errors.extend(report["errors"])
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("public Model Promotion projection: policy and contract checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
