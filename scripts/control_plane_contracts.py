#!/usr/bin/env python3
"""Validate Atlas control-plane contracts with the Python standard library.

The implementation intentionally supports only the JSON Schema 2020-12
keywords used by ``contracts/v1``. Keeping the subset explicit makes the
assurance path dependency-free without pretending to be a general-purpose
JSON Schema implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
EXPECTED_SCHEMAS = (
    "backup-evidence.schema.json",
    "control-plane-summary.schema.json",
    "evidence-envelope.schema.json",
    "finding.schema.json",
    "release-evidence.schema.json",
    "remediation-proposal.schema.json",
    "runbook-index-entry.schema.json",
    "service-contract.schema.json",
)
SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "password",
    "private_key",
    "secret",
    "token",
}
SAFE_AGGREGATE_KEYS = {"secret_declaration", "secret_hygiene"}
UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    """Return the canonical representation used for SHA-256 inputs."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_hex(value: Any) -> str:
    """Hash a JSON-compatible value after canonicalisation."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _json_pointer(root: dict[str, Any], pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise ValueError(f"unsupported JSON Schema reference: {pointer}")
    current: Any = root
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        current = current[part]
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported JSON Schema type: {expected}")


def _format_errors(value: str, format_name: str, path: str) -> list[str]:
    if format_name == "date-time":
        if not UTC_TIMESTAMP.fullmatch(value):
            return [f"{path}: must be a UTC RFC 3339 timestamp ending in Z"]
        try:
            datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
        except ValueError:
            return [f"{path}: is not a valid calendar timestamp"]
    elif format_name == "uri":
        parsed = urlsplit(value)
        if parsed.scheme not in {"https"} or not parsed.netloc or parsed.username:
            return [f"{path}: must be an HTTPS URI without user information"]
    else:
        raise ValueError(f"unsupported JSON Schema format: {format_name}")
    return []


def validate_instance(
    value: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> list[str]:
    """Validate an instance against the supported JSON Schema subset."""
    root = root_schema or schema
    if "$ref" in schema:
        target = _json_pointer(root, str(schema["$ref"]))
        return validate_instance(value, target, root_schema=root, path=path)

    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None:
        choices = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(value, choice) for choice in choices):
            return [f"{path}: expected type {' or '.join(choices)}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']!r}")

    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            errors.append(f"{path}: is shorter than minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            errors.append(f"{path}: is longer than maxLength")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            errors.append(f"{path}: does not match required pattern")
        if "format" in schema:
            errors.extend(_format_errors(value, str(schema["format"]), path))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: is above maximum {schema['maximum']}")

    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            errors.append(f"{path}: has fewer than minItems")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append(f"{path}: has more than maxItems")
        if schema.get("uniqueItems"):
            canonical_items = [canonical_json(item) for item in value]
            if len(canonical_items) != len(set(canonical_items)):
                errors.append(f"{path}: items must be unique")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                errors.extend(
                    validate_instance(
                        item,
                        schema["items"],
                        root_schema=root,
                        path=f"{path}[{index}]",
                    )
                )

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(
                    validate_instance(
                        item,
                        properties[key],
                        root_schema=root,
                        path=child_path,
                    )
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property {key!r} is not allowed")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors.extend(
                    validate_instance(
                        item,
                        schema["additionalProperties"],
                        root_schema=root,
                        path=child_path,
                    )
                )

    for child in schema.get("allOf", []):
        errors.extend(validate_instance(value, child, root_schema=root, path=path))

    if "anyOf" in schema:
        candidates = [
            validate_instance(value, child, root_schema=root, path=path)
            for child in schema["anyOf"]
        ]
        if not any(not candidate for candidate in candidates):
            errors.append(f"{path}: does not satisfy anyOf")

    if "oneOf" in schema:
        matches = sum(
            not validate_instance(value, child, root_schema=root, path=path)
            for child in schema["oneOf"]
        )
        if matches != 1:
            errors.append(f"{path}: must satisfy exactly one oneOf branch")

    if "if" in schema:
        condition_errors = validate_instance(
            value,
            schema["if"],
            root_schema=root,
            path=path,
        )
        branch = schema.get("then") if not condition_errors else schema.get("else")
        if isinstance(branch, dict):
            errors.extend(validate_instance(value, branch, root_schema=root, path=path))

    return errors


def _value_at_path(value: dict[str, Any], dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def calculate_fingerprint(
    rule_name: str,
    instance: dict[str, Any],
    fingerprint_rules: dict[str, Any],
) -> str:
    """Calculate one declared fingerprint or payload digest."""
    rule = fingerprint_rules["rules"][rule_name]
    if rule["kind"] == "payload-digest":
        payload = _value_at_path(instance, rule["content_path"])
        return sha256_hex(payload)

    canonical_fields: dict[str, Any] = {}
    sorted_arrays = set(rule.get("sort_arrays", []))
    for dotted_path in rule["fields"]:
        field_value = copy.deepcopy(_value_at_path(instance, dotted_path))
        if dotted_path in sorted_arrays and isinstance(field_value, list):
            field_value = sorted(field_value, key=canonical_json)
        canonical_fields[dotted_path] = field_value
    return str(rule.get("prefix", "")) + sha256_hex(canonical_fields)


def _sensitive_key_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            segments = set(normalized.split("_"))
            sensitive = normalized in SENSITIVE_KEYS or bool(
                segments.intersection(SENSITIVE_KEYS)
            )
            if sensitive and normalized not in SAFE_AGGREGATE_KEYS:
                errors.append(f"{path}: secret-bearing property {key!r} is prohibited")
            errors.extend(_sensitive_key_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_sensitive_key_errors(child, f"{path}[{index}]"))
    return errors


def semantic_errors(
    schema_name: str,
    instance: dict[str, Any],
    fingerprint_rules: dict[str, Any],
) -> list[str]:
    """Apply cross-field rules JSON Schema cannot express cleanly."""
    errors = _sensitive_key_errors(instance)
    for rule_name, rule in fingerprint_rules["rules"].items():
        if rule["schema"] != schema_name:
            continue
        if (
            rule["kind"] == "payload-digest"
            and _value_at_path(instance, rule["content_path"]) is None
        ):
            continue
        expected = calculate_fingerprint(rule_name, instance, fingerprint_rules)
        actual = _value_at_path(instance, rule["output_path"])
        if actual != expected:
            errors.append(
                f"$.{rule['output_path']}: deterministic {rule_name} value does not match canonical input"
            )

    if schema_name == "release-evidence.schema.json":
        started_at = instance.get("started_at")
        completed_at = instance.get("completed_at")
        if isinstance(started_at, str) and isinstance(completed_at, str):
            try:
                started = datetime.fromisoformat(
                    started_at.removesuffix("Z") + "+00:00"
                )
                completed = datetime.fromisoformat(
                    completed_at.removesuffix("Z") + "+00:00"
                )
            except ValueError:
                pass
            else:
                if completed < started:
                    errors.append("$.completed_at: must not precede started_at")

    if schema_name == "evidence-envelope.schema.json" and "payload" in instance:
        payload_size = len(canonical_json(instance["payload"]).encode("utf-8"))
        if payload_size > 16_384:
            errors.append("$.payload: canonical inline payload exceeds 16384 bytes")
    return errors


def classify_schema_change(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    """Return deterministic breaking-change reasons for the supported policy."""
    reasons: list[str] = []
    previous_required = set(previous.get("required", []))
    current_required = set(current.get("required", []))
    for field in sorted(current_required - previous_required):
        reasons.append(f"required field added: {field}")

    previous_properties = previous.get("properties", {})
    current_properties = current.get("properties", {})
    for field in sorted(set(previous_properties) - set(current_properties)):
        reasons.append(f"property removed: {field}")
    for field in sorted(set(previous_properties) & set(current_properties)):
        old = previous_properties[field]
        new = current_properties[field]
        if old.get("type") != new.get("type"):
            reasons.append(f"property type changed: {field}")
        if "const" in old and old.get("const") != new.get("const"):
            reasons.append(f"property const changed: {field}")
        if "enum" in old:
            removed = set(old["enum"]) - set(new.get("enum", []))
            if removed:
                reasons.append(f"enum values removed from {field}: {sorted(removed)!r}")
    return reasons


def fingerprint_rule_change(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    """Flag any v1 identity-input change as major-version breaking."""
    reasons: list[str] = []
    old_rules = previous.get("rules", {})
    new_rules = current.get("rules", {})
    for name in sorted(set(old_rules) | set(new_rules)):
        if old_rules.get(name) != new_rules.get(name):
            reasons.append(f"fingerprint rule changed: {name}")
    return reasons


def _schema_metadata_errors(name: str, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    stem = name.removesuffix(".schema.json")
    expected_version = f"atlas-control-plane/{stem}/v1"
    if schema.get("$schema") != DRAFT_2020_12:
        errors.append(f"{name}: $schema must declare JSON Schema 2020-12")
    expected_id = f"https://schemas.atlas-systems.uk/control-plane/v1/{name}"
    if schema.get("$id") != expected_id:
        errors.append(f"{name}: $id must be {expected_id}")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append(f"{name}: top-level object must reject additional properties")
    version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if version != expected_version:
        errors.append(f"{name}: schema_version const must be {expected_version}")
    owner = schema.get("x-owner", {})
    if owner.get("repository") != "AtlasReaper311/atlas-infra":
        errors.append(f"{name}: x-owner.repository must be AtlasReaper311/atlas-infra")
    if not isinstance(schema.get("examples"), list) or not schema["examples"]:
        errors.append(f"{name}: at least one embedded example is required")
    return errors


def validate_repository(root: Path) -> dict[str, Any]:
    """Validate the complete v1 contract set and return a stable report."""
    contract_root = root / "contracts" / "v1"
    errors: list[str] = []
    schemas: dict[str, dict[str, Any]] = {}
    actual_schema_names = tuple(
        sorted(path.name for path in contract_root.glob("*.schema.json"))
    )
    if actual_schema_names != EXPECTED_SCHEMAS:
        errors.append(
            "contracts/v1: schema inventory mismatch; "
            f"expected {EXPECTED_SCHEMAS!r}, found {actual_schema_names!r}"
        )

    for name in EXPECTED_SCHEMAS:
        path = contract_root / name
        try:
            schema = load_json(path)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{name}: cannot load schema: {error}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"{name}: schema root must be an object")
            continue
        schemas[name] = schema
        errors.extend(_schema_metadata_errors(name, schema))

    try:
        fingerprint_rules = load_json(contract_root / "fingerprint-rules.json")
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"fingerprint-rules.json: cannot load: {error}")
        fingerprint_rules = {"rules": {}}
    expected_rule_schemas = {
        "evidence-envelope.schema.json",
        "finding.schema.json",
        "remediation-proposal.schema.json",
    }
    actual_rule_schemas = {
        rule.get("schema") for rule in fingerprint_rules.get("rules", {}).values()
    }
    if actual_rule_schemas != expected_rule_schemas:
        errors.append("fingerprint-rules.json: rule schema coverage is incomplete")

    for supporting_name in ("compatibility-policy.json", "ownership.json"):
        try:
            supporting = load_json(contract_root / supporting_name)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{supporting_name}: cannot load: {error}")
            continue
        if not isinstance(supporting, dict) or not supporting.get("schema_version"):
            errors.append(f"{supporting_name}: schema_version is required")

    positive_count = 0
    negative_count = 0
    fixture_count = 0
    try:
        fixture_manifest = load_json(contract_root / "fixtures" / "manifest.json")
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"fixtures/manifest.json: cannot load: {error}")
        fixture_manifest = {"fixtures": []}

    fixture_coverage: dict[str, set[bool]] = {
        name: set() for name in EXPECTED_SCHEMAS
    }
    for fixture in fixture_manifest.get("fixtures", []):
        fixture_count += 1
        schema_name = fixture.get("schema")
        relative_path = fixture.get("path")
        expected_valid = fixture.get("valid")
        if schema_name not in schemas or not isinstance(relative_path, str):
            errors.append(f"fixtures/manifest.json: invalid fixture entry {fixture!r}")
            continue
        if not isinstance(expected_valid, bool):
            errors.append("fixtures/manifest.json: fixture validity must be boolean")
            continue
        fixture_coverage[schema_name].add(expected_valid)
        positive_count += int(expected_valid)
        negative_count += int(not expected_valid)
        fixture_path = contract_root / "fixtures" / relative_path
        try:
            instance = load_json(fixture_path)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{relative_path}: cannot load fixture: {error}")
            continue
        instance_errors = validate_instance(instance, schemas[schema_name])
        if isinstance(instance, dict):
            instance_errors.extend(
                semantic_errors(schema_name, instance, fingerprint_rules)
            )
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
                    f"{relative_path}: expected error containing {expected_error!r}; "
                    f"got {instance_errors!r}"
                )

    for schema_name, coverage in fixture_coverage.items():
        if coverage != {False, True}:
            errors.append(
                f"fixtures/manifest.json: {schema_name} needs positive and negative fixtures"
            )

    for name, schema in schemas.items():
        for index, example in enumerate(schema.get("examples", [])):
            example_errors = validate_instance(example, schema)
            if isinstance(example, dict):
                example_errors.extend(
                    semantic_errors(name, example, fingerprint_rules)
                )
            if example_errors:
                errors.append(
                    f"{name}: embedded example {index} failed: {example_errors[0]}"
                )

    return {
        "schema_version": "atlas-control-plane/validation-report/v1",
        "contracts_root": "contracts/v1",
        "schemas_checked": len(schemas),
        "fixtures_checked": fixture_count,
        "positive_fixtures": positive_count,
        "negative_fixtures": negative_count,
        "errors": sorted(errors),
    }
