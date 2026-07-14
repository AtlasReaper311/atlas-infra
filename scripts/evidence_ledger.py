#!/usr/bin/env python3
"""Metadata-only SQLite evidence ledger with deterministic ingestion and search."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any, Iterable

try:
    from .control_plane_io import canonical_json, digest_file, digest_json, load_json, parse_timestamp, safe_child, utc_now_text, write_json
except ImportError:  # direct script execution
    from control_plane_io import canonical_json, digest_file, digest_json, load_json, parse_timestamp, safe_child, utc_now_text, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy/evidence-ledger.json"
SCHEMA_VERSION = "1.0.0"
SECRET_PATTERN = re.compile(r"(?i)(bearer\s+[a-z0-9._~+/-]{8,}|gh[pousr]_[a-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")

DDL = """
CREATE TABLE IF NOT EXISTS evidence (
    record_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    service_id TEXT,
    repository TEXT,
    state TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS evidence_kind_idx ON evidence(kind);
CREATE INDEX IF NOT EXISTS evidence_service_idx ON evidence(service_id);
CREATE INDEX IF NOT EXISTS evidence_repo_idx ON evidence(repository);
CREATE INDEX IF NOT EXISTS evidence_state_idx ON evidence(state);
CREATE INDEX IF NOT EXISTS evidence_observed_idx ON evidence(observed_at);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(DDL)
    return connection


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "retention_days", "max_records_per_ingest", "max_summary_characters",
        "raw_payload_storage", "allowed_kinds", "allowed_states", "forbidden_field_fragments",
        "searchable_metadata_days",
    }
    missing = sorted(required - set(policy))
    errors.extend(f"missing policy field: {field}" for field in missing)
    if policy.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1.0.0")
    if policy.get("raw_payload_storage") is not False:
        errors.append("raw_payload_storage must remain false")
    return errors


