#!/usr/bin/env python3
"""Deterministic, read-only RunbookIndexEntry matcher.

The canonical RunbookIndexEntry objects remain contract-conformant and inert.
Additional matching metadata lives in a separate routing policy keyed by
``entry_id`` so the strict v1 contract is never weakened with extra fields.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

try:
    from .control_plane_io import digest_json, load_json, write_json
except ImportError:  # direct script execution
    from control_plane_io import digest_json, load_json, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "policy" / "runbook-index.json"
DEFAULT_ROUTING = ROOT / "policy" / "runbook-routing.json"
CONTRACT_SCHEMA = ROOT / "contracts" / "v1" / "runbook-index-entry.schema.json"
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
ENTRY_KEYS = {
    "schema_version",
    "entry_id",
    "failure_fingerprints",
    "categories",
    "service_id",
    "repository",
    "runbook_path",
    "diagnostic_commands",
    "escalation",
    "last_validated_at",
}
ROUTE_KEYS = {
    "title",
    "services",
    "repositories",
    "states",
    "severities",
    "triggers",
    "diagnostics",
    "blocked_actions",
}


def _tokens(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.update(TOKEN_RE.findall(str(key).lower()))
            found.update(_tokens(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_tokens(item))
    elif value is not None:
        found.update(TOKEN_RE.findall(str(value).lower()))
    return found


def _values(event: dict[str, Any], keys: Iterable[str]) -> set[str]:
    result: set[str] = set()
    stack: list[Any] = [event]
    keyset = set(keys)
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if key in keyset:
                    if isinstance(value, list):
                        result.update(str(v).lower() for v in value)
                    elif value is not None:
                        result.add(str(value).lower())
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return result


def _contract_errors(entry: dict[str, Any], position: int) -> list[str]:
    """Validate the exact shape used by RunbookIndexEntry v1.

    The repository's canonical validator is also invoked when available. This
    small local check keeps ``doctor`` useful even in an isolated bundle test.
    """
    prefix = f"entries[{position}]"
    errors: list[str] = []
    missing = sorted(ENTRY_KEYS - set(entry))
    extra = sorted(set(entry) - ENTRY_KEYS)
    errors.extend(f"{prefix}: missing {field}" for field in missing)
    errors.extend(f"{prefix}: unexpected {field}" for field in extra)
    if entry.get("schema_version") != "atlas-control-plane/runbook-index-entry/v1":
        errors.append(f"{prefix}.schema_version is invalid")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(entry.get("entry_id", ""))):
        errors.append(f"{prefix}.entry_id is invalid")
    if not isinstance(entry.get("failure_fingerprints"), list):
        errors.append(f"{prefix}.failure_fingerprints must be an array")
    if not isinstance(entry.get("categories"), list) or not entry.get("categories"):
        errors.append(f"{prefix}.categories must be a non-empty array")
    path_text = entry.get("runbook_path")
    if not isinstance(path_text, str) or path_text.startswith("/") or ".." in Path(path_text).parts:
        errors.append(f"{prefix}.runbook_path must be repository-relative")
    commands = entry.get("diagnostic_commands")
    if not isinstance(commands, list) or not commands:
        errors.append(f"{prefix}.diagnostic_commands must be a non-empty array")
    escalation = entry.get("escalation")
    if not isinstance(escalation, dict) or set(escalation) != {"owner", "channel_ref"}:
        errors.append(f"{prefix}.escalation is invalid")
    return errors


def _canonical_schema_errors(entry: dict[str, Any]) -> list[str]:
    if not CONTRACT_SCHEMA.is_file():
        return [f"canonical schema missing: {CONTRACT_SCHEMA.relative_to(ROOT)}"]
    try:
        try:
            from .control_plane_contracts import validate_instance
        except ImportError:
            from control_plane_contracts import validate_instance
    except (ImportError, AttributeError):
        return []
    schema = load_json(CONTRACT_SCHEMA)
    return [f"contract: {error}" for error in validate_instance(entry, schema)]


def validate_index(index: dict[str, Any], routing: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if index.get("schema_version") != "1.0.0":
        errors.append("index schema_version must be 1.0.0")
    if routing.get("schema_version") != "1.0.0":
        errors.append("routing schema_version must be 1.0.0")
    entries = index.get("entries")
    routes = routing.get("routes")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list")
        return errors
    if not isinstance(routes, dict):
        errors.append("routes must be an object")
        return errors

    seen: set[str] = set()
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{position}] must be an object")
            continue
        errors.extend(_contract_errors(entry, position))
        errors.extend(f"entries[{position}].{item}" for item in _canonical_schema_errors(entry))
        entry_id = entry.get("entry_id")
        if isinstance(entry_id, str):
            if entry_id in seen:
                errors.append(f"duplicate entry_id: {entry_id}")
            seen.add(entry_id)
            route = routes.get(entry_id)
            if not isinstance(route, dict):
                errors.append(f"routing missing for entry_id: {entry_id}")
            else:
                missing_route = sorted(ROUTE_KEYS - set(route))
                extra_route = sorted(set(route) - ROUTE_KEYS)
                errors.extend(f"routes.{entry_id}: missing {field}" for field in missing_route)
                errors.extend(f"routes.{entry_id}: unexpected {field}" for field in extra_route)
                for field in ROUTE_KEYS - {"title"}:
                    if field in route and not isinstance(route[field], list):
                        errors.append(f"routes.{entry_id}.{field} must be an array")
        path_text = entry.get("runbook_path")
        if isinstance(path_text, str):
            candidate = (root / path_text).resolve()
            if root.resolve() != candidate and root.resolve() not in candidate.parents:
                errors.append(f"entries[{position}].runbook_path escapes repository")

    unknown_routes = sorted(set(routes) - seen)
    errors.extend(f"routing references unknown entry_id: {entry_id}" for entry_id in unknown_routes)
    return errors


def _score(
    contract: dict[str, Any], route: dict[str, Any], event: dict[str, Any], query: str | None
) -> tuple[int, list[str]]:
    event_tokens = _tokens(event)
    query_tokens = _tokens(query or "")
    services = _values(event, {"service_id", "service", "serviceId"})
    repositories = _values(event, {"repository", "repo", "repository_full_name"})
    states = _values(event, {"state", "status", "release_status", "freshness_state", "restore_drill_state"})
    severities = _values(event, {"severity", "level"})
    fingerprints = _values(event, {"fingerprint", "failure_fingerprint"})
    categories = _values(event, {"category", "kind", "type", "finding_type", "rule_id"})

    score = 0
    anchored = False
    reasons: list[str] = []
    route_services = {str(v).lower() for v in route.get("services", [])}
    route_repositories = {str(v).lower() for v in route.get("repositories", [])}
    route_states = {str(v).lower() for v in route.get("states", [])}
    route_severities = {str(v).lower() for v in route.get("severities", [])}
    route_triggers = {str(v).lower() for v in route.get("triggers", [])}
    contract_categories = {str(v).lower() for v in contract.get("categories", [])}
    contract_fingerprints = {str(v).lower() for v in contract.get("failure_fingerprints", [])}

    exact_services = services & route_services
    if exact_services:
        score += 45
        anchored = True
        reasons.append("service")
    elif services and "*" in route_services:
        score += 5
        reasons.append("service-wildcard")
    if repositories & route_repositories:
        score += 30
        anchored = True
        reasons.append("repository")
    if states & route_states:
        score += 25
        reasons.append("state")
    if severities & route_severities:
        score += 10
        reasons.append("severity")
    if categories & contract_categories:
        score += 30
        anchored = True
        reasons.append("category")
    if fingerprints & contract_fingerprints:
        score += 100
        anchored = True
        reasons.append("fingerprint")
    trigger_hits = event_tokens & route_triggers
    if trigger_hits:
        score += 60 + min(20, len(trigger_hits) * 5)
        anchored = True
        reasons.append("trigger:" + ",".join(sorted(trigger_hits)))

    searchable = _tokens(
        {
            "entry_id": contract.get("entry_id"),
            "title": route.get("title"),
            "categories": contract.get("categories", []),
            "triggers": route.get("triggers", []),
            "diagnostics": route.get("diagnostics", []),
        }
    )
    query_hits = query_tokens & searchable
    if query_hits:
        score += min(40, len(query_hits) * 8)
        anchored = True
        reasons.append("query:" + ",".join(sorted(query_hits)))
    return (score if anchored else 0), reasons


def match(
    index: dict[str, Any],
    routing: dict[str, Any],
    event: dict[str, Any],
    query: str | None,
    limit: int,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = validate_index(index, routing, root)
    if errors:
        return {"schema_version": "1.0.0", "status": "failed", "errors": errors, "matches": []}

    routes = routing["routes"]
    ranked: list[dict[str, Any]] = []
    for contract in index["entries"]:
        route = routes[contract["entry_id"]]
        score, reasons = _score(contract, route, event, query)
        if score <= 0:
            continue
        path = root / contract["runbook_path"]
        ranked.append(
            {
                "runbook_id": contract["entry_id"],
                "title": route["title"],
                "path": contract["runbook_path"],
                "path_exists": path.is_file(),
                "owner": contract["escalation"]["owner"],
                "channel_ref": contract["escalation"]["channel_ref"],
                "score": score,
                "confidence": "high" if score >= 90 else "medium" if score >= 50 else "low",
                "matched_by": reasons,
                "diagnostics": route["diagnostics"],
                "blocked_actions": route["blocked_actions"],
                "manual_commands": [
                    {"command": command, "execution": "manual-owner-reviewed-only"}
                    for command in contract["diagnostic_commands"]
                ],
                "last_validated_at": contract["last_validated_at"],
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["runbook_id"]))
    matches = ranked[: max(1, min(limit, 20))]
    report = {
        "schema_version": "1.0.0",
        "status": "matched" if matches else "no-match",
        "event_digest": digest_json(event),
        "query": query,
        "match_count": len(matches),
        "matches": matches,
        "safety": {"commands_executed": False, "provider_calls": False, "writes_performed": False},
    }
    report["report_digest"] = digest_json(report)
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Runbook match report", "", f"Status: **{report['status']}**", ""]
    if not report.get("matches"):
        lines.extend(
            [
                "No matching runbook was found.",
                "",
                "Review the event classification and update the canonical index through a pull request.",
            ]
        )
    for item in report.get("matches", []):
        lines.extend(
            [
                f"## {item['title']}",
                "",
                f"- ID: `{item['runbook_id']}`",
                f"- Path: `{item['path']}`",
                f"- Confidence: `{item['confidence']}`",
                f"- Score: `{item['score']}`",
                f"- File present: `{str(item['path_exists']).lower()}`",
                "",
                "### Suggested diagnostics",
                "",
            ]
        )
        lines.extend(f"- {step}" for step in item["diagnostics"])
        lines.extend(["", "### Manual commands", ""])
        lines.extend(f"- `{command['command']}` ({command['execution']})" for command in item["manual_commands"])
        lines.extend(["", "### Blocked actions", ""])
        lines.extend(f"- {action}" for action in item["blocked_actions"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def doctor(index_path: Path, routing_path: Path) -> int:
    index = load_json(index_path)
    routing = load_json(routing_path)
    errors = validate_index(index, routing)
    missing = [
        entry["runbook_path"]
        for entry in index.get("entries", [])
        if isinstance(entry, dict) and not (ROOT / str(entry.get("runbook_path", ""))).is_file()
    ]
    payload = {
        "status": "passed" if not errors and not missing else "failed",
        "entries": len(index.get("entries", [])),
        "contract_schema": str(CONTRACT_SCHEMA.relative_to(ROOT)),
        "errors": errors,
        "missing_runbook_files": sorted(missing),
        "commands_executable": False,
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if payload["status"] == "passed" else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    doctor_parser.add_argument("--routing", type=Path, default=DEFAULT_ROUTING)
    match_parser = sub.add_parser("match")
    match_parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    match_parser.add_argument("--routing", type=Path, default=DEFAULT_ROUTING)
    match_parser.add_argument("--event", type=Path, required=True)
    match_parser.add_argument("--query")
    match_parser.add_argument("--limit", type=int, default=5)
    match_parser.add_argument("--report", type=Path)
    match_parser.add_argument("--markdown", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "doctor":
        return doctor(args.index, args.routing)
    index = load_json(args.index)
    routing = load_json(args.routing)
    event = load_json(args.event)
    if not isinstance(event, dict):
        print("event must be a JSON object", file=sys.stderr)
        return 2
    report = match(index, routing, event, args.query, args.limit)
    if args.report:
        write_json(args.report, report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
