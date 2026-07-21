#!/usr/bin/env python3
"""Build the repository registry consumed by default estate assurance."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

DEFAULT_ASSURANCE_EXCLUSION = "default-assurance"
PUBLIC_ASSURANCE_REPOSITORIES = "public-assurance-repositories.json"
PUBLIC_ASSURANCE_SCHEMA_VERSION = "atlas-public-assurance/repositories/v2"
CLASSIFICATION_KEYS = {"repository", "lifecycle", "scope", "provenance"}


def filter_default_assurance(registry: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with repositories excluded from default assurance removed."""
    repositories = registry.get("repositories", [])
    if not isinstance(repositories, list):
        raise ValueError("estate registry repositories must be a list")

    filtered = copy.deepcopy(registry)
    filtered["repositories"] = [
        item
        for item in repositories
        if not (
            isinstance(item, dict)
            and isinstance(item.get("exclusions"), list)
            and DEFAULT_ASSURANCE_EXCLUSION in item["exclusions"]
        )
    ]
    return filtered


def add_public_assurance_repositories(
    registry: dict[str, Any], supplement_path: Path
) -> dict[str, Any]:
    """Add classified public non-runtime repositories without private identities."""
    if not supplement_path.is_file():
        return registry

    supplement = json.loads(supplement_path.read_text(encoding="utf-8"))
    if not isinstance(supplement, dict):
        raise ValueError("public assurance repository supplement must be an object")
    if supplement.get("schema_version") != PUBLIC_ASSURANCE_SCHEMA_VERSION:
        raise ValueError("unsupported public assurance repository supplement schema")

    entries = supplement.get("repositories", [])
    if not isinstance(entries, list):
        raise ValueError("public assurance repository supplement must be a list")

    merged = copy.deepcopy(registry)
    repositories = merged.setdefault("repositories", [])
    present = {
        item.get("repository")
        for item in repositories
        if isinstance(item, dict) and isinstance(item.get("repository"), str)
    }
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != CLASSIFICATION_KEYS:
            raise ValueError(
                "public assurance entries must contain repository and classification axes"
            )
        repository = entry.get("repository")
        if not isinstance(repository, str) or not repository:
            raise ValueError("public assurance repository names must be non-empty strings")
        if entry.get("scope") != "public":
            raise ValueError("public assurance non-runtime repositories must have public scope")
        if repository in present:
            raise ValueError(
                f"public assurance repository overlaps runtime registry: {repository}"
            )
        repositories.append(
            {
                "repository": repository,
                "lifecycle": entry["lifecycle"],
                "scope": entry["scope"],
                "provenance": entry["provenance"],
                "runtime_service": False,
            }
        )
        present.add(repository)

    repositories.sort(key=lambda item: str(item.get("repository", "")))
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    registry = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError("estate registry root must be an object")

    filtered = filter_default_assurance(registry)
    supplement_path = args.input.parent / PUBLIC_ASSURANCE_REPOSITORIES
    filtered = add_public_assurance_repositories(filtered, supplement_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(filtered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    before = len(registry.get("repositories", []))
    after = len(filtered.get("repositories", []))
    print(f"default assurance scope: {after} repositories ({after - before:+d} net)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
