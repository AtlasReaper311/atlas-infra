#!/usr/bin/env python3
"""Label-only governance for Atlas Systems repositories.

Public audits are allowlist-driven from the canonical public repository
classification projection. Private audits are source-local and query only the
caller repository after validating its .atlas/governance.json boundary.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.repository_hygiene import (  # noqa: E402
    Finding,
    GitHubClient,
    HygieneError,
    label_findings,
    load_json,
    load_projection,
    validate_policy_document,
    write_json,
    write_text,
)
from scripts.repository_metadata import load_private_governance  # noqa: E402

DEFAULT_POLICY = ROOT / "policy" / "repository-hygiene.json"
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"


def fetch_repository_labels(client: GitHubClient, repository: str) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    path = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}/labels?per_page=100"
    document = client.get_json(path)
    if not isinstance(document, list):
        raise HygieneError(f"GitHub labels response was not an array for {repository}")
    return [item for item in document if isinstance(item, dict)]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas Systems repository label audit",
        "",
        f"Scope: `{report['scope']}`",
        f"Mode: `{report['mode']}`",
        f"Repositories checked: **{report['summary']['repositories_checked']}**",
        f"Findings: **{report['summary']['finding_count']}**",
        "",
    ]
    if not report["findings"]:
        lines.extend(["All checked repositories satisfy the current label policy.", ""])
        return "\n".join(lines)

    lines.extend(["| Repository | Rule | Finding |", "|---|---|---|"])
    for finding in report["findings"]:
        message = finding["message"].replace("|", "\\|")
        lines.append(f"| `{finding['repository']}` | `{finding['rule_id']}` | {message} |")
    lines.append("")
    return "\n".join(lines)


def build_report(
    *,
    scope: str,
    mode: str,
    authority: str,
    projection: str | None,
    repositories_checked: int,
    findings: list[Finding],
) -> tuple[dict[str, Any], int]:
    findings.sort(key=lambda item: (item.repository.lower(), item.rule_id, item.message))
    report = {
        "schema_version": "atlas-repository-labels/report/v1",
        "scope": scope,
        "mode": mode,
        "authority": authority,
        "repository_projection": projection,
        "summary": {
            "repositories_checked": repositories_checked,
            "finding_count": len(findings),
            "repositories_with_findings": len({finding.repository for finding in findings}),
        },
        "findings": [finding.as_dict() for finding in findings],
    }
    return report, 1 if mode == "enforce" and findings else 0


def audit_public(
    policy: dict[str, Any],
    projection_path: Path,
    client: GitHubClient,
    mode: str,
) -> tuple[dict[str, Any], int]:
    classifications = load_projection(projection_path)
    findings: list[Finding] = []
    for classification in classifications:
        repository = classification["repository"]
        try:
            labels = fetch_repository_labels(client, repository)
            findings.extend(label_findings(repository, labels, policy))
        except HygieneError as error:
            findings.append(Finding(repository, "audit", "provider-read-failed", str(error)))

    return build_report(
        scope="public",
        mode=mode,
        authority=policy["authority"],
        projection=policy["repository_projection"],
        repositories_checked=len(classifications),
        findings=findings,
    )


def audit_private(
    policy: dict[str, Any],
    governance_path: Path,
    client: GitHubClient,
    mode: str,
    repository: str,
) -> tuple[dict[str, Any], int]:
    load_private_governance(governance_path, repository)
    labels = fetch_repository_labels(client, repository)
    findings = label_findings(repository, labels, policy)
    return build_report(
        scope="private-source-local",
        mode=mode,
        authority=policy["authority"],
        projection=None,
        repositories_checked=1,
        findings=findings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Atlas Systems repository labels.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-policy")
    check.add_argument("--policy", type=Path, default=DEFAULT_POLICY)

    public = subparsers.add_parser("audit-public")
    public.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    public.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    public.add_argument("--mode", choices=("advisory", "enforce"), default="advisory")
    public.add_argument("--json-out", type=Path, required=True)
    public.add_argument("--markdown-out", type=Path, required=True)

    private = subparsers.add_parser("audit-private")
    private.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    private.add_argument("--governance", type=Path, required=True)
    private.add_argument("--mode", choices=("advisory", "enforce"), default="enforce")
    private.add_argument("--json-out", type=Path, required=True)
    private.add_argument("--markdown-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        policy = load_json(args.policy)
        if not isinstance(policy, dict):
            raise HygieneError("repository hygiene policy root must be an object")
        errors = validate_policy_document(policy)
        if errors:
            raise HygieneError("invalid repository hygiene policy: " + "; ".join(errors))

        if args.command == "check-policy":
            print("repository label policy validation passed")
            return 0

        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise HygieneError("GITHUB_TOKEN is required for live label audit")
        client = GitHubClient(token)

        if args.command == "audit-public":
            report, status = audit_public(policy, args.projection, client, args.mode)
        else:
            repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
            if not repository:
                raise HygieneError("GITHUB_REPOSITORY is required for private label audit")
            report, status = audit_private(policy, args.governance, client, args.mode, repository)

        write_json(args.json_out, report)
        write_text(args.markdown_out, render_markdown(report))
        print(
            f"checked {report['summary']['repositories_checked']} repositories; "
            f"found {report['summary']['finding_count']} label findings"
        )
        return status
    except (OSError, json.JSONDecodeError, HygieneError) as error:
        print(f"repository label audit failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
