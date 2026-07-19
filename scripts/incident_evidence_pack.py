#!/usr/bin/env python3
"""Assemble a deterministic incident evidence pack from local files.

The pack links the reliability evidence around one incident: the affected
service and objective, detection times, the burn transition, any related
release, journey and notification evidence, recovery evidence, the applicable
runbook, DORA correlation, and a chaos experiment identifier when one applies.

Rules:

- inputs are local files only; nothing is fetched and nothing is written
  anywhere except the requested output path;
- linked artifacts become path plus SHA-256 digest references, never embedded
  payloads;
- absent evidence is recorded as absent, never inferred;
- identical inputs produce byte-identical output (``generated_at`` is a
  required argument, not wall time);
- no incident is created anywhere and no external system is contacted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from .control_plane_io import digest_file, digest_json, load_json
except ImportError:  # direct script execution
    from control_plane_io import digest_file, digest_json, load_json

ROOT = Path(__file__).resolve().parents[1]
PACK_SCHEMA = ROOT / "policy/schemas/incident-evidence-pack.schema.json"
RUNBOOK_INDEX = ROOT / "policy/runbook-index.json"

TIMESTAMP_HELP = "UTC RFC 3339 timestamp ending in Z"


def _contracts_module():
    try:
        from . import control_plane_contracts
    except ImportError:  # direct script execution
        import control_plane_contracts
    return control_plane_contracts


def _reference(kind: str, path: Path) -> dict[str, str]:
    return {"kind": kind, "path": str(path), "digest": digest_file(path)}


def _runbook_for_state(state: str, root: Path = ROOT) -> str | None:
    """Deterministic runbook lookup from the committed index."""
    index = load_json(root / "policy/runbook-index.json")
    wanted = {
        "budget_exhausted": "reliability-budget-exhausted",
        "budget_at_risk": "reliability-budget-exhausted",
        "stale_evidence": "reliability-evidence-stale",
        "unavailable_source": "reliability-source-unavailable",
        "malformed_evidence": "reliability-source-unavailable",
    }.get(state)
    if wanted is None:
        return None
    for entry in index.get("entries", []):
        if entry.get("entry_id") == wanted:
            return entry.get("runbook_path")
    return None


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    result = load_json(args.reliability_result)
    entry = next(
        (
            item
            for item in result.get("results", [])
            if item.get("service_id") == args.service_id
        ),
        None,
    )
    if entry is None:
        raise SystemExit(
            f"reliability result has no entry for service {args.service_id!r}"
        )

    references = [_reference("reliability-result", args.reliability_result)]
    burn = entry.get("burn", {})
    fast_rate = burn.get("fast", {}).get("rate")
    slow_rate = burn.get("slow", {}).get("rate")
    burn_transition = None
    if fast_rate is not None or slow_rate is not None:
        burn_transition = f"fast {fast_rate} slow {slow_rate} at {result.get('evaluated_at')}"

    incident_id = None
    if args.incident:
        incident = load_json(args.incident)
        incident_id = str(incident.get("id")) if incident.get("id") is not None else None
        references.append(_reference("incident", args.incident))

    release: dict[str, Any] = {
        "related": "unknown",
        "repository": None,
        "deploy_event_at": None,
        "reference": None,
    }
    if args.release_evidence:
        evidence = load_json(args.release_evidence)
        release = {
            "related": "linked",
            "repository": evidence.get("repository"),
            "deploy_event_at": evidence.get("completed_at"),
            "reference": f"release-evidence:{evidence.get('deployment_id')}",
        }
        references.append(_reference("release-evidence", args.release_evidence))
    elif args.no_related_release:
        release["related"] = "none-identified"

    journey: dict[str, Any] = {"state": "unknown", "reference": None}
    if args.release_evidence:
        evidence = load_json(args.release_evidence)
        journey = {
            "state": evidence.get("journey_result", "unknown"),
            "reference": f"release-evidence:{evidence.get('deployment_id')}",
        }

    notifications: dict[str, Any] = {
        "delivered_count": 0,
        "suppressed": None,
        "reference": None,
    }
    if args.notify_events:
        events = load_json(args.notify_events)
        listed = events.get("events", []) if isinstance(events, dict) else events
        notifications = {
            "delivered_count": min(len(listed), 1000),
            "suppressed": bool(events.get("suppressed")) if isinstance(events, dict) and "suppressed" in events else None,
            "reference": "notify-events export",
        }
        references.append(_reference("notify-events", args.notify_events))

    recovery: dict[str, Any] = {
        "state": "unknown",
        "confirmed_at": None,
        "reference": None,
    }
    if args.recovery_result:
        recovered = load_json(args.recovery_result)
        recovered_entry = next(
            (
                item
                for item in recovered.get("results", [])
                if item.get("service_id") == args.service_id
            ),
            None,
        )
        if recovered_entry and recovered_entry.get("state") == "objective_met":
            recovery = {
                "state": "confirmed",
                "confirmed_at": recovered.get("evaluated_at"),
                "reference": "recovery-result",
            }
        else:
            recovery = {
                "state": "not-confirmed",
                "confirmed_at": None,
                "reference": "recovery-result",
            }
        references.append(_reference("recovery-result", args.recovery_result))

    correlation_block: dict[str, Any] = {"state": "unavailable", "reference": None}
    if args.correlation:
        correlation_block = {"state": "available", "reference": "correlation export"}
        references.append(_reference("correlation", args.correlation))

    chaos_experiment_id = None
    if args.chaos_report:
        chaos = load_json(args.chaos_report)
        reports = chaos.get("reports", []) if isinstance(chaos, dict) else []
        if reports and isinstance(reports[0], dict):
            chaos_experiment_id = reports[0].get("experiment_id")
        elif isinstance(chaos, dict):
            chaos_experiment_id = chaos.get("experiment_id")
        references.append(_reference("chaos-report", args.chaos_report))

    pack: dict[str, Any] = {
        "schema": "atlas-incident-evidence-pack/v1",
        "generated_at": args.generated_at,
        "service_id": args.service_id,
        "objective_id": entry.get("objective_id"),
        "indicator": entry.get("indicator"),
        "detection": {
            "first_detected_at": args.first_detected_at,
            "last_healthy_at": args.last_healthy_at,
            "incident_id": incident_id,
        },
        "reliability": {
            "state": entry.get("state"),
            "burn_transition": burn_transition,
            "result_reference": f"reliability-result:{result.get('fingerprint')}",
        },
        "release": release,
        "journey": journey,
        "notifications": notifications,
        "recovery": recovery,
        "runbook_ref": _runbook_for_state(entry.get("state")),
        "dora_correlation": correlation_block,
        "chaos_experiment_id": chaos_experiment_id,
        "references": references,
    }
    pack["fingerprint"] = digest_json(pack)
    return pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-id", required=True)
    parser.add_argument("--reliability-result", type=Path, required=True)
    parser.add_argument("--generated-at", required=True, help=TIMESTAMP_HELP)
    parser.add_argument("--first-detected-at", required=True, help=TIMESTAMP_HELP)
    parser.add_argument("--last-healthy-at", help=TIMESTAMP_HELP)
    parser.add_argument("--incident", type=Path)
    parser.add_argument("--release-evidence", type=Path)
    parser.add_argument("--no-related-release", action="store_true",
                        help="record that no related release was identified")
    parser.add_argument("--notify-events", type=Path)
    parser.add_argument("--recovery-result", type=Path)
    parser.add_argument("--correlation", type=Path)
    parser.add_argument("--chaos-report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.last_healthy_at is None:
        args.last_healthy_at = None

    pack = build_pack(args)

    contracts = _contracts_module()
    schema = load_json(PACK_SCHEMA)
    errors = contracts.validate_instance(pack, schema)
    errors.extend(contracts._sensitive_key_errors(pack))
    if errors:
        for problem in errors:
            print(f"ERROR {problem}", file=sys.stderr)
        return 1

    rendered = json.dumps(pack, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
