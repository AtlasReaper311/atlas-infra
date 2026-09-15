#!/usr/bin/env python3
"""Validate the public-safe Model Promotion projection and its policy.

The JSON Schema is the field allowlist. The dependency-neutral rules module
adds only cross-field rules that the repository's dependency-free schema subset
cannot express, such as lifecycle consistency, count arithmetic, freshness, and
supersession.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import control_plane_contracts as base
from model_promotion_public_projection_rules import (
    semantic_errors as public_semantic_errors,
)


SCHEMA_NAME = "public-model-promotion-projection.schema.json"
POLICY_PATH = Path("policy/model-promotion-public-projection.json")
POLICY_SCHEMA_PATH = Path("policy/model-promotion-public-projection.schema.json")
POLICY_SCHEMA_VERSION = "atlas-model-promotion/public-projection-policy/v1"


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


def semantic_errors(instance: dict[str, Any], *, root: Path) -> list[str]:
    """Load the policy and apply dependency-neutral public semantic rules."""

    try:
        policy = load_policy(root)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"public Model Promotion policy cannot be loaded: {error}"]
    return public_semantic_errors(instance, policy)


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
