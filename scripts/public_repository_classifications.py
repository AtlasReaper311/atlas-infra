#!/usr/bin/env python3
"""Build the deterministic public repository classification projection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = Path("policy/estate-registry.json")
DEFAULT_SUPPLEMENT = Path("policy/public-assurance-repositories.json")
DEFAULT_OUTPUT = Path("policy/public-repository-classifications.json")
SCHEMA_VERSION = "atlas-public-repository-classifications/projection/v1"
SUPPLEMENT_SCHEMA_VERSION = "atlas-public-assurance/repositories/v2"
LIFECYCLES = {"production", "active", "experimental", "deprecated", "archived"}
SCOPES = {"public", "internal"}
PROVENANCES = {"original", "external-derived"}


class ClassificationProjectionError(ValueError):
    """Raised when classification authority inputs are malformed or conflicting."""


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ClassificationProjectionError(f"JSON object required: {path}")
    return value


def _classification(
    item: dict[str, Any], *, runtime_service: bool
) -> dict[str, Any]:
    repository = item.get("repository")
    lifecycle = item.get("lifecycle")
    scope = item.get("scope")
    provenance = item.get("provenance")

    if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
        raise ClassificationProjectionError("repository identity is missing or malformed")
    if lifecycle not in LIFECYCLES:
        raise ClassificationProjectionError(f"invalid lifecycle for {repository}")
    if scope not in SCOPES:
        raise ClassificationProjectionError(f"invalid scope for {repository}")
    if provenance not in PROVENANCES:
        raise ClassificationProjectionError(f"invalid provenance for {repository}")

    return {
        "repository": repository,
        "lifecycle": lifecycle,
        "scope": scope,
        "provenance": provenance,
        "runtime_service": runtime_service,
    }


def build_projection(
    registry: dict[str, Any], supplement: dict[str, Any]
) -> dict[str, Any]:
    """Combine non-overlapping Atlas Infra classification sources."""

    if registry.get("schema_version") != "atlas-contract-registry/estate-registry/v1":
        raise ClassificationProjectionError("unsupported estate registry schema")
    if supplement.get("schema_version") != SUPPLEMENT_SCHEMA_VERSION:
        raise ClassificationProjectionError("unsupported public assurance supplement schema")

    runtime_values = registry.get("repositories")
    supplement_values = supplement.get("repositories")
    if not isinstance(runtime_values, list) or not isinstance(supplement_values, list):
        raise ClassificationProjectionError("repository collections must be lists")

    classifications: dict[str, dict[str, Any]] = {}
    for item in runtime_values:
        if not isinstance(item, dict):
            raise ClassificationProjectionError("runtime registry entry must be an object")
        entry = _classification(item, runtime_service=bool(item.get("runtime_service")))
        if entry["runtime_service"] is not True:
            raise ClassificationProjectionError(
                f"runtime registry contains non-runtime repository {entry['repository']}"
            )
        repository = entry["repository"]
        if repository in classifications:
            raise ClassificationProjectionError(f"duplicate repository: {repository}")
        classifications[repository] = entry

    for item in supplement_values:
        if not isinstance(item, dict):
            raise ClassificationProjectionError("public assurance entry must be an object")
        if set(item) != {"repository", "lifecycle", "scope", "provenance"}:
            raise ClassificationProjectionError(
                "public assurance entries must contain only repository and classification axes"
            )
        entry = _classification(item, runtime_service=False)
        if entry["scope"] != "public":
            raise ClassificationProjectionError(
                f"public non-runtime repository must have public scope: {entry['repository']}"
            )
        repository = entry["repository"]
        if repository in classifications:
            raise ClassificationProjectionError(
                f"classification authority overlap for repository: {repository}"
            )
        classifications[repository] = entry

    repositories = [classifications[name] for name in sorted(classifications)]
    fingerprint_material = json.dumps(
        {"repositories": repositories},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    source_fingerprint = "sha256:" + hashlib.sha256(fingerprint_material).hexdigest()

    return {
        "schema_version": SCHEMA_VERSION,
        "authority": "AtlasReaper311/atlas-infra",
        "sources": {
            "runtime_registry": "policy/estate-registry.json",
            "public_non_runtime": "policy/public-assurance-repositories.json",
        },
        "source_fingerprint": source_fingerprint,
        "repository_count": len(repositories),
        "repositories": repositories,
    }


def render_json(value: dict[str, Any]) -> str:
    """Render a stable review-friendly projection with one repository per line."""

    lines = [
        "{",
        f'  "authority": {json.dumps(value["authority"])},',
        '  "repositories": [',
    ]
    repositories = value["repositories"]
    for index, repository in enumerate(repositories):
        suffix = "," if index < len(repositories) - 1 else ""
        lines.append(
            "    "
            + json.dumps(
                repository,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + suffix
        )
    lines.extend(
        [
            "  ],",
            f'  "repository_count": {value["repository_count"]},',
            f'  "schema_version": {json.dumps(value["schema_version"])},',
            f'  "source_fingerprint": {json.dumps(value["source_fingerprint"])},',
            '  "sources": {',
            f'    "public_non_runtime": {json.dumps(value["sources"]["public_non_runtime"])},',
            f'    "runtime_registry": {json.dumps(value["sources"]["runtime_registry"])}',
            "  }",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify the Atlas public repository classification projection."
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    projection = build_projection(load_object(args.registry), load_object(args.supplement))
    rendered = render_json(projection)

    if args.check:
        if not args.output.is_file():
            raise ClassificationProjectionError(
                f"classification projection is missing: {args.output}"
            )
        if args.output.read_text(encoding="utf-8") != rendered:
            raise ClassificationProjectionError(
                "classification projection differs from authoritative Atlas Infra inputs"
            )
        print(
            f"classification projection verified: {projection['repository_count']} repositories "
            f"({projection['source_fingerprint']})"
        )
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"classification projection written: {projection['repository_count']} repositories "
        f"({projection['source_fingerprint']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
