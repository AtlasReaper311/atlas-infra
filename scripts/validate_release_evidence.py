#!/usr/bin/env python3
"""Validate one ReleaseEvidence document with the canonical v1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from control_plane_contracts import load_json, semantic_errors, validate_instance


def validate_release_evidence(root: Path, instance_path: Path) -> dict[str, object]:
    """Return a stable validation report for one ReleaseEvidence document."""
    contract_root = root / "contracts" / "v1"
    schema_name = "release-evidence.schema.json"
    errors: list[str] = []

    try:
        schema = load_json(contract_root / schema_name)
        rules = load_json(contract_root / "fingerprint-rules.json")
        instance = load_json(instance_path)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        errors.append(f"cannot load release evidence or contract: {error}")
    else:
        if not isinstance(instance, dict):
            errors.append("$: release evidence root must be an object")
        else:
            errors.extend(validate_instance(instance, schema))
            errors.extend(semantic_errors(schema_name, instance, rules))

    return {
        "schema_version": "atlas-control-plane/release-evidence-validation/v1",
        "instance": instance_path.name,
        "valid": not errors,
        "errors": sorted(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="atlas-infra repository root",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = validate_release_evidence(args.root.resolve(), args.instance.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")

    if not args.quiet:
        print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
