#!/usr/bin/env python3
"""Audit and score repository conformance across the declared Atlas estate."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
BANNED_WORDS = ("lever" + "aged", "util" + "ised", "ro" + "bust", "sea" + "mless")

DEFAULT_RULES = {
    "readme": {"weight": 10, "severity": "error"},
    "license": {"weight": 4, "severity": "warning"},
    "gitignore": {"weight": 4, "severity": "warning"},
    "npm-lock": {"weight": 12, "severity": "error"},
    "workflow-permissions": {"weight": 10, "severity": "warning"},
    "workflow-timeout": {"weight": 8, "severity": "warning"},
    "workflow-concurrency": {"weight": 8, "severity": "warning"},
    "actions-pin": {"weight": 18, "severity": "warning"},
    "prose-dash": {"weight": 5, "severity": "warning"},
    "banned-word": {"weight": 5, "severity": "warning"},
    "unfinished-copy": {"weight": 6, "severity": "warning"},
    "worker-meta": {"weight": 10, "severity": "warning"},
}


@dataclass(frozen=True)
class Finding:
    repo: str
    severity: str
    rule: str
    path: str
    message: str


@dataclass(frozen=True)
class RuleResult:
    rule: str
    status: str
    severity: str
    weight: float
    applicable: bool
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "status": self.status,
            "severity": self.severity,
            "weight": self.weight,
            "applicable": self.applicable,
            "findings": [asdict(item) for item in self.findings],
        }


class GitHubReader:
    def __init__(self, token: str | None) -> None:
        self.token = token or ""

    def request(self, url: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "atlas-estate-policy/2.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def repo(self, full_name: str) -> dict[str, Any]:
        return self.request(f"https://api.github.com/repos/{full_name}")

    def tree(self, full_name: str, ref: str) -> list[dict[str, Any]]:
        encoded_ref = urllib.parse.quote(ref, safe="")
        payload = self.request(
            f"https://api.github.com/repos/{full_name}/git/trees/{encoded_ref}?recursive=1"
        )
        return payload.get("tree", [])

    def text(self, full_name: str, path: str, ref: str) -> str:
        encoded_path = urllib.parse.quote(path)
        encoded_ref = urllib.parse.quote(ref, safe="")
        payload = self.request(
            f"https://api.github.com/repos/{full_name}/contents/{encoded_path}?ref={encoded_ref}"
        )
        if payload.get("encoding") != "base64":
            raise ValueError(f"Unsupported encoding for {full_name}:{path}")
        return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(source: str) -> dict[str, Any]:
    if source.startswith("https://"):
        request = urllib.request.Request(
            source,
            headers={"User-Agent": "atlas-estate-policy/2.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def normalize_repo(url: str) -> str:
    cleaned = url.removesuffix(".git").rstrip("/")
    if "github.com/" in cleaned:
        return cleaned.split("github.com/", 1)[1]
    return cleaned


def manifest_repositories(manifest: dict[str, Any]) -> list[str]:
    repositories: set[str] = set()
    for item in manifest.get("repositories", []):
        if not isinstance(item, dict):
            continue
        full_name = item.get("repository")
        if isinstance(full_name, str) and full_name:
            repositories.add(full_name)
            continue
        url = item.get("url")
        if isinstance(url, str) and url:
            repositories.add(normalize_repo(url))
    return sorted(repositories)


def action_ref_findings(repo: str, path: str, text: str) -> list[Finding]:
    findings = []
    for value in USES_LINE.findall(text):
        if value.startswith("./") or value.startswith("docker://"):
            continue
        if "@" not in value:
            findings.append(
                Finding(repo, "error", "actions-pin", path, f"Action has no ref: {value}")
            )
            continue
        action, ref = value.rsplit("@", 1)
        if not FULL_SHA.fullmatch(ref):
            findings.append(
                Finding(
                    repo,
                    "warning",
                    "actions-pin",
                    path,
                    f"Action is not pinned to a full commit SHA: {action}@{ref}",
                )
            )
    return findings


def rule_config(policy: dict[str, Any], rule: str) -> dict[str, Any]:
    configured = policy.get("rules", {}).get(rule, {})
    fallback = DEFAULT_RULES[rule]
    return {
        "weight": float(configured.get("weight", fallback["weight"])),
        "severity": str(configured.get("severity", fallback["severity"])),
    }


def make_result(
    policy: dict[str, Any],
    rule: str,
    findings: list[Finding],
    *,
    applicable: bool = True,
) -> RuleResult:
    config = rule_config(policy, rule)
    if not applicable:
        status = "not_applicable"
    elif not findings:
        status = "pass"
    elif any(item.severity == "error" for item in findings):
        status = "error"
    else:
        status = "warning"
    return RuleResult(
        rule=rule,
        status=status,
        severity=config["severity"],
        weight=config["weight"],
        applicable=applicable,
        findings=tuple(findings),
    )


def repository_score(results: list[RuleResult]) -> float | None:
    factors = {"pass": 1.0, "warning": 0.5, "error": 0.0}
    applicable = [
        result
        for result in results
        if result.applicable and result.status in factors
    ]
    denominator = sum(result.weight for result in applicable)
    if denominator <= 0:
        return None
    numerator = sum(result.weight * factors[result.status] for result in applicable)
    return round(numerator / denominator * 100.0, 1)


def evaluate_repository(
    reader: GitHubReader,
    full_name: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    try:
        metadata = reader.repo(full_name)
        ref = metadata.get("default_branch") or "main"
        tree = reader.tree(full_name, ref)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
        return {
            "repository": full_name,
            "status": "unknown",
            "score": None,
            "default_branch": None,
            "rules": [],
            "findings": [
                asdict(
                    Finding(
                        full_name,
                        "warning",
                        "repository-read",
                        "",
                        f"Could not read repository: {error}",
                    )
                )
            ],
        }

    paths = {item.get("path", "") for item in tree if item.get("type") == "blob"}
    lower_paths = {path.lower(): path for path in paths}
    results: list[RuleResult] = []

    readme_findings = []
    if "readme.md" not in lower_paths:
        readme_findings.append(
            Finding(full_name, "error", "readme", "README.md", "README.md is missing")
        )
    results.append(make_result(policy, "readme", readme_findings))

    licence_findings = []
    if not any(path.lower().startswith("license") for path in paths if "/" not in path):
        licence_findings.append(
            Finding(
                full_name,
                "warning",
                "license",
                "LICENSE",
                "Top-level licence file is missing",
            )
        )
    results.append(make_result(policy, "license", licence_findings))

    gitignore_findings = []
    if ".gitignore" not in paths:
        gitignore_findings.append(
            Finding(
                full_name,
                "warning",
                "gitignore",
                ".gitignore",
                ".gitignore is missing",
            )
        )
    results.append(make_result(policy, "gitignore", gitignore_findings))

    npm_applicable = "package.json" in paths
    npm_findings = []
    if npm_applicable and "package-lock.json" not in paths:
        npm_findings.append(
            Finding(
                full_name,
                "error",
                "npm-lock",
                "package-lock.json",
                "package.json exists without package-lock.json",
            )
        )
    results.append(make_result(policy, "npm-lock", npm_findings, applicable=npm_applicable))

    workflow_paths = sorted(
        path
        for path in paths
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    )
    workflow_findings = {
        "workflow-permissions": [],
        "workflow-timeout": [],
        "workflow-concurrency": [],
        "actions-pin": [],
    }
    for path in workflow_paths:
        try:
            text = reader.text(full_name, path, ref)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
            workflow_findings["workflow-permissions"].append(
                Finding(
                    full_name,
                    "warning",
                    "workflow-permissions",
                    path,
                    f"Could not read workflow: {error}",
                )
            )
            continue
        if not re.search(r"^permissions:\s*$", text, re.MULTILINE):
            workflow_findings["workflow-permissions"].append(
                Finding(
                    full_name,
                    "warning",
                    "workflow-permissions",
                    path,
                    "Workflow has no explicit top-level permissions block",
                )
            )
        if "timeout-minutes:" not in text:
            workflow_findings["workflow-timeout"].append(
                Finding(
                    full_name,
                    "warning",
                    "workflow-timeout",
                    path,
                    "Workflow declares no job timeout",
                )
            )
        if not re.search(r"^concurrency:\s*$", text, re.MULTILINE):
            workflow_findings["workflow-concurrency"].append(
                Finding(
                    full_name,
                    "warning",
                    "workflow-concurrency",
                    path,
                    "Workflow has no top-level concurrency policy",
                )
            )
        workflow_findings["actions-pin"].extend(action_ref_findings(full_name, path, text))

    for rule in (
        "workflow-permissions",
        "workflow-timeout",
        "workflow-concurrency",
        "actions-pin",
    ):
        results.append(
            make_result(
                policy,
                rule,
                workflow_findings[rule],
                applicable=bool(workflow_paths),
            )
        )

    docs_findings = {
        "prose-dash": [],
        "banned-word": [],
        "unfinished-copy": [],
    }
    public_docs = sorted(
        path
        for path in paths
        if path.lower() == "readme.md"
        or path.lower().startswith("docs/")
        and path.lower().endswith(".md")
    )
    for path in public_docs:
        try:
            text = reader.text(full_name, path, ref)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
            continue
        if "\u2014" in text:
            docs_findings["prose-dash"].append(
                Finding(
                    full_name,
                    "warning",
                    "prose-dash",
                    path,
                    "Portfolio-facing prose contains an em dash",
                )
            )
        lowered = text.lower()
        for word in policy.get("banned_words", BANNED_WORDS):
            if re.search(rf"\b{re.escape(word.lower())}\b", lowered):
                docs_findings["banned-word"].append(
                    Finding(
                        full_name,
                        "warning",
                        "banned-word",
                        path,
                        f"Portfolio-facing prose contains banned word: {word}",
                    )
                )
        if re.search(r"\b(TODO|PLACEHOLDER)\b", text, re.IGNORECASE):
            docs_findings["unfinished-copy"].append(
                Finding(
                    full_name,
                    "warning",
                    "unfinished-copy",
                    path,
                    "Portfolio-facing prose contains TODO or placeholder text",
                )
            )

    for rule in ("prose-dash", "banned-word", "unfinished-copy"):
        results.append(
            make_result(
                policy,
                rule,
                docs_findings[rule],
                applicable=bool(public_docs),
            )
        )

    worker_applicable = "wrangler.toml" in paths
    worker_findings = []
    if worker_applicable:
        source_paths = [
            path
            for path in paths
            if path.startswith("src/") and path.endswith((".js", ".ts"))
        ]
        meta_seen = False
        for path in source_paths:
            try:
                if "_meta" in reader.text(full_name, path, ref):
                    meta_seen = True
                    break
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
                continue
        if not meta_seen:
            worker_findings.append(
                Finding(
                    full_name,
                    "warning",
                    "worker-meta",
                    "src/",
                    "Worker source does not visibly mount the /_meta convention",
                )
            )
    results.append(
        make_result(
            policy,
            "worker-meta",
            worker_findings,
            applicable=worker_applicable,
        )
    )

    findings = [item for result in results for item in result.findings]
    score = repository_score(results)
    if any(item.severity == "error" for item in findings):
        status = "error"
    elif findings:
        status = "warning"
    else:
        status = "pass"

    return {
        "repository": full_name,
        "status": status,
        "score": score,
        "default_branch": ref,
        "rules": [result.as_dict() for result in results],
        "findings": [asdict(item) for item in findings],
    }


def audit_repository(
    reader: GitHubReader,
    full_name: str,
    policy: dict[str, Any],
) -> list[Finding]:
    """Compatibility wrapper returning only findings."""
    report = evaluate_repository(reader, full_name, policy)
    return [Finding(**item) for item in report["findings"]]


def build_report(
    reports: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    source_repository: str,
    source_commit: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or utc_now()
    scored = [item for item in reports if item.get("score") is not None]
    estate_score = (
        round(sum(float(item["score"]) for item in scored) / len(scored), 1)
        if scored
        else None
    )
    findings = [finding for report in reports for finding in report.get("findings", [])]
    summary = {
        "repositories_scanned": len(reports),
        "repositories_scored": len(scored),
        "estate_score": estate_score,
        "errors": sum(item.get("severity") == "error" for item in findings),
        "warnings": sum(item.get("severity") == "warning" for item in findings),
        "unknown": sum(item.get("status") == "unknown" for item in reports),
        "passing": sum(item.get("status") == "pass" for item in reports),
    }
    report = {
        "schema": "atlas-estate-conformance-report/v1",
        "generated_at": generated,
        "policy_version": str(policy.get("version", "1.0.0")),
        "source": {
            "repository": source_repository,
            "commit": source_commit,
        },
        "summary": summary,
        "rules": [
            {
                "id": rule,
                "weight": rule_config(policy, rule)["weight"],
                "severity": rule_config(policy, rule)["severity"],
                "description": policy.get("rules", {}).get(rule, {}).get("description", ""),
            }
            for rule in DEFAULT_RULES
        ],
        "repositories": reports,
        "findings": findings,
        "scoring": {
            "pass": 1.0,
            "warning": 0.5,
            "error": 0.0,
            "not_applicable": "excluded",
            "unknown": "unscored",
        },
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Atlas Systems estate conformance",
        "",
        f"Estate score: **{summary['estate_score'] if summary['estate_score'] is not None else 'unscored'}**  ",
        f"Repositories scanned: **{summary['repositories_scanned']}**  ",
        f"Errors: **{summary['errors']}**  ",
        f"Warnings: **{summary['warnings']}**  ",
        f"Unknown: **{summary['unknown']}**",
        "",
        "| Repository | Score | Status | Errors | Warnings |",
        "|---|---:|---|---:|---:|",
    ]
    for repository in sorted(report["repositories"], key=lambda item: item["repository"]):
        errors = sum(item["severity"] == "error" for item in repository["findings"])
        warnings = sum(item["severity"] == "warning" for item in repository["findings"])
        score = repository["score"] if repository["score"] is not None else "unknown"
        lines.append(
            f"| `{repository['repository']}` | {score} | {repository['status']} | {errors} | {warnings} |"
        )
    if report["findings"]:
        lines.extend(
            [
                "",
                "## Findings",
                "",
                "| Severity | Repository | Rule | Path | Finding |",
                "|---|---|---|---|---|",
            ]
        )
        for item in sorted(
            report["findings"],
            key=lambda value: (
                value["severity"] != "error",
                value["repo"],
                value["rule"],
                value["path"],
            ),
        ):
            message = item["message"].replace("|", "\\|")
            lines.append(
                f"| {item['severity']} | `{item['repo']}` | `{item['rule']}` | "
                f"`{item['path']}` | {message} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--policy", default="policy/estate-policy.json")
    parser.add_argument("--markdown", default="reports/estate-policy.md")
    parser.add_argument("--json", dest="json_path", default="reports/estate-policy.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    policy = load_json(args.policy)
    token = os.getenv("GH_DIGEST_PAT") or os.getenv("GITHUB_TOKEN")
    reader = GitHubReader(token)
    repositories = manifest_repositories(manifest)

    reports = []
    for repository in repositories:
        print(f"Auditing {repository}", flush=True)
        reports.append(evaluate_repository(reader, repository, policy))

    report = build_report(
        reports,
        policy,
        source_repository=os.getenv("GITHUB_REPOSITORY", "AtlasReaper311/atlas-infra"),
        source_commit=os.getenv("GITHUB_SHA", "local"),
    )
    markdown = render_markdown(report)
    Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown).write_text(markdown, encoding="utf-8")
    Path(args.json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(markdown)

    errors = report["summary"]["errors"]
    warnings = report["summary"]["warnings"]
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"errors={errors}\n")
            handle.write(f"warnings={warnings}\n")
            handle.write(f"score={report['summary']['estate_score']}\n")
            handle.write(f"fingerprint={report['fingerprint']}\n")
    if errors > 0 or args.strict and warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
