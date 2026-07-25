#!/usr/bin/env python3
"""Validate chaos target capabilities and stamp policy provenance into reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import chaos_harness


def canonical_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonical_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical_json_value(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def fingerprint(value: dict[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("fingerprint", None)
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def string_set(value: Any, field: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty list")
        return set()
    items = {str(item) for item in value if isinstance(item, str) and item}
    if len(items) != len(value):
        errors.append(f"{field} must contain unique non-empty strings")
    return items


def validate_capabilities(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    version = policy.get("version")
    if not isinstance(version, str) or not version:
        errors.append("version must be a non-empty string")

    capabilities = policy.get("target_capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("target_capabilities must be a non-empty object")
        return errors

    declared_faults: set[str] = set()
    target_classes: dict[str, tuple[set[str], set[str]]] = {}
    for target, contract in capabilities.items():
        if not isinstance(contract, dict):
            errors.append(f"target_capabilities.{target} must be an object")
            continue
        live = string_set(
            contract.get("live_faults"),
            f"target_capabilities.{target}.live_faults",
            errors,
        )
        test_only = string_set(
            contract.get("test_only_faults"),
            f"target_capabilities.{target}.test_only_faults",
            errors,
        )
        overlap = live & test_only
        if overlap:
            errors.append(
                f"target_capabilities.{target} classifies faults twice: "
                f"{', '.join(sorted(overlap))}"
            )
        if contract.get("single_active_lease") is not True:
            errors.append(
                f"target_capabilities.{target}.single_active_lease must be true"
            )
        target_classes[str(target)] = (live, test_only)
        declared_faults.update(live)
        declared_faults.update(test_only)

    harness_faults = set(chaos_harness.ALLOWED_FAULTS)
    if declared_faults != harness_faults:
        missing = harness_faults - declared_faults
        extra = declared_faults - harness_faults
        if missing:
            errors.append(
                "target capabilities omit harness faults: "
                + ", ".join(sorted(missing))
            )
        if extra:
            errors.append(
                "target capabilities declare unsupported faults: "
                + ", ".join(sorted(extra))
            )

    maximum = policy.get("defaults", {}).get("maximum_duration_seconds")
    if maximum != chaos_harness.MAX_DURATION_SECONDS:
        errors.append(
            "defaults.maximum_duration_seconds must match the harness maximum"
        )

    for experiment in policy.get("experiments", []):
        if not isinstance(experiment, dict):
            continue
        identifier = str(experiment.get("id", "unnamed"))
        target = str(experiment.get("target", ""))
        fault = str(experiment.get("fault", ""))
        if target not in target_classes:
            errors.append(f"{identifier}: target has no capability contract: {target}")
            continue
        live, test_only = target_classes[target]
        if fault in test_only:
            errors.append(f"{identifier}: test-only fault cannot enter live policy: {fault}")
        elif fault not in live:
            errors.append(f"{identifier}: fault is not authorised for target {target}: {fault}")

    return errors


def stamp_report(
    policy: dict[str, Any],
    report_path: str | Path,
    markdown_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_json(report_path)
    if document.get("schema") != "atlas-chaos-report-set/v1":
        raise ValueError("report schema must be atlas-chaos-report-set/v1")

    experiments = {
        str(item.get("id")): item
        for item in policy.get("experiments", [])
        if isinstance(item, dict)
    }
    policy_version = str(policy["version"])
    for item in document.get("experiments", []):
        identifier = str(item.get("experiment_id", ""))
        declared = experiments.get(identifier)
        if declared is None:
            raise ValueError(f"report contains an undeclared experiment: {identifier}")
        for field in ("target", "fault"):
            if item.get(field) != declared.get(field):
                raise ValueError(
                    f"report {identifier} {field} does not match policy"
                )
        if str(item.get("experiment_version")) != str(declared.get("version")):
            raise ValueError(
                f"report {identifier} experiment version does not match policy"
            )
        item["policy_version"] = policy_version
        item["capability_class"] = "live"
        item["fingerprint"] = fingerprint(item)

    document["policy"] = {
        "schema": policy.get("schema"),
        "version": policy_version,
        "path": "policy/chaos-experiments.json",
    }
    document["fingerprint"] = fingerprint(document)

    report_file = Path(report_path)
    report_file.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if markdown_path is not None:
        Path(markdown_path).write_text(render_markdown(document), encoding="utf-8")
    return document


def render_markdown(document: dict[str, Any]) -> str:
    reports = document.get("experiments", [])
    mode = reports[0].get("mode", "none") if reports else "none"
    policy_version = document.get("policy", {}).get("version", "unknown")
    summary = document.get("summary", {})
    lines = [
        "# Atlas Systems chaos assurance",
        "",
        f"Mode: **{mode}**  ",
        f"Policy version: **{policy_version}**  ",
        f"Experiments: **{summary.get('experiments', 0)}**  ",
        f"Passed: **{summary.get('passed', 0)}**  ",
        f"Failed: **{summary.get('failed', 0)}**",
        "",
        "| Experiment | Fault | Preflight | Detection | Notification | Recovery | Verdict |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in reports:
        stages = item.get("stages", {})
        lines.append(
            f"| `{item.get('experiment_id')}` | `{item.get('fault')}` | "
            f"{'pass' if stages.get('preflight', {}).get('ok') else 'fail'} | "
            f"{stages.get('detection', {}).get('latency_ms', 'n/a')}ms | "
            f"{stages.get('notification', {}).get('latency_ms', 'n/a')}ms | "
            f"{stages.get('recovery', {}).get('latency_ms', 'n/a')}ms | "
            f"{'pass' if item.get('passed') else 'fail'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate")
    validate.add_argument("--policy", required=True)

    stamp = subcommands.add_parser("stamp")
    stamp.add_argument("--policy", required=True)
    stamp.add_argument("--report", required=True)
    stamp.add_argument("--markdown")

    args = parser.parse_args()
    policy = load_json(args.policy)
    errors = chaos_harness.validate_policy(policy) + validate_capabilities(policy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(
            f"Validated chaos policy {policy['version']} with "
            f"{len(policy['experiments'])} live experiment(s)."
        )
        return 0

    try:
        document = stamp_report(policy, args.report, args.markdown)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(
        f"Stamped chaos report with policy {policy['version']}; "
        f"fingerprint {document['fingerprint']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
