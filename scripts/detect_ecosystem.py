#!/usr/bin/env python3
"""Detect supported Dependabot ecosystems without cloning a repository."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

from github_api import GitHubClient, quote_path, quote_ref


MANIFESTS = {
    "npm": {"package.json"},
    "pip": {"requirements.txt", "pyproject.toml", "setup.py"},
    "cargo": {"Cargo.toml"},
}


@dataclass(frozen=True)
class Detection:
    ecosystem: str
    directories: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"package_ecosystem": self.ecosystem, "directories": list(self.directories)}


def _contents(client: GitHubClient, repository: str, path: str, ref: str) -> list[dict[str, Any]]:
    encoded_path = quote_path(path)
    encoded_ref = quote_ref(ref)
    suffix = f"/{encoded_path}" if encoded_path else ""
    payload = client.get(f"/repos/{repository}/contents{suffix}?ref={encoded_ref}")
    if not isinstance(payload, list):
        raise RuntimeError(f"expected a directory listing for {repository}:{path or '/'}")
    return payload


def detect_ecosystem_locations(
    client: GitHubClient, repository: str, default_branch: str | None = None
) -> list[Detection]:
    if default_branch is None:
        metadata = client.get(f"/repos/{repository}")
        default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise RuntimeError(f"repository has no default branch: {repository}")

    root = _contents(client, repository, "", default_branch)
    locations: dict[str, set[str]] = {name: set() for name in MANIFESTS}
    root_files = {item.get("name") for item in root if item.get("type") == "file"}
    for ecosystem, manifests in MANIFESTS.items():
        if root_files & manifests:
            locations[ecosystem].add("/")

    if "Dockerfile" in root_files:
        locations["docker"] = {"/"}

    directories = sorted(
        item["name"]
        for item in root
        if item.get("type") == "dir" and item.get("name") not in {".git", ".github"}
    )
    for directory in directories:
        children = _contents(client, repository, directory, default_branch)
        child_files = {item.get("name") for item in children if item.get("type") == "file"}
        for ecosystem, manifests in MANIFESTS.items():
            if child_files & manifests:
                locations[ecosystem].add(f"/{directory}")

    github_dir = next(
        (item for item in root if item.get("type") == "dir" and item.get("name") == ".github"),
        None,
    )
    if github_dir is not None:
        github_children = _contents(client, repository, ".github", default_branch)
        if any(item.get("type") == "dir" and item.get("name") == "workflows" for item in github_children):
            workflows = _contents(client, repository, ".github/workflows", default_branch)
            if any(
                item.get("type") == "file"
                and str(item.get("name", "")).lower().endswith((".yml", ".yaml"))
                for item in workflows
            ):
                locations["github-actions"] = {"/"}

    return [
        Detection(ecosystem, tuple(sorted(paths)))
        for ecosystem, paths in sorted(locations.items())
        if paths
    ]


def detect_ecosystems(
    client: GitHubClient, repository: str, default_branch: str | None = None
) -> list[str]:
    return [item.ecosystem for item in detect_ecosystem_locations(client, repository, default_branch)]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Repository in owner/name form")
    parser.add_argument("--ref", help="Default branch or another branch to inspect")
    parser.add_argument("--token-env", default="ATLAS_ESTATE_READ_TOKEN")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        client = GitHubClient(os.environ.get(args.token_env, ""))
        detections = detect_ecosystem_locations(client, args.repository, args.ref)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ecosystem detection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps([item.as_dict() for item in detections], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
