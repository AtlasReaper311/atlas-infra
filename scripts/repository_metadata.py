#!/usr/bin/env python3
"""Metadata-only governance for Atlas Systems repositories.

Public audits are allowlist-driven from the canonical public repository
classification projection. Private audits are source-local: the caller supplies
its own .atlas/governance.json and the script queries only that repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
    load_json,
    load_projection,
    metadata_findings,
    write_json,
    write_text,
)

DEFAULT_POLICY = ROOT / "policy" / "repository-hygiene.json"
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"


def validate_metadata_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metadata = policy.get("metadata")
    if not isinstance(metadata, dict):
        return ["metadata policy must be an object"]

    allowed = metadata.get("allowed_topics")
    required = metadata.get("required_topics")
    minimum = metadata.get("minimum_topic_count")
    maximum = metadata.get("maximum_topic_count")

    if not isinstance(allowed, list) or allowed != sorted(set(allowed)):
        errors.append("metadata.allowed_topics must be sorted and unique")
        allowed = []
    else:
        for topic in allowed:
            if not isinstance(topic, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,49}", topic):
                errors.append(f"metadata.allowed_topics contains invalid GitHub topic: {topic!r}")

    if not isinstance(required, list) or required != sorted(set(required)):
        errors.append("metadata.required_topics must be sorted and unique")
        required = []
    elif any(topic not in set(allowed) for topic in required):
        errors.append("metadata.required_topics must be contained in metadata.allowed_topics")

    if not isinstance(minimum, int) or minimum < 1:
        errors.append("metadata.minimum_topic_count must be a positive integer")
    if not isinstance(maximum, int) or maximum < 1:
        errors.append("metadata.maximum_topic_count must be a positive integer")
    if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
        errors.append("metadata.minimum_topic_count must not exceed metadata.maximum_topic_count")

    if metadata.get("private_visibility") != "private":
        errors.append("metadata.private_visibility must be private")
    return errors


def topic_findings(
    repository: str,
    repository_data: dict[str, Any],
    policy: dict[str, Any],
) -> list[Finding]:
    cfg = policy["metadata"]
    topics_raw = repository_data.get("topics")
    topics = [str(topic).lower() for topic in topics_raw] if isinstance(topics_raw, list) else []
    findings: list[Finding] = []

    minimum = cfg["minimum_topic_count"]
    maximum = cfg["maximum_topic_count"]
    if len(topics) < minimum:
        findings.append(
            Finding(
                repository,
                "metadata",
                "topic-count",
                f"Repository must have at least {minimum} topic(s); observed {len(topics)}.",
            )
        )
    if len(topics) > maximum:
        findings.append(
            Finding(
                repository,
                "metadata",
                "topic-count",
                f"Repository must have at most {maximum} topic(s); observed {len(topics)}.",
            )
        )

    allowed = set(cfg["allowed_topics"])
    invalid = sorted(topic for topic in topics if topic not in allowed)
    if invalid:
        findings.append(
            Finding(
                repository,
                "metadata",
                "topic-vocabulary",
                "Repository contains topics outside the controlled Atlas vocabulary: "
                + ", ".join(invalid),
            )
        )
    return findings


def findings_for_repository(
    repository: str,
    repository_data: dict[str, Any],
    classification: dict[str, Any],
    policy: dict[str, Any],
    *,
    expected_visibility: str,
) -> list[Finding]:
    policy_for_repo = json.loads(json.dumps(policy))
    policy_for_repo["metadata"]["visibility"] = expected_visibility
    findings = metadata_findings(repository, repository_data, classification, policy_for_repo)
    findings.extend(topic_findings(repository, repository_data, policy))
    return findings


def fetch_repository_metadata(client: GitHubClient, repository: str) -> dict[str, Any]:
    owner, name = repository.split("/", 1)
    path = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}"
    document = client.get_json(path)
    if not isinstance(document, dict):
        raise HygieneError(f"GitHub repository response was not an object for {repository}")
    return document


def render_markdown(report: dict[str, Any]) -> str:
    scope = report["scope"]
    lines = [
        "# Atlas Systems repository metadata audit",
        "",
        f"Scope: `{scope}`",
        f"Mode: `{report['mode']}`",
        f"Repositories checked: **{report['summary']['repositories_checked']}**",
        f"Findings: **{report['summary']['finding_count']}**",
        "",
    ]
    if not report["findings"]:
        lines.append("All checked repositories satisfy the current metadata policy.")
        lines.append("")
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
        "schema_version": "atlas-repository-metadata/report/v1",
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
            data = fetch_repository_metadata(client, repository)
            findings.extend(
                findings_for_repository(
                    repository,
                    data,
                    classification,
                    policy,
                    expected_visibility=policy["metadata"]["visibility"],
                )
            )
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


def load_private_governance(path: Path, expected_repository: str) -> dict[str, Any]:
    governance = load_json(path)
    if not isinstance(governance, dict):
        raise HygieneError("private governance root must be an object")
    if governance.get("schema_version") != "atlas-repository-governance/v1":
        raise HygieneError("unexpected private governance schema_version")
    if governance.get("repository") != expected_repository:
        raise HygieneError("private governance repository does not match github.repository")
    if governance.get("visibility") != "private":
        raise HygieneError("private metadata validation requires visibility=private")
    if governance.get("public_projection") is not False:
        raise HygieneError("private metadata validation requires public_projection=false")
    lifecycle = governance.get("lifecycle")
    if not isinstance(lifecycle, str) or not lifecycle:
        raise HygieneError("private governance lifecycle is required")
    return governance


def audit_private(
    policy: dict[str, Any],
    governance_path: Path,
    client: GitHubClient,
    mode: str,
    repository: str,
) -> tuple[dict[str, Any], int]:
    governance = load_private_governance(governance_path, repository)
    data = fetch_repository_metadata(client, repository)
    findings = findings_for_repository(
        repository,
        data,
        governance,
        policy,
        expected_visibility=policy["metadata"]["private_visibility"],
    )
    return build_report(
        scope="private-source-local",
        mode=mode,
        authority=policy["authority"],
        projection=None,
        repositories_checked=1,
        findings=findings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Atlas Systems repository metadata.")
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
        errors = validate_metadata_policy(policy)
        if errors:
            raise HygieneError("invalid metadata policy: " + "; ".join(errors))

        if args.command == "check-policy":
            print("repository metadata policy validation passed")
            return 0

        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise HygieneError("GITHUB_TOKEN is required for live metadata audit")
        client = GitHubClient(token)

        if args.command == "audit-public":
            report, status = audit_public(policy, args.projection, client, args.mode)
        else:
            repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
            if not repository:
                raise HygieneError("GITHUB_REPOSITORY is required for private metadata audit")
            report, status = audit_private(
                policy,
                args.governance,
                client,
                args.mode,
                repository,
            )

        write_json(args.json_out, report)
        write_text(args.markdown_out, render_markdown(report))
        print(
            f"checked {report['summary']['repositories_checked']} repositories; "
            f"found {report['summary']['finding_count']} metadata findings"
        )
        return status
    except (OSError, json.JSONDecodeError, HygieneError) as error:
        print(f"repository metadata audit failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
