#!/usr/bin/env python3
"""Validate the declared public Cloudflare topology offline.

The policy is an allowlist, not an account inventory. It may name only topology
that Atlas Systems intentionally publishes. Unknown provider objects remain
private by default and are never inferred into this document.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import control_plane_contracts as contracts

TOPOLOGY = Path("policy/public-cloudflare-topology.json")
SCHEMA = Path("policy/public-cloudflare-topology.schema.json")
STORAGE = Path("policy/public-cloudflare-resources.json")
SERVICE_CONTRACTS = Path("policy/service-contracts")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_url(contract: dict[str, Any]) -> str | None:
    endpoint = contract.get("metadata_endpoint")
    if not isinstance(endpoint, dict) or endpoint.get("state") != "known":
        return None
    origin = endpoint.get("origin")
    path = endpoint.get("path")
    if isinstance(origin, str) and isinstance(path, str):
        return origin.rstrip("/") + path
    return None


def service_contracts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((root / SERVICE_CONTRACTS).glob("*.json")):
        value = load(path)
        if isinstance(value, dict) and isinstance(value.get("service_id"), str):
            result[value["service_id"]] = value
    return result


def storage_index(storage: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (item["kind"], item["provider_id"]): item
        for item in storage.get("resources", [])
        if isinstance(item, dict)
        and isinstance(item.get("kind"), str)
        and isinstance(item.get("provider_id"), str)
    }


def validate(root: Path) -> dict[str, Any]:
    topology = load(root / TOPOLOGY)
    schema = load(root / SCHEMA)
    storage = load(root / STORAGE)
    service_map = service_contracts(root)
    errors = contracts.validate_instance(topology, schema)
    errors.extend(contracts._sensitive_key_errors(topology))

    if topology.get("account_id") != storage.get("account_id"):
        errors.append("$.account_id: topology and storage authority must target the same account")

    script_names: set[str] = set()
    route_owners: dict[str, str] = {}
    page_names: set[str] = set()
    storage_by_id = storage_index(storage)

    for index, worker in enumerate(topology.get("workers", [])):
        if not isinstance(worker, dict):
            continue
        prefix = f"$.workers[{index}]"
        script = worker.get("script_name")
        service_id = worker.get("service_id")
        repository = worker.get("repository")
        if script in script_names:
            errors.append(f"{prefix}.script_name: duplicate public Worker {script!r}")
        if isinstance(script, str):
            script_names.add(script)

        contract = service_map.get(service_id)
        if contract is None:
            errors.append(f"{prefix}.service_id: no current service contract for {service_id!r}")
        else:
            if contract.get("source_repository") != repository:
                errors.append(f"{prefix}.repository: does not match service-contract source_repository")
            if contract.get("runtime", {}).get("kind") != "cloudflare-worker":
                errors.append(f"{prefix}.service_id: service contract is not a Cloudflare Worker")
            expected_meta = metadata_url(contract)
            if expected_meta and worker.get("metadata_url") != expected_meta:
                errors.append(
                    f"{prefix}.metadata_url: expected {expected_meta!r} from the service contract"
                )

        binding_names: set[str] = set()
        for binding in worker.get("service_bindings", []):
            if not isinstance(binding, dict):
                continue
            name = binding.get("binding")
            target = binding.get("service")
            if name in binding_names:
                errors.append(f"{prefix}.service_bindings: duplicate binding name {name!r}")
            if isinstance(name, str):
                binding_names.add(name)
            if target not in service_map:
                errors.append(f"{prefix}.service_bindings: unknown target service {target!r}")

        for binding in worker.get("storage_bindings", []):
            if not isinstance(binding, dict):
                continue
            name = binding.get("binding")
            if name in binding_names:
                errors.append(f"{prefix}.storage_bindings: duplicate binding name {name!r}")
            if isinstance(name, str):
                binding_names.add(name)
            if binding.get("kind") == "durable-object":
                continue
            key = (binding.get("kind"), binding.get("provider_id"))
            declared = storage_by_id.get(key)
            if declared is None:
                errors.append(f"{prefix}.storage_bindings: {key!r} is absent from storage authority")
                continue
            participants = {
                (declared.get("owner") or {}).get("service_id"),
                *{
                    consumer.get("service_id")
                    for consumer in declared.get("consumers", [])
                    if isinstance(consumer, dict)
                },
            }
            if service_id not in participants:
                errors.append(
                    f"{prefix}.storage_bindings: service {service_id!r} is neither owner nor declared consumer of {key!r}"
                )

        for route in worker.get("routes", []):
            if not isinstance(route, dict):
                continue
            pattern = route.get("pattern")
            if pattern in route_owners:
                errors.append(
                    f"{prefix}.routes: exact route {pattern!r} is also owned by {route_owners[pattern]!r}"
                )
            elif isinstance(pattern, str):
                route_owners[pattern] = str(script)

        meta = worker.get("metadata_url")
        if isinstance(meta, str):
            parsed = urlsplit(meta)
            if parsed.scheme != "https" or parsed.query or parsed.fragment:
                errors.append(f"{prefix}.metadata_url: must be bounded HTTPS without query/fragment")

    for index, project in enumerate(topology.get("pages_projects", [])):
        if not isinstance(project, dict):
            continue
        prefix = f"$.pages_projects[{index}]"
        name = project.get("project_name")
        if name in page_names:
            errors.append(f"{prefix}.project_name: duplicate Pages project {name!r}")
        if isinstance(name, str):
            page_names.add(name)
        repository = project.get("repository")
        matching = [
            contract for contract in service_map.values()
            if contract.get("source_repository") == repository
            and contract.get("runtime", {}).get("kind") == "cloudflare-pages"
        ]
        if not matching:
            errors.append(f"{prefix}.repository: no Cloudflare Pages service contract for {repository!r}")

    return {
        "schema_version": "atlas-public-cloudflare-topology/validation/v1",
        "workers": len(topology.get("workers", [])),
        "pages_projects": len(topology.get("pages_projects", [])),
        "routes": sum(len(worker.get("routes", [])) for worker in topology.get("workers", []) if isinstance(worker, dict)),
        "service_bindings": sum(len(worker.get("service_bindings", [])) for worker in topology.get("workers", []) if isinstance(worker, dict)),
        "storage_bindings": sum(len(worker.get("storage_bindings", [])) for worker in topology.get("workers", []) if isinstance(worker, dict)),
        "errors": sorted(set(errors)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = validate(args.root.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
