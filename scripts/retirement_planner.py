#!/usr/bin/env python3
"""Build a non-mutating retirement plan from current Atlas authorities.

The planner reports what still prevents a repository or service from being
retired. It never archives repositories, deletes Workers, changes DNS, removes
bindings, edits provider state, or changes lifecycle declarations.

Checks that require external runtime or GitHub evidence remain `unknown` until a
separate bounded evidence file supplies an owner-reviewed state. An eligible
plan therefore means all required evidence is either verified or explicitly
not applicable; it is not permission to execute the plan automatically.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EVIDENCE_STATES = {"verified", "failed", "unknown", "unavailable", "not-applicable"}
CLEAR_STATES = {"verified", "not-applicable"}
EXTERNAL_KEYS = {
    "worker_allowlist_clear",
    "production_prs_clear",
    "historical_evidence_preserved",
    "recovery_handled",
}


class RetirementPlanError(ValueError):
    """Retirement planning input is invalid or ambiguous."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RetirementPlanError(f"missing required file: {path}") from error
    except json.JSONDecodeError as error:
        raise RetirementPlanError(f"invalid JSON in {path}: {error}") from error


def service_contracts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "policy" / "service-contracts").glob("*.json")):
        value = load_json(path)
        if isinstance(value, dict) and isinstance(value.get("service_id"), str):
            result[value["service_id"]] = value
    return result


