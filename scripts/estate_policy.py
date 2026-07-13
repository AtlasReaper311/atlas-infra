#!/usr/bin/env python3
"""Audit repository conformance against the Atlas Systems estate policy."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
BANNED_WORDS = ("lever" + "aged", "util" + "ised", "ro" + "bust", "sea" + "mless")


@dataclass(frozen=True)
class Finding:
    repo: str
    severity: str
    rule: str
    path: str
    message: str


class GitHubReader:
    def __init__(self, token: str | None) -> None:
        self.token = token or ""

    def request(self, url: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "atlas-estate-policy/1.0",
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


def load_json(source: str) -> dict[str, Any]:
    if source.startswith("https://"):
        request = urllib.request.Request(source, headers={"User-Agent": "atlas-estate-policy/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def normalize_repo(url: str) -> str:
    cleaned = url.removesuffix(".git").rstrip("/")
    if "github.com/" in cleaned:
        return cleaned.split("github.com/", 1)[1]
    return cleaned


def action_ref_findings(repo: str, path: str, text: str) -> list[Finding]:
    findings = []
    for value in USES_LINE.findall(text):
        if value.startswith("./") or value.startswith("docker://"):
            continue
        if "@" not in value:
            findings.append(Finding(repo, "error", "actions-ref", path, f"Action has no ref: {value}"))
            continue
        action, ref = value.rsplit("@", 1)
        if not FULL_SHA.fullmatch(ref):
            findings.append(
                Finding(repo, "warning", "actions-pin", path, f"Action is not pinned to a full commit SHA: {action}@{ref}")
            )
    return findings


def audit_repository(reader: GitHubReader, full_name: str, policy: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        metadata = reader.repo(full_name)
        ref = metadata.get("default_branch") or "main"
        tree = reader.tree(full_name, ref)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
        return [Finding(full_name, "warning", "repository-read", "", f"Could not read repository: {error}")]

    paths = {item.get("path", "") for item in tree if item.get("type") == "blob"}
    lower_paths = {path.lower(): path for path in paths}

    if "readme.md" not in lower_paths:
        findings.append(Finding(full_name, "error", "readme", "README.md", "README.md is missing"))
    if not any(path.lower().startswith("license") for path in paths if "/" not in path):
        findings.append(Finding(full_name, "warning", "license", "LICENSE", "Top-level licence file is missing"))
    if ".gitignore" not in paths:
        findings.append(Finding(full_name, "warning", "gitignore", ".gitignore", ".gitignore is missing"))
    if "package.json" in paths and "package-lock.json" not in paths:
        findings.append(Finding(full_name, "error", "npm-lock", "package-lock.json", "package.json exists without package-lock.json"))

    workflow_paths = sorted(path for path in paths if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")))
    for path in workflow_paths:
        try:
            text = reader.text(full_name, path, ref)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
            findings.append(Finding(full_name, "warning", "workflow-read", path, f"Could not read workflow: {error}"))
            continue
        if not re.search(r"^permissions:\s*$", text, re.MULTILINE):
            findings.append(Finding(full_name, "warning", "workflow-permissions", path, "Workflow has no explicit top-level permissions block"))
        if "timeout-minutes:" not in text:
            findings.append(Finding(full_name, "warning", "workflow-timeout", path, "Workflow declares no job timeout"))
        if not re.search(r"^concurrency:\s*$", text, re.MULTILINE):
            findings.append(Finding(full_name, "warning", "workflow-concurrency", path, "Workflow has no top-level concurrency policy"))
        findings.extend(action_ref_findings(full_name, path, text))

    public_docs = sorted(
        path
        for path in paths
        if path.lower() == "readme.md" or path.lower().startswith("docs/") and path.lower().endswith(".md")
    )
    for path in public_docs:
        try:
            text = reader.text(full_name, path, ref)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
            continue
        if "\u2014" in text:
            findings.append(Finding(full_name, "warning", "prose-dash", path, "Portfolio-facing prose contains an em dash"))
        lowered = text.lower()
        for word in policy.get("banned_words", BANNED_WORDS):
            if re.search(rf"\b{re.escape(word.lower())}\b", lowered):
                findings.append(Finding(full_name, "warning", "banned-word", path, f"Portfolio-facing prose contains banned word: {word}"))
        if re.search(r"\b(TODO|PLACEHOLDER)\b", text, re.IGNORECASE):
            findings.append(Finding(full_name, "warning", "unfinished-copy", path, "Portfolio-facing prose contains TODO or placeholder text"))

    if "wrangler.toml" in paths:
        source_paths = [path for path in paths if path.startswith("src/") and path.endswith((".js", ".ts"))]
        meta_seen = False
        for path in source_paths:
            try:
                if "_meta" in reader.text(full_name, path, ref):
                    meta_seen = True
                    break
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
                continue
        if not meta_seen:
            findings.append(Finding(full_name, "warning", "worker-meta", "src/", "Worker source does not visibly mount the /_meta convention"))

    return findings


def render_markdown(findings: list[Finding], repo_count: int) -> str:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    lines = [
        "# Atlas Systems estate policy report",
        "",
        f"Repositories scanned: **{repo_count}**  ",
        f"Errors: **{len(errors)}**  ",
        f"Warnings: **{len(warnings)}**",
        "",
    ]
    if not findings:
        lines.append("No policy findings.")
        return "\n".join(lines) + "\n"
    lines.extend(["| Severity | Repository | Rule | Path | Finding |", "|---|---|---|---|---|"])
    for item in sorted(findings, key=lambda value: (value.severity != "error", value.repo, value.rule, value.path)):
        message = item.message.replace("|", "\\|")
        lines.append(f"| {item.severity} | `{item.repo}` | `{item.rule}` | `{item.path}` | {message} |")
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

    repos = []
    for item in manifest.get("repositories", []):
        url = item.get("url")
        if url:
            repos.append(normalize_repo(url))
    repos = sorted(set(repos))

    findings: list[Finding] = []
    for repo in repos:
        print(f"Auditing {repo}", flush=True)
        findings.extend(audit_repository(reader, repo, policy))

    markdown = render_markdown(findings, len(repos))
    Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown).write_text(markdown, encoding="utf-8")
    Path(args.json_path).write_text(
        json.dumps(
            {
                "schema": "atlas-estate-policy-report/v1",
                "repositories_scanned": len(repos),
                "errors": sum(item.severity == "error" for item in findings),
                "warnings": sum(item.severity == "warning" for item in findings),
                "findings": [asdict(item) for item in findings],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(markdown)

    error_count = sum(item.severity == "error" for item in findings)
    warning_count = sum(item.severity == "warning" for item in findings)
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"errors={error_count}\n")
            handle.write(f"warnings={warning_count}\n")
    if error_count > 0 or args.strict and warning_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
