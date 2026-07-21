#!/usr/bin/env python3
"""Validate and assemble deterministic Atlas Trace evidence graphs offline.

Wave 3.1 deliberately has no provider integration. This module consumes saved
evidence-node and evidence-edge documents, reuses the canonical Atlas control
plane JSON and SHA-256 implementation, and emits a bounded graph projection.
Public graph assembly is intentionally deferred to the later bounded public
projection, where explicit publication authority can be checked.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import control_plane_contracts as contracts


TRACE_SCHEMA_NAMES = (
    "evidence-edge.schema.json",
    "evidence-graph.schema.json",
    "evidence-node.schema.json",
)
TRACE_ROOT_RELATIVE = Path("contracts") / "v1" / "atlas-trace"
VISIBILITY_RANK = {
    "public": 0,
    "internal": 1,
    "restricted-metadata": 2,
}
EXPECTED_CANONICALIZATION = {
    "encoding": "UTF-8",
    "json": "RFC 8259 object with lexicographically sorted keys and compact separators",
    "unicode": "preserved without ASCII escaping",
    "digest": "SHA-256 lowercase hexadecimal",
}
EXPECTED_TRACE_RULES = {
    "evidence-node": {
        "kind": "selected-fields",
        "schema": "evidence-node.schema.json",
        "fields": ["kind", "identity.key"],
        "sort_arrays": [],
        "prefix": "node:sha256:",
        "output_path": "node_id",
    },
    "evidence-edge": {
        "kind": "selected-fields",
        "schema": "evidence-edge.schema.json",
        "fields": ["from_node", "relation", "to_node"],
        "sort_arrays": [],
        "prefix": "edge:sha256:",
        "output_path": "edge_id",
    },
    "evidence-graph": {
        "kind": "selected-fields",
        "schema": "evidence-graph.schema.json",
        "fields": ["visibility", "nodes", "edges"],
        "sort_arrays": ["nodes", "edges"],
        "prefix": "graph:sha256:",
        "output_path": "fingerprint",
    },
}


class TraceError(RuntimeError):
    """Atlas Trace input or contract failure."""


def trace_root(root: Path) -> Path:
    return root / TRACE_ROOT_RELATIVE


def _value_at_path(value: dict[str, Any], dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def calculate_trace_fingerprint(
    rule_name: str,
    instance: dict[str, Any],
    fingerprint_rules: dict[str, Any],
) -> str:
    """Calculate one Atlas Trace stable identifier using canonical Atlas JSON."""
    rule = fingerprint_rules["trace_rules"][rule_name]
    selected: dict[str, Any] = {}
    sorted_arrays = set(rule.get("sort_arrays", []))
    for dotted_path in rule["fields"]:
        field_value = _value_at_path(instance, dotted_path)
        if dotted_path in sorted_arrays and isinstance(field_value, list):
            field_value = sorted(field_value, key=contracts.canonical_json)
        selected[dotted_path] = field_value
    return str(rule["prefix"]) + contracts.sha256_hex(selected)


def canonical_bytes(value: Any) -> bytes:
    """Return the exact byte representation used for assembled graph output."""
    return (contracts.canonical_json(value) + "\n").encode("utf-8")


def _sort_evidence(value: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(value, key=contracts.canonical_json)


def normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(contracts.canonical_json(node))
    evidence = normalized.get("evidence")
    if isinstance(evidence, list):
        normalized["evidence"] = _sort_evidence(evidence)
    return normalized


def normalize_edge(edge: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(contracts.canonical_json(edge))
    evidence = normalized.get("evidence")
    if isinstance(evidence, list):
        normalized["evidence"] = _sort_evidence(evidence)
    match_keys = normalized.get("basis", {}).get("match_keys")
    if isinstance(match_keys, list):
        normalized["basis"]["match_keys"] = sorted(match_keys)
    return normalized


def _visibility_errors(
    container_visibility: str,
    evidence: list[dict[str, Any]],
    path: str,
) -> list[str]:
    errors: list[str] = []
    container_rank = VISIBILITY_RANK.get(container_visibility)
    if container_rank is None:
        return errors
    for index, reference in enumerate(evidence):
        reference_visibility = reference.get("visibility")
        reference_rank = VISIBILITY_RANK.get(reference_visibility)
        if reference_rank is not None and reference_rank > container_rank:
            errors.append(
                f"{path}[{index}].visibility: evidence visibility "
                f"{reference_visibility!r} exceeds container visibility "
                f"{container_visibility!r}"
            )
    return errors


def trace_semantic_errors(
    schema_name: str,
    instance: dict[str, Any],
    fingerprint_rules: dict[str, Any],
    schemas: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Apply deterministic identity, privacy, and relationship semantics."""
    errors = contracts._sensitive_key_errors(instance)

    rule_name = schema_name.removesuffix(".schema.json")
    if rule_name in fingerprint_rules.get("trace_rules", {}):
        expected = calculate_trace_fingerprint(rule_name, instance, fingerprint_rules)
        output_path = fingerprint_rules["trace_rules"][rule_name]["output_path"]
        actual = _value_at_path(instance, output_path)
        if actual != expected:
            errors.append(
                f"$.{output_path}: deterministic {rule_name} value does not match canonical input"
            )

    if schema_name == "evidence-node.schema.json":
        evidence = instance.get("evidence")
        if isinstance(evidence, list):
            errors.extend(
                _visibility_errors(
                    str(instance.get("visibility")),
                    evidence,
                    "$.evidence",
                )
            )
            if evidence != _sort_evidence(evidence):
                errors.append("$.evidence: evidence references must be canonically sorted")

        identity = instance.get("identity")
        kind = instance.get("kind")
        if isinstance(identity, dict):
            if kind == "repository":
                repository = identity.get("repository")
                if not isinstance(repository, str):
                    errors.append("$.identity.repository: repository nodes require repository")
                elif identity.get("key") != repository:
                    errors.append(
                        "$.identity.key: repository node key must equal repository identity"
                    )
            elif kind == "commit":
                repository = identity.get("repository")
                commit_sha = identity.get("commit_sha")
                if not isinstance(repository, str) or not isinstance(commit_sha, str):
                    errors.append(
                        "$.identity: commit nodes require repository and commit_sha"
                    )
                elif identity.get("key") != f"{repository}@{commit_sha}":
                    errors.append(
                        "$.identity.key: commit node key must equal repository@commit_sha"
                    )

    elif schema_name == "evidence-edge.schema.json":
        if instance.get("from_node") == instance.get("to_node"):
            errors.append("$: self-referential evidence edges are prohibited")

        basis = instance.get("basis")
        relation = instance.get("relation")
        if isinstance(basis, dict):
            method = basis.get("method")
            if relation == "CORRELATED_WITH":
                if method != "correlation-with-explicit-evidence":
                    errors.append(
                        "$.basis.method: CORRELATED_WITH requires "
                        "correlation-with-explicit-evidence"
                    )
            elif method == "correlation-with-explicit-evidence":
                errors.append(
                    "$.basis.method: correlation basis is allowed only for CORRELATED_WITH"
                )

            match_keys = basis.get("match_keys")
            if isinstance(match_keys, list) and match_keys != sorted(match_keys):
                errors.append("$.basis.match_keys: match keys must be sorted")

        evidence = instance.get("evidence")
        if isinstance(evidence, list):
            errors.extend(
                _visibility_errors(
                    str(instance.get("visibility")),
                    evidence,
                    "$.evidence",
                )
            )
            if evidence != _sort_evidence(evidence):
                errors.append("$.evidence: evidence references must be canonically sorted")

    elif schema_name == "evidence-graph.schema.json":
        nodes = instance.get("nodes")
        edges = instance.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return errors

        if instance.get("node_count") != len(nodes):
            errors.append("$.node_count: must equal the number of nodes")
        if instance.get("edge_count") != len(edges):
            errors.append("$.edge_count: must equal the number of edges")

        node_ids = [node.get("node_id") for node in nodes if isinstance(node, dict)]
        edge_ids = [edge.get("edge_id") for edge in edges if isinstance(edge, dict)]
        if len(node_ids) != len(set(node_ids)):
            errors.append("$.nodes: node_id values must be unique")
        if len(edge_ids) != len(set(edge_ids)):
            errors.append("$.edges: edge_id values must be unique")
        if node_ids != sorted(node_ids):
            errors.append("$.nodes: nodes must be sorted by node_id")
        if edge_ids != sorted(edge_ids):
            errors.append("$.edges: edges must be sorted by edge_id")

        graph_visibility = instance.get("visibility")
        graph_rank = VISIBILITY_RANK.get(graph_visibility)
        known_nodes = set(node_ids)

        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            if schemas is not None:
                errors.extend(
                    f"$.nodes[{index}]{item.removeprefix('$')}"
                    for item in validate_trace_instance(
                        "evidence-node.schema.json",
                        node,
                        schemas,
                        fingerprint_rules,
                    )
                )
            node_rank = VISIBILITY_RANK.get(node.get("visibility"))
            if (
                graph_rank is not None
                and node_rank is not None
                and node_rank > graph_rank
            ):
                errors.append(
                    f"$.nodes[{index}].visibility: node visibility "
                    f"{node.get('visibility')!r} exceeds graph visibility "
                    f"{graph_visibility!r}"
                )

        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                continue
            if schemas is not None:
                errors.extend(
                    f"$.edges[{index}]{item.removeprefix('$')}"
                    for item in validate_trace_instance(
                        "evidence-edge.schema.json",
                        edge,
                        schemas,
                        fingerprint_rules,
                    )
                )
            edge_rank = VISIBILITY_RANK.get(edge.get("visibility"))
            if (
                graph_rank is not None
                and edge_rank is not None
                and edge_rank > graph_rank
            ):
                errors.append(
                    f"$.edges[{index}].visibility: edge visibility "
                    f"{edge.get('visibility')!r} exceeds graph visibility "
                    f"{graph_visibility!r}"
                )
            for field in ("from_node", "to_node"):
                node_id = edge.get(field)
                if node_id not in known_nodes:
                    errors.append(
                        f"$.edges[{index}].{field}: referenced node is absent from graph"
                    )

    return errors


