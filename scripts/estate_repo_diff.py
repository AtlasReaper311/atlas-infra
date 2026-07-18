#!/usr/bin/env python3
"""Reconcile repositories owned on GitHub with the Atlas estate registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github_api import GitHubClient


DEFAULT_OWNER = "AtlasReaper311"
DEFAULT_REGISTRY = Path("policy/estate-registry.json")
TEMP_ROOT = Path(tempfile.gettempdir())
DEFAULT_MARKDOWN = TEMP_ROOT / "estate-repo-diff.md"
DEFAULT_JSON = TEMP_ROOT / "estate-repo-diff.json"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        raise ValueError("estate registry repositories must be a list")
    return payload


def registry_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in registry["repositories"]:
        if not isinstance(item, dict) or not isinstance(item.get("repository"), str):
            raise ValueError("each estate registry entry must declare repository")
        name = item["repository"]
        if name in result:
            raise ValueError(f"duplicate estate registry repository: {name}")
        result[name] = item
    return result


def list_owned_repositories(client: GitHubClient, owner: str) -> dict[str, dict[str, Any]]:
    if not client.token:
        raise RuntimeError(
            "an authenticated token is required to reconcile public and private repositories"
        )
    payload = client.paginate(
        "/user/repos?affiliation=owner&visibility=all&sort=full_name&direction=asc"
    )
    repositories: dict[str, dict[str, Any]] = {}
    for item in payload:
        item_owner = item.get("owner", {}).get("login")
        full_name = item.get("full_name")
        if item_owner != owner or not isinstance(full_name, str):
            continue
        repositories[full_name] = {
            "repository": full_name,
            "default_branch": item.get("default_branch"),
            "archived": bool(item.get("archived")),
            "private": bool(item.get("private")),
            "visibility": item.get("visibility"),
            "id": item.get("id"),
        }
    return repositories


def reconcile(
    registry: dict[str, Any], github_repositories: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    declared = registry_map(registry)
    github_names = set(github_repositories)
    registry_names = set(declared)
    matches = []
    for name in sorted(github_names & registry_names, key=str.casefold):
        matches.append(
            {
                **github_repositories[name],
                "lifecycle": declared[name].get("lifecycle"),
                "scope": declared[name].get("scope"),
                "provenance": declared[name].get("provenance"),
                "runtime_service": declared[name].get("runtime_service"),
            }
        )
    stable = {
        "github_only": sorted(github_names - registry_names, key=str.casefold),
        "registry_only": sorted(registry_names - github_names, key=str.casefold),
        "matches": matches,
        "registry_reviewed_at": registry.get("reviewed_at"),
        "registry_digest": hashlib.sha256(canonical_bytes(registry)).hexdigest(),
    }
    stable["reconciliation_digest"] = hashlib.sha256(canonical_bytes(stable)).hexdigest()
    return stable


def render_markdown(result: dict[str, Any], owner: str) -> str:
    def names_section(title: str, names: list[str], meaning: str) -> list[str]:
        lines = [f"## {title}", "", meaning, ""]
        if names:
            lines.extend(f"- `{name}`" for name in names)
        else:
            lines.append("None.")
        lines.append("")
        return lines

    lines = [
        "# Estate repository reconciliation",
        "",
        f"Owner: `{owner}`",
        "",
        f"Reconciliation digest: `{result['reconciliation_digest']}`",
        "",
    ]
    lines.extend(
        names_section(
            "On GitHub but absent from the registry",
            result["github_only"],
            "These repositories are excluded from rollout until they are classified and approved.",
        )
    )
    lines.extend(
        names_section(
            "In the registry but absent from GitHub",
            result["registry_only"],
            "Review these entries for rename, deletion, or token access problems.",
        )
    )
    lines.extend(
        [
            "## Confirmed in GitHub and the registry",
            "",
            "| Repository | Lifecycle | Visibility | Default branch | Archived on GitHub |",
            "|---|---|---|---|---|",
        ]
    )
    for item in result["matches"]:
        archived = "yes" if item["archived"] else "no"
        lines.append(
            f"| `{item['repository']}` | `{item['lifecycle']}` | "
            f"`{item['visibility']}` | `{item['default_branch']}` | {archived} |"
        )
    lines.extend(
        [
            "",
            f"Confirmed: {len(result['matches'])}",
            "",
            "This report changes no GitHub or registry state.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(result: dict[str, Any], owner: str, markdown: Path, json_path: Path) -> None:
    payload = {
        "schema_version": "atlas-dependabot/reconciliation/v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "owner": owner,
        **result,
    }
    markdown.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(render_markdown(payload, owner), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--token-env", default="ATLAS_ESTATE_READ_TOKEN")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        token = os.environ.get(args.token_env, "")
        registry = load_registry(args.registry)
        result = reconcile(registry, list_owned_repositories(GitHubClient(token), args.owner))
        write_reports(result, args.owner, args.output, args.json_output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"estate repository reconciliation failed: {error}", file=sys.stderr)
        return 2
    print(args.output.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