def forbidden_paths(value: Any, fragments: list[str], prefix: str = "$") -> list[str]:
    errors: list[str] = []
    lowered_fragments = [fragment.lower() for fragment in fragments]
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in lowered_fragments):
                errors.append(f"forbidden field: {prefix}.{key}")
            errors.extend(forbidden_paths(item, fragments, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(forbidden_paths(item, fragments, f"{prefix}[{index}]"))
    elif isinstance(value, str) and SECRET_PATTERN.search(value):
        errors.append(f"credential-like value at {prefix}")
    return errors


def first(value: dict[str, Any], names: Iterable[str]) -> Any:
    stack: list[Any] = [value]
    name_set = set(names)
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, item in current.items():
                if key in name_set and item not in (None, "", []):
                    return item
                stack.append(item)
        elif isinstance(current, list):
            stack.extend(current)
    return None


def infer_kind(payload: dict[str, Any], path: Path) -> str:
    explicit = first(payload, {"evidence_kind", "kind", "type"})
    if isinstance(explicit, str):
        candidate = explicit.lower().replace("_", "-")
        aliases = {
            "releaseevidence": "release-evidence", "backupevidence": "backup-evidence",
            "remediationproposal": "gardener-proposal", "controlplanesummary": "control-plane-summary",
        }
        return aliases.get(candidate.replace("-", ""), candidate)
    name = path.name.lower()
    for candidate in ("release-evidence", "backup-evidence", "quota-report", "secret-watch-report", "registry-report", "deploy-plan", "runbook-match", "control-plane-summary", "gardener-proposal", "finding", "incident"):
        if candidate in name:
            return candidate
    if "fingerprint" in payload and "severity" in payload:
        return "finding"
    return "incident"


def normalize(payload: dict[str, Any], source: Path, source_root: Path, policy: dict[str, Any], now: datetime) -> dict[str, Any]:
    errors = forbidden_paths(payload, policy["forbidden_field_fragments"])
    if errors:
        raise ValueError("; ".join(errors))
    kind = infer_kind(payload, source)
    if kind not in policy["allowed_kinds"]:
        raise ValueError(f"evidence kind is not allowed: {kind}")
    state_value = first(payload, {"state", "status", "result_state", "release_status", "freshness_state"})
    state = str(state_value or "unknown").lower().replace("_", "-")
    if state not in policy["allowed_states"]:
        state = "unknown"
    observed_value = first(payload, {"observed_at", "timestamp", "completed_at", "audit_timestamp", "generated_at", "created_at"})
    observed = parse_timestamp(str(observed_value)) if observed_value else now
    service = first(payload, {"service_id", "service"})
    repository = first(payload, {"repository", "repository_full_name", "repo"})
    summary_value = first(payload, {"summary", "message", "title", "description", "evidence_summary"})
    summary = str(summary_value or f"{kind} metadata from {source.name}")
    summary = SECRET_PATTERN.sub("[REDACTED]", summary)[: policy["max_summary_characters"]]
    relative = safe_child(source_root, source).relative_to(source_root.resolve()).as_posix()
    source_digest = digest_file(source)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "service_id": str(service) if service is not None else None,
        "repository": str(repository) if repository is not None else None,
        "state": state,
        "observed_at": observed.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": relative,
        "source_digest": source_digest,
        "summary": summary,
    }
    record_id = digest_json(metadata)
    expires = observed + timedelta(days=int(policy["retention_days"]))
    return {
        **metadata,
        "record_id": record_id,
        "ingested_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expires_at": expires.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def input_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.rglob("*.json") if candidate.is_file() and not candidate.is_symlink())


def ingest(database: Path, input_path: Path, source_root: Path, policy_path: Path, now: datetime) -> dict[str, Any]:
    policy = load_json(policy_path)
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    files = input_files(input_path)
    if len(files) > policy["max_records_per_ingest"]:
        raise ValueError("input exceeds max_records_per_ingest")
    inserted = 0
    duplicates = 0
    rejected: list[dict[str, str]] = []
    with connect(database) as connection:
        for path in files:
            try:
                payload = load_json(path)
                if not isinstance(payload, dict):
                    raise ValueError("top-level JSON must be an object")
                record = normalize(payload, path, source_root, policy, now)
                cursor = connection.execute(
                    """INSERT OR IGNORE INTO evidence
                    (record_id, kind, service_id, repository, state, observed_at, ingested_at, expires_at, source_path, source_digest, summary, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record["record_id"], record["kind"], record["service_id"], record["repository"],
                        record["state"], record["observed_at"], record["ingested_at"], record["expires_at"],
                        record["source_path"], record["source_digest"], record["summary"], canonical_json(record),
                    ),
                )
                if cursor.rowcount:
                    inserted += 1
                else:
                    duplicates += 1
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                rejected.append({"path": str(path), "error": str(exc)})
        connection.commit()
    return {"status": "passed" if not rejected else "warning", "inserted": inserted, "duplicates": duplicates, "rejected": rejected, "raw_payloads_stored": False}


def search(database: Path, args: argparse.Namespace) -> dict[str, Any]:
    clauses: list[str] = []
    parameters: list[Any] = []
    for column, value in (("kind", args.kind), ("service_id", args.service), ("repository", args.repository), ("state", args.state)):
        if value:
            clauses.append(f"{column} = ?")
            parameters.append(value)
    if args.query:
        clauses.append("(summary LIKE ? OR metadata_json LIKE ?)")
        token = f"%{args.query}%"
        parameters.extend([token, token])
    sql = "SELECT * FROM evidence"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY observed_at DESC, record_id ASC LIMIT ?"
    parameters.append(max(1, min(args.limit, 500)))
    with connect(database) as connection:
        rows = [dict(row) for row in connection.execute(sql, parameters)]
    records = [json.loads(row.pop("metadata_json")) for row in rows]
    report = {"schema_version": SCHEMA_VERSION, "status": "passed", "count": len(records), "records": records}
    report["report_digest"] = digest_json(report)
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Evidence ledger search", "", f"Records: **{report['count']}**", ""]
    for record in report["records"]:
        lines.extend([
            f"## {record['kind']}: {record['state']}", "",
            f"- ID: `{record['record_id']}`",
            f"- Service: `{record.get('service_id') or 'unknown'}`",
            f"- Repository: `{record.get('repository') or 'unknown'}`",
            f"- Observed: `{record['observed_at']}`",
            f"- Source: `{record['source_path']}`",
            f"- Digest: `{record['source_digest']}`",
            "", record["summary"], "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def prune(database: Path, now: datetime) -> int:
    cutoff = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with connect(database) as connection:
        cursor = connection.execute("DELETE FROM evidence WHERE expires_at < ?", (cutoff,))
        connection.commit()
        return cursor.rowcount


def doctor(database: Path, policy_path: Path) -> dict[str, Any]:
    policy = load_json(policy_path)
    errors = validate_policy(policy)
    with connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    return {
        "status": "passed" if not errors and integrity == "ok" else "failed",
        "policy_errors": errors,
        "sqlite_integrity": integrity,
        "record_count": count,
        "raw_payload_storage": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("init", "doctor", "prune", "search", "ingest"):
        command = sub.add_parser(name)
        command.add_argument("--database", type=Path, required=True)
        command.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
        if name in {"prune", "ingest"}:
            command.add_argument("--now", default=utc_now_text())
    ingest_parser = sub.choices["ingest"]
    ingest_parser.add_argument("--input", type=Path, required=True)
    ingest_parser.add_argument("--source-root", type=Path, required=True)
    search_parser = sub.choices["search"]
    search_parser.add_argument("--kind")
    search_parser.add_argument("--service")
    search_parser.add_argument("--repository")
    search_parser.add_argument("--state")
    search_parser.add_argument("--query")
    search_parser.add_argument("--limit", type=int, default=100)
    search_parser.add_argument("--report", type=Path)
    search_parser.add_argument("--markdown", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "init":
        with connect(args.database):
            pass
        print(json.dumps({"status": "passed", "database": str(args.database)}, sort_keys=True))
        return 0
    if args.command == "doctor":
        report = doctor(args.database, args.policy)
    elif args.command == "prune":
        report = {"status": "passed", "deleted": prune(args.database, parse_timestamp(args.now))}
    elif args.command == "ingest":
        report = ingest(args.database, args.input, args.source_root, args.policy, parse_timestamp(args.now))
    else:
        report = search(args.database, args)
        if args.report:
            write_json(args.report, report)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
