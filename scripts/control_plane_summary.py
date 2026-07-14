#!/usr/bin/env python3
"""Build a deterministic ControlPlaneSummary from local source documents.

The aggregator is deliberately offline. It reads only the eleven allowlisted
JSON files in a supplied directory, performs no discovery or provider calls,
and never treats an absent or malformed source as healthy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from control_plane_contracts import load_json, validate_instance

STATES = {"healthy", "warning", "failed", "stale", "unavailable", "unknown"}
STATE_PRIORITY = {
    "healthy": 0,
    "unknown": 1,
    "warning": 2,
    "stale": 3,
    "unavailable": 4,
    "failed": 5,
}
SOURCE_FILES = {
    "health": "health.json",
    "journeys": "journeys.json",
    "release": "release.json",
    "contract_registry": "contract-registry.json",
    "quota": "quota.json",
    "findings": "findings.json",
    "gardener_proposals": "gardener-proposals.json",
    "secret_hygiene": "secret-watch.json",
    "backups": "backups.json",
    "runbooks": "runbooks.json",
    "evidence": "evidence.json",
}
REQUIRED_DATA_FIELDS = {
    "health": ("components_total", "components_healthy", "active_incidents"),
    "journeys": ("total", "failed"),
    "release": (
        "repository",
        "environment",
        "commit",
        "completed_at",
        "evidence_ref",
    ),
    "contract_registry": ("contracts_total", "contracts_valid", "drift_count"),
    "quota": (
        "used_percent",
        "projected_percent",
        "highest_meter",
        "period_ends_at",
    ),
    "findings": ("total", "by_severity", "oldest_detected_at"),
    "gardener_proposals": ("total", "validation_failed", "open_pull_requests"),
    "secret_hygiene": ("required", "present", "stale", "unknown"),
    "backups": ("total", "healthy", "stale", "failed", "unknown"),
    "runbooks": ("valid", "invalid", "stale"),
    "evidence": ("searchable_records", "newest_record_at", "expiring_soon"),
}


def _parse_utc(value: str) -> datetime:
    """Parse the contract's RFC 3339 UTC timestamp form."""
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must end in Z")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _empty_source() -> dict[str, Any]:
    return {
        "state": "unknown",
        "generated_at": None,
        "stale_after": None,
        "data": {},
    }


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _nullable_number(value: Any) -> bool:
    return value is None or (
        isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
    )


def _nullable_string(value: Any) -> bool:
    return value is None or (isinstance(value, str) and bool(value))


def _valid_data(source_name: str, data: dict[str, Any]) -> bool:
    """Validate source value classes before projecting defaults."""
    count_fields = {
        "health": ("components_total", "components_healthy", "active_incidents"),
        "journeys": ("total", "failed"),
        "contract_registry": ("contracts_total", "contracts_valid", "drift_count"),
        "gardener_proposals": ("total", "validation_failed", "open_pull_requests"),
        "secret_hygiene": ("required", "present", "stale", "unknown"),
        "backups": ("total", "healthy", "stale", "failed", "unknown"),
        "runbooks": ("valid", "invalid", "stale"),
    }
    if source_name in count_fields:
        return all(_nonnegative_int(data.get(field)) for field in count_fields[source_name])
    if source_name == "release":
        return all(
            _nullable_string(data.get(field))
            for field in REQUIRED_DATA_FIELDS[source_name]
        )
    if source_name == "quota":
        return (
            _nullable_number(data.get("used_percent"))
            and _nullable_number(data.get("projected_percent"))
            and _nullable_string(data.get("highest_meter"))
            and _nullable_string(data.get("period_ends_at"))
        )
    if source_name == "findings":
        severity = data.get("by_severity")
        return (
            _nonnegative_int(data.get("total"))
            and isinstance(severity, dict)
            and all(
                _nonnegative_int(severity.get(level))
                for level in ("info", "warning", "failure", "critical")
            )
            and _nullable_string(data.get("oldest_detected_at"))
        )
    if source_name == "evidence":
        return (
            _nonnegative_int(data.get("searchable_records"))
            and _nullable_string(data.get("newest_record_at"))
            and _nonnegative_int(data.get("expiring_soon"))
        )
    return False


