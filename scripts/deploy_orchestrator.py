#!/usr/bin/env python3
"""Deterministic, dry-run-only deployment orchestration planning."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
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

SCHEMA_VERSION = "atlas-deploy-orchestrator/deployment-plan/v1"
VALIDATION_SCHEMA_VERSION = "atlas-deploy-orchestrator/policy-validation/v1"
POLICY_LOCATION = "policy/deploy-orchestrator.json"
DEFAULT_RUNBOOK = "docs/runbooks/deploy-orchestrator-failed-preflight.md"
RUNBOOKS = {
    "dependency-cycle": "docs/runbooks/deploy-orchestrator-dependency-cycle.md",
    "disabled-service-requested": "docs/runbooks/deploy-orchestrator-disabled-service.md",
    "dispatch-execution-disabled": "docs/runbooks/deploy-orchestrator-failed-dispatch-authorization.md",
    "dispatch-executor-noop": "docs/runbooks/deploy-orchestrator-failed-dispatch-authorization.md",
    "missing-deploy-workflow": "docs/runbooks/deploy-orchestrator-missing-workflow.md",
    "production-approval-missing": "docs/runbooks/deploy-orchestrator-production-approval-missing.md",
    "service-excluded": "docs/runbooks/deploy-orchestrator-disabled-service.md",
}
COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _load_document(path: Path) -> tuple[Any | None, str | None]:
    try:
        return load_json(path), None
    except FileNotFoundError:
        return None, "file is missing"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON at line {error.lineno}, column {error.colno}"


def _bounded_summary(value: str) -> str:
    clean = " ".join(value.split())
    return clean if len(clean) <= 500 else clean[:497] + "..."


def _finding(
    *,
    rules: dict[str, Any],
    detected_at: str,
    rule_id: str,
    summary: str,
    service_id: str | None = None,
    repository: str = "AtlasReaper311/atlas-infra",
    location: str = POLICY_LOCATION,
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
        "category": "release",
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
            "reason": "Deployment orchestration policy changes require owner review.",
        },
        "runbook_ref": RUNBOOKS.get(rule_id, DEFAULT_RUNBOOK),
    }
    if service_id:
        finding["subject"]["service_id"] = service_id
    finding["fingerprint"] = calculate_fingerprint("finding", finding, rules)
    return finding


def _append_finding(findings: list[dict[str, Any]], **kwargs: Any) -> None:
    findings.append(_finding(**kwargs))


def _sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda item: (
            item["rule_id"],
            item["subject"]["repository"],
            item["subject"].get("service_id", ""),
            item["location"],
            item["fingerprint"],
        ),
    )


def _finding_schema_errors(
    *,
    findings: list[dict[str, Any]],
    finding_schema: dict[str, Any],
    rules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for index, finding in enumerate(findings):
        item_errors = validate_instance(finding, finding_schema)
        item_errors.extend(semantic_errors("finding.schema.json", finding, rules))
        errors.extend(f"finding[{index}]: {error}" for error in item_errors)
    return sorted(errors)


def _repository_entries(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = registry.get("repositories", [])
    if not isinstance(entries, list):
        return {}
    return {
        entry["repository"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("repository"), str)
    }


def _load_contracts(contracts_dir: Path) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    if not contracts_dir.is_dir():
        return contracts
    for path in sorted(contracts_dir.glob("*.json"), key=lambda item: item.name):
        document, error = _load_document(path)
        if error is None and isinstance(document, dict):
            service_id = document.get("service_id")
            if isinstance(service_id, str):
                contracts[service_id] = document
    return contracts


def _target_key(target: dict[str, Any]) -> tuple[str, str]:
    return (str(target.get("service_id", "")), str(target.get("environment", "")))


def _target_map(policy: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    targets = policy.get("targets", [])
    if not isinstance(targets, list):
        return {}
    return {
        _target_key(target): target
        for target in targets
        if isinstance(target, dict)
        and isinstance(target.get("service_id"), str)
        and isinstance(target.get("environment"), str)
    }


def _validate_target_shape(
    *,
    target: dict[str, Any],
    root: Path,
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> None:
    service_id = target.get("service_id")
    service = service_id if isinstance(service_id, str) else None
    repository = target.get("repository")
    subject_repository = (
        repository
        if isinstance(repository, str) and repository.startswith("AtlasReaper311/")
        else "AtlasReaper311/atlas-infra"
    )
    dispatch = target.get("dispatch")
    workflow = dispatch.get("workflow") if isinstance(dispatch, dict) else None
    if not isinstance(workflow, str) or not workflow.strip():
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-deploy-workflow",
            repository=subject_repository,
            service_id=service,
            summary="The deployment target does not declare a workflow name or dispatch target.",
        )
    owner = target.get("owner")
    if not isinstance(owner, str) or not owner.strip():
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-owner",
            repository=subject_repository,
            service_id=service,
            summary="The deployment target does not declare an owner.",
        )
    rollback = target.get("rollback_runbook")
    if not isinstance(rollback, str) or not rollback.strip():
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-rollback-runbook",
            repository=subject_repository,
            service_id=service,
            summary="The deployment target does not declare a rollback runbook.",
        )
    elif not (root / rollback).is_file():
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-rollback-runbook",
            repository=subject_repository,
            service_id=service,
            summary=f"The declared rollback runbook does not exist: {rollback}.",
        )


def _validate_target_registry_relationship(
    *,
    target: dict[str, Any],
    entries: dict[str, dict[str, Any]],
    contracts: dict[str, dict[str, Any]],
    policy: dict[str, Any],
    rules: dict[str, Any],
    detected_at: str,
    findings: list[dict[str, Any]],
) -> None:
    service_id = target.get("service_id")
    repository = target.get("repository")
    environment = target.get("environment")
    if not isinstance(service_id, str) or not isinstance(repository, str):
        return
    if service_id == "simple-proxy" or repository == "AtlasReaper311/simple-proxy":
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="service-excluded",
            repository=repository,
            service_id=service_id,
            summary="simple-proxy is explicitly excluded from deployment orchestration.",
        )
        return

    entry = entries.get(repository)
    contract = contracts.get(service_id)
    if entry is None:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-service-missing",
            repository=repository,
            service_id=service_id,
            summary="The target repository is absent from the Phase 6 estate registry.",
        )
        return
    if contract is None:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="service-contract-missing",
            repository=repository,
            service_id=service_id,
            summary="The target service is absent from the Phase 6 ServiceContract registry.",
        )
        return

    if service_id not in entry.get("service_ids", []):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-service-mismatch",
            repository=repository,
            service_id=service_id,
            summary="The target service ID is not owned by the declared registry repository.",
        )
    if contract.get("source_repository") != repository:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-service-mismatch",
            repository=repository,
            service_id=service_id,
            summary="The deployment policy repository does not match the ServiceContract source repository.",
        )
    if entry.get("deployment_owner") != repository:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="deployment-owner-mismatch",
            repository=repository,
            service_id=service_id,
            summary="The Phase 6 registry does not assign deployment ownership to the target repository.",
        )
    if environment not in contract.get("environments", []):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="environment-ineligible",
            repository=repository,
            service_id=service_id,
            summary=f"Environment {environment!r} is not declared by the ServiceContract.",
        )

    lifecycle = entry.get("lifecycle")
    provenance = entry.get("provenance")
    defaults = policy.get("eligibility", {})
    excluded_lifecycles = defaults.get("excluded_lifecycles", [])
    excluded_provenance = defaults.get("excluded_provenance", [])
    if lifecycle in excluded_lifecycles:
        rule_id = (
            f"{lifecycle}-service-ineligible"
            if lifecycle in {"archived", "deprecated"}
            else "lifecycle-ineligible"
        )
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id=rule_id,
            repository=repository,
            service_id=service_id,
            summary=f"Lifecycle {lifecycle!r} is excluded from default orchestration.",
        )
    if provenance in excluded_provenance:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="external-derived-ineligible",
            repository=repository,
            service_id=service_id,
            summary="External-derived repositories are excluded from default orchestration.",
        )

    classification = contract.get("classification", {})
    for field in ("lifecycle", "scope", "provenance"):
        if classification.get(field) != entry.get(field):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="classification-mismatch",
                repository=repository,
                service_id=service_id,
                summary=f"Registry and ServiceContract disagree on {field} classification.",
            )
    control_policy = contract.get("control_plane_policy", {})
    if control_policy.get("deployment_orchestration") is not True:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="service-excluded",
            repository=repository,
            service_id=service_id,
            summary="The ServiceContract disables deployment orchestration.",
        )

    metadata = contract.get("metadata_endpoint")
    if not isinstance(metadata, dict) or metadata.get("state") != "known":
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="release-watch-target-missing",
            repository=repository,
            service_id=service_id,
            summary="A known metadata endpoint is required to plan post-deploy release watch.",
        )


def _dependency_findings(
    *,
    targets: dict[tuple[str, str], dict[str, Any]],
    rules: dict[str, Any],
    detected_at: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for (service_id, environment), target in sorted(targets.items()):
        repository = target.get("repository", "AtlasReaper311/atlas-infra")
        dependencies = target.get("dependencies", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if (dependency, environment) not in targets:
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="missing-dependency",
                    repository=repository,
                    service_id=service_id,
                    summary=f"Dependency {dependency!r} has no target for environment {environment!r}.",
                )
    return findings


def _cycle_nodes(
    targets: dict[tuple[str, str], dict[str, Any]], environment: str
) -> list[str]:
    services = sorted(
        service_id
        for service_id, target_environment in targets
        if target_environment == environment
    )
    service_set = set(services)
    dependencies = {
        service_id: {
            dependency
            for dependency in targets[(service_id, environment)].get("dependencies", [])
            if dependency in service_set
        }
        for service_id in services
    }
    ready = sorted(service for service in services if not dependencies[service])
    ordered: list[str] = []
    while ready:
        service = ready.pop(0)
        ordered.append(service)
        for dependent in services:
            if service in dependencies[dependent]:
                dependencies[dependent].remove(service)
                if (
                    not dependencies[dependent]
                    and dependent not in ordered
                    and dependent not in ready
                ):
                    ready.append(dependent)
                    ready.sort()
    return sorted(service_set - set(ordered))


def validate_deploy_policy(
    *,
    root: Path,
    policy_path: Path,
    registry_path: Path,
    contracts_dir: Path,
) -> dict[str, Any]:
    """Validate orchestration policy and its Phase 6 registry relationships."""
    contract_root = root / "contracts" / "v1"
    rules = load_json(contract_root / "fingerprint-rules.json")
    finding_schema = load_json(contract_root / "finding.schema.json")
    policy_schema = load_json(root / "policy" / "deploy-orchestrator.schema.json")
    registry_schema = load_json(root / "policy" / "estate-registry.schema.json")
    service_schema = load_json(contract_root / "service-contract.schema.json")

    policy, policy_error = _load_document(policy_path)
    registry, registry_error = _load_document(registry_path)
    detected_at = (
        registry.get("reviewed_at")
        if isinstance(registry, dict) and isinstance(registry.get("reviewed_at"), str)
        else "1970-01-01T00:00:00Z"
    )
    findings: list[dict[str, Any]] = []
    policy_errors: list[str] = []
    registry_errors: list[str] = []
    contract_errors: list[str] = []

    if policy_error or not isinstance(policy, dict):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="deploy-policy-invalid",
            summary=f"The deploy policy cannot be loaded: {policy_error or 'root must be an object'}.",
        )
        policy = {"targets": []}
    else:
        policy_errors = validate_instance(policy, policy_schema)
        if policy_errors:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="deploy-policy-invalid",
                summary=f"The deploy policy is malformed: {policy_errors[0]}",
            )

    if registry_error or not isinstance(registry, dict):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="registry-invalid",
            summary=f"The Phase 6 registry cannot be loaded: {registry_error or 'root must be an object'}.",
            location="policy/estate-registry.json",
        )
        registry = {"repositories": [], "reviewed_at": detected_at}
    else:
        registry_errors = validate_instance(registry, registry_schema)
        if registry_errors:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="registry-invalid",
                summary=f"The Phase 6 registry is malformed: {registry_errors[0]}",
                location="policy/estate-registry.json",
            )

    entries = _repository_entries(registry)
    contracts = _load_contracts(contracts_dir)
    for service_id, contract in sorted(contracts.items()):
        errors = validate_instance(contract, service_schema)
        errors.extend(semantic_errors("service-contract.schema.json", contract, rules))
        contract_errors.extend(f"{service_id}: {error}" for error in errors)
    if contract_errors:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="service-contract-invalid",
            summary=f"A Phase 6 ServiceContract is malformed: {contract_errors[0]}",
            location="policy/service-contracts",
        )

    targets_list = policy.get("targets", [])
    if not isinstance(targets_list, list):
        targets_list = []
    keys = [_target_key(target) for target in targets_list if isinstance(target, dict)]
    if len(keys) != len(set(keys)):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="duplicate-deploy-target",
            summary="Deployment policy contains a duplicate service and environment target.",
        )
    if keys != sorted(keys):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="deploy-policy-not-sorted",
            summary="Deployment targets must be sorted by service ID and environment.",
        )

    targets = _target_map(policy)
    for target in targets_list:
        if not isinstance(target, dict):
            continue
        _validate_target_shape(
            target=target,
            root=root,
            rules=rules,
            detected_at=detected_at,
            findings=findings,
        )
        _validate_target_registry_relationship(
            target=target,
            entries=entries,
            contracts=contracts,
            policy=policy,
            rules=rules,
            detected_at=detected_at,
            findings=findings,
        )
        for field in ("dependencies", "preflight_checks", "required_approvals"):
            value = target.get(field)
            if isinstance(value, list) and value != sorted(value, key=canonical_json):
                _append_finding(
                    findings,
                    rules=rules,
                    detected_at=detected_at,
                    rule_id="deploy-policy-not-sorted",
                    repository=target.get("repository", "AtlasReaper311/atlas-infra"),
                    service_id=target.get("service_id"),
                    summary=f"{field} must use stable canonical sort order.",
                )

    findings.extend(
        _dependency_findings(
            targets=targets,
            rules=rules,
            detected_at=detected_at,
        )
    )
    environments = sorted({environment for _, environment in targets})
    for environment in environments:
        cycle = _cycle_nodes(targets, environment)
        if cycle:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="dependency-cycle",
                summary=f"Dependency cycle detected for {environment}: {', '.join(cycle)}.",
            )

    findings = _sort_findings(findings)
    finding_errors = _finding_schema_errors(
        findings=findings,
        finding_schema=finding_schema,
        rules=rules,
    )
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "reviewed_at": detected_at,
        "status": "passed" if not findings and not finding_errors else "failed",
        "policy_digest": "sha256:" + sha256_hex(policy),
        "registry_digest": "sha256:" + sha256_hex(registry),
        "targets_checked": len(targets),
        "finding_count": len(findings),
        "policy_schema_errors": sorted(policy_errors),
        "registry_schema_errors": sorted(registry_errors),
        "service_contract_schema_errors": sorted(contract_errors),
        "finding_schema_errors": finding_errors,
        "findings": findings,
    }


def _dependency_order(
    *,
    requested_services: list[str],
    environment: str,
    targets: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[str], list[str]]:
    closure: set[str] = set()
    missing: set[str] = set()

    def visit(service_id: str) -> None:
        if service_id in closure:
            return
        target = targets.get((service_id, environment))
        if target is None:
            missing.add(service_id)
            return
        closure.add(service_id)
        for dependency in target.get("dependencies", []):
            visit(dependency)

    for service_id in sorted(set(requested_services)):
        visit(service_id)
    if missing:
        return [], sorted(missing)

    dependencies = {
        service_id: set(targets[(service_id, environment)].get("dependencies", []))
        & closure
        for service_id in closure
    }
    ready = sorted(service_id for service_id in closure if not dependencies[service_id])
    order: list[str] = []
    while ready:
        service_id = ready.pop(0)
        order.append(service_id)
        for dependent in sorted(closure):
            if service_id in dependencies[dependent]:
                dependencies[dependent].remove(service_id)
                if (
                    not dependencies[dependent]
                    and dependent not in order
                    and dependent not in ready
                ):
                    ready.append(dependent)
                    ready.sort()
    return order, sorted(closure - set(order))


def _metadata_url(contract: dict[str, Any]) -> str | None:
    endpoint = contract.get("metadata_endpoint")
    if not isinstance(endpoint, dict) or endpoint.get("state") != "known":
        return None
    origin = endpoint.get("origin")
    path = endpoint.get("path")
    if isinstance(origin, str) and isinstance(path, str):
        return origin + path
    return None


def _release_watch_plan(
    *,
    target: dict[str, Any],
    contract: dict[str, Any],
    commit: str | None,
) -> dict[str, Any]:
    release_watch = target["post_deploy_release_watch"]
    expected_commit = commit or "FULL_COMMIT_REQUIRED"
    deployment_target = contract["runtime"]["deployment_target"]
    metadata_endpoint = _metadata_url(contract)
    inputs = {
        "commit": expected_commit,
        "deployment_id": "WORKFLOW_RUN_ID_REQUIRED",
        "deployment_target": deployment_target,
        "environment": target["environment"],
        "metadata_url": metadata_endpoint,
        "repository": target["repository"],
        "rollback_ref": target["rollback_runbook"],
        "service_id": target["service_id"],
    }
    command_parts = [
        "gh",
        "workflow",
        "run",
        release_watch["workflow"],
        "--repo",
        release_watch["repository"],
        "--ref",
        release_watch["ref"],
    ]
    for key, value in sorted(inputs.items()):
        command_parts.extend(["-f", f"{key}={value}"])
    return {
        "expected_repository": target["repository"],
        "expected_commit": commit,
        "service_id": target["service_id"],
        "environment": target["environment"],
        "metadata_endpoint": metadata_endpoint,
        "journey_target": release_watch["journey_target"],
        "registry_eligible": bool(contract.get("release_watch_eligible")),
        "dispatch": {
            "target_repository": release_watch["repository"],
            "workflow": release_watch["workflow"],
            "ref": release_watch["ref"],
            "inputs": inputs,
            "required_token_capabilities": ["Actions: write", "Metadata: read"],
            "timeout_minutes": release_watch["timeout_minutes"],
            "expected_evidence": ["release-evidence.json"],
        },
        "command": shlex.join(command_parts),
    }


def _dispatch_plan(
    *,
    target: dict[str, Any],
    contract: dict[str, Any],
    commit: str | None,
) -> dict[str, Any]:
    dispatch = target["dispatch"]
    preflight = [
        {
            **check,
            "status": "required-at-approved-dispatch",
        }
        for check in target["preflight_checks"]
    ]
    if not contract.get("release_watch_eligible"):
        preflight.append(
            {
                "check_id": "release-watch-identity-readiness",
                "kind": "registry-policy",
                "required": False,
                "description": (
                    "Phase 6 does not yet mark this service release-watch eligible; "
                    "a future approved dispatch must treat verification as unknown until identity support is proven."
                ),
                "status": "warning",
            }
        )
    preflight.sort(key=canonical_json)
    return {
        "service_id": target["service_id"],
        "repository": target["repository"],
        "environment": target["environment"],
        "classification": contract["classification"],
        "owner": target["owner"],
        "dependencies": target["dependencies"],
        "disabled": target["disabled"],
        "dry_run_only": target["dry_run_only"],
        "preflight_checks": preflight,
        "required_approvals": target["required_approvals"],
        "timeout_minutes": target["timeout_minutes"],
        "rollback_runbook": target["rollback_runbook"],
        "dispatch": {
            "target_repository": target["repository"],
            "workflow": dispatch["workflow"],
            "ref": dispatch["ref"],
            "inputs": dispatch["inputs"],
            "required_token_capabilities": dispatch["required_token_capabilities"],
            "timeout_minutes": target["timeout_minutes"],
            "expected_evidence": dispatch["expected_evidence"],
            "expected_commit": commit,
        },
        "post_deploy_release_watch": _release_watch_plan(
            target=target,
            contract=contract,
            commit=commit,
        ),
    }


def build_plan(
    *,
    root: Path,
    policy_path: Path,
    registry_path: Path,
    contracts_dir: Path,
    requested_services: list[str],
    environment: str,
    commit: str | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    """Build a deterministic dependency-resolved dry-run plan."""
    validation = validate_deploy_policy(
        root=root,
        policy_path=policy_path,
        registry_path=registry_path,
        contracts_dir=contracts_dir,
    )
    policy = load_json(policy_path)
    registry = load_json(registry_path)
    contracts = _load_contracts(contracts_dir)
    rules = load_json(root / "contracts" / "v1" / "fingerprint-rules.json")
    finding_schema = load_json(root / "contracts" / "v1" / "finding.schema.json")
    plan_schema = load_json(root / "policy" / "deploy-plan.schema.json")
    detected_at = registry["reviewed_at"]
    findings = list(validation["findings"])
    targets = _target_map(policy)
    requested = sorted(set(requested_services))

    if commit is not None and not COMMIT_PATTERN.fullmatch(commit):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="invalid-commit",
            summary="Expected commit must be a full lowercase 40- or 64-character hexadecimal SHA.",
        )
    order, unresolved = _dependency_order(
        requested_services=requested,
        environment=environment,
        targets=targets,
    )
    for service_id in unresolved:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="missing-dependency",
            service_id=service_id,
            summary=f"No deployment target exists for {service_id!r} in {environment!r}.",
        )
    if not unresolved and len(order) < len(
        {
            service_id
            for service_id, target_environment in targets
            if target_environment == environment
            and (service_id in requested or service_id in order)
        }
    ):
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="dependency-cycle",
            summary=f"The requested {environment} dependency graph contains a cycle.",
        )

    for service_id in order:
        target = targets[(service_id, environment)]
        if target.get("disabled"):
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="disabled-service-requested",
                repository=target["repository"],
                service_id=service_id,
                summary="The requested deployment target is disabled by policy.",
            )

    execution = policy.get("execution", {})
    if execute:
        if execution.get("enabled") is not True:
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="dispatch-execution-disabled",
                summary="Dispatch execution is disabled by Phase 7 policy.",
            )
        elif execution.get("executor") == "noop":
            _append_finding(
                findings,
                rules=rules,
                detected_at=detected_at,
                rule_id="dispatch-executor-noop",
                summary="The configured executor is a dry-run no-op and cannot dispatch workflows.",
            )

    production = environment == "production"
    approval_required = production or any(
        bool(targets[(service_id, environment)].get("required_approvals"))
        for service_id in order
    )
    if execute and production:
        _append_finding(
            findings,
            rules=rules,
            detected_at=detected_at,
            rule_id="production-approval-missing",
            summary="Production dispatch requires a separate human approval; no approval can be supplied to this Phase 7 no-op executor.",
        )

    findings = _sort_findings(findings)
    dispatches = []
    if not findings:
        dispatches = [
            _dispatch_plan(
                target=targets[(service_id, environment)],
                contract=contracts[service_id],
                commit=commit,
            )
            for service_id in order
        ]

    identity = {
        "requested_services": requested,
        "environment": environment,
        "expected_commit": commit,
        "order": order,
        "policy_digest": validation["policy_digest"],
        "registry_digest": validation["registry_digest"],
    }
    plan_id = "sha256:" + sha256_hex(identity)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "generated_at": detected_at,
        "mode": "dry-run",
        "status": "invalid" if findings else "ready",
        "request": {
            "services": requested,
            "environment": environment,
            "expected_commit": commit,
        },
        "sources": {
            "policy": POLICY_LOCATION,
            "policy_digest": validation["policy_digest"],
            "registry": "policy/estate-registry.json",
            "registry_digest": validation["registry_digest"],
        },
        "approval": {
            "required": approval_required,
            "status": "missing" if approval_required else "not-required",
            "gates": sorted(
                {
                    approval
                    for service_id in order
                    for approval in targets[(service_id, environment)].get(
                        "required_approvals", []
                    )
                }
            ),
            "protected_environment": policy["approval_model"]["protected_environment"],
            "two_owner_fallback": policy["approval_model"]["two_owner_fallback"],
        },
        "execution": {
            "requested": execute,
            "enabled_by_policy": execution.get("enabled") is True,
            "executor": execution.get("executor", "noop"),
            "allowed": False,
            "reason": "Phase 7 provides planning only; actual workflow dispatch is disabled.",
        },
        "order": order if not findings else [],
        "dispatches": dispatches,
        "aggregate_release_evidence": {
            "schema_version": "atlas-deploy-orchestrator/aggregate-release-evidence-reference/v1",
            "status": "planned" if not findings else "not-created",
            "plan_id": plan_id,
            "release_evidence_contract": "contracts/v1/release-evidence.schema.json",
            "persistence": "workflow-artifact-only",
            "records": [
                {
                    "service_id": service_id,
                    "repository": targets[(service_id, environment)]["repository"],
                    "status": "not-created",
                    "expected_artifact": "release-evidence.json",
                }
                for service_id in (order if not findings else [])
            ],
        },
        "finding_count": len(findings),
        "finding_schema_errors": _finding_schema_errors(
            findings=findings,
            finding_schema=finding_schema,
            rules=rules,
        ),
        "findings": findings,
        "plan_schema_errors": [],
    }
    plan_errors = validate_instance(plan, plan_schema)
    plan["plan_schema_errors"] = sorted(plan_errors)
    if plan_errors:
        plan["status"] = "invalid"
    return plan


def render_markdown(report: dict[str, Any]) -> str:
    """Render a deterministic human-readable policy or plan report."""
    if report.get("schema_version") == VALIDATION_SCHEMA_VERSION:
        lines = [
            "# Deploy orchestrator policy validation",
            "",
            f"Status: **{report['status'].upper()}**  ",
            f"Targets: **{report['targets_checked']}**  ",
            f"Findings: **{report['finding_count']}**",
            "",
        ]
    else:
        lines = [
            "# Deploy orchestrator dry-run plan",
            "",
            f"Status: **{report['status'].upper()}**  ",
            f"Plan: `{report['plan_id']}`  ",
            f"Environment: **{report['request']['environment']}**  ",
            f"Execution: **{report['execution']['executor']} / disabled**  ",
            f"Approval: **{report['approval']['status']}**",
            "",
        ]
        if report["order"]:
            lines.extend(["## Dependency-resolved order", ""])
            lines.extend(
                f"{index}. `{service_id}`"
                for index, service_id in enumerate(report["order"], start=1)
            )
            lines.append("")
        if report["dispatches"]:
            lines.extend(
                [
                    "## Planned dispatches",
                    "",
                    "| Service | Repository | Workflow | Ref | Release watch |",
                    "|---|---|---|---|---|",
                ]
            )
            for item in report["dispatches"]:
                release = item["post_deploy_release_watch"]
                lines.append(
                    "| `{service}` | `{repository}` | `{workflow}` | `{ref}` | `{release_workflow}` |".format(
                        service=item["service_id"],
                        repository=item["repository"],
                        workflow=item["dispatch"]["workflow"],
                        ref=item["dispatch"]["ref"],
                        release_workflow=release["dispatch"]["workflow"],
                    )
                )
            lines.append("")

    findings = report.get("findings", [])
    if not findings:
        lines.append("No blocking planning findings.")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "## Findings",
            "",
            "| Severity | Rule | Service | Finding |",
            "|---|---|---|---|",
        ]
    )
    for finding in findings:
        lines.append(
            "| {severity} | `{rule}` | `{service}` | {summary} |".format(
                severity=finding["severity"],
                rule=finding["rule_id"],
                service=finding["subject"].get("service_id", "-"),
                summary=finding["evidence"]["summary"].replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--policy", type=Path, default=Path("policy/deploy-orchestrator.json")
    )
    parser.add_argument(
        "--registry", type=Path, default=Path("policy/estate-registry.json")
    )
    parser.add_argument(
        "--contracts", type=Path, default=Path("policy/service-contracts")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--quiet", action="store_true")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    _add_common_arguments(validate_parser)
    plan_parser = subparsers.add_parser("plan")
    _add_common_arguments(plan_parser)
    plan_parser.add_argument("--service", action="append", required=True)
    plan_parser.add_argument(
        "--environment",
        choices=("development", "preview", "production"),
        required=True,
    )
    plan_parser.add_argument("--commit")
    plan_parser.add_argument(
        "--execute",
        action="store_true",
        help="Request execution; Phase 7 always refuses because its executor is a no-op.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    policy_path = _resolve(root, args.policy)
    registry_path = _resolve(root, args.registry)
    contracts_dir = _resolve(root, args.contracts)
    if args.command == "validate":
        first = validate_deploy_policy(
            root=root,
            policy_path=policy_path,
            registry_path=registry_path,
            contracts_dir=contracts_dir,
        )
        second = validate_deploy_policy(
            root=root,
            policy_path=policy_path,
            registry_path=registry_path,
            contracts_dir=contracts_dir,
        )
        report = {**first, "idempotent": first == second}
    else:
        first = build_plan(
            root=root,
            policy_path=policy_path,
            registry_path=registry_path,
            contracts_dir=contracts_dir,
            requested_services=args.service,
            environment=args.environment,
            commit=args.commit,
            execute=args.execute,
        )
        second = build_plan(
            root=root,
            policy_path=policy_path,
            registry_path=registry_path,
            contracts_dir=contracts_dir,
            requested_services=args.service,
            environment=args.environment,
            commit=args.commit,
            execute=args.execute,
        )
        report = {**first, "idempotent": first == second}

    if args.output:
        _write_json(args.output, report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if not args.quiet:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"passed", "ready"} and report["idempotent"] else 1


if __name__ == "__main__":
    sys.exit(main())
