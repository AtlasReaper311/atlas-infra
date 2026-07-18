#!/usr/bin/env python3
"""Build a reviewed, write-free Dependabot rollout plan for the Atlas estate."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from detect_ecosystem import Detection, detect_ecosystem_locations
from estate_repo_diff import (
    DEFAULT_OWNER,
    list_owned_repositories,
    load_registry,
    reconcile,
    registry_map,
    write_reports,
)
from github_api import GitHubApiError, GitHubClient, quote_path, quote_ref


DEFAULT_REGISTRY = Path("policy/estate-registry.json")
TEMP_ROOT = Path(tempfile.gettempdir())
DEFAULT_OUTPUT = TEMP_ROOT / "dependabot-rollout-plan"
DEFAULT_TEMPLATE = Path("templates/dependabot-automerge.yml")
ACTIVE_LIFECYCLES = {"active", "production"}
ROLLOUT_EXCLUSIONS = {"AtlasReaper311/atlas-dep-audit"}
READ_TOKEN_ENV = "ATLAS_DEPENDABOT_READ_TOKEN"


def schedule_for(entry: dict[str, Any]) -> dict[str, str]:
    if entry.get("lifecycle") == "production" or entry.get("runtime_service") is True:
        return {
            "interval": "weekly",
            "day": "monday",
            "time": "04:00",
            "timezone": "Europe/London",
        }
    return {
        "interval": "monthly",
        "time": "04:00",
        "timezone": "Europe/London",
    }


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_dependabot(
    detections: list[Detection], entry: dict[str, Any], default_branch: str
) -> str:
    limit = 10 if entry["lifecycle"] == "production" else 5
    schedule = schedule_for(entry)
    lines = ["version: 2", "updates:"]
    for detection in detections:
        for directory in detection.directories:
            ecosystem = detection.ecosystem
            lines.extend(
                [
                    f"  - package-ecosystem: {_quoted(ecosystem)}",
                    f"    directory: {_quoted(directory)}",
                    "    schedule:",
                    f"      interval: {_quoted(schedule['interval'])}",
                ]
            )
            if "day" in schedule:
                lines.append(f"      day: {_quoted(schedule['day'])}")
            lines.extend(
                [
                    f"      time: {_quoted(schedule['time'])}",
                    f"      timezone: {_quoted(schedule['timezone'])}",
                    f"    open-pull-requests-limit: {limit}",
                    "    labels:",
                    '      - "dependencies"',
                    f"      - {_quoted(ecosystem)}",
                    f"    target-branch: {_quoted(default_branch)}",
                    "    groups:",
                    f"      {ecosystem}-minor-patch:",
                    '        applies-to: "version-updates"',
                    "        patterns:",
                    '          - "*"',
                    "        update-types:",
                    '          - "minor"',
                    '          - "patch"',
                ]
            )
    return "\n".join(lines) + "\n"


def validate_dependabot_text(
    text: str, detections: list[Detection], entry: dict[str, Any], default_branch: str
) -> list[str]:
    errors: list[str] = []
    expected_entries = sum(len(item.directories) for item in detections)
    if not text.startswith("version: 2\nupdates:\n"):
        errors.append("configuration must declare Dependabot version 2 and updates")
    if text.count("  - package-ecosystem:") != expected_entries:
        errors.append("configuration does not contain one entry per detected directory")
    if text.count(f"    target-branch: {_quoted(default_branch)}") != expected_entries:
        errors.append("every update entry must target the live default branch")
    expected_limit = 10 if entry["lifecycle"] == "production" else 5
    if text.count(f"    open-pull-requests-limit: {expected_limit}") != expected_entries:
        errors.append("every update entry must carry the lifecycle pull request limit")
    if text.count('          - "major"'):
        errors.append("major updates must not be grouped")
    schedule = schedule_for(entry)
    if schedule["interval"] == "monthly" and "      day:" in text:
        errors.append("monthly schedules must not use the weekly-only day option")
    for detection in detections:
        marker = f"  - package-ecosystem: {_quoted(detection.ecosystem)}"
        if marker not in text:
            errors.append(f"missing ecosystem: {detection.ecosystem}")
    return errors


def _content_text(client: GitHubClient, repository: str, path: str, ref: str) -> str | None:
    encoded_path = quote_path(path)
    encoded_ref = quote_ref(ref)
    payload = client.get_optional(
        f"/repos/{repository}/contents/{encoded_path}?ref={encoded_ref}"
    )
    if payload is None:
        return None
    if payload.get("encoding") != "base64":
        raise RuntimeError(f"unsupported content encoding for {repository}:{path}")
    return base64.b64decode(payload["content"]).decode("utf-8")


def _required_checks(client: GitHubClient, repository: str, branch: str) -> tuple[list[str], str]:
    checks: set[str] = set()
    access_unknown = False
    path = f"/repos/{repository}/branches/{quote_ref(branch)}/protection/required_status_checks"
    try:
        payload = client.get_optional(path)
    except GitHubApiError as error:
        if error.status == 403:
            access_unknown = True
            payload = None
        else:
            raise
    if isinstance(payload, dict):
        for context in payload.get("contexts", []):
            if isinstance(context, str):
                checks.add(context)
        for check in payload.get("checks", []):
            if isinstance(check, dict) and isinstance(check.get("context"), str):
                checks.add(check["context"])

    rules_path = f"/repos/{repository}/rules/branches/{quote_ref(branch)}"
    try:
        rules = client.get_optional(rules_path)
    except GitHubApiError as error:
        if error.status == 403:
            access_unknown = True
            rules = None
        else:
            raise
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
                continue
            parameters = rule.get("parameters", {})
            if not isinstance(parameters, dict):
                continue
            for check in parameters.get("required_status_checks", []):
                if isinstance(check, dict) and isinstance(check.get("context"), str):
                    checks.add(check["context"])

    if checks:
        return sorted(checks), "configured"
    return [], "unknown" if access_unknown else "none"


def _repo_plan(
    client: GitHubClient,
    repository: dict[str, Any],
    entry: dict[str, Any],
    template_text: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    full_name = repository["repository"]
    default_branch = repository.get("default_branch")
    lifecycle = entry.get("lifecycle")
    base = {
        "repository": full_name,
        "lifecycle": lifecycle,
        "default_branch": default_branch,
        "runtime_service": bool(entry.get("runtime_service")),
        "files": [],
        "blockers": [],
        "notes": [],
    }
    files: dict[str, str] = {}
    if full_name in ROLLOUT_EXCLUSIONS:
        base.update(action="skip", schedule="none", ecosystems=[], grouped="no")
        base["notes"].append(
            "excluded from this rollout; existing dependency audit governance remains unchanged"
        )
        return base, files
    if repository.get("archived") or lifecycle == "archived":
        base.update(action="skip", schedule="none", ecosystems=[], grouped="no")
        base["notes"].append("archived repositories are read-only")
        if repository.get("archived") and lifecycle != "archived":
            base["blockers"].append(
                "GitHub marks the repository archived but the registry lifecycle differs"
            )
        return base, files
    if lifecycle == "deprecated":
        base.update(action="security-alerts-only", schedule="none", ecosystems=[], grouped="no")
        base["notes"].append(
            "enable vulnerability alerts only; do not enable version updates or automated security fixes"
        )
        return base, files
    if lifecycle not in ACTIVE_LIFECYCLES:
        base.update(action="skip", schedule="none", ecosystems=[], grouped="no")
        base["blockers"].append(f"unsupported lifecycle for rollout: {lifecycle}")
        return base, files
    if not isinstance(default_branch, str) or not default_branch:
        base.update(action="blocked", schedule="none", ecosystems=[], grouped="no")
        base["blockers"].append("repository has no default branch")
        return base, files

    detections = detect_ecosystem_locations(client, full_name, default_branch)
    ecosystems = [item.ecosystem for item in detections]
    base["ecosystems"] = ecosystems
    base["directories"] = {
        item.ecosystem: list(item.directories) for item in detections
    }
    schedule = schedule_for(entry)
    base["schedule"] = schedule["interval"]
    base["grouped"] = "minor and patch"
    if not detections:
        base["action"] = "blocked"
        base["blockers"].append("no supported ecosystem detected")
        return base, files

    dependabot_text = render_dependabot(detections, entry, default_branch)
    errors = validate_dependabot_text(dependabot_text, detections, entry, default_branch)
    if errors:
        base["action"] = "blocked"
        base["blockers"].extend(errors)
        return base, files

    existing_config = _content_text(
        client, full_name, ".github/dependabot.yml", default_branch
    )
    alternate_config = _content_text(
        client, full_name, ".github/dependabot.yaml", default_branch
    )
    existing_workflow = _content_text(
        client, full_name, ".github/workflows/dependabot-automerge.yml", default_branch
    )
    if alternate_config is not None:
        base["blockers"].append("existing .github/dependabot.yaml requires owner reconciliation")
    if existing_config is not None and existing_config != dependabot_text:
        base["blockers"].append("existing .github/dependabot.yml requires owner reconciliation")
    if existing_workflow is not None and existing_workflow != template_text:
        base["blockers"].append("existing auto-merge workflow requires owner reconciliation")

    checks, check_state = _required_checks(client, full_name, default_branch)
    base["required_checks"] = checks
    base["required_checks_state"] = check_state
    metadata = client.get(f"/repos/{full_name}")
    base["allow_auto_merge"] = bool(metadata.get("allow_auto_merge"))
    base["free_tier_automerge_eligible"] = not bool(repository.get("private"))
    base["automerge_enabled_by_plan"] = False
    if check_state != "configured":
        base["notes"].append(
            "no required checks confirmed; auto-merge remains inert until protection requires a check"
        )
    if not base["allow_auto_merge"]:
        base["notes"].append("repository auto-merge is disabled; workflow remains inert")
    if not base["free_tier_automerge_eligible"]:
        base["notes"].append(
            "private free-tier repository; auto-merge remains inert and dependency pull requests need manual merge"
        )
    base["notes"].append(
        "set DEPENDABOT_AUTOMERGE_ENABLED only after required checks and auto-merge are confirmed"
    )
    base["required_labels"] = sorted({"dependencies", "dependabot-major", *ecosystems})
    base["action"] = "blocked" if base["blockers"] else "propose"
    if existing_config is None and alternate_config is None:
        files[".github/dependabot.yml"] = dependabot_text
    elif existing_config == dependabot_text:
        base["notes"].append("Dependabot configuration already matches")
    if existing_workflow is None:
        files[".github/workflows/dependabot-automerge.yml"] = template_text
    elif existing_workflow == template_text:
        base["notes"].append("auto-merge workflow already matches")
    if base["blockers"]:
        files = {}
    base["files"] = sorted(files)
    return base, files


def _summary(plans: list[dict[str, Any]], reconciliation: dict[str, Any]) -> str:
    lines = [
        "# Dependabot rollout plan",
        "",
        f"Reconciliation digest: `{reconciliation['reconciliation_digest']}`",
        "",
        "| Repository | Lifecycle | Ecosystems | Schedule | Grouping | Action | Auto-merge readiness |",
        "|---|---|---|---|---|---|---|",
    ]
    for plan in plans:
        ecosystems = ", ".join(plan.get("ecosystems", [])) or "none"
        readiness = "ready"
        if (
            plan.get("required_checks_state") != "configured"
            or not plan.get("allow_auto_merge", False)
            or not plan.get("free_tier_automerge_eligible", False)
        ):
            readiness = "inert"
        if plan.get("action") in {"skip", "security-alerts-only"}:
            readiness = "not applicable"
        lines.append(
            f"| `{plan['repository']}` | `{plan['lifecycle']}` | {ecosystems} | "
            f"{plan['schedule']} | {plan['grouped']} | {plan['action']} | {readiness} |"
        )
    lines.extend(["", "## Excluded mismatches", ""])
    excluded = reconciliation["github_only"] + reconciliation["registry_only"]
    if excluded:
        lines.extend(f"- `{name}`" for name in excluded)
    else:
        lines.append("None.")
    lines.extend(["", "## Blockers and notes", ""])
    for plan in plans:
        for blocker in plan.get("blockers", []):
            lines.append(f"- `{plan['repository']}` blocker: {blocker}")
        for note in plan.get("notes", []):
            lines.append(f"- `{plan['repository']}`: {note}")
    lines.append("")
    return "\n".join(lines)


def build_plan(
    client: GitHubClient,
    registry: dict[str, Any],
    github_repositories: dict[str, dict[str, Any]],
    template_text: str,
) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    reconciliation = reconcile(registry, github_repositories)
    declared = registry_map(registry)
    plans: list[dict[str, Any]] = []
    files: dict[str, dict[str, str]] = {}
    for repository in reconciliation["matches"]:
        plan, repo_files = _repo_plan(
            client, repository, declared[repository["repository"]], template_text
        )
        plans.append(plan)
        files[repository["repository"]] = repo_files
    stable = {
        "schema_version": "atlas-dependabot/rollout-plan/v1",
        "owner": DEFAULT_OWNER,
        "registry_reviewed_at": registry.get("reviewed_at"),
        "registry_digest": reconciliation["registry_digest"],
        "reconciliation_digest": reconciliation["reconciliation_digest"],
        "github_only": reconciliation["github_only"],
        "registry_only": reconciliation["registry_only"],
        "repositories": plans,
    }
    stable["plan_digest"] = hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return stable, files


def materialize_plan(
    plan: dict[str, Any],
    files: dict[str, dict[str, str]],
    output: Path,
    reconciliation: dict[str, Any],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for full_name, repo_files in files.items():
        repo_name = full_name.split("/", 1)[1]
        for relative, text in repo_files.items():
            destination = output / repo_name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8")
    (output / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (output / "summary.md").write_text(
        _summary(plan["repositories"], reconciliation), encoding="utf-8"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--token-env", default=READ_TOKEN_ENV)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Refuse cross-repository writes and explain the governed execution boundary",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print(
            "apply refused: atlas-gardener is the approved cross-repository write boundary; "
            "review this plan before an approved gardener execution phase",
            file=sys.stderr,
        )
        return 2
    try:
        token = os.environ.get(args.token_env, "")
        client = GitHubClient(token)
        registry = load_registry(args.registry)
        repositories = list_owned_repositories(client, DEFAULT_OWNER)
        reconciliation = reconcile(registry, repositories)
        write_reports(
            reconciliation,
            DEFAULT_OWNER,
            TEMP_ROOT / "estate-repo-diff.md",
            TEMP_ROOT / "estate-repo-diff.json",
        )
        template_text = args.template.read_text(encoding="utf-8")
        plan, files = build_plan(client, registry, repositories, template_text)
        materialize_plan(plan, files, args.output, reconciliation)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Dependabot rollout planning failed: {error}", file=sys.stderr)
        return 2
    print((args.output / "summary.md").read_text(encoding="utf-8"), end="")
    print(f"Plan digest: {plan['plan_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