def _load_source(path: Path, source_name: str, now: datetime) -> dict[str, Any]:
    """Load one bounded source, degrading invalid input without guessing."""
    if not path.is_file():
        return _empty_source()
    try:
        document = load_json(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {**_empty_source(), "state": "unavailable"}

    if not isinstance(document, dict):
        return {**_empty_source(), "state": "unavailable"}
    state = document.get("state")
    data = document.get("data")
    if state not in STATES or not isinstance(data, dict):
        return {**_empty_source(), "state": "unavailable"}
    try:
        generated_at = _parse_utc(document["generated_at"])
        stale_after = _parse_utc(document["stale_after"])
    except (KeyError, TypeError, ValueError):
        return {**_empty_source(), "state": "unavailable"}
    if stale_after < generated_at:
        return {**_empty_source(), "state": "unavailable"}

    missing_fields = [
        field for field in REQUIRED_DATA_FIELDS[source_name] if field not in data
    ]
    if missing_fields:
        state = "unknown"
    elif not _valid_data(source_name, data):
        return {**_empty_source(), "state": "unavailable"}
    if now > stale_after and state != "unavailable":
        state = "stale"
    return {
        "state": state,
        "generated_at": _iso(generated_at),
        "stale_after": _iso(stale_after),
        "data": data,
    }


def load_sources(source_directory: Path, now: datetime) -> dict[str, dict[str, Any]]:
    """Load only the fixed Phase 9 source filenames."""
    return {
        name: _load_source(source_directory / filename, name, now)
        for name, filename in SOURCE_FILES.items()
    }


def worst_state(states: list[str]) -> str:
    """Return the shared aggregate state using the approved precedence."""
    return max(states, key=STATE_PRIORITY.__getitem__) if states else "unknown"


def _int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _number_or_none(data: dict[str, Any], key: str) -> int | float | None:
    value = data.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _string_or_none(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    return value if isinstance(value, str) and value else None


def build_summary(source_directory: Path, now: datetime) -> dict[str, Any]:
    """Build one deterministic, schema-compatible summary."""
    sources = load_sources(source_directory, now)
    states = [source["state"] for source in sources.values()]
    fingerprint_input = {
        "now": _iso(now),
        "sources": sources,
    }
    request_digest = hashlib.sha256(
        _canonical(fingerprint_input).encode("utf-8")
    ).hexdigest()[:20]

    health = sources["health"]
    journeys = sources["journeys"]
    release = sources["release"]
    registry = sources["contract_registry"]
    quota = sources["quota"]
    findings = sources["findings"]
    gardener = sources["gardener_proposals"]
    secrets = sources["secret_hygiene"]
    backups = sources["backups"]
    runbooks = sources["runbooks"]
    evidence = sources["evidence"]

    by_severity = findings["data"].get("by_severity")
    if not isinstance(by_severity, dict):
        by_severity = {}

    return {
        "schema_version": "atlas-control-plane/control-plane-summary/v1",
        "generated_at": _iso(now),
        "stale_after": _iso(now + timedelta(minutes=10)),
        "request_id": f"phase9-{request_digest}",
        "state": worst_state(states),
        "health": {
            "state": health["state"],
            "components_total": _int(health["data"], "components_total"),
            "components_healthy": _int(health["data"], "components_healthy"),
            "active_incidents": _int(health["data"], "active_incidents"),
        },
        "journeys": {
            "state": journeys["state"],
            "total": _int(journeys["data"], "total"),
            "failed": _int(journeys["data"], "failed"),
        },
        "release": {
            "state": release["state"],
            "repository": _string_or_none(release["data"], "repository"),
            "environment": _string_or_none(release["data"], "environment"),
            "commit": _string_or_none(release["data"], "commit"),
            "completed_at": _string_or_none(release["data"], "completed_at"),
            "evidence_ref": _string_or_none(release["data"], "evidence_ref"),
        },
        "contract_registry": {
            "state": registry["state"],
            "contracts_total": _int(registry["data"], "contracts_total"),
            "contracts_valid": _int(registry["data"], "contracts_valid"),
            "drift_count": _int(registry["data"], "drift_count"),
        },
        "quota": {
            "state": quota["state"],
            "used_percent": _number_or_none(quota["data"], "used_percent"),
            "projected_percent": _number_or_none(
                quota["data"], "projected_percent"
            ),
            "highest_meter": _string_or_none(quota["data"], "highest_meter"),
            "period_ends_at": _string_or_none(quota["data"], "period_ends_at"),
        },
        "findings": {
            "state": findings["state"],
            "total": _int(findings["data"], "total"),
            "by_severity": {
                severity: _int(by_severity, severity)
                for severity in ("info", "warning", "failure", "critical")
            },
            "oldest_detected_at": _string_or_none(
                findings["data"], "oldest_detected_at"
            ),
        },
        "gardener_proposals": {
            "state": gardener["state"],
            "total": _int(gardener["data"], "total"),
            "validation_failed": _int(gardener["data"], "validation_failed"),
            "open_pull_requests": _int(
                gardener["data"], "open_pull_requests"
            ),
        },
        "secret_hygiene": {
            "state": secrets["state"],
            "required": _int(secrets["data"], "required"),
            "present": _int(secrets["data"], "present"),
            "stale": _int(secrets["data"], "stale"),
            "unknown": _int(secrets["data"], "unknown"),
        },
        "backups": {
            "state": backups["state"],
            "total": _int(backups["data"], "total"),
            "healthy": _int(backups["data"], "healthy"),
            "stale": _int(backups["data"], "stale"),
            "failed": _int(backups["data"], "failed"),
            "unknown": _int(backups["data"], "unknown"),
        },
        "runbooks": {
            "state": runbooks["state"],
            "valid": _int(runbooks["data"], "valid"),
            "invalid": _int(runbooks["data"], "invalid"),
            "stale": _int(runbooks["data"], "stale"),
        },
        "evidence": {
            "state": evidence["state"],
            "searchable_records": _int(evidence["data"], "searchable_records"),
            "newest_record_at": _string_or_none(
                evidence["data"], "newest_record_at"
            ),
            "expiring_soon": _int(evidence["data"], "expiring_soon"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--now", required=True, help="UTC RFC 3339 timestamp")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "contracts"
        / "v1"
        / "control-plane-summary.schema.json",
    )
    args = parser.parse_args()

    try:
        now = _parse_utc(args.now)
    except ValueError as error:
        parser.error(str(error))
    summary = build_summary(args.sources.resolve(), now)
    schema = load_json(args.schema.resolve())
    errors = validate_instance(summary, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
