#!/usr/bin/env python3
"""Offline validation and reporting for the public Atlas contract registry.

The public registry is intentionally data-driven. It validates only repositories
and service contracts committed to this public control-plane repository. Private
repositories own their governance documents inside their own repositories and
are validated through the reusable governance workflow instead of being named
or indexed here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from control_plane_contracts import (
    calculate_fingerprint,
    canonical_json,
    load_json,
    semantic_errors,
    sha256_hex,
    validate_instance,
)

CLASSIFICATION_AXES = {
    "lifecycle": ["active", "archived", "deprecated", "experimental", "production"],
    "scope": ["internal", "public"],
    "provenance": ["external-derived", "original"],
}

PHASE6_CONTRACT_FIELDS = (
    "environments",
    "health_endpoint",
    "metadata_endpoint",
    "journey_coverage",
    "quota_policy",
    "secret_declaration",
    "backup_relevance",
    "release_watch_eligible",
    "escalation",
    "route_exceptions",
    "contract_notes",
)

RUNBOOKS = {
    "duplicate-route-owner": "docs/runbooks/contract-registry-duplicate-route-owner.md",
    "missing-service-contract": "docs/runbooks/contract-registry-missing-service-contract.md",
    "lifecycle-conflict": "docs/runbooks/contract-registry-lifecycle-conflict.md",
    "public-internal-mismatch": "docs/runbooks/contract-registry-public-internal-mismatch.md",
    "missing-metadata-endpoint": "docs/runbooks/contract-registry-missing-metadata-endpoint.md",
    "stale-registry-entry": "docs/runbooks/contract-registry-stale-registry-entry.md",
    "unknown-service-id": "docs/runbooks/contract-registry-unknown-service-id.md",
}
DEFAULT_RUNBOOK = "docs/runbooks/contract-registry-validation.md"


def _bounded_summary(value: str) -> str:
    clean = " ".join(value.split())
    return clean if len(clean) <= 500 else clean[:497] + "..."


def _load_document(path: Path) -> tuple[Any | None, str | None]:
    try:
        return load_json(path), None
    except FileNotFoundError:
        return None, "file is missing"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON at line {error.lineno}, column {error.colno}"


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
            "producer_version": "1.0.0",
        },
        "subject": {"repository": repository},
        "category": "contract",
        "severity": severity,
        "rule_id": rule_id,
        "location": location,
        "evidence": {
            "summary": _bounded_summary(summary),
            "references": [],
            "redacted": True,
        },
        "detected_at": detected_at,
        "fingerprint": "sha256:" + "0" * 64,
        "remediation": {
            "eligible": False,
            "reason": "Contract registry changes require owner review.",
        },
        "runbook_ref": RUNBOOKS.get(rule_id, DEFAULT_RUNBOOK),
    }
    if service_id:
        finding["subject"]["service_id"] = service_id
    finding["fingerprint"] = calculate_fingerprint("finding", finding, rules)
    return finding


def _append_finding(findings: list[dict[str, Any]], **kwargs: Any) -> None:
    findings.append(_finding(**kwargs))


def _contract_location(file_name: str) -> str:
    return f"policy/service-contracts/{file_name}"


def _endpoint_errors(contract: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for field in ("health_endpoint", "metadata_endpoint"):
        endpoint = contract.get(field)
        if not isinstance(endpoint, dict):
            continue
        known = endpoint.get("state") == "known"
        has_target = bool(endpoint.get("origin")) and bool(endpoint.get("path"))
        if known != has_target:
            errors.append(
                (
                    f"{field.replace('_', '-')}-state",
                    f"{field} known state must match whether origin and path are declared.",
                )
            )
    metadata = contract.get("metadata_endpoint")
    if isinstance(metadata, dict):
        known = metadata.get("state") == "known"
        shape = metadata.get("expected_shape")
        if known and shape in {"unknown", "not-applicable", None}:
            errors.append(
                (
                    "metadata-shape-unknown",
                    "A known metadata endpoint requires a known expected shape.",
                )
            )
        if not known and metadata.get("state") in {"unknown", "not-applicable"}:
            if shape != metadata.get("state"):
                errors.append(
                    (
                        "metadata-shape-state",
                        "Unknown and not-applicable metadata endpoints must use the matching expected_shape value.",
                    )
                )
        legacy_route = contract.get("metadata_route")
        if legacy_route is not None and (
            not known or legacy_route != metadata.get("path")
        ):
            errors.append(
                (
                    "metadata-route-mismatch",
                    "metadata_route must match a known metadata_endpoint path when declared.",
                )
            )
    return errors


def _sorted_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "dependencies",
        "environments",
        "runbooks",
        "slo_refs",
        "contract_notes",
    ):
        value = contract.get(field)
        if isinstance(value, list) and value != sorted(value, key=canonical_json):
            errors.append(f"{field} must be sorted")

    routes = contract.get("routes")
    if isinstance(routes, list):
        route_keys = [
            (
                str(route.get("origin", "")),
                str(route.get("path", "")),
                canonical_json(route.get("methods", [])),
                str(route.get("visibility", "")),
            )
            for route in routes
            if isinstance(route, dict)
        ]
        if route_keys != sorted(route_keys):
            errors.append("routes must be sorted by origin, path, methods, and visibility")
        for route in routes:
            if isinstance(route, dict):
                methods = route.get("methods")
                if isinstance(methods, list) and methods != sorted(methods):
                    errors.append("route methods must be sorted")

    exceptions = contract.get("route_exceptions")
    if isinstance(exceptions, list):
        keys = [
            (str(item.get("origin", "")), str(item.get("path", "")))
            for item in exceptions
            if isinstance(item, dict)
        ]
        if keys != sorted(keys):
            errors.append("route_exceptions must be sorted by origin and path")
    return errors


def _load_contracts(
    *,
    contracts_dir: Path,
    contract_schema: dict[str, Any],
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    contracts: dict[str, dict[str, Any]] = {}
    contract_files: dict[str, str] = {}
    if not contracts_dir.is_dir():
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-service-contract",
            repository="AtlasReaper311/atlas-infra",
            location="policy/service-contracts",
            summary="The public service-contract directory is missing.",
        )
        return contracts, contract_files

    for path in sorted(contracts_dir.glob("*.json"), key=lambda item: item.name):
        location = _contract_location(path.name)
        contract, load_error = _load_document(path)
        if load_error or not isinstance(contract, dict):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="contract-json-invalid",
                repository="AtlasReaper311/atlas-infra",
                location=location,
                summary=f"Service contract cannot be loaded: {load_error or 'root must be an object'}.",
            )
            continue

        repository = contract.get("source_repository")
        if not isinstance(repository, str) or not repository:
            repository = "AtlasReaper311/atlas-infra"
        service_id = contract.get("service_id")
        subject_service = service_id if isinstance(service_id, str) else None

        schema_errors = validate_instance(contract, contract_schema)
        schema_errors.extend(
            semantic_errors("service-contract.schema.json", contract, rules)
        )
        schema_errors.extend(_sorted_contract_errors(contract))
        if schema_errors:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="contract-schema-invalid",
                repository=repository,
                service_id=subject_service,
                location=location,
                summary=f"ServiceContract is malformed: {schema_errors[0]}",
            )

        if not isinstance(contract.get("owner"), dict) or not contract["owner"].get("github"):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="missing-service-owner",
                repository=repository,
                service_id=subject_service,
                location=location,
                summary="ServiceContract has no approved owner.",
            )

        missing_fields = [
            field for field in PHASE6_CONTRACT_FIELDS if field not in contract
        ]
        if missing_fields:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="contract-registry-fields-missing",
                repository=repository,
                service_id=subject_service,
                location=location,
                summary=f"Registry fields are missing: {', '.join(missing_fields)}.",
            )

        for rule_id, message in _endpoint_errors(contract):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id=rule_id,
                repository=repository,
                service_id=subject_service,
                location=location,
                summary=message,
            )

        if not isinstance(service_id, str) or not service_id:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="unknown-service-id",
                repository=repository,
                location=location,
                summary="ServiceContract has no service_id.",
            )
            continue
        if service_id in contracts:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="duplicate-service-id",
                repository=repository,
                service_id=service_id,
                location=location,
                summary="Service ID is declared by more than one contract.",
            )
            continue
        contracts[service_id] = contract
        contract_files[service_id] = path.name
    return contracts, contract_files


def _validate_registry_inventory(
    *,
    registry: dict[str, Any],
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    repositories = registry.get("repositories", [])
    entries = [entry for entry in repositories if isinstance(entry, dict)]
    names = [entry.get("repository") for entry in entries]
    valid_names = [name for name in names if isinstance(name, str)]

    if valid_names != sorted(valid_names):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-not-sorted",
            repository="AtlasReaper311/atlas-infra",
            location="policy/estate-registry.json",
            summary="Repository entries must be sorted by full repository name.",
        )
    if len(valid_names) != len(set(valid_names)):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="duplicate-repository",
            repository="AtlasReaper311/atlas-infra",
            location="policy/estate-registry.json",
            summary="The public registry contains duplicate repository entries.",
        )

    approved_count = registry.get("approved_repository_count")
    if approved_count != len(entries):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-count-mismatch",
            repository="AtlasReaper311/atlas-infra",
            location="policy/estate-registry.json",
            summary="approved_repository_count must equal the number of public registry entries.",
        )

    axes = registry.get("classification_axes")
    if isinstance(axes, dict):
        normalized = {
            key: sorted(value) if isinstance(value, list) else value
            for key, value in axes.items()
        }
        if normalized != CLASSIFICATION_AXES:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="classification-axes-invalid",
                repository="AtlasReaper311/atlas-infra",
                location="policy/estate-registry.json",
                summary="Lifecycle, scope, and provenance must remain separate approved axes.",
            )

    entries_by_repo: dict[str, dict[str, Any]] = {}
    for entry in entries:
        repository = entry.get("repository")
        if not isinstance(repository, str):
            continue
        entries_by_repo.setdefault(repository, entry)
        service_ids = entry.get("service_ids")
        if isinstance(service_ids, list) and service_ids != sorted(service_ids):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="registry-not-sorted",
                repository=repository,
                location="policy/estate-registry.json",
                summary="Repository service_ids must be sorted.",
            )
    return entries_by_repo


def _validate_contract_relationships(
    *,
    root: Path,
    entries_by_repo: dict[str, dict[str, Any]],
    contracts: dict[str, dict[str, Any]],
    contract_files: dict[str, str],
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> None:
    referenced_ids: set[str] = set()
    for repository, entry in sorted(entries_by_repo.items()):
        service_ids = entry.get("service_ids", [])
        if not isinstance(service_ids, list):
            service_ids = []
        referenced_ids.update(item for item in service_ids if isinstance(item, str))
        runtime = entry.get("runtime_service") is True
        required = entry.get("contract_required") is True
        exception = entry.get("contract_exception")

        if runtime and not required:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="missing-service-contract",
                repository=repository,
                location="policy/estate-registry.json",
                summary="Runtime repositories must require a service contract.",
            )
        if runtime and not service_ids:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="missing-service-contract",
                repository=repository,
                location="policy/estate-registry.json",
                summary="Runtime repository has no declared service ID.",
            )
        if not runtime and (required or service_ids) and not exception:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="non-runtime-contract",
                repository=repository,
                location="policy/estate-registry.json",
                summary="A non-runtime repository may have a service contract only with an explicit justification.",
            )

        for service_id in service_ids:
            contract = contracts.get(service_id)
            if contract is None:
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="missing-service-contract",
                    repository=repository,
                    service_id=service_id,
                    location="policy/estate-registry.json",
                    summary="Declared public runtime service has no ServiceContract file.",
                )
                continue
            if contract.get("source_repository") != repository:
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="contract-repository-mismatch",
                    repository=repository,
                    service_id=service_id,
                    location=_contract_location(contract_files[service_id]),
                    summary="ServiceContract source_repository does not match its public registry owner.",
                )

            classification = contract.get("classification", {})
            expected = {
                "lifecycle": entry.get("lifecycle"),
                "scope": entry.get("scope"),
                "provenance": entry.get("provenance"),
            }
            if classification != expected:
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="lifecycle-conflict",
                    repository=repository,
                    service_id=service_id,
                    location=_contract_location(contract_files[service_id]),
                    summary="ServiceContract classification conflicts with the public registry entry.",
                )

            if entry.get("lifecycle") == "production" and runtime:
                registry_runbook = entry.get("runbook_reference")
                contract_runbooks = contract.get("runbooks", [])
                registry_runbook_exists = (
                    isinstance(registry_runbook, str) and (root / registry_runbook).is_file()
                )
                contract_runbook_exists = any(
                    isinstance(reference, str) and (root / reference).is_file()
                    for reference in contract_runbooks
                )
                if not registry_runbook_exists or not contract_runbook_exists:
                    _append_finding(
                        findings,
                        rules=rules,
                        detected_at=detected_at,
                        rule_id="missing-production-runbook",
                        repository=repository,
                        service_id=service_id,
                        location=_contract_location(contract_files[service_id]),
                        summary="Production runtime service has no registry and ServiceContract runbook reference.",
                    )

    for service_id, contract in sorted(contracts.items()):
        repository = contract.get("source_repository", "AtlasReaper311/atlas-infra")
        location = _contract_location(contract_files[service_id])
        if repository not in entries_by_repo:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="stale-registry-entry",
                repository=repository,
                service_id=service_id,
                location=location,
                summary="Public ServiceContract names a repository outside the public runtime registry.",
            )
        elif service_id not in referenced_ids:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="unknown-service-id",
                repository=repository,
                service_id=service_id,
                location=location,
                summary="ServiceContract is not indexed by its public repository registry entry.",
            )

        metadata = contract.get("metadata_endpoint", {})
        if contract.get("release_watch_eligible") is True and (
            not isinstance(metadata, dict) or metadata.get("state") != "known"
        ):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="missing-metadata-endpoint",
                repository=repository,
                service_id=service_id,
                location=location,
                summary="Release-watch eligibility requires a known metadata endpoint and expected shape.",
            )

        known_ids = set(contracts)
        for dependency in contract.get("dependencies", []):
            if dependency not in known_ids:
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="unknown-service-id",
                    repository=repository,
                    service_id=service_id,
                    location=location,
                    summary=f"Dependency references unknown public service ID {dependency}.",
                )


def _validate_routes(
    *,
    contracts: dict[str, dict[str, Any]],
    contract_files: dict[str, str],
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_owners: dict[tuple[str, str, str], list[str]] = {}
    route_catalog: list[dict[str, Any]] = []
    for service_id, contract in sorted(contracts.items()):
        repository = contract.get("source_repository", "AtlasReaper311/atlas-infra")
        classification = contract.get("classification", {})
        exceptions = {
            (item.get("origin"), item.get("path"))
            for item in contract.get("route_exceptions", [])
            if isinstance(item, dict)
        }
        for route in contract.get("routes", []):
            if not isinstance(route, dict):
                continue
            origin = route.get("origin")
            path = route.get("path")
            if not isinstance(origin, str) or not isinstance(path, str):
                continue
            route_catalog.append(
                {
                    "service_id": service_id,
                    "repository": repository,
                    "origin": origin,
                    "path": path,
                    "methods": sorted(route.get("methods", [])),
                    "visibility": route.get("visibility"),
                }
            )
            for method in route.get("methods", []):
                route_owners.setdefault((origin, path, method), []).append(service_id)

            if (
                classification.get("scope") == "internal"
                and route.get("visibility") == "public"
                and (origin, path) not in exceptions
            ):
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="public-internal-mismatch",
                    repository=repository,
                    service_id=service_id,
                    location=_contract_location(contract_files[service_id]),
                    summary="Internal service claims a public route without an approved route exception.",
                )

    for (origin, path, method), service_ids in sorted(route_owners.items()):
        unique_owners = sorted(set(service_ids))
        if len(unique_owners) > 1:
            first = unique_owners[0]
            contract = contracts[first]
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="duplicate-route-owner",
                repository=contract.get("source_repository", "AtlasReaper311/atlas-infra"),
                service_id=first,
                location=_contract_location(contract_files[first]),
                summary=f"{method} {origin}{path} is claimed by {', '.join(unique_owners)}.",
            )
    return sorted(
        route_catalog,
        key=lambda item: (
            item["origin"],
            item["path"],
            canonical_json(item["methods"]),
            item["service_id"],
        ),
    )


def build_dependency_graph(contracts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    edges = []
    for service_id, contract in sorted(contracts.items()):
        classification = contract.get("classification", {})
        nodes.append(
            {
                "service_id": service_id,
                "repository": contract.get("source_repository"),
                "lifecycle": classification.get("lifecycle"),
                "scope": classification.get("scope"),
                "provenance": classification.get("provenance"),
                "environments": sorted(contract.get("environments", [])),
            }
        )
        for dependency in sorted(contract.get("dependencies", [])):
            edges.append({"source": service_id, "target": dependency})
    return {
        "schema_version": "atlas-contract-registry/dependency-graph/v1",
        "nodes": nodes,
        "edges": sorted(edges, key=lambda item: (item["source"], item["target"])),
    }


def _service_catalog(contracts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    catalog = []
    for service_id, contract in sorted(contracts.items()):
        classification = contract.get("classification", {})
        metadata = contract.get("metadata_endpoint", {})
        public_routes = sorted(
            f"{route.get('origin')}{route.get('path')}"
            for route in contract.get("routes", [])
            if isinstance(route, dict) and route.get("visibility") == "public"
        )
        catalog.append(
            {
                "service_id": service_id,
                "repository": contract.get("source_repository"),
                "declared_state": contract.get("registry_visibility"),
                "lifecycle": classification.get("lifecycle"),
                "scope": classification.get("scope"),
                "environments": sorted(contract.get("environments", [])),
                "public_routes": public_routes,
                "metadata": {
                    "state": metadata.get("state") if isinstance(metadata, dict) else None,
                    "origin": metadata.get("origin") if isinstance(metadata, dict) else None,
                    "path": metadata.get("path") if isinstance(metadata, dict) else None,
                    "expected_shape": metadata.get("expected_shape") if isinstance(metadata, dict) else None,
                },
            }
        )
    return catalog


def validate_contract_registry(
    *,
    root: Path,
    registry_path: Path,
    contracts_dir: Path,
) -> dict[str, Any]:
    contract_root = root / "contracts" / "v1"
    fingerprint_rules = load_json(contract_root / "fingerprint-rules.json")
    finding_schema = load_json(contract_root / "finding.schema.json")
    service_schema = load_json(contract_root / "service-contract.schema.json")
    registry_schema = load_json(root / "policy" / "estate-registry.schema.json")

    findings: list[dict[str, Any]] = []
    registry, registry_error = _load_document(registry_path)
    detected_at = (
        registry.get("reviewed_at")
        if isinstance(registry, dict) and isinstance(registry.get("reviewed_at"), str)
        else "1970-01-01T00:00:00Z"
    )
    if registry_error or not isinstance(registry, dict):
        _append_finding(
            findings,
            rules=fingerprint_rules,
            detected_at=detected_at,
            rule_id="registry-json-invalid",
            repository="AtlasReaper311/atlas-infra",
            location="policy/estate-registry.json",
            summary=f"Public registry cannot be loaded: {registry_error or 'root must be an object'}.",
        )
        registry = {"repositories": [], "reviewed_at": detected_at}
    else:
        registry_errors = validate_instance(registry, registry_schema)
        if registry_errors:
            _append_finding(
                findings,
                rules=fingerprint_rules,
                detected_at=detected_at,
                rule_id="registry-schema-invalid",
                repository="AtlasReaper311/atlas-infra",
                location="policy/estate-registry.json",
                summary=f"Public registry is malformed: {registry_errors[0]}",
            )

    contracts, contract_files = _load_contracts(
        contracts_dir=contracts_dir,
        contract_schema=service_schema,
        rules=fingerprint_rules,
        detected_at=detected_at,
        findings=findings,
    )
    entries_by_repo = _validate_registry_inventory(
        registry=registry,
        rules=fingerprint_rules,
        detected_at=detected_at,
        findings=findings,
    )
    _validate_contract_relationships(
        root=root,
        entries_by_repo=entries_by_repo,
        contracts=contracts,
        contract_files=contract_files,
        rules=fingerprint_rules,
        detected_at=detected_at,
        findings=findings,
    )
    routes = _validate_routes(
        contracts=contracts,
        contract_files=contract_files,
        rules=fingerprint_rules,
        detected_at=detected_at,
        findings=findings,
    )

    findings = sorted(
        findings,
        key=lambda item: (
            item["rule_id"],
            item["subject"]["repository"],
            item["subject"].get("service_id", ""),
            item["location"],
            item["fingerprint"],
        ),
    )
    finding_schema_errors: list[str] = []
    for index, finding in enumerate(findings):
        errors = validate_instance(finding, finding_schema)
        errors.extend(semantic_errors("finding.schema.json", finding, fingerprint_rules))
        finding_schema_errors.extend(f"finding[{index}]: {error}" for error in errors)

    graph = build_dependency_graph(contracts)
    return {
        "schema_version": "atlas-contract-registry/validation-report/v1",
        "reviewed_at": detected_at,
        "status": "passed" if not findings and not finding_schema_errors else "failed",
        "registry_digest": "sha256:" + sha256_hex(registry),
        "contract_set_digest": "sha256:"
        + sha256_hex({key: contracts[key] for key in sorted(contracts)}),
        "repositories_checked": len(entries_by_repo),
        "contracts_checked": len(contracts),
        "routes_checked": len(routes),
        "finding_count": len(findings),
        "finding_schema_errors": sorted(finding_schema_errors),
        "findings": findings,
        "route_ownership": routes,
        "dependency_graph": graph,
        "service_catalog": _service_catalog(contracts),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Contract registry validation",
        "",
        f"Status: **{report['status'].upper()}**  ",
        f"Repositories: **{report['repositories_checked']}**  ",
        f"Service contracts: **{report['contracts_checked']}**  ",
        f"Declared routes: **{report['routes_checked']}**  ",
        f"Findings: **{report['finding_count']}**",
        "",
    ]
    if not report["findings"]:
        lines.append("No registry findings.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| Severity | Rule | Repository | Service | Location | Finding |",
            "|---|---|---|---|---|---|",
        ]
    )
    for finding in report["findings"]:
        subject = finding["subject"]
        summary = finding["evidence"]["summary"].replace("|", "\\|")
        lines.append(
            "| {severity} | `{rule}` | `{repository}` | `{service}` | `{location}` | {summary} |".format(
                severity=finding["severity"],
                rule=finding["rule_id"],
                repository=subject["repository"],
                service=subject.get("service_id", "-"),
                location=finding["location"],
                summary=summary,
            )
        )
    return "\n".join(lines) + "\n"
