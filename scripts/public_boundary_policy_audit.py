#!/usr/bin/env python3
"""Apply reviewed literal exceptions to the public projection boundary audit.

The base boundary auditor deliberately treats every private repository name as a
protected literal. Some public contracts may intentionally reuse the same short
string as a capability identifier. This layer permits that only when a reviewed
policy binds the literal to one exact JSON pointer in one exact public
projection. The full private repository identity remains protected everywhere.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

import public_boundary_audit as base

APPROVED_LITERALS_KEY = "approved_public_literals"
APPROVED_LITERAL_KEYS = {
    "authority",
    "json_pointer",
    "path",
    "repository",
    "value",
}


def _load_approved_literals(
    path: Path,
    owner: str,
    targets: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Load exact public-literal approvals after base policy validation."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise base.BoundaryAuditError("cannot load public literal approvals") from None

    raw = document.get(APPROVED_LITERALS_KEY, [])
    if not isinstance(raw, list):
        raise base.BoundaryAuditError(
            f"{APPROVED_LITERALS_KEY} must be a list"
        )

    target_coordinates = {
        (target["repository"], target["path"])
        for target in targets
    }
    approvals: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != APPROVED_LITERAL_KEYS:
            raise base.BoundaryAuditError(
                "approved public literal entries must contain only authority, "
                "json_pointer, path, repository, and value"
            )
        if not all(isinstance(item[key], str) and item[key] for key in APPROVED_LITERAL_KEYS):
            raise base.BoundaryAuditError(
                "approved public literal entries must contain non-empty strings"
            )
        repository = item["repository"]
        source_path = item["path"]
        pointer = item["json_pointer"]
        authority = item["authority"]
        if not repository.startswith(owner + "/"):
            raise base.BoundaryAuditError(
                "approved public literal repository is outside audit owner"
            )
        if (repository, source_path) not in target_coordinates:
            raise base.BoundaryAuditError(
                "approved public literal must reference a governed projection target"
            )
        if not source_path.endswith(".json"):
            raise base.BoundaryAuditError(
                "approved public literals are supported only for JSON projections"
            )
        if not pointer.startswith("/") or pointer.endswith("/"):
            raise base.BoundaryAuditError(
                "approved public literal JSON pointer is invalid"
            )
        if not authority.startswith("ADR-"):
            raise base.BoundaryAuditError(
                "approved public literal must cite an ADR authority"
            )
        approvals.append({key: item[key] for key in APPROVED_LITERAL_KEYS})

    sort_key = lambda item: (
        item["repository"],
        item["path"],
        item["json_pointer"],
        item["value"],
        item["authority"],
    )
    normalized = sorted(approvals, key=sort_key)
    if approvals != normalized:
        raise base.BoundaryAuditError("approved public literal entries must be sorted")
    identity = [sort_key(item) for item in approvals]
    if len(identity) != len(set(identity)):
        raise base.BoundaryAuditError("approved public literal entries must be unique")
    return approvals


def _escape_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _walk_strings(
    value: Any,
    pointer: str = "",
) -> Iterable[tuple[str, str, bool]]:
    """Yield JSON string values and object keys with stable pointer context."""

    if isinstance(value, dict):
        for key, child in value.items():
            token = _escape_pointer_token(str(key))
            child_pointer = f"{pointer}/{token}"
            yield child_pointer, str(key), True
            yield from _walk_strings(child, child_pointer)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{pointer}/{index}")
        return
    if isinstance(value, str):
        yield pointer, value, False


def _audit_approved_target(
    client: base.GitHubClient,
    target: dict[str, str],
    identities: list[str],
    approvals: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Audit one target while allowing only exact reviewed JSON values."""

    repository = target["repository"]
    source_path = target["path"]
    approved_values = {item["value"] for item in approvals}

    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    stale = [item for item in approvals if item["value"] not in identities]
    if stale:
        errors.append(
            "approved public literal no longer maps to a protected identity: "
            f"{repository}:{source_path}"
        )

    remaining_identities = [
        identity for identity in identities if identity not in approved_values
    ]
    base_report = base.audit_github_public_projections(
        client,
        repository.split("/", 1)[0],
        remaining_identities,
        [target],
    )
    findings.extend(base_report.get("findings", []))
    errors.extend(base_report.get("errors", []))

    try:
        text = base._projection_text(client, repository, source_path)
        document = json.loads(text)
    except base.BoundaryAuditError as error:
        errors.append(str(error))
        return findings, errors
    except json.JSONDecodeError:
        errors.append(
            f"governed projection with approved literal is not valid JSON: "
            f"{repository}:{source_path}"
        )
        return findings, errors

    approval_keys = {
        (item["json_pointer"], item["value"])
        for item in approvals
    }
    used: set[tuple[str, str]] = set()
    unexpected = False

    for pointer, value, is_key in _walk_strings(document):
        matching = [needle for needle in approved_values if needle in value]
        if not matching:
            continue
        if not is_key and (pointer, value) in approval_keys:
            used.add((pointer, value))
            continue
        unexpected = True

    if unexpected:
        findings.append(base._redacted_finding(repository, source_path))

    if used != approval_keys:
        errors.append(
            "approved public literal is absent from its reviewed JSON pointer: "
            f"{repository}:{source_path}"
        )

    return findings, errors


