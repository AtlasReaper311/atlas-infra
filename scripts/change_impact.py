#!/usr/bin/env python3
"""Render change impact from the canonical Atlas Systems estate manifest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
}


def load_json(source: str) -> dict[str, Any]:
    if source.startswith("https://"):
        request = urllib.request.Request(source, headers={"User-Agent": "atlas-change-impact/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def repo_name(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.removesuffix(".git").rstrip("/")
    if "github.com/" in cleaned:
        cleaned = cleaned.split("github.com/", 1)[1]
    parts = cleaned.split("/")
    if len(parts) < 2:
        return None
    return "/".join(parts[-2:]).lower()


def read_changed_files(path: str | None, base: str | None, head: str | None) -> list[str]:
    if path:
        return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not base or not head:
        raise ValueError("Provide --changed-files or both --base and --head")
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def classify_files(paths: list[str]) -> tuple[set[str], str]:
    categories: set[str] = set()
    for path in paths:
        lower = path.lower()
        name = Path(path).name
        if lower.startswith(".github/workflows/"):
            categories.add("pipeline")
        if name in DEPENDENCY_FILES or name.endswith(".lock"):
            categories.add("dependencies")
        if lower.startswith("docs/") or name.lower().startswith("readme") or lower.endswith(".md"):
            categories.add("documentation")
        if any(part in lower for part in ("src/", "app/", "api/", "routes/")):
            categories.add("runtime")
        if "openapi" in lower or "_meta" in lower or "schema" in lower:
            categories.add("contract")
        if "wrangler.toml" in lower or "docker" in lower or "compose" in lower:
            categories.add("deployment")
        if lower.startswith("tests/") or "/tests/" in lower:
            categories.add("tests")
    if not categories:
        categories.add("general")

    if categories <= {"documentation", "tests"}:
        risk = "low"
    elif {"contract", "runtime", "deployment"} & categories:
        risk = "high"
    else:
        risk = "medium"
    return categories, risk


def component_maps(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    components = {item["name"]: item for item in manifest.get("components", []) if item.get("name")}
    reverse: dict[str, set[str]] = defaultdict(set)
    for name, component in components.items():
        for dependency in component.get("depends_on", []):
            reverse[dependency].add(name)
    return components, reverse


def transitive_consumers(start: set[str], reverse: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    direct = set()
    for name in start:
        direct.update(reverse.get(name, set()))
    all_consumers = set(direct)
    queue = deque(direct)
    while queue:
        current = queue.popleft()
        for consumer in reverse.get(current, set()):
            if consumer not in all_consumers and consumer not in start:
                all_consumers.add(consumer)
                queue.append(consumer)
    return direct, all_consumers - direct


def recommended_checks(
    components: dict[str, dict[str, Any]],
    changed_components: set[str],
    categories: set[str],
) -> list[str]:
    checks = set()
    if "pipeline" in categories:
        checks.add("Run the estate policy workflow against the changed workflow files")
    if "dependencies" in categories:
        checks.add("Run atlas-dep-audit and compare the new SBOM with the previous report")
    if "contract" in categories:
        checks.add("Run OpenAPI and /_meta contract checks")
    if "deployment" in categories:
        checks.add("Run the deployment dry run and verify the live route after release")
    for name in changed_components:
        component = components.get(name, {})
        feeds = set(component.get("feeds", []))
        kind = component.get("kind", "")
        if kind == "worker":
            checks.add("Run Worker bundle, route, health, and /_meta checks")
        if name == "atlas-corpus" or "estate search" in feeds:
            checks.add("Run corpus search provenance and Ramone citation journeys")
        if name in {"atlas-api-public", "atlas-api-index"} or "public API" in feeds:
            checks.add("Run public API index, registry, search, and OpenAPI journeys")
        if "lab" in feeds or "portfolio" in feeds:
            checks.add("Run the Lab rendering journey")
        if "status" in feeds or name == "status":
            checks.add("Run the public status surface journey")
    return sorted(checks)


def render_report(
    repository: str,
    changed_files: list[str],
    changed_components: set[str],
    direct: set[str],
    indirect: set[str],
    categories: set[str],
    risk: str,
    checks: list[str],
) -> str:
    lines = [
        "# Atlas Systems change impact",
        "",
        f"**Repository:** `{repository}`  ",
        f"**Risk:** `{risk}`  ",
        f"**Changed files:** `{len(changed_files)}`  ",
        f"**Change classes:** {', '.join(f'`{item}`' for item in sorted(categories))}",
        "",
        "## Changed components",
        "",
    ]
    lines.extend(f"- `{name}`" for name in sorted(changed_components))
    if not changed_components:
        lines.append("- No component in the manifest currently maps to this repository")

    lines.extend(["", "## Direct consumers", ""])
    lines.extend(f"- `{name}`" for name in sorted(direct))
    if not direct:
        lines.append("- None declared")

    lines.extend(["", "## Indirect consumers", ""])
    lines.extend(f"- `{name}`" for name in sorted(indirect))
    if not indirect:
        lines.append("- None declared")

    lines.extend(["", "## Required verification", ""])
    lines.extend(f"- {item}" for item in checks)
    if not checks:
        lines.append("- Run the repository's normal test and validation suite")

    lines.extend(["", "## Changed paths", ""])
    lines.extend(f"- `{path}`" for path in changed_files[:100])
    if len(changed_files) > 100:
        lines.append(f"- `{len(changed_files) - 100}` additional paths omitted")

    lines.extend(
        [
            "",
            "## Deployment order",
            "",
            "1. Deploy the changed component.",
            "2. Run its direct contract checks.",
            "3. Run journeys covering direct consumers.",
            "4. Watch the affected SLO and notification surfaces before considering the change complete.",
            "",
            "This report is derived from `estate.manifest.json`. Missing dependency edges remain visible as missing impact, not guessed relationships.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--changed-files")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--output", default="change-impact.md")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    changed_files = read_changed_files(args.changed_files, args.base, args.head)
    categories, risk = classify_files(changed_files)
    components, reverse = component_maps(manifest)
    target_repo = repo_name(args.repository)
    changed_components = {
        name
        for name, component in components.items()
        if repo_name(component.get("repo")) == target_repo
    }
    direct, indirect = transitive_consumers(changed_components, reverse)
    checks = recommended_checks(components, changed_components, categories)
    report = render_report(
        args.repository,
        changed_files,
        changed_components,
        direct,
        indirect,
        categories,
        risk,
        checks,
    )
    Path(args.output).write_text(report, encoding="utf-8")
    print(report)

    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"risk={risk}\n")
            handle.write(f"affected_count={len(direct) + len(indirect)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
