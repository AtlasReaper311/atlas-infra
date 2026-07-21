#!/usr/bin/env python3
"""Validate the offline Wave 3.1 governance contracts.

These contracts intentionally live beside, not inside, the closed root v1 schema
inventory. They reuse the existing control-plane JSON Schema subset,
canonicalisation, SHA-256 implementation, and secret-bearing key checks.
Nothing in this module performs network or provider operations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import control_plane_contracts as base

SCHEMA_NAMES = (
    "adr-runtime-relationship.schema.json",
    "model-promotion.schema.json",
    "retirement-evidence.schema.json",
)


def contract_root(root: Path) -> Path:
    return root / "contracts" / "v1" / "wave3"


def load_rules(root: Path) -> dict[str, Any]:
    rules = base.load_json(root / "contracts" / "v1" / "fingerprint-rules.json")
    wave3_rules = rules.get("wave3_rules")
    if not isinstance(wave3_rules, dict):
        raise ValueError("fingerprint-rules.json: wave3_rules is required")
    return {"rules": wave3_rules}


def _schema_metadata_errors(name: str, schema: dict[str, Any]) -> list[str]:
    stem = name.removesuffix(".schema.json")
    errors: list[str] = []
    if schema.get("$schema") != base.DRAFT_2020_12:
        errors.append(f"{name}: $schema must declare JSON Schema 2020-12")
    expected_id = f"https://schemas.atlas-systems.uk/control-plane/v1/{name}"
    if schema.get("$id") != expected_id:
        errors.append(f"{name}: $id must be {expected_id}")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append(f"{name}: top-level object must reject additional properties")
    expected_version = f"atlas-control-plane/{stem}/v1"
    version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if version != expected_version:
        errors.append(f"{name}: schema_version const must be {expected_version}")
    owner = schema.get("x-owner", {})
    if owner.get("repository") != "AtlasReaper311/atlas-infra":
        errors.append(f"{name}: x-owner.repository must be AtlasReaper311/atlas-infra")
    examples = schema.get("examples")
    if not isinstance(examples, list) or not examples:
        errors.append(f"{name}: at least one embedded example is required")
    return errors


def semantic_errors(
    schema_name: str,
    instance: dict[str, Any],
    fingerprint_rules: dict[str, Any],
) -> list[str]:
    errors = base._sensitive_key_errors(instance)

    rule_name = schema_name.removesuffix(".schema.json")
    rule = fingerprint_rules.get("rules", {}).get(rule_name)
    if not isinstance(rule, dict):
        errors.append(f"{schema_name}: deterministic fingerprint rule is missing")
    else:
        expected = base.calculate_fingerprint(rule_name, instance, fingerprint_rules)
        actual = base._value_at_path(instance, str(rule["output_path"]))
        if actual != expected:
            errors.append(
                f"$.{rule['output_path']}: deterministic {rule_name} value does not match canonical input"
            )

    if schema_name == "retirement-evidence.schema.json":
        subject = instance.get("subject")
        if isinstance(subject, dict):
            kind = subject.get("kind")
            if kind == "repository" and "service_id" in subject:
                errors.append("$.subject: repository retirement must not also declare service_id")
            if kind == "service" and "repository" in subject:
                errors.append("$.subject: service retirement must not also declare repository")

        if instance.get("state") == "archived":
            evidence = instance.get("evidence")
            if isinstance(evidence, dict) and any(
                value not in {"verified", "not-applicable"}
                for value in evidence.values()
            ):
                errors.append(
                    "$.evidence: archived retirement requires verified or not-applicable evidence"
                )

    if schema_name == "model-promotion.schema.json":
        evaluation = instance.get("evaluation")
        if isinstance(evaluation, dict):
            pass_rate = evaluation.get("pass_rate")
            minimum = evaluation.get("minimum_pass_rate")
            if (
                isinstance(pass_rate, (int, float))
                and not isinstance(pass_rate, bool)
                and isinstance(minimum, (int, float))
                and not isinstance(minimum, bool)
                and pass_rate < minimum
            ):
                errors.append(
                    "$.evaluation.pass_rate: pass_rate must meet or exceed minimum_pass_rate"
                )

    return errors


def validate_repository(root: Path) -> dict[str, Any]:
    wave3_root = contract_root(root)
    errors: list[str] = []
    schemas: dict[str, dict[str, Any]] = {}

    actual = tuple(sorted(path.name for path in wave3_root.glob("*.schema.json")))
    if actual != SCHEMA_NAMES:
        errors.append(
            "contracts/v1/wave3: schema inventory mismatch; "
            f"expected {SCHEMA_NAMES!r}, found {actual!r}"
        )

    for name in SCHEMA_NAMES:
        try:
            schema = base.load_json(wave3_root / name)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{name}: cannot load schema: {error}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"{name}: schema root must be an object")
            continue
        schemas[name] = schema
        errors.extend(_schema_metadata_errors(name, schema))

    try:
        rules = load_rules(root)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        errors.append(str(error))
        rules = {"rules": {}}

    expected_rule_schemas = set(SCHEMA_NAMES)
    actual_rule_schemas = {
        rule.get("schema") for rule in rules.get("rules", {}).values()
        if isinstance(rule, dict)
    }
    if actual_rule_schemas != expected_rule_schemas:
        errors.append("fingerprint-rules.json: Wave 3.1 rule schema coverage is incomplete")

    fixture_manifest_path = wave3_root / "fixtures" / "manifest.json"
    try:
        manifest = base.load_json(fixture_manifest_path)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"wave3 fixtures/manifest.json: cannot load: {error}")
        manifest = {"fixtures": []}

    coverage: dict[str, set[bool]] = {name: set() for name in SCHEMA_NAMES}
    positive = 0
    negative = 0
    fixture_count = 0

    for fixture in manifest.get("fixtures", []):
        fixture_count += 1
        schema_name = fixture.get("schema")
        relative_path = fixture.get("path")
        expected_valid = fixture.get("valid")
        if schema_name not in schemas or not isinstance(relative_path, str):
            errors.append(f"wave3 fixtures/manifest.json: invalid fixture entry {fixture!r}")
            continue
        if not isinstance(expected_valid, bool):
            errors.append("wave3 fixtures/manifest.json: fixture validity must be boolean")
            continue
        coverage[schema_name].add(expected_valid)
        positive += int(expected_valid)
        negative += int(not expected_valid)
        try:
            instance = base.load_json(wave3_root / "fixtures" / relative_path)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{relative_path}: cannot load fixture: {error}")
            continue
        instance_errors = base.validate_instance(instance, schemas[schema_name])
        if isinstance(instance, dict):
            instance_errors.extend(semantic_errors(schema_name, instance, rules))
        if expected_valid and instance_errors:
            errors.append(
                f"{relative_path}: expected valid fixture but failed: {instance_errors[0]}"
            )
        elif not expected_valid and not instance_errors:
            errors.append(f"{relative_path}: expected invalid fixture but it passed")
        elif not expected_valid and fixture.get("expected_error"):
            expected_error = str(fixture["expected_error"])
            if not any(expected_error in item for item in instance_errors):
                errors.append(
                    f"{relative_path}: expected error containing {expected_error!r}; got {instance_errors!r}"
                )

    for schema_name, states in coverage.items():
        if states != {False, True}:
            errors.append(
                f"wave3 fixtures/manifest.json: {schema_name} needs positive and negative fixtures"
            )

    for name, schema in schemas.items():
        for index, example in enumerate(schema.get("examples", [])):
            example_errors = base.validate_instance(example, schema)
            if isinstance(example, dict):
                example_errors.extend(semantic_errors(name, example, rules))
            if example_errors:
                errors.append(
                    f"{name}: embedded example {index} failed: {example_errors[0]}"
                )

    return {
        "schema_version": "atlas-control-plane/wave3-validation-report/v1",
        "contracts_root": "contracts/v1/wave3",
        "schemas_checked": len(schemas),
        "fixtures_checked": fixture_count,
        "positive_fixtures": positive,
        "negative_fixtures": negative,
        "errors": sorted(errors),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    report = validate_repository(args.root.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
