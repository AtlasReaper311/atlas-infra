#!/usr/bin/env python3
"""Apply Atlas Infra policy dispositions to raw GitHub conformance evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from github_api import GitHubApiError, GitHubClient
import github_conformance_scoreboard as evidence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"
DEFAULT_REQUIREMENTS = ROOT / "policy" / "github-conformance-requirements.json"
SCHEMA_VERSION = "atlas-github-conformance-scoreboard/report/v2"
REQUIREMENTS_SCHEMA_VERSION = "atlas-github-conformance-requirements/v1"
AUTHORITY = "AtlasReaper311/atlas-infra"
CHECK_IDS = (
    "description",
    "topics",
    "license",
    "dependabot",
    "codeql",
    "scorecard",
    "security_contact",
    "release_workflow",
    "release_history",
    "default_branch_guard",
)
DISPOSITIONS = {"required", "not_applicable", "exception", "deferred"}


class PolicyError(RuntimeError):
    """Raised when the conformance requirements policy is malformed."""


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def canonical_fingerprint(document: Any) -> str:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_requirements(path: Path) -> dict[str, Any]:
    requirements = load_json(path)
    if not isinstance(requirements, dict):
        raise PolicyError("requirements root must be an object")
    if requirements.get("schema_version") != REQUIREMENTS_SCHEMA_VERSION:
        raise PolicyError("unexpected requirements schema_version")
    if requirements.get("authority") != AUTHORITY:
        raise PolicyError("requirements authority must be Atlas Infra")
    defaults = requirements.get("defaults")
    if not isinstance(defaults, dict) or set(defaults) != set(CHECK_IDS):
        raise PolicyError("requirements defaults must define every supported check exactly once")
    for check_id, disposition in defaults.items():
        if disposition not in DISPOSITIONS:
            raise PolicyError(f"invalid default disposition for {check_id}")
    repositories = requirements.get("repositories")
    if not isinstance(repositories, dict):
        raise PolicyError("requirements repositories must be an object")
    for repository, overrides in repositories.items():
        if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
            raise PolicyError("requirements contain an invalid repository identity")
        if not isinstance(overrides, dict):
            raise PolicyError(f"requirements overrides for {repository} must be an object")
        for check_id, rule in overrides.items():
            if check_id not in CHECK_IDS:
                raise PolicyError(f"requirements contain unknown check {check_id}")
            if not isinstance(rule, dict):
                raise PolicyError(f"requirements rule for {repository} {check_id} must be an object")
            if rule.get("disposition") not in DISPOSITIONS:
                raise PolicyError(f"invalid disposition for {repository} {check_id}")
            if not isinstance(rule.get("reason"), str) or not rule["reason"].strip():
                raise PolicyError(f"requirements rule for {repository} {check_id} needs a reason")
    return requirements


def validate_requirement_repositories(
    projection: dict[str, Any], requirements: dict[str, Any]
) -> None:
    projected = {item["repository"] for item in projection["repositories"]}
    unknown = sorted(set(requirements["repositories"]) - projected)
    if unknown:
        raise PolicyError(
            "requirements reference repositories outside the projection: " + ", ".join(unknown)
        )


def policy_rule(
    requirements: dict[str, Any], repository: str, check_id: str
) -> tuple[str, str]:
    disposition = requirements["defaults"][check_id]
    reason = "Estate-wide default requirement."
    override = requirements["repositories"].get(repository, {}).get(check_id)
    if isinstance(override, dict):
        disposition = override["disposition"]
        reason = override["reason"]
    return disposition, reason


def policy_outcome(status: str, disposition: str) -> str:
    if disposition == "required":
        return status
    if disposition in {"exception", "deferred"} and status == "passed":
        return "passed"
    return disposition


def apply_policy(
    raw_report: dict[str, Any],
    requirements: dict[str, Any],
    projection: dict[str, Any],
) -> dict[str, Any]:
    validate_requirement_repositories(projection, requirements)
    report = copy.deepcopy(raw_report)
    report["schema_version"] = SCHEMA_VERSION
    report["requirements_policy"] = "policy/github-conformance-requirements.json"
    report["requirements_fingerprint"] = canonical_fingerprint(requirements)

    for repository in report["repositories"]:
        policy_checks: list[dict[str, Any]] = []
        for check in repository["checks"]:
            check_id = check["id"]
            if check_id == "provider_read":
                disposition = "required"
                reason = "Provider metadata is required to evaluate repository conformance."
            else:
                if check_id not in CHECK_IDS:
                    raise PolicyError(f"raw report contains unsupported check {check_id}")
                disposition, reason = policy_rule(
                    requirements, repository["repository"], check_id
                )
            check["requirement"] = disposition
            check["outcome"] = policy_outcome(check["status"], disposition)
            check["policy_message"] = reason
            policy_checks.append(check)

        summary = repository["summary"]
        repository["evidence_score"] = repository.get("score")
        required = [
            check
            for check in policy_checks
            if check["outcome"] in {"passed", "failed", "unknown"}
        ]
        known = [check for check in required if check["outcome"] in {"passed", "failed"}]
        passed = [check for check in known if check["outcome"] == "passed"]
        repository["policy_score"] = (
            None if not known else round((len(passed) / len(known)) * 100)
        )
        summary.update(
            {
                "policy_required": len(required),
                "policy_passed": len(passed),
                "policy_failed": len(
                    [check for check in required if check["outcome"] == "failed"]
                ),
                "policy_unknown": len(
                    [check for check in required if check["outcome"] == "unknown"]
                ),
                "not_applicable": len(
                    [check for check in policy_checks if check["outcome"] == "not_applicable"]
                ),
                "exception": len(
                    [check for check in policy_checks if check["outcome"] == "exception"]
                ),
                "deferred": len(
                    [check for check in policy_checks if check["outcome"] == "deferred"]
                ),
            }
        )

    summary = report["summary"]
    summary.update(
        {
            "policy_checks_required": sum(
                item["summary"]["policy_required"] for item in report["repositories"]
            ),
            "policy_checks_passed": sum(
                item["summary"]["policy_passed"] for item in report["repositories"]
            ),
            "policy_checks_failed": sum(
                item["summary"]["policy_failed"] for item in report["repositories"]
            ),
            "policy_checks_unknown": sum(
                item["summary"]["policy_unknown"] for item in report["repositories"]
            ),
            "checks_not_applicable": sum(
                item["summary"]["not_applicable"] for item in report["repositories"]
            ),
            "checks_exception": sum(
                item["summary"]["exception"] for item in report["repositories"]
            ),
            "checks_deferred": sum(
                item["summary"]["deferred"] for item in report["repositories"]
            ),
        }
    )
    return report


def labels_for_outcome(repository: dict[str, Any], outcome: str) -> list[str]:
    return [
        check["label"] for check in repository["checks"] if check["outcome"] == outcome
    ]


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Atlas Systems GitHub conformance scoreboard",
        "",
        "Evidence source: `policy/public-repository-classifications.json`",
        "Policy source: `policy/github-conformance-requirements.json`",
        f"Projection fingerprint: `{report['source_fingerprint']}`",
        f"Requirements fingerprint: `{report['requirements_fingerprint']}`",
        f"Repositories checked: **{summary['repositories_checked']}**",
        "",
        "## Policy conformance",
        "",
        f"Required checks passed: **{summary['policy_checks_passed']}**",
        f"Required checks failed: **{summary['policy_checks_failed']}**",
        f"Required checks unknown: **{summary['policy_checks_unknown']}**",
        f"Not applicable: **{summary['checks_not_applicable']}**",
        f"Approved exceptions: **{summary['checks_exception']}**",
        f"Deferred: **{summary['checks_deferred']}**",
        "",
        "## Raw evidence inventory",
        "",
        f"Checks passed: **{summary['checks_passed']}**",
        f"Checks failed: **{summary['checks_failed']}**",
        f"Checks unknown: **{summary['checks_unknown']}**",
        "",
        "| Repository | Lifecycle | Scope | Evidence | Policy | Failed | Unknown | N/A | Exceptions | Deferred |",
        "|---|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for repository in report["repositories"]:
        evidence_score = (
            "n/a"
            if repository["evidence_score"] is None
            else f"{repository['evidence_score']}%"
        )
        policy_score = (
            "n/a"
            if repository["policy_score"] is None
            else f"{repository['policy_score']}%"
        )
        cells = {
            outcome: labels_for_outcome(repository, outcome)
            for outcome in (
                "failed",
                "unknown",
                "not_applicable",
                "exception",
                "deferred",
            )
        }
        lines.append(
            "| "
            f"`{repository['repository']}` | "
            f"`{repository['lifecycle']}` | "
            f"`{repository['scope']}` | "
            f"{evidence_score} | "
            f"{policy_score} | "
            f"{', '.join(cells['failed']) if cells['failed'] else 'None'} | "
            f"{', '.join(cells['unknown']) if cells['unknown'] else 'None'} | "
            f"{', '.join(cells['not_applicable']) if cells['not_applicable'] else 'None'} | "
            f"{', '.join(cells['exception']) if cells['exception'] else 'None'} | "
            f"{', '.join(cells['deferred']) if cells['deferred'] else 'None'} |"
        )
    lines.extend(
        [
            "",
            "## Outcome meaning",
            "",
            "- **passed**: required evidence was observed.",
            "- **failed**: required evidence was readable and absent.",
            "- **unknown**: required evidence could not be proved with the available GitHub token.",
            "- **not applicable**: the check does not describe this repository class.",
            "- **exception**: accepted policy explicitly permits the missing evidence.",
            "- **deferred**: evidence is intentionally postponed until a separately approved milestone.",
            "",
            "Raw evidence remains in the JSON report even when policy marks a check not applicable, excepted, or deferred.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the policy-aware Atlas Systems GitHub conformance scoreboard."
    )
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        projection = evidence.load_projection(args.projection)
        requirements = load_requirements(args.requirements)
        branch_guard_token = os.environ.get("GITHUB_BRANCH_GUARD_TOKEN", "")
        raw_report = evidence.build_scoreboard(
            GitHubClient(os.environ.get("GITHUB_TOKEN", "")),
            projection,
            branch_guard_client=GitHubClient(branch_guard_token)
            if branch_guard_token
            else None,
            max_workers=args.max_workers,
        )
        report = apply_policy(raw_report, requirements, projection)
    except (
        OSError,
        json.JSONDecodeError,
        PolicyError,
        evidence.ScoreboardError,
        GitHubApiError,
    ) as error:
        print(f"github conformance scoreboard failed: {error}", file=sys.stderr)
        return 2
    evidence.write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(
        f"checked {report['summary']['repositories_checked']} repositories; "
        f"{report['summary']['policy_checks_failed']} policy failures; "
        f"{report['summary']['policy_checks_unknown']} policy unknowns"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
