#!/usr/bin/env python3
"""Build one deterministic, publication-safe RAMONE control-plane read model.

The producer is offline. It reads only policy-declared JSON documents, validates
public identity and leak boundaries, records canonical source fingerprints, and
writes a local artifact plus a dry-run receipt. It has no network, provider, KV,
secret, deployment, or workflow-dispatch capability.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from control_plane_contracts import canonical_json, load_json, validate_instance
from control_plane_summary import REQUIRED_DATA_FIELDS, SOURCE_FILES, _valid_data, build_summary

READ_MODEL_SCHEMA_VERSION = "atlas-control-plane/control-plane-read-model/v1"
SOURCE_SCHEMA_VERSION = "atlas-control-plane/control-plane-read-model-source/v1"
POLICY_SCHEMA_VERSION = "atlas-control-plane/read-model-policy/v1"
RECEIPT_SCHEMA_VERSION = "atlas-control-plane/read-model-dry-run-receipt/v1"
EXPECTED_COLLECTIONS = (
    "services",
    "releases",
    "findings",
    "quota",
    "backups",
    "gardener_proposals",
    "runbooks",
    "evidence",
)
STATES = {"healthy", "warning", "failed", "stale", "unavailable", "unknown"}
STATE_PRIORITY = {
    "healthy": 0,
    "unknown": 1,
    "warning": 2,
    "stale": 3,
    "unavailable": 4,
    "failed": 5,
}
FORBIDDEN_KEYS = {
    "authorization",
    "backup_contents",
    "command",
    "cookie",
    "diagnostic_commands",
    "graphql",
    "headers",
    "home_assistant_service",
    "http_method",
    "password",
    "payload",
    "private_key",
    "raw_evidence",
    "request_body",
    "secret",
    "secret_value",
    "shell_command",
    "token",
    "token_value",
    "url",
}
SAFE_SECRET_AGGREGATES = {"secret_hygiene"}
REFERENCE_FIELDS = {
    "evidence_ref",
    "evidence_refs",
    "reference",
    "review_url",
    "runbook_ref",
    "runbook_refs",
}
PRIVATE_VALUE = re.compile(
    r"(?:localhost|127\.0\.0\.1|192\.168\.|10\.\d{1,3}\.|"
    r"172\.(?:1[6-9]|2\d|3[01])\.|[A-Za-z]:\\|/config/|/home/|/Users/)",
    re.IGNORECASE,
)
FULL_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
SOURCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProducerError(ValueError):
    """Raised when an input fails the bounded producer contract."""


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProducerError("timestamp must be a UTC RFC 3339 value ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise ProducerError("timestamp is not a valid calendar value") from error
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _worst_state(states: list[str]) -> str:
    bounded = [state for state in states if state in STATES]
    return max(bounded, key=STATE_PRIORITY.__getitem__) if bounded else "unknown"


def _safe_path(root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ProducerError(f"unsafe source path: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative_path).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ProducerError(f"source path escapes root: {relative}")
    return resolved


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except FileNotFoundError as error:
        raise ProducerError(f"missing required {label}: {path.name}") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProducerError(f"malformed required {label}: {path.name}") from error
    if not isinstance(value, dict):
        raise ProducerError(f"{label} must be a JSON object: {path.name}")
    return value


def _load_policy(path: Path) -> dict[str, Any]:
    policy = _load_object(path, "read-model policy")
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ProducerError("unsupported read-model policy schema")
    if policy.get("owner") != "AtlasReaper311/atlas-infra":
        raise ProducerError("read-model policy owner is not atlas-infra")
    output = policy.get("output")
    if not isinstance(output, dict):
        raise ProducerError("read-model policy output section is missing")
    if output.get("schema_version") != READ_MODEL_SCHEMA_VERSION:
        raise ProducerError("read-model policy output schema is unexpected")
    if output.get("kv_key") != "control-plane:read-model:v1":
        raise ProducerError("read-model policy may name only the bounded KV key")
    max_bytes = output.get("max_bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1024:
        raise ProducerError("read-model policy max_bytes is invalid")
    max_age_seconds = output.get("max_age_seconds")
    if (
        not isinstance(max_age_seconds, int)
        or isinstance(max_age_seconds, bool)
        or not 60 <= max_age_seconds <= 3600
    ):
        raise ProducerError("read-model policy max_age_seconds is invalid")

    collections = policy.get("collections")
    if not isinstance(collections, list):
        raise ProducerError("read-model policy collections are missing")
    names = [entry.get("name") for entry in collections if isinstance(entry, dict)]
    if tuple(names) != EXPECTED_COLLECTIONS:
        raise ProducerError("read-model policy must declare the exact collection order")
    paths = [entry.get("path") for entry in collections if isinstance(entry, dict)]
    if len(paths) != len(set(paths)) or any(not isinstance(path, str) for path in paths):
        raise ProducerError("read-model collection paths must be unique strings")
    for entry in collections:
        max_items = entry.get("max_items")
        if not isinstance(max_items, int) or isinstance(max_items, bool) or not 1 <= max_items <= 100:
            raise ProducerError(f"invalid max_items for collection {entry.get('name')!r}")
    return policy


def _source_receipt(
    *,
    source_id: str,
    relative_path: str,
    document: dict[str, Any],
    required: bool,
    effective_state: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "relative_path": relative_path,
        "schema_version": str(document.get("schema_version", "unknown")),
        "generated_at": document.get("generated_at"),
        "stale_after": document.get("stale_after"),
        "state": effective_state,
        "required": required,
        "sha256": _sha256(document),
    }


def _validate_timestamp_window(document: dict[str, Any], now: datetime, label: str) -> str:
    generated = _parse_utc(document.get("generated_at"))
    stale_after = _parse_utc(document.get("stale_after"))
    if stale_after < generated:
        raise ProducerError(f"{label} stale_after precedes generated_at")
    state = document.get("state")
    if state not in STATES:
        raise ProducerError(f"{label} state is not allowlisted")
    if now > stale_after and STATE_PRIORITY[state] < STATE_PRIORITY["stale"]:
        return "stale"
    return state


def _walk_for_leaks(
    value: Any,
    allowed_reference_origins: tuple[str, ...],
    path: str = "$",
) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            segments = set(normalized.split("_"))
            sensitive = normalized in FORBIDDEN_KEYS or bool(
                segments.intersection({"authorization", "cookie", "password", "secret", "token"})
            )
            if sensitive and normalized not in SAFE_SECRET_AGGREGATES:
                errors.append(f"{path}.{key}: forbidden or secret-bearing key")
            if key in REFERENCE_FIELDS:
                references = child if isinstance(child, list) else [child]
                for reference in references:
                    if reference is None:
                        continue
                    if not isinstance(reference, str) or not reference.startswith(allowed_reference_origins):
                        errors.append(f"{path}.{key}: reference origin is not approved")
            errors.extend(_walk_for_leaks(child, allowed_reference_origins, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_for_leaks(child, allowed_reference_origins, f"{path}[{index}]"))
    elif isinstance(value, str):
        if PRIVATE_VALUE.search(value):
            errors.append(f"{path}: machine-local or private value")
        if len(value) > 500:
            errors.append(f"{path}: string exceeds 500 characters")
    return errors


def _validate_summary_document(source_id: str, document: dict[str, Any], now: datetime) -> str:
    expected_schema = f"atlas-control-plane/source-{SOURCE_FILES[source_id].removesuffix('.json')}/v1"
    if document.get("schema_version") != expected_schema:
        raise ProducerError(f"summary source {source_id} has an unexpected schema")
    if set(document) != {"schema_version", "generated_at", "stale_after", "state", "data"}:
        raise ProducerError(f"summary source {source_id} has undeclared fields")
    data = document.get("data")
    if not isinstance(data, dict):
        raise ProducerError(f"summary source {source_id} data must be an object")
    missing = [field for field in REQUIRED_DATA_FIELDS[source_id] if field not in data]
    if missing:
        raise ProducerError(f"summary source {source_id} is missing required data fields: {missing}")
    if not _valid_data(source_id, data):
        raise ProducerError(f"summary source {source_id} contains malformed data")
    return _validate_timestamp_window(document, now, f"summary source {source_id}")


def _validate_collection_source(
    *,
    entry: dict[str, Any],
    document: dict[str, Any],
    now: datetime,
    source_schema: dict[str, Any],
) -> str:
    errors = validate_instance(document, source_schema)
    if errors:
        raise ProducerError(f"collection source {entry['name']} failed schema: {errors[0]}")
    if document.get("source_id") != entry.get("source_id"):
        raise ProducerError(f"collection source {entry['name']} identity mismatch")
    items = document.get("items")
    if len(items) > entry["max_items"]:
        raise ProducerError(f"collection source {entry['name']} exceeds its policy bound")
    return _validate_timestamp_window(document, now, f"collection source {entry['name']}")


def _load_public_authority(authority_root: Path, policy: dict[str, Any]) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    authority_entries = policy.get("authorities")
    if not isinstance(authority_entries, list) or len(authority_entries) != 2:
        raise ProducerError("read-model policy must declare exactly two authorities")

    receipts: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    for entry in authority_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ProducerError("authority policy entry is malformed")
        path = _safe_path(authority_root, entry["path"])
        document = _load_object(path, f"authority {entry.get('source_id')}")
        source_id = str(entry.get("source_id"))
        documents[source_id] = document
        receipts.append(
            {
                "source_id": source_id,
                "relative_path": entry["path"],
                "schema_version": str(document.get("schema_version", "unknown")),
                "generated_at": document.get("reviewed_at") or document.get("generated_at"),
                "stale_after": None,
                "state": "healthy",
                "required": True,
                "sha256": _sha256(document),
            }
        )

    classifications = documents.get("public-repository-classifications")
    registry = documents.get("estate-registry")
    if not classifications or not registry:
        raise ProducerError("required public authority documents are missing")

    public_repositories = {
        item["repository"]
        for item in classifications.get("repositories", [])
        if isinstance(item, dict)
        and isinstance(item.get("repository"), str)
        and item.get("lifecycle") != "archived"
    }
    if not public_repositories:
        raise ProducerError("public repository authority is empty")

    public_services: set[str] = set()
    for item in registry.get("repositories", []):
        if not isinstance(item, dict) or item.get("public_surface") is not True:
            continue
        if item.get("repository") not in public_repositories:
            raise ProducerError("estate registry contains a service outside public repository authority")
        for service_id in item.get("service_ids", []):
            if isinstance(service_id, str):
                public_services.add(service_id)
    if not public_services:
        raise ProducerError("public service authority is empty")
    return public_repositories, public_services, receipts


def _repository_full_name(slug: str) -> str:
    return f"AtlasReaper311/{slug}"


def _validate_public_identities(
    collections: dict[str, list[dict[str, Any]]],
    public_repositories: set[str],
    public_services: set[str],
) -> None:
    repository_slugs = {name.split("/", 1)[1] for name in public_repositories}

    for item in collections["services"]:
        if item.get("service_id") not in public_services:
            raise ProducerError("services collection contains a non-public service identity")
        dependencies = item.get("dependencies", [])
        if any(dependency not in public_services for dependency in dependencies):
            raise ProducerError("services collection contains a non-public dependency identity")
    for item in collections["releases"]:
        repository = item.get("repository")
        if repository not in repository_slugs:
            raise ProducerError("releases collection contains a non-public repository identity")
    for item in collections["findings"]:
        if item.get("service_id") not in public_services:
            raise ProducerError("findings collection contains a non-public service identity")
    for item in collections["backups"]:
        if item.get("service_id") not in public_services:
            raise ProducerError("backups collection contains a non-public service identity")
    for item in collections["gardener_proposals"]:
        repository = item.get("repository")
        if repository not in repository_slugs:
            raise ProducerError("Gardener collection contains a non-public repository identity")
    for item in collections["runbooks"]:
        if item.get("service_id") not in public_services:
            raise ProducerError("runbooks collection contains a non-public service identity")
    for item in collections["evidence"]:
        producer = item.get("producer")
        if not isinstance(producer, str) or _repository_full_name(producer) not in public_repositories:
            raise ProducerError("evidence collection contains a non-public producer identity")


def _apply_source_state(items: list[dict[str, Any]], source_state: str) -> list[dict[str, Any]]:
    rendered = copy.deepcopy(items)
    for item in rendered:
        item_state = item.get("state") if item.get("state") in STATES else "unknown"
        item["state"] = _worst_state([item_state, source_state])
    return rendered


def _read_model_fingerprint(model: dict[str, Any]) -> str:
    payload = copy.deepcopy(model)
    payload.pop("read_model_fingerprint", None)
    return _sha256(payload)


def build_read_model(
    *,
    summary_sources: Path,
    collection_sources: Path,
    authority_root: Path,
    policy_path: Path,
    schema_path: Path,
    source_schema_path: Path,
    summary_schema_path: Path,
    now: datetime,
    source_revision: str,
    summary_builder: Callable[[Path, datetime], dict[str, Any]] = build_summary,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build and validate one deterministic read model and dry-run receipt."""
    if not FULL_SHA.fullmatch(source_revision):
        raise ProducerError("source_revision must be a full lower-case Git SHA")

    policy = _load_policy(policy_path)
    schema = _load_object(schema_path, "read-model schema")
    source_schema = _load_object(source_schema_path, "read-model source schema")
    allowed_origins_raw = policy.get("allowed_reference_origins")
    if not isinstance(allowed_origins_raw, list) or not allowed_origins_raw:
        raise ProducerError("read-model policy has no allowed reference origins")
    allowed_origins = tuple(str(origin) for origin in allowed_origins_raw)
    if any(
        urlsplit(origin).scheme != "https" or not urlsplit(origin).netloc
        for origin in allowed_origins
    ):
        raise ProducerError("reference origins must be absolute HTTPS URLs")

    expected_summary_paths = set(SOURCE_FILES.values())
    actual_summary_paths = {
        path.relative_to(summary_sources).as_posix()
        for path in summary_sources.rglob("*.json")
        if path.is_file()
    }
    if actual_summary_paths != expected_summary_paths:
        missing = sorted(expected_summary_paths - actual_summary_paths)
        unexpected = sorted(actual_summary_paths - expected_summary_paths)
        raise ProducerError(f"summary source inventory mismatch: missing={missing}, unexpected={unexpected}")

    expected_collection_paths = {entry["path"] for entry in policy["collections"]}
    actual_collection_paths = {
        path.relative_to(collection_sources).as_posix()
        for path in collection_sources.rglob("*.json")
        if path.is_file()
    }
    if actual_collection_paths != expected_collection_paths:
        missing = sorted(expected_collection_paths - actual_collection_paths)
        unexpected = sorted(actual_collection_paths - expected_collection_paths)
        raise ProducerError(f"collection source inventory mismatch: missing={missing}, unexpected={unexpected}")

    source_receipts: list[dict[str, Any]] = []
    summary_states: list[str] = []
    for source_id, filename in SOURCE_FILES.items():
        document = _load_object(summary_sources / filename, f"summary source {source_id}")
        state = _validate_summary_document(source_id, document, now)
        leak_errors = _walk_for_leaks(document, allowed_origins)
        if leak_errors:
            raise ProducerError(leak_errors[0])
        summary_states.append(state)
        source_receipts.append(
            _source_receipt(
                source_id=f"summary-{source_id.replace('_', '-')}",
                relative_path=f"summary/{filename}",
                document=document,
                required=True,
                effective_state=state,
            )
        )

    public_repositories, public_services, authority_receipts = _load_public_authority(
        authority_root, policy
    )
    source_receipts.extend(authority_receipts)

    collections: dict[str, list[dict[str, Any]]] = {}
    collection_states: list[str] = []
    for entry in policy["collections"]:
        path = _safe_path(collection_sources, entry["path"])
        document = _load_object(path, f"collection source {entry['name']}")
        source_state = _validate_collection_source(
            entry=entry,
            document=document,
            now=now,
            source_schema=source_schema,
        )
        if document.get("producer") not in public_repositories:
            raise ProducerError(f"collection source {entry['name']} producer is not public")
        leak_errors = _walk_for_leaks(document, allowed_origins)
        if leak_errors:
            raise ProducerError(leak_errors[0])
        collections[entry["name"]] = _apply_source_state(document["items"], source_state)
        collection_states.append(source_state)
        source_receipts.append(
            _source_receipt(
                source_id=entry["source_id"],
                relative_path=f"collections/{entry['path']}",
                document=document,
                required=True,
                effective_state=source_state,
            )
        )

    _validate_public_identities(collections, public_repositories, public_services)

    summary = summary_builder(summary_sources, now)
    summary_errors = validate_instance(
        summary,
        _load_object(
            summary_schema_path,
            "control-plane summary schema",
        ),
    )
    if summary_errors:
        raise ProducerError(f"generated summary failed canonical schema: {summary_errors[0]}")

    leak_errors = _walk_for_leaks(summary, allowed_origins)
    if leak_errors:
        raise ProducerError(leak_errors[0])

    source_receipts = sorted(source_receipts, key=lambda item: item["source_id"])
    stale_candidates = [
        _parse_utc(item["stale_after"])
        for item in source_receipts
        if isinstance(item.get("stale_after"), str)
    ]
    stale_candidates.append(_parse_utc(summary["stale_after"]))
    stale_candidates.append(
        now + timedelta(seconds=policy["output"]["max_age_seconds"])
    )
    if not stale_candidates:
        raise ProducerError("read model has no freshness evidence")

    model: dict[str, Any] = {
        "schema_version": READ_MODEL_SCHEMA_VERSION,
        "producer": {
            "repository": "AtlasReaper311/atlas-infra",
            "component": "scripts/control_plane_read_model.py",
            "source_revision": source_revision,
        },
        "generated_at": _iso(now),
        "stale_after": _iso(min(stale_candidates)),
        "state": _worst_state([summary.get("state", "unknown"), *summary_states, *collection_states]),
        "source_fingerprint": _sha256(source_receipts),
        "read_model_fingerprint": "sha256:" + "0" * 64,
        "sources": source_receipts,
        "summary": summary,
        **collections,
    }
    model["read_model_fingerprint"] = _read_model_fingerprint(model)

    model_errors = validate_instance(model, schema)
    if model_errors:
        raise ProducerError(f"generated read model failed schema: {model_errors[0]}")
    leak_errors = _walk_for_leaks(model, allowed_origins)
    if leak_errors:
        raise ProducerError(leak_errors[0])

    rendered = json.dumps(model, indent=2, sort_keys=True) + "\n"
    output_bytes = len(rendered.encode("utf-8"))
    max_bytes = policy["output"]["max_bytes"]
    if output_bytes > max_bytes:
        raise ProducerError(f"generated read model exceeds {max_bytes} bytes")

    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "mode": "dry-run",
        "generated_at": _iso(now),
        "source_revision": source_revision,
        "source_count": len(source_receipts),
        "source_fingerprint": model["source_fingerprint"],
        "read_model_fingerprint": model["read_model_fingerprint"],
        "state": model["state"],
        "stale_after": model["stale_after"],
        "collection_counts": {
            name: len(model[name]) for name in EXPECTED_COLLECTIONS
        },
        "output_bytes": output_bytes,
        "bounded_kv_key": policy["output"]["kv_key"],
        "provider_write_performed": False,
    }
    return model, receipt


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-sources", required=True, type=Path)
    parser.add_argument("--collection-sources", required=True, type=Path)
    parser.add_argument("--authority-root", type=Path, default=root)
    parser.add_argument(
        "--policy",
        type=Path,
        default=root / "policy" / "control-plane-read-model.json",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=root / "contracts" / "ramone" / "v1" / "control-plane-read-model.schema.json",
    )
    parser.add_argument(
        "--source-schema",
        type=Path,
        default=root / "contracts" / "ramone" / "v1" / "control-plane-read-model-source.schema.json",
    )
    parser.add_argument(
        "--summary-schema",
        type=Path,
        default=root / "contracts" / "v1" / "control-plane-summary.schema.json",
    )
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    try:
        now = _parse_utc(args.now)
        model, receipt = build_read_model(
            summary_sources=args.summary_sources.resolve(),
            collection_sources=args.collection_sources.resolve(),
            authority_root=args.authority_root.resolve(),
            policy_path=args.policy.resolve(),
            schema_path=args.schema.resolve(),
            source_schema_path=args.source_schema.resolve(),
            summary_schema_path=args.summary_schema.resolve(),
            now=now,
            source_revision=args.source_revision,
        )
    except ProducerError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    _write_json(args.output.resolve(), model)
    _write_json(args.receipt.resolve(), receipt)
    print(f"read_model_fingerprint={model['read_model_fingerprint']}")
    print(f"source_fingerprint={model['source_fingerprint']}")
    print("provider_write_performed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
