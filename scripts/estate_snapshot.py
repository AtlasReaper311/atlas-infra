#!/usr/bin/env python3
"""Generate a deterministic Atlas estate snapshot from current authority.

Classification comes from the existing public-repository projection. GitHub
owner listing and atlas-api-public topology are observation inputs only. The
generator reports missing or contradictory authority instead of inventing or
reconciling values. It does not observe deployment, runtime, or live state.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from control_plane_contracts import sha256_hex, validate_instance
from github_api import GitHubClient
import estate_repo_diff
import public_repository_classifications

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "policy" / "estate-registry.json"
DEFAULT_SUPPLEMENT = ROOT / "policy" / "public-assurance-repositories.json"
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"
DEFAULT_SCHEMA = ROOT / "policy" / "estate-snapshot.schema.json"
DEFAULT_JSON = ROOT / "reports" / "estate-snapshot.json"
DEFAULT_MARKDOWN = ROOT / "reports" / "estate-snapshot.md"
SCHEMA_VERSION = "atlas-estate-snapshot/snapshot/v1"
AUTHORITY = "AtlasReaper311/atlas-infra"
DEFAULT_OWNER = "AtlasReaper311"
GITHUB_ROUTE = "github_rest:/user/repos?affiliation=owner&visibility=all"
UNKNOWN = "UNKNOWN / NOT OBSERVED"
NOT_APPLICABLE = "NOT APPLICABLE"
EVIDENCE_BOUNDARY = {
    "delivery_stage_claimed": "SOURCE",
    "later_stage_observation": UNKNOWN,
    "does_not_prove": [
        "DEPLOYMENT OBSERVED",
        "DEPLOYED",
        "RUNTIME VERIFIED",
        "LIVE VERIFIED",
    ],
}


class EstateSnapshotError(ValueError):
    """Raised when snapshot inputs are malformed or projection authority is bypassed."""


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EstateSnapshotError(f"JSON object required: {path}")
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def validate_generated_at(value: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EstateSnapshotError("generated_at must be a UTC RFC 3339 value ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise EstateSnapshotError("generated_at is not a valid calendar timestamp") from error
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def resolve_source_commit(explicit: str | None, root: Path) -> str:
    if explicit:
        return explicit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN
    commit = result.stdout.strip()
    return commit if commit else UNKNOWN


def relative_source(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def github_full_name(value: str | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").casefold()
    if host in {"github.com", "www.github.com"}:
        parts = [
            part
            for part in parsed.path.removesuffix(".git").strip("/").split("/")
            if part
        ]
        if len(parts) < 2:
            return None
        owner, name = parts[0], parts[1]
    else:
        parts = [part for part in raw.removesuffix(".git").strip("/").split("/") if part]
        if len(parts) != 2:
            return None
        owner, name = parts
    if owner.casefold() != DEFAULT_OWNER.casefold():
        return None
    return f"{DEFAULT_OWNER}/{name}"


def load_github_observation(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    payload = load_object(path)
    route = payload.get("route")
    if not isinstance(route, str) or not route.strip():
        raise EstateSnapshotError("GitHub observation file must declare route")
    owner = payload.get("owner")
    if owner != DEFAULT_OWNER:
        raise EstateSnapshotError("GitHub observation owner must be AtlasReaper311")
    values = payload.get("repositories")
    if not isinstance(values, list):
        raise EstateSnapshotError("GitHub observation repositories must be a list")
    return _github_map(values), route.strip()


def list_owned_github_repositories(token: str) -> dict[str, dict[str, Any]]:
    return estate_repo_diff.list_owned_repositories(GitHubClient(token), DEFAULT_OWNER)


def discover_github(token: str) -> dict[str, dict[str, Any]]:
    return list_owned_github_repositories(token)


def _github_map(values: list[Any]) -> dict[str, dict[str, Any]]:
    repositories: dict[str, dict[str, Any]] = {}
    for item in values:
        if not isinstance(item, dict):
            raise EstateSnapshotError("GitHub observation entry must be an object")
        name = item.get("repository")
        if not isinstance(name, str) or not name.startswith(f"{DEFAULT_OWNER}/"):
            raise EstateSnapshotError("GitHub observation repository identity is malformed")
        if name in repositories:
            raise EstateSnapshotError(f"duplicate GitHub observation repository: {name}")
        repositories[name] = {
            "repository": name,
            "default_branch": item.get("default_branch"),
            "archived": bool(item.get("archived")),
            "private": bool(item.get("private")),
            "visibility": item.get("visibility"),
        }
    return repositories


def load_presentation(path: Path) -> dict[str, Any]:
    manifest = load_object(path)
    components = manifest.get("components")
    if "components" in manifest and not isinstance(components, list):
        raise EstateSnapshotError("presentation components must be a list")
    return manifest


def verify_projection(
    registry: dict[str, Any],
    supplement: dict[str, Any],
    committed: dict[str, Any],
) -> dict[str, Any]:
    built = public_repository_classifications.build_projection(registry, supplement)
    if committed != built:
        raise EstateSnapshotError(
            "classification projection differs from authoritative Atlas Infra inputs"
        )
    return built


def _finding(kind: str, subject: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "subject": subject, "detail": detail}


def _topology_component(item: dict[str, Any]) -> dict[str, Any]:
    public_surface = item.get("public_surface")
    lifecycle = item.get("lifecycle")
    return {
        "name": item.get("name"),
        "kind": item.get("kind"),
        "layer": item.get("layer"),
        "public_surface": public_surface if isinstance(public_surface, str) else None,
        "presentation_lifecycle": lifecycle if isinstance(lifecycle, str) else None,
    }


def build_snapshot(
    *,
    registry: dict[str, Any],
    supplement: dict[str, Any],
    projection: dict[str, Any],
    github_repositories: dict[str, dict[str, Any]] | None,
    github_route: str,
    presentation: dict[str, Any] | None,
    presentation_source: str,
    generated_at: str,
    source_commit: str,
) -> dict[str, Any]:
    built = verify_projection(registry, supplement, projection)
    classified = {item["repository"]: item for item in built["repositories"]}
    missing: list[dict[str, str]] = []
    contradictions: list[dict[str, str]] = []

    approved_count = registry.get("approved_repository_count")
    runtime_count = len(registry.get("repositories", []))
    if isinstance(approved_count, int) and approved_count != runtime_count:
        contradictions.append(
            _finding(
                "registry-count-mismatch",
                "policy/estate-registry.json",
                "approved_repository_count does not equal the runtime registry list length; "
                "the snapshot count is derived from the list, not the stored total.",
            )
        )

    topology_by_repo: dict[str, list[dict[str, Any]]] = {}
    repository_less: list[dict[str, Any]] = []
    if presentation is not None:
        repositories_field = presentation.get("repositories")
        if isinstance(repositories_field, list) and repositories_field:
            contradictions.append(
                _finding(
                    "presentation-repositories-not-authority",
                    presentation_source,
                    "presentation repositories array is not classification authority and was not used as such.",
                )
            )
        for item in presentation.get("components") or []:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            repo_name = github_full_name(item.get("repo") if isinstance(item.get("repo"), str) else None)
            component = _topology_component(item)
            if not all(isinstance(component[key], str) for key in ("name", "kind", "layer")):
                continue
            if repo_name is None:
                repository_less.append(
                    {
                        "name": component["name"],
                        "kind": component["kind"],
                        "layer": component["layer"],
                        "public_surface": component["public_surface"],
                        "classification": NOT_APPLICABLE,
                    }
                )
                continue
            topology_by_repo.setdefault(repo_name, []).append(component)
            if repo_name not in classified:
                missing.append(
                    _finding(
                        "presentation-repo-without-classification",
                        repo_name,
                        "topology component names a repository that has no Atlas Infra classification.",
                    )
                )

    github_observed = github_repositories is not None
    if github_observed:
        github_names = set(github_repositories)
        for name in sorted(github_names - set(classified)):
            missing.append(
                _finding(
                    "github-without-classification",
                    name,
                    "GitHub-owned repository has no Atlas Infra classification.",
                )
            )
        for name in sorted(set(classified) - github_names):
            missing.append(
                _finding(
                    "classification-without-github",
                    name,
                    "classified repository was not present in the GitHub owner listing.",
                )
            )

    repositories: list[dict[str, Any]] = []
    for item in built["repositories"]:
        name = item["repository"]
        github_entry: dict[str, Any]
        if not github_observed:
            github_entry = {"observation": UNKNOWN}
        elif name in github_repositories:
            observed = github_repositories[name]
            github_entry = {
                "observation": "observed",
                "visibility": observed.get("visibility")
                if isinstance(observed.get("visibility"), str)
                else UNKNOWN,
                "private": bool(observed.get("private")),
                "archived": bool(observed.get("archived")),
                "default_branch": observed.get("default_branch")
                if isinstance(observed.get("default_branch"), str)
                else None,
            }
            if github_entry["private"] and item["scope"] == "public":
                contradictions.append(
                    _finding(
                        "github-private-public-scope",
                        name,
                        "GitHub observation is private while classification scope is public.",
                    )
                )
            archived = github_entry["archived"]
            lifecycle_archived = item["lifecycle"] == "archived"
            if archived != lifecycle_archived:
                contradictions.append(
                    _finding(
                        "github-archived-lifecycle-mismatch",
                        name,
                        "GitHub archived state disagrees with classification lifecycle.",
                    )
                )
        else:
            github_entry = {"observation": UNKNOWN}

        if presentation is None:
            topology_entry: dict[str, Any] = {"observation": UNKNOWN, "components": []}
        elif name in topology_by_repo:
            components = sorted(topology_by_repo[name], key=lambda value: value["name"])
            topology_entry = {"observation": "observed", "components": components}
            for component in components:
                presented = component["presentation_lifecycle"]
                if presented is not None and presented != item["lifecycle"]:
                    contradictions.append(
                        _finding(
                            "presentation-lifecycle-mismatch",
                            f"{name}:{component['name']}",
                            "presentation lifecycle is not classification authority and disagrees with Atlas Infra classification.",
                        )
                    )
        else:
            topology_entry = {"observation": NOT_APPLICABLE, "components": []}

        repositories.append(
            {
                "repository": name,
                "lifecycle": item["lifecycle"],
                "scope": item["scope"],
                "provenance": item["provenance"],
                "runtime_service": item["runtime_service"],
                "github": github_entry,
                "topology": topology_entry,
            }
        )

    missing.sort(key=lambda item: (item["kind"], item["subject"]))
    contradictions.sort(key=lambda item: (item["kind"], item["subject"]))
    repository_less.sort(key=lambda item: item["name"])

    estate = {
        "classified_repository_count": len(repositories),
        "github_observed_repository_count": len(github_repositories)
        if github_observed
        else UNKNOWN,
        "repositories": repositories,
        "repository_less_topology": repository_less,
        "missing_authority": missing,
        "contradictory_authority": contradictions,
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "observation": {
            "generated_at": validate_generated_at(generated_at),
            "source_commit": source_commit,
            "github": {
                "status": "observed" if github_observed else UNKNOWN,
                "route": github_route,
                "owner": DEFAULT_OWNER,
            },
            "presentation": {
                "status": "observed" if presentation is not None else UNKNOWN,
                "source": presentation_source,
            },
            "classification": {
                "runtime_registry": "policy/estate-registry.json",
                "public_non_runtime": "policy/public-assurance-repositories.json",
                "projection": "policy/public-repository-classifications.json",
                "source_fingerprint": built["source_fingerprint"],
            },
        },
        "estate": estate,
        "content_fingerprint": "sha256:" + sha256_hex(estate),
    }
    return snapshot


def render_json(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(snapshot: dict[str, Any]) -> str:
    observation = snapshot["observation"]
    estate = snapshot["estate"]
    github_count = estate["github_observed_repository_count"]
    github_count_text = (
        f"**{github_count}**" if isinstance(github_count, int) else f"`{github_count}`"
    )
    lines = [
        "# Atlas Systems estate snapshot",
        "",
        f"Authority: `{snapshot['authority']}`",
        "",
        "This snapshot is generated from Atlas Infra classification authority plus optional GitHub and topology observation. It does not prove `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`. Missing later evidence remains `UNKNOWN / NOT OBSERVED`.",
        "",
        "## Observation",
        "",
        f"- Generated at: `{observation['generated_at']}`",
        f"- Source commit: `{observation['source_commit']}`",
        f"- GitHub: `{observation['github']['status']}` via `{observation['github']['route']}`",
        f"- Presentation: `{observation['presentation']['status']}` from `{observation['presentation']['source']}`",
        f"- Classification fingerprint: `{observation['classification']['source_fingerprint']}`",
        f"- Content fingerprint: `{snapshot['content_fingerprint']}`",
        "",
        "## Counts",
        "",
        f"- Classified repositories: **{estate['classified_repository_count']}** (derived from the classification projection, not a hand-maintained total)",
        f"- GitHub observed repositories: {github_count_text}",
        f"- Missing authority findings: **{len(estate['missing_authority'])}**",
        f"- Contradictory authority findings: **{len(estate['contradictory_authority'])}**",
        "",
        "## Missing authority",
        "",
    ]
    if estate["missing_authority"]:
        for item in estate["missing_authority"]:
            lines.append(f"- `{item['kind']}` `{item['subject']}`: {item['detail']}")
    else:
        lines.append("None.")
    lines.extend(["", "## Contradictory authority", ""])
    if estate["contradictory_authority"]:
        for item in estate["contradictory_authority"]:
            lines.append(f"- `{item['kind']}` `{item['subject']}`: {item['detail']}")
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Classified repositories",
            "",
            "| Repository | Lifecycle | Scope | Provenance | Runtime | GitHub | Topology |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in estate["repositories"]:
        runtime = "yes" if item["runtime_service"] else "no"
        github_status = item["github"]["observation"]
        topology_status = item["topology"]["observation"]
        lines.append(
            f"| `{item['repository']}` | `{item['lifecycle']}` | `{item['scope']}` | "
            f"`{item['provenance']}` | {runtime} | `{github_status}` | `{topology_status}` |"
        )
    lines.extend(["", "## Repository-less topology", ""])
    if estate["repository_less_topology"]:
        for item in estate["repository_less_topology"]:
            lines.append(
                f"- `{item['name']}` (`{item['kind']}`, `{item['layer']}`): classification `{item['classification']}`"
            )
    else:
        lines.append("None observed, or presentation was `UNKNOWN / NOT OBSERVED`.")
    boundary = estate["evidence_boundary"]
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            f"- Delivery stage claimed: `{boundary['delivery_stage_claimed']}`",
            f"- Later stage observation: `{boundary['later_stage_observation']}`",
            "- Does not prove: "
            + ", ".join(f"`{item}`" for item in boundary["does_not_prove"]),
            "",
        ]
    )
    return "\n".join(lines)


def validate_snapshot(snapshot: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = validate_instance(snapshot, schema)
    if errors:
        raise EstateSnapshotError(errors[0])
    expected = "sha256:" + sha256_hex(snapshot["estate"])
    if snapshot.get("content_fingerprint") != expected:
        raise EstateSnapshotError("content fingerprint does not match deterministic estate content")


def deterministic_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(snapshot))
    clone.get("observation", {}).pop("generated_at", None)
    return clone


def write_outputs(snapshot: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(render_json(snapshot), encoding="utf-8")
    markdown_path.write_text(render_markdown(snapshot), encoding="utf-8")


def build_from_paths(
    *,
    root: Path,
    registry_path: Path,
    supplement_path: Path,
    projection_path: Path,
    github_observation: Path | None,
    discover_github: bool,
    token_env: str,
    presentation_path: Path | None,
    generated_at: str,
    source_commit: str | None,
) -> dict[str, Any]:
    if github_observation is not None and discover_github:
        raise EstateSnapshotError("use either --github-observation or --discover-github, not both")
    registry = load_object(registry_path)
    supplement = load_object(supplement_path)
    projection = load_object(projection_path)
    github_repositories: dict[str, dict[str, Any]] | None = None
    github_route = GITHUB_ROUTE
    if github_observation is not None:
        github_repositories, recorded_route = load_github_observation(github_observation)
        github_route = recorded_route or (
            f"recorded-observation:{relative_source(github_observation, root)}"
        )
    elif discover_github:
        token = os.environ.get(token_env, "") or os.environ.get("GITHUB_TOKEN", "")
        github_repositories = list_owned_github_repositories(token)
    presentation = load_presentation(presentation_path) if presentation_path else None
    presentation_source = (
        relative_source(presentation_path, root) if presentation_path else UNKNOWN
    )
    return build_snapshot(
        registry=registry,
        supplement=supplement,
        projection=projection,
        github_repositories=github_repositories,
        github_route=github_route,
        presentation=presentation,
        presentation_source=presentation_source,
        generated_at=generated_at,
        source_commit=resolve_source_commit(source_commit, root),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or verify the Atlas estate snapshot from current authority."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--github-observation", type=Path)
    parser.add_argument("--discover-github", action="store_true")
    parser.add_argument("--token-env", default="ATLAS_ESTATE_READ_TOKEN")
    parser.add_argument("--presentation", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-at", type=str)
    parser.add_argument("--source-commit", type=str)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generated_at = args.generated_at or utc_now()
        snapshot = build_from_paths(
            root=args.root,
            registry_path=args.registry,
            supplement_path=args.supplement,
            projection_path=args.projection,
            github_observation=args.github_observation,
            discover_github=args.discover_github,
            token_env=args.token_env,
            presentation_path=args.presentation,
            generated_at=generated_at,
            source_commit=args.source_commit,
        )
        schema = load_object(args.schema)
        validate_snapshot(snapshot, schema)
        if not args.discover_github:
            second = build_from_paths(
                root=args.root,
                registry_path=args.registry,
                supplement_path=args.supplement,
                projection_path=args.projection,
                github_observation=args.github_observation,
                discover_github=False,
                token_env=args.token_env,
                presentation_path=args.presentation,
                generated_at=snapshot["observation"]["generated_at"],
                source_commit=snapshot["observation"]["source_commit"],
            )
            if deterministic_payload(snapshot) != deterministic_payload(second):
                raise EstateSnapshotError(
                    "snapshot is not deterministic for identical inputs"
                )
        if args.check:
            if args.json_out.is_file() or args.markdown_out.is_file():
                if not args.json_out.is_file() or not args.markdown_out.is_file():
                    raise EstateSnapshotError("snapshot outputs are incomplete")
                existing = json.loads(args.json_out.read_text(encoding="utf-8"))
                if deterministic_payload(existing) != deterministic_payload(snapshot):
                    raise EstateSnapshotError(
                        "committed snapshot JSON differs from authoritative inputs"
                    )
                existing_markdown = args.markdown_out.read_text(encoding="utf-8")
                if existing_markdown != render_markdown(existing):
                    raise EstateSnapshotError(
                        "committed snapshot Markdown is not generated from the JSON model"
                    )
            print(
                "estate snapshot verified: "
                f"{snapshot['estate']['classified_repository_count']} classified repositories "
                f"({snapshot['content_fingerprint']})"
            )
            return 0
        write_outputs(snapshot, args.json_out, args.markdown_out)
        print(
            f"estate snapshot written: {snapshot['estate']['classified_repository_count']} "
            f"classified repositories ({snapshot['content_fingerprint']})"
        )
    except (
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        public_repository_classifications.ClassificationProjectionError,
    ) as error:
        print(f"estate snapshot failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
