#!/usr/bin/env python3
"""Validate and publish one exact RAMONE control-plane read-model artifact.

The publisher is intentionally narrow. It accepts one fixed bundle shape, checks
an operator-supplied file digest and model fingerprint, revalidates the canonical
read-model contract and freshness, writes one fixed KV key through one fixed
Cloudflare API endpoint, and verifies the exact bytes by reading the key back.

No key, namespace, account, URL, request body, delete, list, bulk, schedule, or
provider-discovery input is exposed by this command.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from control_plane_contracts import canonical_json, load_json, validate_instance

POLICY_SCHEMA_VERSION = "atlas-control-plane/read-model-publisher-policy/v1"
MODEL_SCHEMA_VERSION = "atlas-control-plane/control-plane-read-model/v1"
PRODUCER_RECEIPT_SCHEMA_VERSION = (
    "atlas-control-plane/read-model-dry-run-receipt/v1"
)
PUBLICATION_RECEIPT_SCHEMA_VERSION = (
    "atlas-control-plane/read-model-publication-receipt/v1"
)
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
RUN_ID = re.compile(r"^[1-9][0-9]*$")
EXPECTED_API_ORIGIN = "https://api.cloudflare.com"
EXPECTED_ACCOUNT_ID = "49e221b7e55a9e5c45b88d08efca5771"
EXPECTED_NAMESPACE_ID = "33fa7cbf66fc495ea0304a5f95ffc9a8"
EXPECTED_KV_KEY = "control-plane:read-model:v1"

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


class PublisherError(ValueError):
    """Raised when publication would cross a declared boundary."""


class PublicationFailure(PublisherError):
    """A redacted receipt is available even though publication failed."""

    def __init__(self, message: str, receipt: dict[str, Any]) -> None:
        super().__init__(message)
        self.receipt = receipt


class KVTransport(Protocol):
    """The only provider operations the publisher may perform."""

    def get(self, url: str, token: str) -> bytes | None:
        """Return the value bytes or ``None`` when the fixed key is absent."""

    def put(self, url: str, token: str, value: bytes) -> None:
        """Replace the value at the fixed key."""


class CloudflareKVTransport:
    """Minimal Cloudflare KV client restricted to GET and PUT for one URL."""

    user_agent = "atlas-infra-control-plane-publisher/1"

    @staticmethod
    def _request(
        method: str,
        url: str,
        token: str,
        value: bytes | None = None,
    ) -> tuple[int, bytes]:
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": CloudflareKVTransport.user_agent,
        }
        if value is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = Request(url, data=value, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return int(response.status), response.read()
        except HTTPError as error:
            if method == "GET" and error.code == 404:
                return 404, b""
            raise PublisherError(
                f"Cloudflare {method} request failed with HTTP {error.code}"
            ) from error
        except URLError as error:
            raise PublisherError(
                f"Cloudflare {method} request failed before receiving a response"
            ) from error

    def get(self, url: str, token: str) -> bytes | None:
        status, body = self._request("GET", url, token)
        return None if status == 404 else body

    def put(self, url: str, token: str, value: bytes) -> None:
        status, body = self._request("PUT", url, token, value)
        if status < 200 or status >= 300:
            raise PublisherError(f"Cloudflare PUT returned unexpected HTTP {status}")
        try:
            envelope = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PublisherError("Cloudflare PUT returned a malformed response") from error
        if not isinstance(envelope, dict) or envelope.get("success") is not True:
            raise PublisherError("Cloudflare PUT did not report success")


@dataclass(frozen=True)
class ValidationResult:
    """Validated publication input, safe to pass to the protected write stage."""

    model: dict[str, Any]
    artifact_bytes: bytes
    artifact_sha256: str
    read_model_fingerprint: str
    source_fingerprint: str
    source_revision: str
    model_generated_at: str
    model_stale_after: str
    source_run_id: str
    source_head_sha: str
    endpoint: str
    kv_key: str
    account_id_suffix: str
    namespace_id_suffix: str


def _publication_safety_errors(
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
                segments.intersection(
                    {"authorization", "cookie", "password", "secret", "token"}
                )
            )
            if sensitive and normalized not in SAFE_SECRET_AGGREGATES:
                errors.append(f"{path}.{key}: forbidden or secret-bearing key")
            if key in REFERENCE_FIELDS:
                references = child if isinstance(child, list) else [child]
                for reference in references:
                    if reference is None:
                        continue
                    if not isinstance(reference, str):
                        errors.append(f"{path}.{key}: reference is not a string")
                        continue
                    parsed = urlsplit(reference)
                    if (
                        parsed.scheme != "https"
                        or not parsed.netloc
                        or not reference.startswith(allowed_reference_origins)
                    ):
                        errors.append(f"{path}.{key}: reference origin is not approved")
            errors.extend(
                _publication_safety_errors(
                    child, allowed_reference_origins, f"{path}.{key}"
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(
                _publication_safety_errors(
                    child, allowed_reference_origins, f"{path}[{index}]"
                )
            )
    elif isinstance(value, str):
        if PRIVATE_VALUE.search(value):
            errors.append(f"{path}: machine-local or private value")
        if len(value) > 500:
            errors.append(f"{path}: string exceeds 500 characters")
    return errors


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PublisherError(f"{label} must be a UTC RFC 3339 timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise PublisherError(f"{label} is not a valid calendar timestamp") from error
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _read_model_fingerprint(model: dict[str, Any]) -> str:
    payload = copy.deepcopy(model)
    payload.pop("read_model_fingerprint", None)
    return _sha256_json(payload)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except FileNotFoundError as error:
        raise PublisherError(f"missing required {label}: {path.name}") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublisherError(f"malformed required {label}: {path.name}") from error
    if not isinstance(value, dict):
        raise PublisherError(f"{label} must be a JSON object")
    return value


def _load_publisher_policy(path: Path) -> dict[str, Any]:
    policy = _load_object(path, "publisher policy")
    required = {
        "schema_version",
        "owner",
        "mode",
        "artifact",
        "cloudflare",
        "workflow",
        "blocked_capabilities",
    }
    if set(policy) != required:
        raise PublisherError("publisher policy has undeclared or missing fields")
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise PublisherError("unsupported publisher policy schema")
    if policy.get("owner") != "AtlasReaper311/atlas-infra":
        raise PublisherError("publisher policy owner is not atlas-infra")
    if policy.get("mode") != "manual-exact-digest-only":
        raise PublisherError("publisher policy mode is not bounded")

    artifact = policy.get("artifact")
    if not isinstance(artifact, dict) or set(artifact) != {
        "artifact_name",
        "model_filename",
        "producer_receipt_filename",
        "max_bytes",
        "max_model_age_seconds",
    }:
        raise PublisherError("publisher artifact policy is malformed")
    if artifact.get("artifact_name") != "ramone-control-plane-read-model":
        raise PublisherError("publisher artifact name is not fixed")
    if artifact.get("model_filename") != "control-plane-read-model.json":
        raise PublisherError("publisher model filename is not fixed")
    if artifact.get("producer_receipt_filename") != "dry-run-receipt.json":
        raise PublisherError("publisher producer receipt filename is not fixed")
    if artifact.get("max_bytes") != 65536:
        raise PublisherError("publisher max_bytes must remain 65536")
    if artifact.get("max_model_age_seconds") != 600:
        raise PublisherError("publisher maximum model age must remain 600 seconds")

    cloudflare = policy.get("cloudflare")
    if not isinstance(cloudflare, dict) or set(cloudflare) != {
        "api_origin",
        "account_id",
        "namespace_id",
        "kv_key",
        "required_token_permission",
    }:
        raise PublisherError("publisher Cloudflare policy is malformed")
    if cloudflare.get("api_origin") != EXPECTED_API_ORIGIN:
        raise PublisherError("publisher Cloudflare origin is not fixed")
    if cloudflare.get("account_id") != EXPECTED_ACCOUNT_ID:
        raise PublisherError("publisher account ID is not fixed")
    if cloudflare.get("namespace_id") != EXPECTED_NAMESPACE_ID:
        raise PublisherError("publisher namespace ID is not fixed")
    if cloudflare.get("kv_key") != EXPECTED_KV_KEY:
        raise PublisherError("publisher KV key is not fixed")
    if cloudflare.get("required_token_permission") != "Workers KV Storage Write":
        raise PublisherError("publisher token permission is not least privilege")

    workflow = policy.get("workflow")
    if not isinstance(workflow, dict) or set(workflow) != {
        "allowed_ref",
        "confirmation",
        "environment",
        "token_secret",
    }:
        raise PublisherError("publisher workflow policy is malformed")
    if workflow.get("allowed_ref") != "refs/heads/main":
        raise PublisherError("publisher workflow ref is not fixed to main")
    if workflow.get("confirmation") != "publish-control-plane-read-model-v1":
        raise PublisherError("publisher confirmation phrase is not fixed")
    if workflow.get("environment") != "ramone-control-plane-publish":
        raise PublisherError("publisher environment is not fixed")
    if workflow.get("token_secret") != "CF_RAMONE_CONTROL_PLANE_KV_WRITE_TOKEN":
        raise PublisherError("publisher token secret name is not fixed")

    blocked = policy.get("blocked_capabilities")
    expected_blocked = {
        "arbitrary-account",
        "arbitrary-artifact-name",
        "arbitrary-http",
        "arbitrary-key",
        "arbitrary-namespace",
        "automatic-dispatch",
        "bulk-write",
        "delete",
        "list",
        "provider-discovery",
        "request-body-input",
        "schedule",
        "token-output",
    }
    if not isinstance(blocked, list) or set(blocked) != expected_blocked:
        raise PublisherError("publisher blocked-capability set has drifted")
    return policy


def _endpoint(policy: dict[str, Any]) -> str:
    cloudflare = policy["cloudflare"]
    origin = urlsplit(cloudflare["api_origin"])
    if origin.scheme != "https" or origin.netloc != "api.cloudflare.com":
        raise PublisherError("publisher API origin is unsafe")
    key = quote(cloudflare["kv_key"], safe="")
    return (
        f"{cloudflare['api_origin']}/client/v4/accounts/"
        f"{cloudflare['account_id']}/storage/kv/namespaces/"
        f"{cloudflare['namespace_id']}/values/{key}"
    )


def _bundle_paths(bundle: Path, policy: dict[str, Any]) -> tuple[Path, Path]:
    if not bundle.is_dir():
        raise PublisherError("artifact bundle directory is missing")
    expected = {
        policy["artifact"]["model_filename"],
        policy["artifact"]["producer_receipt_filename"],
    }
    actual = {entry.name for entry in bundle.iterdir()}
    if actual != expected:
        raise PublisherError(
            f"artifact bundle inventory mismatch: expected={sorted(expected)}, actual={sorted(actual)}"
        )
    model_path = bundle / policy["artifact"]["model_filename"]
    receipt_path = bundle / policy["artifact"]["producer_receipt_filename"]
    for path in (model_path, receipt_path):
        if path.is_symlink() or not path.is_file():
            raise PublisherError(f"artifact bundle member is not a regular file: {path.name}")
    return model_path, receipt_path


def _validate_producer_receipt(
    receipt: dict[str, Any],
    model: dict[str, Any],
    artifact_bytes: bytes,
    kv_key: str,
) -> None:
    expected_fields = {
        "schema_version",
        "mode",
        "generated_at",
        "source_revision",
        "source_count",
        "source_fingerprint",
        "read_model_fingerprint",
        "state",
        "stale_after",
        "collection_counts",
        "output_bytes",
        "bounded_kv_key",
        "provider_write_performed",
    }
    if set(receipt) != expected_fields:
        raise PublisherError("producer receipt has undeclared or missing fields")
    if receipt.get("schema_version") != PRODUCER_RECEIPT_SCHEMA_VERSION:
        raise PublisherError("producer receipt schema is unexpected")
    if receipt.get("mode") != "dry-run":
        raise PublisherError("producer receipt mode is not dry-run")
    if receipt.get("provider_write_performed") is not False:
        raise PublisherError("producer receipt claims a provider write")
    if receipt.get("bounded_kv_key") != kv_key:
        raise PublisherError("producer receipt names a different KV key")
    expected_pairs = {
        "generated_at": model["generated_at"],
        "source_revision": model["producer"]["source_revision"],
        "source_fingerprint": model["source_fingerprint"],
        "read_model_fingerprint": model["read_model_fingerprint"],
        "state": model["state"],
        "stale_after": model["stale_after"],
        "source_count": len(model["sources"]),
        "output_bytes": len(artifact_bytes),
    }
    for field, expected in expected_pairs.items():
        if receipt.get(field) != expected:
            raise PublisherError(f"producer receipt field {field!r} does not match model")
    collection_counts = receipt.get("collection_counts")
    expected_counts = {
        name: len(model[name])
        for name in (
            "services",
            "releases",
            "findings",
            "quota",
            "backups",
            "gardener_proposals",
            "runbooks",
            "evidence",
        )
    }
    if collection_counts != expected_counts:
        raise PublisherError("producer receipt collection counts do not match model")


def validate_bundle(
    *,
    bundle: Path,
    expected_artifact_sha256: str,
    expected_read_model_fingerprint: str,
    source_run_id: str,
    source_head_sha: str,
    now: datetime,
    policy_path: Path,
    schema_path: Path,
    producer_policy_path: Path,
) -> ValidationResult:
    """Fail closed unless the bundle is exactly publication-safe."""
    if not SHA256.fullmatch(expected_artifact_sha256):
        raise PublisherError("expected artifact SHA-256 is malformed")
    if not SHA256.fullmatch(expected_read_model_fingerprint):
        raise PublisherError("expected read-model fingerprint is malformed")
    if not RUN_ID.fullmatch(source_run_id):
        raise PublisherError("source workflow run ID is malformed")
    if not FULL_SHA.fullmatch(source_head_sha):
        raise PublisherError("source workflow head SHA is malformed")

    policy = _load_publisher_policy(policy_path)
    model_path, receipt_path = _bundle_paths(bundle, policy)
    artifact_bytes = model_path.read_bytes()
    if len(artifact_bytes) > policy["artifact"]["max_bytes"]:
        raise PublisherError("read-model artifact exceeds the fixed byte limit")
    artifact_sha256 = _sha256_bytes(artifact_bytes)
    if artifact_sha256 != expected_artifact_sha256:
        raise PublisherError("read-model artifact SHA-256 does not match approval input")

    try:
        model = json.loads(artifact_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublisherError("read-model artifact is not valid UTF-8 JSON") from error
    if not isinstance(model, dict):
        raise PublisherError("read-model artifact must be a JSON object")
    schema = _load_object(schema_path, "read-model schema")
    schema_errors = validate_instance(model, schema)
    if schema_errors:
        raise PublisherError(f"read-model artifact failed schema: {schema_errors[0]}")
    if model.get("schema_version") != MODEL_SCHEMA_VERSION:
        raise PublisherError("read-model artifact schema version is unexpected")

    producer_policy = _load_object(producer_policy_path, "producer policy")
    allowed_origins = producer_policy.get("allowed_reference_origins")
    if not isinstance(allowed_origins, list) or not allowed_origins:
        raise PublisherError("producer policy has no approved reference origins")
    safety_errors = _publication_safety_errors(
        model, tuple(str(origin) for origin in allowed_origins)
    )
    if safety_errors:
        raise PublisherError(safety_errors[0])

    source_fingerprint = _sha256_json(model["sources"])
    if model.get("source_fingerprint") != source_fingerprint:
        raise PublisherError("read-model source fingerprint does not match sources")
    read_model_fingerprint = _read_model_fingerprint(model)
    if model.get("read_model_fingerprint") != read_model_fingerprint:
        raise PublisherError("read-model fingerprint does not match canonical model")
    if read_model_fingerprint != expected_read_model_fingerprint:
        raise PublisherError("read-model fingerprint does not match approval input")

    generated_at = _parse_utc(model.get("generated_at"), "model generated_at")
    stale_after = _parse_utc(model.get("stale_after"), "model stale_after")
    if generated_at > now:
        raise PublisherError("read-model artifact is future-dated")
    if stale_after < generated_at:
        raise PublisherError("read-model stale_after precedes generated_at")
    max_age = int(policy["artifact"]["max_model_age_seconds"])
    if (stale_after - generated_at).total_seconds() > max_age:
        raise PublisherError("read-model freshness window exceeds policy")
    if now > stale_after:
        raise PublisherError("read-model artifact is stale")

    producer = model.get("producer")
    if not isinstance(producer, dict):
        raise PublisherError("read-model producer identity is missing")
    source_revision = str(producer.get("source_revision", ""))
    if not FULL_SHA.fullmatch(source_revision):
        raise PublisherError("read-model source revision is malformed")

    producer_receipt = _load_object(receipt_path, "producer dry-run receipt")
    _validate_producer_receipt(
        producer_receipt,
        model,
        artifact_bytes,
        policy["cloudflare"]["kv_key"],
    )

    cloudflare = policy["cloudflare"]
    return ValidationResult(
        model=model,
        artifact_bytes=artifact_bytes,
        artifact_sha256=artifact_sha256,
        read_model_fingerprint=read_model_fingerprint,
        source_fingerprint=source_fingerprint,
        source_revision=source_revision,
        model_generated_at=_iso(generated_at),
        model_stale_after=_iso(stale_after),
        source_run_id=source_run_id,
        source_head_sha=source_head_sha,
        endpoint=_endpoint(policy),
        kv_key=cloudflare["kv_key"],
        account_id_suffix=cloudflare["account_id"][-6:],
        namespace_id_suffix=cloudflare["namespace_id"][-6:],
    )


def _previous_model_fingerprint(value: bytes | None) -> str | None:
    if value is None:
        return None
    try:
        decoded = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(decoded, dict):
        return None
    fingerprint = decoded.get("read_model_fingerprint")
    return fingerprint if isinstance(fingerprint, str) and SHA256.fullmatch(fingerprint) else None


def _receipt(
    validation: ValidationResult,
    *,
    mode: str,
    status: str,
    now: datetime,
    previous: bytes | None,
    provider_write_performed: bool,
    provider_write_outcome: str,
    read_back_verified: bool,
    error_code: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": PUBLICATION_RECEIPT_SCHEMA_VERSION,
        "mode": mode,
        "status": status,
        "generated_at": _iso(now),
        "artifact_source_run_id": validation.source_run_id,
        "artifact_source_head_sha": validation.source_head_sha,
        "artifact_sha256": validation.artifact_sha256,
        "read_model_fingerprint": validation.read_model_fingerprint,
        "source_fingerprint": validation.source_fingerprint,
        "source_revision": validation.source_revision,
        "model_generated_at": validation.model_generated_at,
        "model_stale_after": validation.model_stale_after,
        "bounded_kv_key": validation.kv_key,
        "account_id_suffix": validation.account_id_suffix,
        "namespace_id_suffix": validation.namespace_id_suffix,
        "previous_value_present": previous is not None,
        "previous_artifact_sha256": _sha256_bytes(previous) if previous is not None else None,
        "previous_read_model_fingerprint": _previous_model_fingerprint(previous),
        "provider_write_performed": provider_write_performed,
        "provider_write_outcome": provider_write_outcome,
        "read_back_verified": read_back_verified,
        "error_code": error_code,
    }


def validate_receipt(validation: ValidationResult, now: datetime) -> dict[str, Any]:
    """Return a redacted credential-free preflight receipt."""
    return _receipt(
        validation,
        mode="validate",
        status="validated",
        now=now,
        previous=None,
        provider_write_performed=False,
        provider_write_outcome="not-performed",
        read_back_verified=False,
    )


def publish_validated(
    validation: ValidationResult,
    *,
    confirmation: str,
    token: str,
    now: datetime,
    policy_path: Path,
    transport: KVTransport | None = None,
) -> dict[str, Any]:
    """Write and read back the one fixed KV key after revalidation."""
    policy = _load_publisher_policy(policy_path)
    expected_confirmation = policy["workflow"]["confirmation"]
    if confirmation != expected_confirmation:
        raise PublisherError("publication confirmation phrase is incorrect")
    if not token or token.isspace():
        raise PublisherError("publisher token is unavailable")
    if now > _parse_utc(validation.model_stale_after, "model stale_after"):
        raise PublisherError("read-model artifact became stale before publication")

    client = transport or CloudflareKVTransport()
    try:
        previous = client.get(validation.endpoint, token)
    except PublisherError as error:
        receipt = _receipt(
            validation,
            mode="publish",
            status="failed",
            now=now,
            previous=None,
            provider_write_performed=False,
            provider_write_outcome="not-performed",
            read_back_verified=False,
            error_code="pre-read-failed",
        )
        raise PublicationFailure(str(error), receipt) from error

    try:
        client.put(validation.endpoint, token, validation.artifact_bytes)
    except PublisherError as error:
        receipt = _receipt(
            validation,
            mode="publish",
            status="failed",
            now=now,
            previous=previous,
            provider_write_performed=False,
            provider_write_outcome="unknown",
            read_back_verified=False,
            error_code="write-outcome-unknown",
        )
        raise PublicationFailure(str(error), receipt) from error

    try:
        read_back = client.get(validation.endpoint, token)
    except PublisherError as error:
        receipt = _receipt(
            validation,
            mode="publish",
            status="failed",
            now=now,
            previous=previous,
            provider_write_performed=True,
            provider_write_outcome="performed",
            read_back_verified=False,
            error_code="read-back-failed",
        )
        raise PublicationFailure(str(error), receipt) from error
    if read_back is None:
        receipt = _receipt(
            validation,
            mode="publish",
            status="failed",
            now=now,
            previous=previous,
            provider_write_performed=True,
            provider_write_outcome="performed",
            read_back_verified=False,
            error_code="read-back-missing",
        )
        raise PublicationFailure(
            "published KV value was absent during read-back", receipt
        )
    if read_back != validation.artifact_bytes:
        receipt = _receipt(
            validation,
            mode="publish",
            status="failed",
            now=now,
            previous=previous,
            provider_write_performed=True,
            provider_write_outcome="performed",
            read_back_verified=False,
            error_code="read-back-mismatch",
        )
        raise PublicationFailure(
            "published KV value did not match exact artifact bytes", receipt
        )
    return _receipt(
        validation,
        mode="publish",
        status="published",
        now=now,
        previous=previous,
        provider_write_performed=True,
        provider_write_outcome="performed",
        read_back_verified=True,
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _now(value: str | None) -> datetime:
    return datetime.now(timezone.utc) if value is None else _parse_utc(value, "--now")


def parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[1]
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--policy",
        type=Path,
        default=root / "policy" / "control-plane-read-model-publisher.json",
    )
    result.add_argument(
        "--schema",
        type=Path,
        default=root / "contracts" / "ramone" / "v1" / "control-plane-read-model.schema.json",
    )
    result.add_argument(
        "--producer-policy",
        type=Path,
        default=root / "policy" / "control-plane-read-model.json",
    )
    subparsers = result.add_subparsers(dest="command", required=True)
    for name in ("validate", "publish"):
        command = subparsers.add_parser(name)
        command.add_argument("--bundle", required=True, type=Path)
        command.add_argument("--expected-artifact-sha256", required=True)
        command.add_argument("--expected-read-model-fingerprint", required=True)
        command.add_argument("--source-run-id", required=True)
        command.add_argument("--source-head-sha", required=True)
        command.add_argument("--now")
        command.add_argument("--receipt", required=True, type=Path)
        if name == "publish":
            command.add_argument("--confirm", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    now = _now(args.now)
    try:
        validation = validate_bundle(
            bundle=args.bundle.resolve(),
            expected_artifact_sha256=args.expected_artifact_sha256,
            expected_read_model_fingerprint=args.expected_read_model_fingerprint,
            source_run_id=args.source_run_id,
            source_head_sha=args.source_head_sha,
            now=now,
            policy_path=args.policy.resolve(),
            schema_path=args.schema.resolve(),
            producer_policy_path=args.producer_policy.resolve(),
        )
        if args.command == "validate":
            receipt = validate_receipt(validation, now)
        else:
            token = os.environ.get("CF_RAMONE_CONTROL_PLANE_KV_WRITE_TOKEN", "")
            receipt = publish_validated(
                validation,
                confirmation=args.confirm,
                token=token,
                now=now,
                policy_path=args.policy.resolve(),
            )
        _write_json(args.receipt.resolve(), receipt)
    except PublicationFailure as error:
        _write_json(args.receipt.resolve(), error.receipt)
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except PublisherError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"status={receipt['status']}")
    print(f"artifact_sha256={receipt['artifact_sha256']}")
    print(f"read_model_fingerprint={receipt['read_model_fingerprint']}")
    print(f"provider_write_performed={str(receipt['provider_write_performed']).lower()}")
    print(f"read_back_verified={str(receipt['read_back_verified']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
