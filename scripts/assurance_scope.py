#!/usr/bin/env python3
"""Build the repository registry consumed by default estate assurance."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

DEFAULT_ASSURANCE_EXCLUSION = "default-assurance"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    registry = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError("estate registry root must be an object")

    filtered = filter_default_assurance(registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(filtered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    before = len(registry.get("repositories", []))
    after = len(filtered.get("repositories", []))
    print(f"default assurance scope: {after} repositories ({before - after} excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
