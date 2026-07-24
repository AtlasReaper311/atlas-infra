#!/usr/bin/env python3
"""Build a read-only GitHub conformance scoreboard for public Atlas repositories."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from github_api import GitHubApiError, GitHubClient, quote_path, quote_ref

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"
SCHEMA_VERSION = "atlas-github-conformance-scoreboard/report/v1"
AUTHORITY = "AtlasReaper311/atlas-infra"
GLOBAL_DEFAULTS_REPOSITORY = "AtlasReaper311/.github"


class ScoreboardError(RuntimeError):
    """Raised when local scoreboard inputs are malformed."""


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    label: str
    status: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.check_id,
            "label": self.label,
            "status": self.status,
            "message": self.message,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_projection(path: Path) -> dict[str, Any]:
    projection = load_json(path)
    if not isinstance(projection, dict):
        raise ScoreboardError("repository projection root must be an object")
    if projection.get("schema_version") != "atlas-public-repository-classifications/projection/v1":
        raise ScoreboardError("unexpected repository projection schema_version")
    if projection.get("authority") != AUTHORITY:
        raise ScoreboardError("repository projection authority must be Atlas Infra")
    repositories = projection.get("repositories")
    if not isinstance(repositories, list):
        raise ScoreboardError("repository projection repositories must be an array")
    if projection.get("repository_count") != len(repositories):
        raise ScoreboardError("repository projection count does not match repository entries")
    for item in repositories:
        if not isinstance(item, dict):
            raise ScoreboardError("repository projection entry must be an object")
        repository = item.get("repository")
        if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
            raise ScoreboardError("repository projection contains an invalid repository identity")
    return projection


def repo_api_path(repository: str) -> str:
    owner, name = repository.split("/", 1)
    return f"/repos/{quote_ref(owner)}/{quote_ref(name)}"


def content_exists(
    client: GitHubClient,
    repository: str,
    default_branch: str,
    candidates: tuple[str, ...],
) -> tuple[str, str]:
    base = repo_api_path(repository)
    for candidate in candidates:
        try:
            document = client.get_optional(
                f"{base}/contents/{quote_path(candidate)}?ref={quote_ref(default_branch)}"
            )
        except GitHubApiError as error:
            return "unknown", f"GitHub could not read {candidate}: {error.status}"
        if document is not None:
            return "passed", candidate
    return "failed", "none of " + ", ".join(candidates)


def list_optional(client: GitHubClient, path: str) -> tuple[str, list[Any]]:
    try:
        payload = client.get(path)
    except GitHubApiError as error:
        return "unknown", [{"message": str(error.status)}]
    if not isinstance(payload, list):
        return "unknown", [{"message": "GitHub response was not an array"}]
    return "passed", payload


def get_optional(client: GitHubClient, path: str) -> tuple[str, Any | None]:
    try:
        return "passed", client.get_optional(path)
    except GitHubApiError as error:
        return "unknown", {"message": str(error.status)}


def has_release_history(client: GitHubClient, repository: str) -> CheckResult:
    base = repo_api_path(repository)
    release_status, releases = list_optional(client, f"{base}/releases?per_page=1")
    tag_status, tags = list_optional(client, f"{base}/tags?per_page=1")
    if release_status == "unknown" and tag_status == "unknown":
        return CheckResult("release_history", "Release or tag exists", "unknown", "GitHub release and tag reads were unavailable.")
    if release_status == "passed" and releases:
        return CheckResult("release_history", "Release or tag exists", "passed", "At least one GitHub Release exists.")
    if tag_status == "passed" and tags:
        return CheckResult("release_history", "Release or tag exists", "passed", "At least one git tag exists.")
    return CheckResult("release_history", "Release or tag exists", "failed", "No GitHub Releases or git tags were observed.")


def ruleset_targets_default_branch(ruleset: dict[str, Any], default_branch: str) -> bool:
    conditions = ruleset.get("conditions")
    if not isinstance(conditions, dict):
        return False
    ref_name = conditions.get("ref_name")
    if not isinstance(ref_name, dict):
        return False
    include = ref_name.get("include")
    if not isinstance(include, list):
        return False
    accepted = {"~DEFAULT_BRANCH", default_branch, f"refs/heads/{default_branch}"}
    return any(str(item) in accepted for item in include)


def ruleset_has_guard_rules(ruleset: dict[str, Any]) -> bool:
    rules = ruleset.get("rules")
    if not isinstance(rules, list):
        name = str(ruleset.get("name", "")).lower()
        return "default branch" in name and "pr guard" in name
    observed = {str(rule.get("type")) for rule in rules if isinstance(rule, dict)}
    required = {"pull_request", "deletion", "non_fast_forward"}
    return required.issubset(observed)


def has_default_branch_guard(
    client: GitHubClient,
    repository: str,
    default_branch: str,
) -> CheckResult:
    base = repo_api_path(repository)
    ruleset_status, rulesets = list_optional(client, f"{base}/rulesets")
    ruleset_detail_unknown = False
    if ruleset_status == "passed":
        for ruleset in rulesets:
            if not isinstance(ruleset, dict):
                continue
            if "conditions" not in ruleset or "rules" not in ruleset:
                detail_path = (
                    ruleset.get("_links", {})
                    if isinstance(ruleset.get("_links"), dict)
                    else {}
                ).get("self", {})
                href = detail_path.get("href") if isinstance(detail_path, dict) else None
                if isinstance(href, str) and href:
                    try:
                        detailed = client.get(href)
                    except GitHubApiError:
                        ruleset_detail_unknown = True
                        continue
                    if isinstance(detailed, dict):
                        ruleset = detailed
                    else:
                        ruleset_detail_unknown = True
                        continue
            if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
                continue
            if ruleset_targets_default_branch(ruleset, default_branch) and ruleset_has_guard_rules(ruleset):
                return CheckResult("default_branch_guard", "Default branch PR guard", "passed", "An active default-branch ruleset was observed.")

    protection_status, protection = get_optional(
        client,
        f"{base}/branches/{quote_ref(default_branch)}/protection",
    )
    if protection_status == "passed" and isinstance(protection, dict):
        if protection.get("required_pull_request_reviews") is not None:
            return CheckResult("default_branch_guard", "Default branch PR guard", "passed", "Classic branch protection requires pull request reviews.")
        return CheckResult("default_branch_guard", "Default branch PR guard", "failed", "Classic protection exists but pull request review protection was not observed.")

    if ruleset_status == "unknown" or protection_status == "unknown" or ruleset_detail_unknown:
        return CheckResult("default_branch_guard", "Default branch PR guard", "unknown", "GitHub ruleset or branch-protection evidence was unavailable.")
    return CheckResult("default_branch_guard", "Default branch PR guard", "failed", "No active default-branch ruleset or classic pull-request guard was observed.")


def score_repository(
    client: GitHubClient,
    classification: dict[str, Any],
    *,
    global_security_default: bool,
) -> dict[str, Any]:
    repository = classification["repository"]
    base = repo_api_path(repository)
    try:
        metadata = client.get(base)
    except GitHubApiError as error:
        checks = [
            CheckResult("provider_read", "GitHub repository read", "unknown", f"GitHub repository metadata read failed: {error.status}")
        ]
        return repository_result(classification, None, checks)
    if not isinstance(metadata, dict):
        checks = [
            CheckResult("provider_read", "GitHub repository read", "unknown", "GitHub repository metadata response was not an object.")
        ]
        return repository_result(classification, None, checks)

    default_branch = str(metadata.get("default_branch") or "main")
    topics = metadata.get("topics") if isinstance(metadata.get("topics"), list) else []
    checks = [
        CheckResult(
            "description",
            "Description",
            "passed" if isinstance(metadata.get("description"), str) and metadata["description"].strip() else "failed",
            "Repository description is present." if isinstance(metadata.get("description"), str) and metadata["description"].strip() else "Repository description is missing.",
        ),
        CheckResult(
            "topics",
            "Topics",
            "passed" if topics else "failed",
            "Repository topics are present." if topics else "Repository topics are missing.",
        ),
        CheckResult(
            "license",
            "License",
            "passed" if metadata.get("license") or content_exists(client, repository, default_branch, ("LICENSE",))[0] == "passed" else "failed",
            "Repository licence evidence is present." if metadata.get("license") else "LICENSE file evidence was checked.",
        ),
    ]

    status, message = content_exists(
        client,
        repository,
        default_branch,
        (".github/dependabot.yml", ".github/dependabot.yaml"),
    )
    checks.append(CheckResult("dependabot", "Dependabot config", status, message))

    status, message = content_exists(
        client,
        repository,
        default_branch,
        (".github/workflows/codeql.yml", ".github/workflows/codeql.yaml"),
    )
    checks.append(CheckResult("codeql", "CodeQL workflow", status, message))

    status, message = content_exists(
        client,
        repository,
        default_branch,
        (".github/workflows/scorecard.yml", ".github/workflows/scorecard.yaml"),
    )
    checks.append(CheckResult("scorecard", "OpenSSF Scorecard workflow", status, message))

    status, message = content_exists(
        client,
        repository,
        default_branch,
        ("SECURITY.md", ".github/SECURITY.md"),
    )
    if status == "failed" and global_security_default:
        status = "passed"
        message = f"Inherited from {GLOBAL_DEFAULTS_REPOSITORY}/SECURITY.md"
    checks.append(CheckResult("security_contact", "Security contact", status, message))

    status, message = content_exists(
        client,
        repository,
        default_branch,
        (".github/workflows/release.yml", ".github/workflows/release.yaml"),
    )
    checks.append(CheckResult("release_workflow", "Release workflow", status, message))
    checks.append(has_release_history(client, repository))
    checks.append(has_default_branch_guard(client, repository, default_branch))
    return repository_result(classification, metadata, checks)


def repository_result(
    classification: dict[str, Any],
    metadata: dict[str, Any] | None,
    checks: list[CheckResult],
) -> dict[str, Any]:
    known = [check for check in checks if check.status in {"passed", "failed"}]
    passed = [check for check in known if check.status == "passed"]
    score = None if not known else round((len(passed) / len(known)) * 100)
    return {
        "repository": classification["repository"],
        "lifecycle": classification["lifecycle"],
        "scope": classification["scope"],
        "runtime_service": classification["runtime_service"],
        "visibility": metadata.get("visibility") if isinstance(metadata, dict) else None,
        "default_branch": metadata.get("default_branch") if isinstance(metadata, dict) else None,
        "score": score,
        "summary": {
            "passed": len(passed),
            "failed": len([check for check in known if check.status == "failed"]),
            "unknown": len([check for check in checks if check.status == "unknown"]),
            "known": len(known),
            "total": len(checks),
        },
        "checks": [check.as_dict() for check in checks],
    }


def global_security_default_available(client: GitHubClient) -> bool:
    status, message = content_exists(
        client,
        GLOBAL_DEFAULTS_REPOSITORY,
        "main",
        ("SECURITY.md",),
    )
    return status == "passed" and message == "SECURITY.md"


def build_scoreboard(
    client: GitHubClient,
    projection: dict[str, Any],
    *,
    max_workers: int = 8,
) -> dict[str, Any]:
    repositories = sorted(
        projection["repositories"],
        key=lambda item: item["repository"].lower(),
    )
    global_security_default = global_security_default_available(client)
    worker_count = max(1, min(max_workers, len(repositories)))
    results_by_repository: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                score_repository,
                client,
                item,
                global_security_default=global_security_default,
            ): item["repository"]
            for item in repositories
        }
        for future in as_completed(futures):
            results_by_repository[futures[future]] = future.result()
    results = [results_by_repository[item["repository"]] for item in repositories]
    return {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "repository_projection": "policy/public-repository-classifications.json",
        "source_fingerprint": projection["source_fingerprint"],
        "global_defaults": {
            "repository": GLOBAL_DEFAULTS_REPOSITORY,
            "security_contact_available": global_security_default,
        },
        "summary": {
            "repositories_checked": len(results),
            "checks_total": sum(item["summary"]["total"] for item in results),
            "checks_passed": sum(item["summary"]["passed"] for item in results),
            "checks_failed": sum(item["summary"]["failed"] for item in results),
            "checks_unknown": sum(item["summary"]["unknown"] for item in results),
        },
        "repositories": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas Systems GitHub conformance scoreboard",
        "",
        "Source: `policy/public-repository-classifications.json`",
        f"Fingerprint: `{report['source_fingerprint']}`",
        f"Repositories checked: **{report['summary']['repositories_checked']}**",
        f"Checks passed: **{report['summary']['checks_passed']}**",
        f"Checks failed: **{report['summary']['checks_failed']}**",
        f"Checks unknown: **{report['summary']['checks_unknown']}**",
        "",
        "| Repository | Lifecycle | Scope | Score | Failed | Unknown |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in report["repositories"]:
        failed = [
            check["label"]
            for check in item["checks"]
            if check["status"] == "failed"
        ]
        unknown = [
            check["label"]
            for check in item["checks"]
            if check["status"] == "unknown"
        ]
        score = "n/a" if item["score"] is None else f"{item['score']}%"
        lines.append(
            "| "
            f"`{item['repository']}` | "
            f"`{item['lifecycle']}` | "
            f"`{item['scope']}` | "
            f"{score} | "
            f"{', '.join(failed) if failed else 'None'} | "
            f"{', '.join(unknown) if unknown else 'None'} |"
        )
    lines.append("")
    lines.append("## Check Meaning")
    lines.append("")
    lines.extend(
        [
            "- **Description**: the GitHub repository has a useful short description.",
            "- **Topics**: the GitHub repository has topics for discovery and grouping.",
            "- **License**: GitHub metadata or a `LICENSE` file exists.",
            "- **Dependabot config**: `.github/dependabot.yml` or `.yaml` exists.",
            "- **CodeQL workflow**: a CodeQL workflow exists in `.github/workflows/`.",
            "- **OpenSSF Scorecard workflow**: a Scorecard workflow exists in `.github/workflows/`.",
            "- **Security contact**: the repository has `SECURITY.md` or inherits the owner default.",
            "- **Release workflow**: a release workflow exists in `.github/workflows/`.",
            "- **Release or tag exists**: at least one GitHub Release or git tag exists.",
            "- **Default branch PR guard**: a repository ruleset or classic branch protection requires pull-request review.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the Atlas Systems public GitHub conformance scoreboard."
    )
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        projection = load_projection(args.projection)
        scoreboard = build_scoreboard(
            GitHubClient(os.environ.get("GITHUB_TOKEN", "")),
            projection,
            max_workers=args.max_workers,
        )
    except (OSError, json.JSONDecodeError, ScoreboardError, GitHubApiError) as error:
        print(f"github conformance scoreboard failed: {error}", file=sys.stderr)
        return 2
    write_json(args.json_out, scoreboard)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_markdown(scoreboard), encoding="utf-8")
    print(
        f"checked {scoreboard['summary']['repositories_checked']} repositories; "
        f"{scoreboard['summary']['checks_failed']} failed checks; "
        f"{scoreboard['summary']['checks_unknown']} unknown checks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