def validate_trace_instance(
    schema_name: str,
    instance: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    fingerprint_rules: dict[str, Any],
) -> list[str]:
    schema = schemas[schema_name]
    errors = contracts.validate_instance(instance, schema)
    errors.extend(
        trace_semantic_errors(
            schema_name,
            instance,
            fingerprint_rules,
            schemas,
        )
    )
    return errors


def load_trace_contracts(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    contract_root = trace_root(root)
    schemas = {
        name: contracts.load_json(contract_root / name)
        for name in TRACE_SCHEMA_NAMES
    }
    fingerprint_rules = contracts.load_json(
        root / "contracts" / "v1" / "fingerprint-rules.json"
    )
    return schemas, fingerprint_rules


def validate_trace_repository(root: Path) -> dict[str, Any]:
    """Validate the complete Atlas Trace v1 contract family and fixtures."""
    contract_root = trace_root(root)
    errors: list[str] = []

    actual_schema_names = tuple(
        sorted(path.name for path in contract_root.glob("*.schema.json"))
    )
    if actual_schema_names != TRACE_SCHEMA_NAMES:
        errors.append(
            "contracts/v1/atlas-trace: schema inventory mismatch; "
            f"expected {TRACE_SCHEMA_NAMES!r}, found {actual_schema_names!r}"
        )

    schemas: dict[str, dict[str, Any]] = {}
    for name in TRACE_SCHEMA_NAMES:
        try:
            schema = contracts.load_json(contract_root / name)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{name}: cannot load schema: {error}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"{name}: schema root must be an object")
            continue
        schemas[name] = schema
        errors.extend(contracts._schema_metadata_errors(name, schema))

    try:
        fingerprint_rules = contracts.load_json(
            root / "contracts" / "v1" / "fingerprint-rules.json"
        )
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"fingerprint-rules.json: cannot load: {error}")
        fingerprint_rules = {}

    if fingerprint_rules.get("canonicalization") != EXPECTED_CANONICALIZATION:
        errors.append(
            "fingerprint-rules.json: Atlas Trace requires the existing canonicalization"
        )
    if fingerprint_rules.get("trace_rules") != EXPECTED_TRACE_RULES:
        errors.append(
            "fingerprint-rules.json: Atlas Trace v1 fingerprint rules do not match "
            "the fixed stable-identity contract"
        )

    try:
        fixture_manifest = contracts.load_json(contract_root / "fixtures" / "manifest.json")
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"atlas-trace fixtures/manifest.json: cannot load: {error}")
        fixture_manifest = {"fixtures": []}

    coverage: dict[str, set[bool]] = {name: set() for name in TRACE_SCHEMA_NAMES}
    fixture_count = 0
    positive_count = 0
    negative_count = 0

    for fixture in fixture_manifest.get("fixtures", []):
        fixture_count += 1
        schema_name = fixture.get("schema")
        relative_path = fixture.get("path")
        expected_valid = fixture.get("valid")
        if schema_name not in schemas or not isinstance(relative_path, str):
            errors.append(f"atlas-trace fixture manifest: invalid entry {fixture!r}")
            continue
        if not isinstance(expected_valid, bool):
            errors.append("atlas-trace fixture manifest: fixture validity must be boolean")
            continue

        coverage[schema_name].add(expected_valid)
        positive_count += int(expected_valid)
        negative_count += int(not expected_valid)

        try:
            instance = contracts.load_json(contract_root / "fixtures" / relative_path)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            errors.append(f"{relative_path}: cannot load fixture: {error}")
            continue

        if not isinstance(instance, dict):
            instance_errors = ["$: fixture root must be an object"]
        else:
            instance_errors = validate_trace_instance(
                schema_name,
                instance,
                schemas,
                fingerprint_rules,
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

    for schema_name, values in coverage.items():
        if values != {False, True}:
            errors.append(
                f"atlas-trace fixtures: {schema_name} needs positive and negative fixtures"
            )

    for name, schema in schemas.items():
        for index, example in enumerate(schema.get("examples", [])):
            if not isinstance(example, dict):
                errors.append(f"{name}: embedded example {index} must be an object")
                continue
            example_errors = validate_trace_instance(
                name,
                example,
                schemas,
                fingerprint_rules,
            )
            if example_errors:
                errors.append(
                    f"{name}: embedded example {index} failed: {example_errors[0]}"
                )

    return {
        "schema_version": "atlas-control-plane/atlas-trace-validation-report/v1",
        "contracts_root": str(TRACE_ROOT_RELATIVE),
        "schemas_checked": len(schemas),
        "fixtures_checked": fixture_count,
        "positive_fixtures": positive_count,
        "negative_fixtures": negative_count,
        "errors": sorted(errors),
    }


def _load_documents(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        raise TraceError(f"input directory does not exist: {directory}")
    documents: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            document = contracts.load_json(path)
        except json.JSONDecodeError as error:
            raise TraceError(f"{path}: invalid JSON: {error}") from error
        if not isinstance(document, dict):
            raise TraceError(f"{path}: document root must be an object")
        documents.append(document)
    return documents


def assemble_graph(
    root: Path,
    input_dir: Path,
    visibility: str,
) -> dict[str, Any]:
    """Assemble one deterministic non-public graph from saved node/edge evidence."""
    if visibility == "public":
        raise TraceError(
            "public graph assembly is deferred until the bounded public projection "
            "can verify explicit publication authority"
        )

    schemas, fingerprint_rules = load_trace_contracts(root)
    nodes = [normalize_node(item) for item in _load_documents(input_dir / "nodes")]
    edges = [normalize_edge(item) for item in _load_documents(input_dir / "edges")]

    for index, node in enumerate(nodes):
        errors = validate_trace_instance(
            "evidence-node.schema.json",
            node,
            schemas,
            fingerprint_rules,
        )
        if errors:
            raise TraceError(f"nodes[{index}]: {errors[0]}")

    for index, edge in enumerate(edges):
        errors = validate_trace_instance(
            "evidence-edge.schema.json",
            edge,
            schemas,
            fingerprint_rules,
        )
        if errors:
            raise TraceError(f"edges[{index}]: {errors[0]}")

    nodes.sort(key=lambda item: item["node_id"])
    edges.sort(key=lambda item: item["edge_id"])
    graph: dict[str, Any] = {
        "schema_version": "atlas-control-plane/evidence-graph/v1",
        "visibility": visibility,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
    graph["fingerprint"] = calculate_trace_fingerprint(
        "evidence-graph",
        graph,
        fingerprint_rules,
    )

    errors = validate_trace_instance(
        "evidence-graph.schema.json",
        graph,
        schemas,
        fingerprint_rules,
    )
    if errors:
        raise TraceError(errors[0])
    return graph


def check_graph(root: Path, path: Path) -> dict[str, Any]:
    schemas, fingerprint_rules = load_trace_contracts(root)
    try:
        instance = contracts.load_json(path)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise TraceError(f"{path}: cannot load graph: {error}") from error
    if not isinstance(instance, dict):
        raise TraceError("$: graph root must be an object")

    errors = validate_trace_instance(
        "evidence-graph.schema.json",
        instance,
        schemas,
        fingerprint_rules,
    )
    if errors:
        raise TraceError(errors[0])

    if path.read_bytes() != canonical_bytes(instance):
        raise TraceError(
            "graph bytes are not canonical; use Atlas Trace assembly output unchanged"
        )
    return instance


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="atlas-infra repository root",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate-contracts",
        help="validate the Atlas Trace schemas, identity rules, and fixtures",
    )
    validate_parser.add_argument("--report", type=Path)

    assemble_parser = subparsers.add_parser(
        "assemble",
        help="assemble saved evidence nodes and edges into canonical graph JSON",
    )
    assemble_parser.add_argument("--input-dir", type=Path, required=True)
    assemble_parser.add_argument("--output", type=Path, required=True)
    assemble_parser.add_argument(
        "--visibility",
        choices=("internal", "restricted-metadata"),
        default="internal",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="validate a canonical assembled graph without network access",
    )
    check_parser.add_argument("--input", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()

    try:
        if args.command == "validate-contracts":
            report = validate_trace_repository(root)
            if args.report:
                _write_json(args.report, report)
            if report["errors"]:
                for error in report["errors"]:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(
                "Atlas Trace contracts valid: "
                f"{report['schemas_checked']} schemas, "
                f"{report['positive_fixtures']} positive fixtures, "
                f"{report['negative_fixtures']} negative fixtures"
            )
            return 0

        if args.command == "assemble":
            graph = assemble_graph(root, args.input_dir.resolve(), args.visibility)
            _write_json(args.output, graph)
            print(
                f"Atlas Trace graph assembled: {graph['node_count']} nodes, "
                f"{graph['edge_count']} edges, {graph['fingerprint']}"
            )
            return 0

        if args.command == "check":
            graph = check_graph(root, args.input.resolve())
            print(
                f"Atlas Trace graph valid: {graph['node_count']} nodes, "
                f"{graph['edge_count']} edges, {graph['fingerprint']}"
            )
            return 0

    except TraceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