def audit_github_public_projections(
    client: base.GitHubClient,
    owner: str,
    identities: list[str],
    targets: list[dict[str, str]],
    approvals: list[dict[str, str]],
) -> dict[str, Any]:
    """Run the base audit plus exact reviewed JSON-literal approvals."""

    by_target: dict[tuple[str, str], list[dict[str, str]]] = {}
    for approval in approvals:
        key = (approval["repository"], approval["path"])
        by_target.setdefault(key, []).append(approval)

    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for target in targets:
        key = (target["repository"], target["path"])
        target_approvals = by_target.get(key, [])
        if target_approvals:
            target_findings, target_errors = _audit_approved_target(
                client,
                target,
                identities,
                target_approvals,
            )
            findings.extend(target_findings)
            errors.extend(target_errors)
            continue

        report = base.audit_github_public_projections(
            client,
            owner,
            identities,
            [target],
        )
        findings.extend(report.get("findings", []))
        errors.extend(report.get("errors", []))

    findings = sorted(
        {
            (
                item["repository"],
                item["path"],
                item.get("line"),
                item["fingerprint"],
            ): item
            for item in findings
        }.values(),
        key=lambda item: (
            item["repository"],
            item["path"],
            item.get("line") or 0,
        ),
    )
    errors = sorted(set(errors))
    return {
        "schema_version": base.SCHEMA_VERSION,
        "mode": "github-public-projections",
        "projection_targets_checked": len(targets),
        "findings": findings,
        "errors": errors,
        "status": "failed" if findings or errors else "passed",
    }


def main(argv: list[str] | None = None) -> int:
    args = base.parse_args(argv)
    if args.root is not None:
        return base.main(argv)

    try:
        token = os.environ.get(args.token_env, "").strip()
        if not token:
            raise base.BoundaryAuditError(
                f"authenticated GitHub token is unavailable in environment variable {args.token_env}"
            )
        client = base.GitHubClient(token)
        identities = base.discover_private_identities(client, args.github_owner)
        targets = base.load_projection_targets(args.projection_policy, args.github_owner)
        approvals = _load_approved_literals(
            args.projection_policy,
            args.github_owner,
            targets,
        )
        report = audit_github_public_projections(
            client,
            args.github_owner,
            identities,
            targets,
            approvals,
        )
    except (base.BoundaryAuditError, OSError) as error:
        print(f"public boundary audit failed: {error}", file=sys.stderr)
        return 2

    base.write_report(report, args.report, args.markdown)
    if not args.quiet:
        print(base.render_markdown(report), end="")
    return 1 if report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
