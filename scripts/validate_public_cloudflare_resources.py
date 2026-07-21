#!/usr/bin/env python3
"""Validate the declared public Cloudflare storage-resource registry offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from control_plane_contracts import load_json, validate_instance


def _service_owners(registry: dict[str, Any]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for entry in registry.get("repositories", []):
        if not isinstance(entry, dict):
            continue
        repository = entry.get("repository")
        if not isinstance(repository, str):
            continue
        for service_id in entry.get("service_ids", []):
            if isinstance(service_id, str):
                owners[service_id] = repository
    return owners


def validate_resource_registry(
    document: dict[str, Any],
    schema: dict[str, Any],
    estate_registry: dict[str, Any],
) -> list[str]:
    errors = list(validate_instance(document, schema))
    resources = document.get("resources", [])
    if not isinstance(resources, list):
        return sorted(errors)

    provider_keys: set[tuple[str, str]] = set()
    owner_order: list[str] = []
    service_owners = _service_owners(estate_registry)

    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            continue
        kind = resource.get("kind")
        provider_id = resource.get("provider_id")
        if isinstance(kind, str) and isinstance(provider_id, str):
            key = (kind, provider_id)
            if key in provider_keys:
                errors.append(
                    f"$.resources[{index}]: duplicate provider identity {kind}/{provider_id}"
                )
            provider_keys.add(key)

        owner = resource.get("owner", {})
        if isinstance(owner, dict):
            service_id = owner.get("service_id")
            repository = owner.get("repository")
            if isinstance(service_id, str):
                owner_order.append(service_id)
                expected_repository = service_owners.get(service_id)
                if expected_repository is None:
                    errors.append(
                        f"$.resources[{index}].owner: unknown public service_id {service_id}"
                    )
                elif repository != expected_repository:
                    errors.append(
                        f"$.resources[{index}].owner: repository does not match estate registry for {service_id}"
                    )

        consumers = resource.get("consumers", [])
        if isinstance(consumers, list):
            consumer_ids = [
                item.get("service_id")
                for item in consumers
                if isinstance(item, dict) and isinstance(item.get("service_id"), str)
            ]
            if consumer_ids != sorted(consumer_ids):
                errors.append(
                    f"$.resources[{index}].consumers: service IDs must be sorted"
                )
            if len(consumer_ids) != len(set(consumer_ids)):
                errors.append(
                    f"$.resources[{index}].consumers: service IDs must be unique"
                )
            owner_service_id = owner.get("service_id") if isinstance(owner, dict) else None
            if owner_service_id in consumer_ids:
                errors.append(
                    f"$.resources[{index}].consumers: owner must not be repeated as a consumer"
                )
            for consumer_index, consumer in enumerate(consumers):
                if not isinstance(consumer, dict):
                    continue
                service_id = consumer.get("service_id")
                repository = consumer.get("repository")
                if not isinstance(service_id, str):
                    continue
                expected_repository = service_owners.get(service_id)
                if expected_repository is None:
                    errors.append(
                        f"$.resources[{index}].consumers[{consumer_index}]: unknown public service_id {service_id}"
                    )
                elif repository != expected_repository:
                    errors.append(
                        f"$.resources[{index}].consumers[{consumer_index}]: repository does not match estate registry for {service_id}"
                    )

    if owner_order != sorted(owner_order):
        errors.append("$.resources: resources must be sorted by owner service_id")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="atlas-infra repository root",
    )
    parser.add_argument(
        "--resources",
        type=Path,
        default=Path("policy/public-cloudflare-resources.json"),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("policy/public-cloudflare-resources.schema.json"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("policy/estate-registry.json"),
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    resolve = lambda path: path if path.is_absolute() else root / path
    document = load_json(resolve(args.resources))
    schema = load_json(resolve(args.schema))
    estate_registry = load_json(resolve(args.registry))
    errors = validate_resource_registry(document, schema, estate_registry)

    report = {
        "schema_version": "atlas-public-cloudflare-resources/validation-report/v1",
        "status": "passed" if not errors else "failed",
        "resource_count": len(document.get("resources", [])),
        "errors": errors,
    }
    if args.json:
        output = resolve(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.quiet:
        print(
            f"public Cloudflare resource registry: {report['resource_count']} resources, "
            f"{len(errors)} errors"
        )
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
