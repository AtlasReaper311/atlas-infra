#!/usr/bin/env python3
"""Validate ADR scope and emit deterministic ADR-to-runtime relationships.

The Markdown ADR remains the only decision authority. This parser reads the
existing TOML frontmatter, validates declared scope against current Atlas Infra
public authorities, and emits the Wave 3 relationship contract. No network
access is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from datetime import date as date_type
from pathlib import Path
from typing import Any

import control_plane_contracts as base
import wave3_contracts as wave3

ADR_ID = re.compile(r"^ADR-[0-9]{4}$")
TITLE = re.compile(r"^# (ADR-[0-9]{4}): (.+)$", re.MULTILINE)
FRONTMATTER = "+++"
STATUSES = {"proposed", "accepted", "superseded"}
VISIBILITY = {"public", "internal", "restricted-metadata"}
SCOPE_KEYS = ("repositories", "services", "contracts", "policies")
SKIP = {"README.md", "TEMPLATE.md"}


class AdrTraceError(ValueError):
    pass


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER:
        raise AdrTraceError("missing +++ frontmatter opening delimiter")
    for position in range(1, len(lines)):
        if lines[position].strip() == FRONTMATTER:
            return "\n".join(lines[1:position]), "\n".join(lines[position + 1 :]).strip()
    raise AdrTraceError("frontmatter opened but never closed")


def _string_list(meta: dict[str, Any], key: str) -> list[str]:
    value = meta.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AdrTraceError(f"frontmatter '{key}' must be an array of strings")
    if len(value) > 50:
        raise AdrTraceError(f"frontmatter '{key}' exceeds 50 entries")
    if len(value) != len(set(value)):
        raise AdrTraceError(f"frontmatter '{key}' must not contain duplicates")
    return sorted(value)


def parse_adr(path: Path) -> dict[str, Any]:
    block, body = split_frontmatter(path.read_text(encoding="utf-8"))
    try:
        meta = tomllib.loads(block)
    except tomllib.TOMLDecodeError as error:
        raise AdrTraceError(f"frontmatter is not valid TOML ({error})") from error

    adr_id = meta.get("id")
    if not isinstance(adr_id, str) or not ADR_ID.fullmatch(adr_id):
        raise AdrTraceError("frontmatter 'id' must match ADR-NNNN")
    status = meta.get("status")
    if status not in STATUSES:
        raise AdrTraceError(f"frontmatter 'status' must be one of {sorted(STATUSES)}")
    raw_date = meta.get("date")
    if isinstance(raw_date, date_type):
        date = raw_date.isoformat()
    elif isinstance(raw_date, str):
        try:
            date = date_type.fromisoformat(raw_date).isoformat()
        except ValueError as error:
            raise AdrTraceError("frontmatter 'date' must be a valid ISO date") from error
    else:
        raise AdrTraceError("frontmatter 'date' must be an ISO date")

    supersedes = meta.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes, str) or not ADR_ID.fullmatch(supersedes):
            raise AdrTraceError("frontmatter 'supersedes' must match ADR-NNNN")
        if supersedes == adr_id:
            raise AdrTraceError("an ADR cannot supersede itself")

    slug = meta.get("slug")
    stem = path.stem
    if stem != adr_id and not stem.startswith(f"{adr_id}-"):
        if not isinstance(slug, str) or slug != stem:
            raise AdrTraceError(
                "legacy ADR filename requires frontmatter 'slug' equal to the filename stem"
            )

    match = TITLE.search(body)
    if not match or match.group(1) != adr_id:
        raise AdrTraceError("ADR body must contain an H1 matching its ADR id")

    visibility = meta.get("visibility")
    if visibility not in VISIBILITY:
        raise AdrTraceError(
            f"frontmatter 'visibility' must be one of {sorted(VISIBILITY)}"
        )

    affects = {key: _string_list(meta, key) for key in SCOPE_KEYS}
    adr = {
        "id": adr_id,
        "path": path.as_posix(),
        "status": status,
        "date": date,
        "title": match.group(2).strip(),
    }
    if supersedes:
        adr["supersedes"] = supersedes
    return {"adr": adr, "affects": affects, "visibility": visibility}


def authorities(root: Path) -> dict[str, set[str]]:
    projection = base.load_json(root / "policy" / "public-repository-classifications.json")
    repositories = {
        item["repository"]
        for item in projection.get("repositories", [])
        if isinstance(item, dict) and isinstance(item.get("repository"), str)
    }

    registry = base.load_json(root / "policy" / "estate-registry.json")
    services: set[str] = set()
    for item in registry.get("repositories", []):
        if not isinstance(item, dict):
            continue
        for service_id in item.get("service_ids", []):
            if isinstance(service_id, str):
                services.add(service_id)

    contracts: set[str] = set()
    for path in sorted((root / "contracts" / "v1").rglob("*.schema.json")):
        try:
            schema = base.load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if isinstance(version, str):
            contracts.add(version)

    policies = {
        path.relative_to(root).as_posix()
        for path in sorted((root / "policy").rglob("*"))
        if path.is_file()
    }
    return {
        "repositories": repositories,
        "services": services,
        "contracts": contracts,
        "policies": policies,
    }


def scope_errors(parsed: dict[str, Any], allowed: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for key in SCOPE_KEYS:
        for value in parsed["affects"][key]:
            if value not in allowed[key]:
                errors.append(f"{parsed['adr']['id']}: unknown public {key[:-1]} reference {value!r}")
    return errors


def relationship(parsed: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    instance = {
        "schema_version": "atlas-control-plane/adr-runtime-relationship/v1",
        "relationship_id": "",
        "adr": parsed["adr"],
        "affects": parsed["affects"],
        "visibility": parsed["visibility"],
    }
    instance["relationship_id"] = base.calculate_fingerprint(
        "adr-runtime-relationship", instance, rules
    )
    return instance


def build_index(root: Path) -> tuple[dict[str, Any], list[str]]:
    allowed = authorities(root)
    rules = wave3.load_rules(root)
    schema = base.load_json(
        root / "contracts" / "v1" / "wave3" / "adr-runtime-relationship.schema.json"
    )
    errors: list[str] = []
    relationships: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for path in sorted((root / "docs" / "adrs").glob("*.md")):
        if path.name in SKIP:
            continue
        relative = path.relative_to(root)
        try:
            parsed = parse_adr(relative if False else path)
            parsed["adr"]["path"] = relative.as_posix()
        except (AdrTraceError, OSError) as error:
            errors.append(f"{relative.as_posix()}: {error}")
            continue
        adr_id = parsed["adr"]["id"]
        if adr_id in seen_ids:
            errors.append(f"{adr_id}: duplicate ADR id")
            continue
        seen_ids.add(adr_id)
        errors.extend(scope_errors(parsed, allowed))
        instance = relationship(parsed, rules)
        instance_errors = base.validate_instance(instance, schema)
        instance_errors.extend(
            wave3.semantic_errors("adr-runtime-relationship.schema.json", instance, rules)
        )
        errors.extend(f"{adr_id}: {item}" for item in instance_errors)
        relationships.append(instance)

    relationships.sort(key=lambda item: item["adr"]["id"])
    return {
        "schema_version": "atlas-control-plane/adr-runtime-index/v1",
        "relationships": relationships,
    }, sorted(errors)


def canonical_bytes(value: Any) -> bytes:
    return (base.canonical_json(value) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, default=Path.cwd())

    emit = sub.add_parser("emit")
    emit.add_argument("--root", type=Path, default=Path.cwd())
    emit.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    index, errors = build_index(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "emit":
        args.output.write_bytes(canonical_bytes(index))
    else:
        print(f"ADR traceability: PASS ({len(index['relationships'])} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
