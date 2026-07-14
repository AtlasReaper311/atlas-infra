#!/usr/bin/env python3
"""Offline backup freshness and disposable restore assurance for Atlas Systems."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from control_plane_contracts import (
    calculate_fingerprint,
    canonical_json,
    load_json,
    semantic_errors,
    validate_instance,
)

REPORT_SCHEMA_VERSION = "atlas-backup-audit/report/v1"
PRODUCER_VERSION = "1.0.0"
UTC = timezone.utc

RUNBOOKS = {
    "backup-coverage-not-declared": "docs/runbooks/backup-audit-missing-evidence.md",
    "backup-classification-conflict": "docs/runbooks/backup-audit-ineligible-target.md",
    "backup-runbook-missing": "docs/runbooks/backup-audit-restore-drill-failed.md",
    "digest-mismatch": "docs/runbooks/backup-audit-digest-mismatch.md",
    "malformed-backup-metadata": "docs/runbooks/backup-audit-malformed-export.md",
    "malformed-backup-policy": "docs/runbooks/backup-audit-malformed-export.md",
    "malformed-export": "docs/runbooks/backup-audit-malformed-export.md",
    "missing-backup-evidence": "docs/runbooks/backup-audit-missing-evidence.md",
    "missing-backup-target-owner": "docs/runbooks/backup-audit-owner-missing.md",
    "restore-drill-failed": "docs/runbooks/backup-audit-restore-drill-failed.md",
    "restore-drill-unavailable": "docs/runbooks/backup-audit-restore-drill-failed.md",
    "retention-policy-missing": "docs/runbooks/backup-audit-retention-violation.md",
    "retention-policy-violated": "docs/runbooks/backup-audit-retention-violation.md",
    "simple-proxy-exclusion": "docs/runbooks/backup-audit-ineligible-target.md",
    "stale-backup": "docs/runbooks/backup-audit-stale-backup.md",
    "unknown-service-id": "docs/runbooks/backup-audit-unknown-service-id.md",
    "unsafe-restore-path": "docs/runbooks/backup-audit-unsafe-restore-path.md",
}

METHOD_BY_STORAGE = {
    "chroma-vector-store": "vector-store-export",
    "cloudflare-kv": "kv-export",
    "github-actions-artifact": "github-artifact",
    "json-export": "json-export",
}

PHASE8_EVIDENCE_FIELDS = {
    "audit_timestamp",
    "backup_timestamp",
    "errors",
    "evidence_digest",
    "freshness_state",
    "redacted_evidence_ref",
    "repository",
    "restore_drill_state",
    "retention_state",
    "result_state",
    "runbook_reference",
    "service_id",
    "source_type",
    "warnings",
}


class BackupAuditError(Exception):
    """Base class for bounded, user-visible audit failures."""


class UnsafeRestorePath(BackupAuditError):
    """A fixture or archive path could escape the disposable target."""


class MalformedExport(BackupAuditError):
    """A fixture cannot be parsed as its declared export type."""


class RestoreDrillUnavailable(BackupAuditError):
    """A declared drill has no supported offline adapter."""


def _bounded(value: str, limit: int = 500) -> str:
    clean = " ".join(value.split())
    return clean if len(clean) <= limit else clean[: limit - 3] + "..."


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be a UTC RFC 3339 value ending in Z")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use UTC")
    return parsed.astimezone(UTC)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _load_document(path: Path) -> tuple[Any | None, str | None]:
    try:
        return load_json(path), None
    except FileNotFoundError:
        return None, "file is missing"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON at line {error.lineno}, column {error.colno}"
    except OSError as error:
        return None, f"cannot read file: {error}"


def _finding(
    *,
    rules: dict[str, Any],
    detected_at: str,
    rule_id: str,
    repository: str,
    location: str,
    summary: str,
    service_id: str | None = None,
    severity: str = "failure",
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "schema_version": "atlas-control-plane/finding/v1",
        "source": {
            "producer": "atlas-infra",
            "check_id": rule_id,
            "producer_version": PRODUCER_VERSION,
        },
        "subject": {"repository": repository},
        "category": "backup",
        "severity": severity,
        "rule_id": rule_id,
        "location": location,
        "evidence": {
            "summary": _bounded(summary),
            "references": [],
            "redacted": True,
        },
        "detected_at": detected_at,
        "fingerprint": "sha256:" + "0" * 64,
        "remediation": {
            "eligible": False,
            "reason": "Backup policy and restore decisions require owner review.",
        },
        "runbook_ref": RUNBOOKS.get(
            rule_id, "docs/runbooks/backup-audit-restore-drill-failed.md"
        ),
    }
    if service_id:
        finding["subject"]["service_id"] = service_id
    finding["fingerprint"] = calculate_fingerprint("finding", finding, rules)
    return finding


def _append_finding(findings: list[dict[str, Any]], **kwargs: Any) -> None:
    findings.append(_finding(**kwargs))


def _finding_sort_key(item: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        item["rule_id"],
        item["subject"]["repository"],
        item["subject"].get("service_id", ""),
        item["location"],
        item["fingerprint"],
    )


def _relative_parts(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise UnsafeRestorePath("path must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(
        part in {"", ".", ".."} or ":" in part or "\x00" in part
        for part in path.parts
    ):
        raise UnsafeRestorePath("absolute and traversal paths are prohibited")
    return path.parts


def safe_fixture_path(base: Path, relative: str) -> Path:
    """Resolve one fixture path while rejecting traversal and every symlink."""
    parts = _relative_parts(relative)
    base_resolved = base.resolve()
    current = base_resolved
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise UnsafeRestorePath(f"symlink fixture path is prohibited: {relative}")
    resolved = current.resolve(strict=False)
    if not resolved.is_relative_to(base_resolved):
        raise UnsafeRestorePath(f"fixture path escapes its target: {relative}")
    return current


def _sha256_file(path: Path, maximum_bytes: int) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file():
        raise UnsafeRestorePath("digest target must be a regular non-symlink file")
    if path.stat().st_mode & 0o111:
        raise UnsafeRestorePath("executable fixture files are prohibited")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            size += len(chunk)
            if size > maximum_bytes:
                raise MalformedExport("fixture exceeds the bounded restore size")
            digest.update(chunk)
    return digest.hexdigest(), size


def _copy_file(source: Path, destination: Path, maximum_bytes: int) -> int:
    if source.is_symlink() or not source.is_file():
        raise UnsafeRestorePath("restore source must be a regular non-symlink file")
    if source.stat().st_mode & 0o111:
        raise UnsafeRestorePath("executable restore sources are prohibited")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copied = 0
    try:
        output = destination.open("xb")
    except FileExistsError as error:
        raise UnsafeRestorePath("restore drill would overwrite an existing file") from error
    with source.open("rb") as input_file, output:
        while chunk := input_file.read(64 * 1024):
            copied += len(chunk)
            if copied > maximum_bytes:
                raise MalformedExport("restore source exceeds the bounded restore size")
            output.write(chunk)
    return copied


def _copy_directory(
    source: Path,
    destination: Path,
    *,
    maximum_files: int,
    maximum_bytes: int,
) -> tuple[int, int]:
    if source.is_symlink() or not source.is_dir():
        raise UnsafeRestorePath("directory restore source must be a real directory")
    if destination.exists():
        raise UnsafeRestorePath("restore drill refuses an existing destination")
    destination.mkdir(mode=0o700)
    files = 0
    total = 0
    for item in sorted(source.rglob("*"), key=lambda value: value.as_posix()):
        relative = item.relative_to(source).as_posix()
        _relative_parts(relative)
        if item.is_symlink():
            raise UnsafeRestorePath(f"symlink export entry is prohibited: {relative}")
        target = destination.joinpath(*PurePosixPath(relative).parts)
        if item.is_dir():
            target.mkdir(mode=0o700, exist_ok=False)
            continue
        if not item.is_file():
            raise UnsafeRestorePath(f"non-regular export entry is prohibited: {relative}")
        files += 1
        if files > maximum_files:
            raise MalformedExport("directory export exceeds the file-count limit")
        copied = _copy_file(item, target, maximum_bytes - total)
        total += copied
        if total > maximum_bytes:
            raise MalformedExport("directory export exceeds the size limit")
    return files, total


def safe_extract_zip(
    archive_path: Path,
    destination: Path,
    *,
    maximum_files: int,
    maximum_bytes: int,
) -> tuple[int, int]:
    """Extract a ZIP into a new empty directory with strict safety bounds."""
    if archive_path.is_symlink() or not archive_path.is_file():
        raise UnsafeRestorePath("archive must be a regular non-symlink file")
    if destination.exists():
        raise UnsafeRestorePath("archive destination must not already exist")
    destination.mkdir(mode=0o700)
    seen: set[str] = set()
    file_count = 0
    total = 0
    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile) as error:
        raise MalformedExport("archive is not a valid ZIP file") from error
    with archive:
        members = archive.infolist()
        if len(members) > maximum_files:
            raise MalformedExport("archive exceeds the entry-count limit")
        for member in sorted(members, key=lambda item: item.filename):
            if member.flag_bits & 0x1:
                raise MalformedExport("encrypted archive entries are unsupported")
            parts = _relative_parts(member.filename.rstrip("/"))
            normalized = PurePosixPath(*parts).as_posix()
            if normalized in seen:
                raise UnsafeRestorePath("duplicate archive paths could overwrite data")
            seen.add(normalized)
            mode = (member.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise UnsafeRestorePath("archive symlink entries are prohibited")
            if not member.is_dir() and mode & 0o111:
                raise UnsafeRestorePath("executable archive entries are prohibited")
            output = destination.joinpath(*parts)
            if not output.resolve(strict=False).is_relative_to(destination.resolve()):
                raise UnsafeRestorePath("archive entry escapes the disposable target")
            if member.is_dir():
                output.mkdir(mode=0o700, parents=True, exist_ok=False)
                continue
            file_count += 1
            total += member.file_size
            if file_count > maximum_files:
                raise MalformedExport("archive exceeds the file-count limit")
            if total > maximum_bytes:
                raise MalformedExport("archive exceeds the uncompressed-size limit")
            output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                destination_file = output.open("xb")
            except FileExistsError as error:
                raise UnsafeRestorePath("archive extraction would overwrite a file") from error
            written = 0
            with archive.open(member) as source, destination_file:
                while chunk := source.read(64 * 1024):
                    written += len(chunk)
                    if written > member.file_size or written > maximum_bytes:
                        raise MalformedExport("archive entry exceeded its declared size")
                    destination_file.write(chunk)
            if written != member.file_size:
                raise MalformedExport("archive entry size does not match metadata")
    return file_count, total


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MalformedExport("export is not a valid UTF-8 JSON document") from error
    if not isinstance(value, dict):
        raise MalformedExport("export root must be a JSON object")
    return value


def _validate_artifact_manifest(path: Path) -> None:
    value = _json_object(path)
    required = {
        "artifact_id",
        "created_at",
        "expires_at",
        "file_count",
        "files",
        "name",
        "schema_version",
        "total_size_bytes",
    }
    if not required.issubset(value):
        raise MalformedExport("artifact manifest is missing required metadata")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise MalformedExport("artifact manifest files must be a non-empty array")
    if value.get("file_count") != len(files):
        raise MalformedExport("artifact file count does not match its manifest")
    total_size = 0
    for item in files:
        if not isinstance(item, dict):
            raise MalformedExport("artifact file metadata must be an object")
        _relative_parts(item.get("path", ""))
        if not isinstance(item.get("size_bytes"), int) or item["size_bytes"] < 0:
            raise MalformedExport("artifact file size must be a non-negative integer")
        total_size += item["size_bytes"]
        digest = item.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise MalformedExport("artifact file digest must be lowercase SHA-256")
    if total_size != value.get("total_size_bytes"):
        raise MalformedExport("artifact byte count does not match its manifest")


def _validate_kv_export(path: Path) -> None:
    value = _json_object(path)
    if value.get("schema_version") != "atlas-backup-fixture/cloudflare-kv-export/v1":
        raise MalformedExport("KV export schema version is unsupported")
    entries = value.get("entries")
    if not isinstance(entries, list) or not entries:
        raise MalformedExport("KV export entries must be a non-empty array")
    keys: list[str] = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"key", "metadata", "value"}:
            raise MalformedExport("KV entries require key, value, and metadata")
        key = item.get("key")
        if not isinstance(key, str) or not key:
            raise MalformedExport("KV entry keys must be non-empty strings")
        keys.append(key)
        if not isinstance(item.get("metadata"), dict):
            raise MalformedExport("KV entry metadata must be an object")
    if len(keys) != len(set(keys)):
        raise MalformedExport("KV export contains duplicate keys")


def _validate_incident_export(path: Path) -> None:
    value = _json_object(path)
    if value.get("schema_version") != "atlas-backup-fixture/incident-export/v1":
        raise MalformedExport("incident export schema version is unsupported")
    incidents = value.get("incidents")
    if not isinstance(incidents, list) or not incidents:
        raise MalformedExport("incident export must contain at least one fixture record")
    identifiers: list[str] = []
    for item in incidents:
        if not isinstance(item, dict):
            raise MalformedExport("incident records must be objects")
        if not {"id", "occurred_at", "status", "summary"}.issubset(item):
            raise MalformedExport("incident record is missing required fields")
        if not isinstance(item["id"], str) or not item["id"]:
            raise MalformedExport("incident ID must be a non-empty string")
        if not isinstance(item["summary"], str) or not item["summary"]:
            raise MalformedExport("incident summary must be a non-empty string")
        _parse_timestamp(item["occurred_at"])
        if item["status"] not in {"open", "closed"}:
            raise MalformedExport("incident status is unsupported")
        identifiers.append(item["id"])
    if len(identifiers) != len(set(identifiers)):
        raise MalformedExport("incident export contains duplicate IDs")


def _validate_chroma_export(path: Path) -> None:
    manifest = _json_object(path / "manifest.json")
    collections_document = _json_object(path / "collections.json")
    if manifest.get("schema_version") != "atlas-backup-fixture/chroma-export/v1":
        raise MalformedExport("Chroma export manifest version is unsupported")
    collections = collections_document.get("collections")
    if not isinstance(collections, list) or not collections:
        raise MalformedExport("Chroma collections fixture is empty")
    collection_by_id: dict[str, dict[str, Any]] = {}
    for collection in collections:
        if not isinstance(collection, dict):
            raise MalformedExport("Chroma collection metadata must be an object")
        if not {"dimension", "id", "name", "record_count"}.issubset(collection):
            raise MalformedExport("Chroma collection metadata is incomplete")
        if not isinstance(collection["id"], str) or not collection["id"]:
            raise MalformedExport("Chroma collection ID must be a non-empty string")
        if not isinstance(collection["dimension"], int) or collection["dimension"] < 1:
            raise MalformedExport("Chroma collection dimension must be positive")
        if collection["id"] in collection_by_id:
            raise MalformedExport("Chroma export contains duplicate collection IDs")
        collection_by_id[collection["id"]] = collection
    if manifest.get("collection_count") != len(collection_by_id):
        raise MalformedExport("Chroma collection count does not match the manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise MalformedExport("Chroma manifest requires file checksums")
    for item in files:
        if not isinstance(item, dict):
            raise MalformedExport("Chroma file metadata must be an object")
        file_path = safe_fixture_path(path, item.get("path", ""))
        actual_digest, actual_size = _sha256_file(file_path, 10_485_760)
        if actual_digest != item.get("sha256") or actual_size != item.get("size_bytes"):
            raise MalformedExport("Chroma file checksum or size does not match")
    records_path = safe_fixture_path(path, "records.jsonl")
    records: list[dict[str, Any]] = []
    try:
        for line in records_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise MalformedExport("Chroma JSONL records must be objects")
                records.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MalformedExport("Chroma records are not valid UTF-8 JSONL") from error
    record_ids: set[str] = set()
    counts: dict[str, int] = {key: 0 for key in collection_by_id}
    for record in records:
        if not {"collection_id", "document", "embedding", "id", "metadata"}.issubset(
            record
        ):
            raise MalformedExport("Chroma record is missing required fields")
        if not isinstance(record["id"], str) or not record["id"]:
            raise MalformedExport("Chroma record ID must be a non-empty string")
        if not isinstance(record["collection_id"], str):
            raise MalformedExport("Chroma record collection ID must be a string")
        collection = collection_by_id.get(record["collection_id"])
        if collection is None:
            raise MalformedExport("Chroma record references an unknown collection")
        embedding = record["embedding"]
        if (
            not isinstance(embedding, list)
            or len(embedding) != collection["dimension"]
            or any(
                not isinstance(value, (int, float)) or isinstance(value, bool)
                for value in embedding
            )
        ):
            raise MalformedExport("Chroma embedding dimension does not match")
        if record["id"] in record_ids:
            raise MalformedExport("Chroma export contains duplicate record IDs")
        record_ids.add(record["id"])
        counts[record["collection_id"]] += 1
    if manifest.get("record_count") != len(records):
        raise MalformedExport("Chroma record count does not match the manifest")
    for collection_id, count in counts.items():
        if collection_by_id[collection_id]["record_count"] != count:
            raise MalformedExport("Chroma collection record count does not match")


def run_restore_drill(
    *,
    target: dict[str, Any],
    metadata: dict[str, Any],
    target_root: Path,
    guardrails: dict[str, Any],
) -> dict[str, Any]:
    """Run one fixture-only drill and return path-free deterministic statistics."""
    if target.get("disposable_restore_location") != "system-temporary-directory":
        raise UnsafeRestorePath("only system temporary directories are permitted")
    try:
        maximum_files = int(guardrails.get("maximum_archive_files", 0))
        maximum_bytes = int(guardrails.get("maximum_uncompressed_bytes", 0))
    except (TypeError, ValueError) as error:
        raise RestoreDrillUnavailable("restore bounds are malformed") from error
    if maximum_files < 1 or maximum_bytes < 1:
        raise RestoreDrillUnavailable("restore bounds are missing")
    source_declaration = metadata.get("restore_source")
    if not isinstance(source_declaration, dict):
        raise RestoreDrillUnavailable("restore source metadata is missing")
    source = safe_fixture_path(target_root, source_declaration.get("path", ""))
    kind = source_declaration.get("kind")
    drill_type = target.get("restore_drill_type")

    with tempfile.TemporaryDirectory(prefix="atlas-backup-audit-") as directory:
        disposable_root = Path(directory)
        if kind in {"metadata-manifest", "json-export"}:
            restored = disposable_root / "restored" / source.name
            total_size = _copy_file(source, restored, maximum_bytes)
            file_count = 1
            if drill_type == "artifact-metadata-validation" and kind == "metadata-manifest":
                _validate_artifact_manifest(restored)
            elif drill_type == "json-export-validation" and kind == "json-export":
                if target.get("data_type") == "cloudflare-kv-export":
                    _validate_kv_export(restored)
                elif target.get("data_type") == "incident-export":
                    _validate_incident_export(restored)
                else:
                    raise RestoreDrillUnavailable("JSON export adapter is not allowlisted")
            else:
                raise RestoreDrillUnavailable("restore source and drill type do not match")
        elif kind == "chroma-export" and drill_type == "chroma-fixture-validation":
            restored = disposable_root / "restored"
            file_count, total_size = _copy_directory(
                source,
                restored,
                maximum_files=maximum_files,
                maximum_bytes=maximum_bytes,
            )
            _validate_chroma_export(restored)
        elif kind == "zip-archive" and drill_type == "archive-extraction":
            restored = disposable_root / "restored"
            file_count, total_size = safe_extract_zip(
                source,
                restored,
                maximum_files=maximum_files,
                maximum_bytes=maximum_bytes,
            )
        else:
            raise RestoreDrillUnavailable("restore drill type is unsupported")

        if file_count != metadata.get("expected_file_count"):
            raise MalformedExport("restored file count does not match backup metadata")
        if total_size != metadata.get("expected_total_size_bytes"):
            raise MalformedExport("restored byte count does not match backup metadata")
        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "temporary_cleanup": "completed",
        }


def _repository_entries(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = registry.get("repositories", []) if isinstance(registry, dict) else []
    return {
        entry["repository"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("repository"), str)
    }


def _load_contracts(contracts_dir: Path) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    if not contracts_dir.is_dir():
        return contracts
    for path in sorted(contracts_dir.glob("*.json")):
        document, error = _load_document(path)
        if not error and isinstance(document, dict) and isinstance(
            document.get("service_id"), str
        ):
            contracts[document["service_id"]] = document
    return contracts


def _empty_evidence(target: dict[str, Any], audited_at: str) -> dict[str, Any]:
    repository = target.get("repository")
    if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
        repository = "AtlasReaper311/atlas-infra"
    service_id = target.get("service_id")
    if not isinstance(service_id, str) or not service_id:
        service_id = "unknown-service"
    target_id = target.get("target_id")
    if not isinstance(target_id, str) or not target_id:
        target_id = "invalid-target"
    retention_days = target.get("retention_expectation_days")
    if not isinstance(retention_days, int) or retention_days < 1:
        retention_days = 1
    rpo_hours = target.get("recovery_point_objective_hours")
    if not isinstance(rpo_hours, int) or rpo_hours < 1:
        rpo_hours = 1
    runbook = target.get("runbook_reference")
    if not isinstance(runbook, str) or not runbook.endswith(".md"):
        runbook = "docs/runbooks/backup-audit-restore-drill-failed.md"
    return {
        "schema_version": "atlas-control-plane/backup-evidence/v1",
        "target_id": target_id,
        "method": METHOD_BY_STORAGE.get(target.get("storage_type"), "filesystem-copy"),
        "last_successful_backup_at": None,
        "restore_tested_at": None,
        "retention_days": retention_days,
        "rpo_hours": rpo_hours,
        "evidence_ref": None,
        "status": "unknown",
        "service_id": service_id,
        "repository": repository,
        "backup_timestamp": None,
        "audit_timestamp": audited_at,
        "freshness_state": "unavailable",
        "restore_drill_state": "not-run",
        "retention_state": "unknown",
        "evidence_digest": None,
        "redacted_evidence_ref": None,
        "source_type": "local-fixture",
        "result_state": "unknown",
        "errors": [],
        "warnings": [],
        "runbook_reference": runbook,
    }


def _target_location(target: dict[str, Any]) -> str:
    return "policy/backup-audit.json"


def _audit_target(
    *,
    root: Path,
    fixtures_dir: Path,
    target: dict[str, Any],
    policy: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
    entries: dict[str, dict[str, Any]],
    metadata_schema: dict[str, Any],
    rules: dict[str, Any],
    now: datetime,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    audited_at = _timestamp(now)
    evidence = _empty_evidence(target, audited_at)
    target_id = evidence["target_id"]
    service_id = evidence["service_id"]
    repository = evidence["repository"]
    location = _target_location(target)

    def record(rule_id: str, summary: str, *, severity: str = "failure") -> None:
        _append_finding(
            findings,
            rules=rules,
            detected_at=audited_at,
            rule_id=rule_id,
            repository=repository,
            service_id=service_id,
            location=location,
            summary=summary,
            severity=severity,
        )
        destination = evidence["warnings"] if severity in {"info", "warning"} else evidence["errors"]
        destination.append(_bounded(summary))

    owner = target.get("owner")
    if not isinstance(owner, str) or not owner.strip():
        record("missing-backup-target-owner", "Backup target owner is missing.")
    for field in (
        "backup_frequency_hours",
        "maximum_allowed_age_hours",
        "recovery_point_objective_hours",
        "recovery_time_objective_hours",
        "retention_expectation_days",
    ):
        value = target.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            record(
                "malformed-backup-policy",
                f"Backup target has an invalid {field} declaration.",
            )
    guardrails = policy.get("guardrails")
    if not isinstance(guardrails, dict) or not all(
        isinstance(guardrails.get(field), int)
        and not isinstance(guardrails.get(field), bool)
        and guardrails[field] > 0
        for field in ("maximum_archive_files", "maximum_uncompressed_bytes")
    ):
        record("malformed-backup-policy", "Backup restore bounds are missing or invalid.")

    contract = contracts.get(service_id)
    entry = entries.get(repository)
    if contract is None or entry is None or service_id not in entry.get("service_ids", []):
        record(
            "unknown-service-id",
            f"Backup target service {service_id!r} is not registered to {repository}.",
        )
    else:
        classification = target.get("classification", {})
        conflicts = [
            field
            for field in ("lifecycle", "scope", "provenance")
            if classification.get(field) != entry.get(field)
        ]
        excluded = policy.get("eligibility", {})
        lifecycle = entry.get("lifecycle")
        provenance = entry.get("provenance")
        if conflicts:
            record(
                "backup-classification-conflict",
                "Backup target classification disagrees with the Phase 6 registry: "
                + ", ".join(conflicts)
                + ".",
            )
        if (
            lifecycle in excluded.get("excluded_lifecycles", [])
            or provenance in excluded.get("excluded_provenance", [])
        ):
            record(
                "backup-classification-conflict",
                "Deprecated, archived, or external-derived repositories cannot receive active backup drills.",
            )
        if service_id in excluded.get("excluded_services", []):
            record(
                "simple-proxy-exclusion",
                "simple-proxy is excluded because it is deprecated, internal, and external-derived.",
                severity="info",
            )
            record(
                "backup-classification-conflict",
                "An excluded service cannot be enabled as an active backup target.",
            )

    runbook = target.get("runbook_reference")
    if not isinstance(runbook, str) or not (root / runbook).is_file():
        record("backup-runbook-missing", "Backup target runbook does not exist.")
    if target.get("disposable_restore_location") != "system-temporary-directory":
        record(
            "unsafe-restore-path",
            "Backup target does not use the allowlisted system temporary restore location.",
        )
    if evidence["errors"]:
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
        return evidence

    evidence_source = target.get("evidence_source")
    try:
        metadata_path = safe_fixture_path(fixtures_dir, evidence_source)
    except (TypeError, UnsafeRestorePath) as error:
        record("unsafe-restore-path", f"Backup metadata path is unsafe: {error}")
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
        return evidence
    metadata, metadata_error = _load_document(metadata_path)
    if metadata_error:
        record(
            "missing-backup-evidence" if metadata_error == "file is missing" else "malformed-backup-metadata",
            f"Backup metadata is unavailable: {metadata_error}.",
        )
        evidence["restore_drill_state"] = "unavailable"
        evidence["result_state"] = "unavailable" if metadata_error == "file is missing" else "failed"
        evidence["status"] = "unknown" if metadata_error == "file is missing" else "failed"
        return evidence
    if not isinstance(metadata, dict):
        record("malformed-backup-metadata", "Backup metadata root must be an object.")
        evidence["restore_drill_state"] = "unavailable"
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
        return evidence

    if "retention" not in metadata:
        record("retention-policy-missing", "Backup retention metadata is missing.")
    for declaration_name in ("digest", "restore_source"):
        declaration = metadata.get(declaration_name)
        if isinstance(declaration, dict) and isinstance(declaration.get("path"), str):
            try:
                safe_fixture_path(metadata_path.parent, declaration["path"])
            except UnsafeRestorePath as error:
                record(
                    "unsafe-restore-path",
                    f"Backup {declaration_name} path is unsafe: {error}",
                )
    if evidence["errors"]:
        evidence["restore_drill_state"] = "failed"
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
        return evidence
    metadata_errors = validate_instance(metadata, metadata_schema)
    missing_required = sorted(
        field
        for field in target.get("required_metadata_fields", [])
        if field not in metadata
    )
    if missing_required:
        metadata_errors.append(
            "required target metadata is missing: " + ", ".join(missing_required)
        )
    for field in ("target_id", "service_id", "repository"):
        if metadata.get(field) != target.get(field):
            metadata_errors.append(f"metadata {field} does not match the target")
    if metadata_errors:
        record(
            "malformed-backup-metadata",
            f"Backup metadata is malformed: {metadata_errors[0]}",
        )
        evidence["restore_drill_state"] = "unavailable"
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
        return evidence

    evidence["last_successful_backup_at"] = metadata["backup_at"]
    evidence["backup_timestamp"] = metadata["backup_at"]
    evidence["evidence_ref"] = metadata["evidence_ref"]
    evidence["redacted_evidence_ref"] = metadata["evidence_ref"]
    evidence["evidence_digest"] = "sha256:" + metadata["digest"]["value"]
    evidence["source_type"] = metadata["source_type"]

    try:
        backup_at = _parse_timestamp(metadata["backup_at"])
        observed_at = _parse_timestamp(metadata["observed_at"])
    except ValueError as error:
        record("malformed-backup-metadata", f"Backup timestamp is invalid: {error}")
        backup_at = now
        observed_at = now
    if backup_at > now or observed_at > now or observed_at < backup_at:
        record(
            "malformed-backup-metadata",
            "Backup and observation timestamps are ordered incorrectly or lie in the future.",
        )
    else:
        age = now - backup_at
        maximum_age = timedelta(hours=target["maximum_allowed_age_hours"])
        if age > maximum_age:
            evidence["freshness_state"] = "stale"
            record(
                "stale-backup",
                f"Backup age exceeds the {target['maximum_allowed_age_hours']}-hour maximum.",
                severity="warning",
            )
        else:
            evidence["freshness_state"] = "fresh"

    retention = metadata.get("retention")
    if isinstance(retention, dict):
        try:
            retained_until = _parse_timestamp(retention["retained_until"])
            required_until = backup_at + timedelta(
                days=target["retention_expectation_days"]
            )
        except (KeyError, TypeError, ValueError) as error:
            record("retention-policy-missing", f"Retention metadata is invalid: {error}")
            evidence["retention_state"] = "missing"
        else:
            if (
                retention.get("expected_days") != target["retention_expectation_days"]
                or retained_until < required_until
                or retained_until < now
            ):
                evidence["retention_state"] = "violated"
                record(
                    "retention-policy-violated",
                    "Backup retention metadata does not meet the declared expectation.",
                )
            else:
                evidence["retention_state"] = "met"
    else:
        evidence["retention_state"] = "missing"

    try:
        digest_path = safe_fixture_path(metadata_path.parent, metadata["digest"]["path"])
        actual_digest, _ = _sha256_file(
            digest_path, guardrails["maximum_uncompressed_bytes"]
        )
    except UnsafeRestorePath as error:
        record("unsafe-restore-path", f"Digest source path is unsafe: {error}")
    except (OSError, MalformedExport) as error:
        record("malformed-export", f"Digest source cannot be read safely: {error}")
    else:
        if actual_digest != metadata["digest"]["value"]:
            record("digest-mismatch", "Backup fixture digest does not match metadata.")

    if not evidence["errors"]:
        try:
            run_restore_drill(
                target=target,
                metadata=metadata,
                target_root=metadata_path.parent,
                guardrails=guardrails,
            )
        except UnsafeRestorePath as error:
            record("unsafe-restore-path", f"Restore drill refused an unsafe path: {error}")
            evidence["restore_drill_state"] = "failed"
        except RestoreDrillUnavailable as error:
            record("restore-drill-unavailable", f"Restore drill is unavailable: {error}")
            evidence["restore_drill_state"] = "unavailable"
        except MalformedExport as error:
            record("malformed-export", f"Disposable restore drill failed: {error}")
            record("restore-drill-failed", f"Disposable restore drill failed: {error}")
            evidence["restore_drill_state"] = "failed"
        except (BackupAuditError, OSError, ValueError) as error:
            record("restore-drill-failed", f"Disposable restore drill failed: {error}")
            evidence["restore_drill_state"] = "failed"
        else:
            evidence["restore_drill_state"] = "passed"
            evidence["restore_tested_at"] = audited_at
    elif evidence["restore_drill_state"] == "not-run":
        evidence["restore_drill_state"] = "failed"

    if evidence["errors"]:
        evidence["result_state"] = "failed"
        evidence["status"] = "failed"
    elif evidence["freshness_state"] == "stale":
        evidence["result_state"] = "stale"
        evidence["status"] = "stale"
    elif evidence["warnings"]:
        evidence["result_state"] = "warning"
        evidence["status"] = "warning"
    else:
        evidence["result_state"] = "healthy"
        evidence["status"] = "healthy"
    evidence["errors"] = sorted(set(evidence["errors"]))
    evidence["warnings"] = sorted(set(evidence["warnings"]))
    return evidence


def _validate_coverage(
    *,
    policy: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
    entries: dict[str, dict[str, Any]],
    rules: dict[str, Any],
    audited_at: str,
    findings: list[dict[str, Any]],
) -> None:
    coverage_items = policy.get("service_coverage", [])
    coverage = {
        item.get("service_id"): item
        for item in coverage_items
        if isinstance(item, dict) and isinstance(item.get("service_id"), str)
    }
    target_ids = {
        item.get("target_id")
        for item in policy.get("targets", [])
        if isinstance(item, dict)
    }
    required: set[str] = set()
    for entry in entries.values():
        if entry.get("runtime_service") and entry.get("lifecycle") == "production":
            required.update(entry.get("service_ids", []))
    for service_id, contract in contracts.items():
        if contract.get("backup_relevance", {}).get("state") == "relevant":
            required.add(service_id)

    for service_id in sorted(required):
        contract = contracts.get(service_id, {})
        repository = contract.get("source_repository", "AtlasReaper311/atlas-infra")
        item = coverage.get(service_id)
        if item is None:
            _append_finding(
                findings,
                rules=rules,
                detected_at=audited_at,
                rule_id="backup-coverage-not-declared",
                repository=repository,
                service_id=service_id,
                location="policy/backup-audit.json",
                summary="Production or backup-relevant service has no backup target, exclusion, or no-backup rationale.",
                severity="warning",
            )
            continue
        if item.get("state") == "not-declared":
            _append_finding(
                findings,
                rules=rules,
                detected_at=audited_at,
                rule_id="backup-coverage-not-declared",
                repository=item["repository"],
                service_id=service_id,
                location="policy/backup-audit.json",
                summary="Backup coverage is explicitly not declared; this state is not healthy.",
                severity="warning",
            )
        if item.get("state") == "target" and any(
            target_id not in target_ids for target_id in item.get("target_ids", [])
        ):
            _append_finding(
                findings,
                rules=rules,
                detected_at=audited_at,
                rule_id="malformed-backup-policy",
                repository=item["repository"],
                service_id=service_id,
                location="policy/backup-audit.json",
                summary="Backup coverage references an unknown target ID.",
            )

    simple_proxy = coverage.get("simple-proxy")
    if simple_proxy and simple_proxy.get("state") == "excluded":
        _append_finding(
            findings,
            rules=rules,
            detected_at=audited_at,
            rule_id="simple-proxy-exclusion",
            repository="AtlasReaper311/simple-proxy",
            service_id="simple-proxy",
            location="policy/backup-audit.json",
            summary="simple-proxy remains excluded from active backup audit by lifecycle, scope, and provenance policy.",
            severity="info",
        )


def audit_backups(
    *,
    root: Path,
    policy_path: Path,
    fixtures_dir: Path,
    registry_path: Path,
    contracts_dir: Path,
    now: datetime,
) -> dict[str, Any]:
    """Validate declarations, audit fixtures, and emit deterministic evidence."""
    now = now.astimezone(UTC).replace(microsecond=0)
    audited_at = _timestamp(now)
    contract_root = root / "contracts" / "v1"
    rules = load_json(contract_root / "fingerprint-rules.json")
    finding_schema = load_json(contract_root / "finding.schema.json")
    evidence_schema = load_json(contract_root / "backup-evidence.schema.json")
    policy_schema = load_json(root / "policy" / "backup-audit.schema.json")
    metadata_schema = load_json(root / "policy" / "backup-metadata.schema.json")
    registry_schema = load_json(root / "policy" / "estate-registry.schema.json")
    service_schema = load_json(contract_root / "service-contract.schema.json")

    findings: list[dict[str, Any]] = []
    policy_errors: list[str] = []
    registry_errors: list[str] = []
    contract_errors: list[str] = []

    policy, policy_error = _load_document(policy_path)
    if policy_error or not isinstance(policy, dict):
        policy_errors.append(policy_error or "policy root must be an object")
        _append_finding(
            findings,
            rules=rules,
            detected_at=audited_at,
            rule_id="malformed-backup-policy",
            repository="AtlasReaper311/atlas-infra",
            location="policy/backup-audit.json",
            summary=f"Backup policy cannot be loaded: {policy_errors[0]}.",
        )
        policy = {"targets": [], "service_coverage": [], "guardrails": {}}
    else:
        policy_errors.extend(validate_instance(policy, policy_schema))
        target_order = [
            item.get("target_id", "")
            for item in policy.get("targets", [])
            if isinstance(item, dict)
        ]
        coverage_order = [
            item.get("service_id", "")
            for item in policy.get("service_coverage", [])
            if isinstance(item, dict)
        ]
        if target_order != sorted(target_order):
            policy_errors.append("$.targets: must be sorted by target_id")
        if coverage_order != sorted(coverage_order):
            policy_errors.append("$.service_coverage: must be sorted by service_id")
        if len(target_order) != len(set(target_order)):
            policy_errors.append("$.targets: target_id values must be unique")
        if len(coverage_order) != len(set(coverage_order)):
            policy_errors.append(
                "$.service_coverage: service_id values must be unique"
            )
        for target in policy.get("targets", []):
            if not isinstance(target, dict):
                continue
            frequency = target.get("backup_frequency_hours")
            maximum_age = target.get("maximum_allowed_age_hours")
            rpo = target.get("recovery_point_objective_hours")
            if (
                isinstance(frequency, int)
                and isinstance(maximum_age, int)
                and frequency > maximum_age
            ):
                policy_errors.append(
                    f"$.targets[{target.get('target_id', '?')}]: backup frequency exceeds maximum age"
                )
            if (
                isinstance(frequency, int)
                and isinstance(rpo, int)
                and frequency > rpo
            ):
                policy_errors.append(
                    f"$.targets[{target.get('target_id', '?')}]: backup frequency exceeds RPO intent"
                )
        if policy_errors:
            _append_finding(
                findings,
                rules=rules,
                detected_at=audited_at,
                rule_id="malformed-backup-policy",
                repository="AtlasReaper311/atlas-infra",
                location="policy/backup-audit.json",
                summary=f"Backup policy is malformed: {policy_errors[0]}",
            )

    registry, registry_error = _load_document(registry_path)
    if registry_error or not isinstance(registry, dict):
        registry_errors.append(registry_error or "registry root must be an object")
        registry = {"repositories": []}
    else:
        registry_errors.extend(validate_instance(registry, registry_schema))
    entries = _repository_entries(registry)
    contracts = _load_contracts(contracts_dir)
    for service_id, contract in sorted(contracts.items()):
        for error in validate_instance(contract, service_schema):
            contract_errors.append(f"{service_id}: {error}")

    if registry_errors:
        _append_finding(
            findings,
            rules=rules,
            detected_at=audited_at,
            rule_id="unknown-service-id",
            repository="AtlasReaper311/atlas-infra",
            location="policy/estate-registry.json",
            summary=f"Phase 6 registry is unavailable or malformed: {registry_errors[0]}",
        )
    if contract_errors:
        _append_finding(
            findings,
            rules=rules,
            detected_at=audited_at,
            rule_id="unknown-service-id",
            repository="AtlasReaper311/atlas-infra",
            location="policy/service-contracts",
            summary=f"Service contract set is malformed: {contract_errors[0]}",
        )

    _validate_coverage(
        policy=policy,
        contracts=contracts,
        entries=entries,
        rules=rules,
        audited_at=audited_at,
        findings=findings,
    )

    evidence: list[dict[str, Any]] = []
    for target in sorted(
        (item for item in policy.get("targets", []) if isinstance(item, dict)),
        key=lambda item: str(item.get("target_id", "")),
    ):
        if target.get("enabled") is not True:
            continue
        evidence.append(
            _audit_target(
                root=root,
                fixtures_dir=fixtures_dir,
                target=target,
                policy=policy,
                contracts=contracts,
                entries=entries,
                metadata_schema=metadata_schema,
                rules=rules,
                now=now,
                findings=findings,
            )
        )

    findings = sorted(findings, key=_finding_sort_key)
    evidence = sorted(evidence, key=lambda item: item["target_id"])
    evidence_schema_errors: list[str] = []
    for index, item in enumerate(evidence):
        missing = sorted(PHASE8_EVIDENCE_FIELDS - set(item))
        if missing:
            evidence_schema_errors.append(
                f"backup_evidence[{index}]: missing Phase 8 fields {missing!r}"
            )
        errors = validate_instance(item, evidence_schema)
        errors.extend(semantic_errors("backup-evidence.schema.json", item, rules))
        evidence_schema_errors.extend(
            f"backup_evidence[{index}]: {error}" for error in errors
        )

    finding_schema_errors: list[str] = []
    for index, item in enumerate(findings):
        errors = validate_instance(item, finding_schema)
        errors.extend(semantic_errors("finding.schema.json", item, rules))
        finding_schema_errors.extend(f"finding[{index}]: {error}" for error in errors)

    evidence_states = [item["result_state"] for item in evidence]
    if (
        policy_errors
        or registry_errors
        or contract_errors
        or evidence_schema_errors
        or finding_schema_errors
        or "failed" in evidence_states
        or any(item["severity"] in {"failure", "critical"} for item in findings)
    ):
        result_state = "failed"
    elif "unavailable" in evidence_states:
        result_state = "unavailable"
    elif "stale" in evidence_states:
        result_state = "stale"
    elif "warning" in evidence_states or any(
        item["severity"] == "warning" for item in findings
    ):
        result_state = "warning"
    elif not evidence:
        result_state = "unknown"
    else:
        result_state = "healthy"

    summary_states = {
        state: sum(item["result_state"] == state for item in evidence)
        for state in ("failed", "healthy", "stale", "unavailable", "unknown", "warning")
    }
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "audit_timestamp": audited_at,
        "mode": policy.get("mode", "fixture-only"),
        "result_state": result_state,
        "summary": {
            "enabled_targets": len(evidence),
            "findings": len(findings),
            "states": summary_states,
            "services_with_coverage_declarations": len(
                policy.get("service_coverage", [])
            ),
        },
        "policy_validation": {"errors": sorted(set(policy_errors))},
        "registry_validation": {
            "contracts_checked": len(contracts),
            "errors": sorted(set(registry_errors + contract_errors)),
            "repositories_checked": len(entries),
        },
        "backup_evidence_schema_errors": sorted(evidence_schema_errors),
        "finding_schema_errors": sorted(finding_schema_errors),
        "backup_evidence": evidence,
        "findings": findings,
        "safety": {
            "fixture_only": True,
            "network_access": False,
            "provider_reads": False,
            "provider_writes": False,
            "live_restore": False,
            "temporary_cleanup": True,
        },
        "idempotent": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a deterministic, redacted Markdown summary."""
    summary = report["summary"]
    lines = [
        "# Backup audit",
        "",
        f"Result: **{report['result_state'].upper()}**  ",
        f"Mode: **{report['mode']}**  ",
        f"Audit timestamp: **{report['audit_timestamp']}**  ",
        f"Enabled fixture targets: **{summary['enabled_targets']}**  ",
        f"Findings: **{summary['findings']}**",
        "",
        "> This report validates local fixtures only. It is not evidence that a live provider backup exists.",
        "",
        "## Backup evidence",
        "",
        "| Target | Service | Freshness | Retention | Restore drill | Result |",
        "|---|---|---|---|---|---|",
    ]
    for item in report["backup_evidence"]:
        lines.append(
            "| `{target}` | `{service}` | {freshness} | {retention} | {restore} | {result} |".format(
                target=item["target_id"],
                service=item["service_id"],
                freshness=item["freshness_state"],
                retention=item["retention_state"],
                restore=item["restore_drill_state"],
                result=item["result_state"],
            )
        )
    lines.extend(["", "## Findings", ""])
    if not report["findings"]:
        lines.append("No backup findings.")
    else:
        lines.extend(
            [
                "| Severity | Rule | Service | Finding | Runbook |",
                "|---|---|---|---|---|",
            ]
        )
        for finding in report["findings"]:
            summary_text = finding["evidence"]["summary"].replace("|", "\\|")
            lines.append(
                "| {severity} | `{rule}` | `{service}` | {summary} | `{runbook}` |".format(
                    severity=finding["severity"],
                    rule=finding["rule_id"],
                    service=finding["subject"].get("service_id", "-"),
                    summary=summary_text,
                    runbook=finding.get("runbook_ref", "-"),
                )
            )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit local backup metadata and run disposable fixture restores."
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--policy", type=Path, default=Path("policy/backup-audit.json"))
    parser.add_argument(
        "--fixtures", type=Path, default=Path("tests/fixtures/backup-audit")
    )
    parser.add_argument(
        "--registry", type=Path, default=Path("policy/estate-registry.json")
    )
    parser.add_argument(
        "--service-contracts",
        type=Path,
        default=Path("policy/service-contracts"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--now",
        required=True,
        help="Deterministic UTC RFC 3339 audit timestamp, for example 2026-07-14T12:00:00Z.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    try:
        now = _parse_timestamp(args.now)
    except ValueError as error:
        print(f"invalid --now: {error}", file=sys.stderr)
        return 2
    arguments = {
        "root": root,
        "policy_path": _resolve(root, args.policy),
        "fixtures_dir": _resolve(root, args.fixtures),
        "registry_path": _resolve(root, args.registry),
        "contracts_dir": _resolve(root, args.service_contracts),
        "now": now,
    }
    report = audit_backups(**arguments)
    second = audit_backups(**arguments)
    report["idempotent"] = report == second
    if not report["idempotent"]:
        report["result_state"] = "failed"
    if args.report:
        _write_json(args.report, report)
    markdown = render_markdown(report)
    if args.markdown:
        _write_text(args.markdown, markdown)
    if not args.quiet:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result_state"] in {"healthy", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
