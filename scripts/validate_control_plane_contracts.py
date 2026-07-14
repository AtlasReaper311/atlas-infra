#!/usr/bin/env python3
"""CLI entry point for deterministic control-plane contract validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from control_plane_contracts import validate_repository


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="atlas-infra repository root",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    first = validate_repository(root)
    second = validate_repository(root)
    idempotent = first == second
    report = {**first, "idempotent": idempotent}
    if not idempotent:
        report["errors"] = sorted(
            [*report["errors"], "validation output changed between identical runs"]
        )

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")

    if not args.quiet:
        print(
            "control-plane contracts: "
            f"{report['schemas_checked']} schemas, "
            f"{report['positive_fixtures']} positive fixtures, "
            f"{report['negative_fixtures']} negative fixtures"
        )
        for error in report["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        print("PASS" if not report["errors"] else "FAIL")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
