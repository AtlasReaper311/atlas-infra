#!/usr/bin/env python3
"""Validate the Atlas estate registry and ServiceContract set offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from contract_registry import render_markdown, validate_contract_registry


def _resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="atlas-infra repository root",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("policy/estate-registry.json"),
    )
    parser.add_argument(
        "--contracts",
        type=Path,
        default=Path("policy/service-contracts"),
    )
    parser.add_argument("--report", type=Path, help="write deterministic JSON report")
    parser.add_argument(
        "--markdown", type=Path, help="write deterministic Markdown report"
    )
    parser.add_argument(
        "--graph", type=Path, help="write deterministic dependency graph JSON"
    )
    parser.add_argument(
        "--catalog", type=Path, help="write deterministic local service catalogue JSON"
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    registry = _resolve(root, args.registry)
    contracts = _resolve(root, args.contracts)
    first = validate_contract_registry(
        root=root,
        registry_path=registry,
        contracts_dir=contracts,
    )
    second = validate_contract_registry(
        root=root,
        registry_path=registry,
        contracts_dir=contracts,
    )
    idempotent = first == second
    report = {**first, "idempotent": idempotent, "validation_errors": []}
    if not idempotent:
        report["status"] = "failed"
        report["validation_errors"].append(
            "validation output changed between identical offline runs"
        )

    if args.report:
        _write_json(args.report, report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if args.graph:
        _write_json(args.graph, report["dependency_graph"])
    if args.catalog:
        _write_json(
            args.catalog,
            {
                "schema_version": "atlas-contract-registry/service-catalog/v1",
                "reviewed_at": report["reviewed_at"],
                "services": report["service_catalog"],
            },
        )

    if not args.quiet:
        print(
            "contract registry: "
            f"{report['repositories_checked']} repositories, "
            f"{report['contracts_checked']} contracts, "
            f"{report['routes_checked']} routes, "
            f"{report['finding_count']} findings"
        )
        for finding in report["findings"]:
            print(
                f"{finding['severity'].upper()}: "
                f"{finding['rule_id']}: {finding['evidence']['summary']}",
                file=sys.stderr,
            )
        for error in report["finding_schema_errors"] + report["validation_errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        print("PASS" if report["status"] == "passed" else "FAIL")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