def repository_services(contracts: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for service_id, contract in contracts.items():
        repository = contract.get("source_repository")
        if isinstance(repository, str):
            result.setdefault(repository, set()).add(service_id)
    return result


def _service_dependants(
    service_id: str, contracts: dict[str, dict[str, Any]]
) -> list[str]:
    return sorted(
        candidate
        for candidate, contract in contracts.items()
        if service_id in (contract.get("dependencies") or [])
    )


def _repository_dependants(
    repository: str,
    contracts: dict[str, dict[str, Any]],
    by_repository: dict[str, set[str]],
) -> list[str]:
    targets = by_repository.get(repository, set())
    return sorted(
        candidate
        for candidate, contract in contracts.items()
        if any(target in (contract.get("dependencies") or []) for target in targets)
        and candidate not in targets
    )


def _topology_workers(topology: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in topology.get("workers", []) if isinstance(item, dict)]


def _service_routes(service_id: str, topology: dict[str, Any]) -> list[str]:
    routes: list[str] = []
    for worker in _topology_workers(topology):
        if worker.get("service_id") != service_id:
            continue
        for route in worker.get("routes", []):
            if isinstance(route, dict) and isinstance(route.get("pattern"), str):
                routes.append(route["pattern"])
    return sorted(set(routes))


def _repository_routes(repository: str, topology: dict[str, Any]) -> list[str]:
    routes: list[str] = []
    for worker in _topology_workers(topology):
        if worker.get("repository") != repository:
            continue
        for route in worker.get("routes", []):
            if isinstance(route, dict) and isinstance(route.get("pattern"), str):
                routes.append(route["pattern"])
    return sorted(set(routes))


def _service_binding_dependants(service_id: str, topology: dict[str, Any]) -> list[str]:
    owners: set[str] = set()
    for worker in _topology_workers(topology):
        for binding in worker.get("service_bindings", []):
            if isinstance(binding, dict) and binding.get("service") == service_id:
                owner = worker.get("service_id")
                if isinstance(owner, str) and owner != service_id:
                    owners.add(owner)
    return sorted(owners)


def _repository_binding_dependants(
    repository: str,
    topology: dict[str, Any],
    by_repository: dict[str, set[str]],
) -> list[str]:
    targets = by_repository.get(repository, set())
    owners: set[str] = set()
    for worker in _topology_workers(topology):
        owner = worker.get("service_id")
        if not isinstance(owner, str) or owner in targets:
            continue
        for binding in worker.get("service_bindings", []):
            if isinstance(binding, dict) and binding.get("service") in targets:
                owners.add(owner)
    return sorted(owners)


def _registry_services(registry: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for entry in registry.get("repositories", []):
        if not isinstance(entry, dict):
            continue
        for service_id in entry.get("service_ids", []):
            if isinstance(service_id, str):
                result.add(service_id)
    return result


def _registry_repositories(registry: dict[str, Any]) -> set[str]:
    return {
        entry["repository"]
        for entry in registry.get("repositories", [])
        if isinstance(entry, dict) and isinstance(entry.get("repository"), str)
    }


def _classification_repositories(classifications: dict[str, Any]) -> set[str]:
    return {
        entry["repository"]
        for entry in classifications.get("repositories", [])
        if isinstance(entry, dict) and isinstance(entry.get("repository"), str)
    }


def _public_topology_services(topology: dict[str, Any]) -> set[str]:
    return {
        worker["service_id"]
        for worker in _topology_workers(topology)
        if isinstance(worker.get("service_id"), str)
    }


def _public_topology_repositories(topology: dict[str, Any]) -> set[str]:
    repositories = {
        worker["repository"]
        for worker in _topology_workers(topology)
        if isinstance(worker.get("repository"), str)
    }
    repositories.update(
        project["repository"]
        for project in topology.get("pages_projects", [])
        if isinstance(project, dict) and isinstance(project.get("repository"), str)
    )
    return repositories


def _derived_state(blockers: list[str]) -> str:
    return "failed" if blockers else "verified"


def load_external_evidence(path: Path | None, subject: dict[str, str]) -> dict[str, str]:
    if path is None:
        return {}

    value = load_json(path)
    if not isinstance(value, dict):
        raise RetirementPlanError("external evidence must be a JSON object")
    if value.get("schema_version") != "atlas-retirement-external-evidence/v1":
        raise RetirementPlanError("unsupported external retirement evidence schema")
    if value.get("subject") != subject:
        raise RetirementPlanError("external evidence subject does not match requested subject")

    result: dict[str, str] = {}
    for key in EXTERNAL_KEYS:
        if key not in value:
            continue
        state = value[key]
        if state not in EVIDENCE_STATES:
            raise RetirementPlanError(f"external evidence {key} has invalid state {state!r}")
        result[key] = state
    return result


def build_plan(
    root: Path,
    *,
    kind: str,
    identifier: str,
    external_evidence: Path | None = None,
) -> dict[str, Any]:
    contracts = service_contracts(root)
    by_repository = repository_services(contracts)
    registry = load_json(root / "policy" / "estate-registry.json")
    classifications = load_json(root / "policy" / "public-repository-classifications.json")
    topology = load_json(root / "policy" / "public-cloudflare-topology.json")

    if kind == "service":
        if identifier not in contracts:
            raise RetirementPlanError(f"unknown service_id {identifier!r}")
        subject = {"kind": "service", "service_id": identifier}
        repository = contracts[identifier].get("source_repository")
        dependencies = _service_dependants(identifier, contracts)
        routes = _service_routes(identifier, topology)
        bindings = _service_binding_dependants(identifier, topology)
        manifest_membership = identifier in _registry_services(registry)
        public_topology_membership = identifier in _public_topology_services(topology)
        classification_membership = (
            isinstance(repository, str)
            and repository in _classification_repositories(classifications)
        )
    elif kind == "repository":
        if identifier not in by_repository and identifier not in _classification_repositories(classifications):
            raise RetirementPlanError(f"unknown Atlas repository {identifier!r}")
        subject = {"kind": "repository", "repository": identifier}
        repository = identifier
        dependencies = _repository_dependants(identifier, contracts, by_repository)
        routes = _repository_routes(identifier, topology)
        bindings = _repository_binding_dependants(identifier, topology, by_repository)
        manifest_membership = identifier in _registry_repositories(registry)
        public_topology_membership = identifier in _public_topology_repositories(topology)
        classification_membership = identifier in _classification_repositories(classifications)
    else:
        raise RetirementPlanError("kind must be service or repository")

    manifest_blockers: list[str] = []
    if manifest_membership:
        manifest_blockers.append("subject remains in policy/estate-registry.json")
    if classification_membership:
        manifest_blockers.append(
            "source repository remains in public repository classification authority"
        )

    public_allowlist_blockers: list[str] = []
    if public_topology_membership:
        public_allowlist_blockers.append(
            "subject remains in the explicit public Cloudflare topology allowlist"
        )

    evidence = {
        "dependencies_clear": _derived_state(dependencies),
        "routes_clear": _derived_state(routes),
        "bindings_clear": _derived_state(bindings),
        "manifest_clear": _derived_state(manifest_blockers),
        # The topology allowlist is a blocker when present, but absence alone does
        # not prove that every downstream Worker registry copy has been cleared.
        "worker_allowlist_clear": "failed" if public_allowlist_blockers else "unknown",
        "production_prs_clear": "unknown",
        "historical_evidence_preserved": "unknown",
        "recovery_handled": "unknown",
    }
    external = load_external_evidence(external_evidence, subject)
    for key, state in external.items():
        if key == "worker_allowlist_clear" and public_allowlist_blockers and state in CLEAR_STATES:
            raise RetirementPlanError(
                "external evidence cannot clear worker_allowlist_clear while the subject remains in public topology authority"
            )
        if key == "worker_allowlist_clear" and public_allowlist_blockers:
            # Current authority is stronger than a weaker external state. Preserve
            # the explicit failure until the source declaration itself is removed.
            evidence[key] = "failed"
            continue
        evidence[key] = state

    blockers = {
        "dependencies_clear": dependencies,
        "routes_clear": routes,
        "bindings_clear": bindings,
        "manifest_clear": manifest_blockers,
        "worker_allowlist_clear": public_allowlist_blockers,
        "production_prs_clear": [] if evidence["production_prs_clear"] in CLEAR_STATES else [
            "GitHub production-PR review evidence is required"
        ],
        "historical_evidence_preserved": []
        if evidence["historical_evidence_preserved"] in CLEAR_STATES
        else ["owner-reviewed historical evidence preservation is required"],
        "recovery_handled": []
        if evidence["recovery_handled"] in CLEAR_STATES
        else ["owner-reviewed recovery/replacement handling is required"],
    }
    if not public_allowlist_blockers and evidence["worker_allowlist_clear"] not in CLEAR_STATES:
        blockers["worker_allowlist_clear"] = [
            "a current downstream Worker allowlist check is required"
        ]

    eligible = all(state in CLEAR_STATES for state in evidence.values())
    sequence = [
        {
            "order": 1,
            "gate": "dependencies_clear",
            "action": "remove or replace inbound service dependencies",
            "state": evidence["dependencies_clear"],
        },
        {
            "order": 2,
            "gate": "routes_clear",
            "action": "remove declared runtime routes through the normal owning repository workflow",
            "state": evidence["routes_clear"],
        },
        {
            "order": 3,
            "gate": "bindings_clear",
            "action": "remove inbound Worker-to-Worker bindings through owning source repositories",
            "state": evidence["bindings_clear"],
        },
        {
            "order": 4,
            "gate": "manifest_clear",
            "action": "remove current public manifest/classification membership only after runtime detach",
            "state": evidence["manifest_clear"],
        },
        {
            "order": 5,
            "gate": "worker_allowlist_clear",
            "action": "prove all public Worker registry/allowlist projections no longer publish the subject",
            "state": evidence["worker_allowlist_clear"],
        },
        {
            "order": 6,
            "gate": "production_prs_clear",
            "action": "review open production PRs and pending rollout references",
            "state": evidence["production_prs_clear"],
        },
        {
            "order": 7,
            "gate": "historical_evidence_preserved",
            "action": "preserve ADR, incident, release, and retirement evidence required for audit history",
            "state": evidence["historical_evidence_preserved"],
        },
        {
            "order": 8,
            "gate": "recovery_handled",
            "action": "record replacement, rollback, or explicit not-applicable recovery handling",
            "state": evidence["recovery_handled"],
        },
    ]

    return {
        "schema_version": "atlas-retirement-plan/v1",
        "subject": subject,
        "eligible_for_owner_retirement_review": eligible,
        "execution_authority": "none",
        "evidence": evidence,
        "blockers": blockers,
        "sequence": sequence,
        "notes": [
            "This plan is evidence only and cannot execute retirement actions.",
            "Eligible means all contract gates are verified or not-applicable; owner approval is still required.",
            "Cloudflare, GitHub, DNS, storage, secrets, and deployment mutations remain separate actions.",
        ],
    }


def render_markdown(plan: dict[str, Any]) -> str:
    subject = plan["subject"]
    label = subject.get("service_id") or subject.get("repository")
    lines = [
        "# Atlas retirement plan",
        "",
        f"Subject: `{label}`  ",
        f"Eligible for owner retirement review: **{'YES' if plan['eligible_for_owner_retirement_review'] else 'NO'}**  ",
        "Execution authority: **none**",
        "",
        "## Evidence gates",
        "",
        "| Gate | State | Blockers |",
        "|---|---|---|",
    ]
    for gate, state in plan["evidence"].items():
        blockers = plan["blockers"].get(gate, [])
        blocker_text = "; ".join(blockers) if blockers else "none"
        lines.append(f"| `{gate}` | **{state}** | {blocker_text} |")
    lines.extend(["", "## Ordered plan", ""])
    for step in plan["sequence"]:
        lines.append(
            f"{step['order']}. **{step['gate']}** [{step['state']}]: {step['action']}."
        )
    lines.extend(
        [
            "",
            "> This report cannot archive, delete, deploy, edit DNS, alter routes, change storage, or mutate provider state.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a fail-closed Atlas retirement plan.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--kind", choices=("service", "repository"), required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--external-evidence", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args(argv)

    try:
        plan = build_plan(
            args.root.resolve(),
            kind=args.kind,
            identifier=args.id,
            external_evidence=args.external_evidence,
        )
    except RetirementPlanError as error:
        print(f"retirement planner failed closed: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(plan), encoding="utf-8")
    if not args.json_out and not args.markdown_out:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
