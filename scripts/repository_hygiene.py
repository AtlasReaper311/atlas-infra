#!/usr/bin/env python3
"""Repository README, metadata, and PR-label governance for Atlas Systems.

The live audit is deliberately allowlist-driven. It may only query repositories
already present in the public repository classification projection owned by
Atlas Infra. It never enumerates account membership and never infers public
portfolio status from GitHub visibility alone.
"""

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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy" / "repository-hygiene.json"
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"
API_BASE = "https://api.github.com"


class HygieneError(RuntimeError):
    """Raised for deterministic policy or live-audit failures."""


@dataclass(frozen=True)
class Finding:
    repository: str
    category: str
    rule_id: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "category": self.category,
            "rule_id": self.rule_id,
            "message": self.message,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_policy_document(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != "atlas-repository-hygiene/v1":
        errors.append("unexpected schema_version")
    if policy.get("authority") != "AtlasReaper311/atlas-infra":
        errors.append("authority must be AtlasReaper311/atlas-infra")
    if policy.get("repository_projection") != "policy/public-repository-classifications.json":
        errors.append("repository_projection must use the canonical public classification projection")

    readme = policy.get("readme")
    if not isinstance(readme, dict):
        errors.append("readme policy must be an object")
    else:
        terms = readme.get("forbidden_terms")
        if not isinstance(terms, list) or terms != sorted(set(terms)):
            errors.append("readme.forbidden_terms must be sorted and unique")
        if readme.get("minimum_badge_count", 0) < 1:
            errors.append("readme.minimum_badge_count must be positive")

    metadata = policy.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata policy must be an object")
    else:
        topics = metadata.get("required_topics")
        if not isinstance(topics, list) or topics != sorted(set(topics)):
            errors.append("metadata.required_topics must be sorted and unique")
        archived = metadata.get("archived_lifecycles")
        if not isinstance(archived, list) or archived != sorted(set(archived)):
            errors.append("metadata.archived_lifecycles must be sorted and unique")

    labels = policy.get("pull_request_labels")
    if not isinstance(labels, list) or not labels:
        errors.append("pull_request_labels must be a non-empty array")
    else:
        names: list[str] = []
        for index, label in enumerate(labels):
            if not isinstance(label, dict):
                errors.append(f"pull_request_labels[{index}] must be an object")
                continue
            name = label.get("name")
            color = label.get("color")
            description = label.get("description")
            if not isinstance(name, str) or not re.fullmatch(r"status:[a-z0-9-]+", name):
                errors.append(f"pull_request_labels[{index}].name is invalid")
            else:
                names.append(name)
            if not isinstance(color, str) or not re.fullmatch(r"[0-9a-f]{6}", color):
                errors.append(f"pull_request_labels[{index}].color must be lowercase six-digit hex")
            if not isinstance(description, str) or not description.strip():
                errors.append(f"pull_request_labels[{index}].description must be non-empty")
        if names != sorted(names):
            errors.append("pull_request_labels must be sorted by name")
        if len(names) != len(set(names)):
            errors.append("pull_request_labels names must be unique")
    return errors


def load_projection(path: Path) -> list[dict[str, Any]]:
    projection = load_json(path)
    if not isinstance(projection, dict):
        raise HygieneError("public repository projection root must be an object")
    if projection.get("schema_version") != "atlas-public-repository-classifications/projection/v1":
        raise HygieneError("unexpected public repository projection schema_version")
    repositories = projection.get("repositories")
    if not isinstance(repositories, list):
        raise HygieneError("public repository projection repositories must be an array")
    expected_count = projection.get("repository_count")
    if expected_count != len(repositories):
        raise HygieneError("public repository projection repository_count does not match repositories")

    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in repositories:
        if not isinstance(item, dict):
            raise HygieneError("public repository projection contains a non-object entry")
        repository = item.get("repository")
        if not isinstance(repository, str) or not repository.startswith("AtlasReaper311/"):
            raise HygieneError("public repository projection contains an invalid repository identity")
        if repository in seen:
            raise HygieneError(f"duplicate projected repository: {repository}")
        seen.add(repository)
        result.append(item)
    return sorted(result, key=lambda item: item["repository"].lower())


def validate_policy_files(policy_path: Path, projection_path: Path) -> list[str]:
    policy = load_json(policy_path)
    if not isinstance(policy, dict):
        return ["repository hygiene policy root must be an object"]
    errors = validate_policy_document(policy)
    try:
        repositories = load_projection(projection_path)
    except (OSError, json.JSONDecodeError, HygieneError) as error:
        errors.append(str(error))
        return errors
    profile = policy.get("readme", {}).get("profile_repository")
    identities = {item["repository"] for item in repositories}
    if profile not in identities:
        errors.append("readme.profile_repository must exist in the public repository projection")
    return errors


def _prose_only(text: str) -> str:
    """Remove fenced and inline code before applying prose-only voice rules."""
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]+`", "", without_fences)


def _count_badges(text: str) -> int:
    header = "\n".join(text.splitlines()[:40])
    return len(re.findall(r"!\[[^\]]*\]\([^\n)]*(?:img\.shields\.io|badge\.svg)[^\n)]*\)", header))


def readme_findings(
    repository: str,
    text: str,
    policy: dict[str, Any],
    *,
    has_license: bool,
) -> list[Finding]:
    cfg = policy["readme"]
    findings: list[Finding] = []
    icon_url = cfg["icon_url"]
    profile_repo = cfg["profile_repository"]

    def add(rule_id: str, message: str) -> None:
        findings.append(Finding(repository, "readme", rule_id, message))

    if repository == profile_repo:
        if icon_url not in text or f'width="{cfg["profile_icon_width"]}"' not in text:
            add("profile-icon", "Profile README must use the canonical Atlas icon at width 120.")
        if "# Atlas Reaper" not in text:
            add("profile-heading", "Profile README must retain the Atlas Reaper H1.")
        if "https://atlas-systems.uk" not in text:
            add("profile-site-link", "Profile README must link to atlas-systems.uk.")
    else:
        repo_name = repository.split("/", 1)[1]
        if icon_url not in text or f'width="{cfg["standard_icon_width"]}"' not in text:
            add("icon", "README must use the canonical Atlas icon at width 88.")
        if not re.search(rf"(?m)^# {re.escape(repo_name)}\s*$", text):
            add("h1", f"README H1 must be exactly '# {repo_name}'.")
        if f'{cfg["required_banner_prefix"]} {repo_name}' not in text:
            add("ascii-banner", "README must contain the repository-specific Atlas Systems ASCII banner.")
        if cfg["required_heading"] not in text:
            add("atlas-fit-heading", "README must include the canonical Atlas Systems integration heading.")
        if cfg["required_footer"] not in text:
            add("footer", "README must include the canonical atlas-systems.uk footer.")
        if cfg["required_badge_label_color"] not in text:
            add("badge-style", "README badges must use the Atlas labelColor=0a0a0f treatment.")
        badge_count = _count_badges(text)
        if badge_count < cfg["minimum_badge_count"]:
            add(
                "badge-count",
                f"README header has {badge_count} recognised badges; at least {cfg['minimum_badge_count']} are required.",
            )
        footer_claims_license = bool(re.search(r"(?mi)^Part of \[atlas-systems\.uk\].*\bLicense\b", text))
        if footer_claims_license and not has_license:
            add("license-claim", "README footer claims a license but no LICENSE file was observed.")

    prose = _prose_only(text)
    lower = prose.lower()
    for term in cfg["forbidden_terms"]:
        if term.lower() in lower:
            add("forbidden-language", f"README contains forbidden portfolio wording: {term}.")
    if cfg.get("forbid_em_dash") and "—" in prose:
        add("em-dash", "README prose contains an em dash; use a semicolon, brackets, or a new sentence.")
    return findings


def _homepage_allowed(homepage: str, allowed_domain: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(homepage)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    domain = allowed_domain.lower().rstrip(".")
    return host == domain or host.endswith("." + domain)


def metadata_findings(
    repository: str,
    repository_data: dict[str, Any],
    classification: dict[str, Any],
    policy: dict[str, Any],
) -> list[Finding]:
    cfg = policy["metadata"]
    findings: list[Finding] = []

    def add(rule_id: str, message: str) -> None:
        findings.append(Finding(repository, "metadata", rule_id, message))

    if repository_data.get("visibility") != cfg["visibility"]:
        add("visibility", f"Repository visibility must be {cfg['visibility']}.")
    if repository_data.get("default_branch") != cfg["default_branch"]:
        add("default-branch", f"Default branch must be {cfg['default_branch']}.")

    description = repository_data.get("description")
    if cfg["description_required"] and (not isinstance(description, str) or not description.strip()):
        add("description", "Repository description is required.")
    elif isinstance(description, str):
        if len(description) > cfg["description_max_length"]:
            add("description-length", "Repository description exceeds the policy length limit.")
        lowered = description.lower()
        for term in policy["readme"]["forbidden_terms"]:
            if term.lower() in lowered:
                add("description-language", f"Repository description contains forbidden wording: {term}.")
        if policy["readme"].get("forbid_em_dash") and "—" in description:
            add("description-em-dash", "Repository description contains an em dash.")

    homepage = repository_data.get("homepage")
    if cfg["homepage_required"]:
        if not isinstance(homepage, str) or not homepage.strip():
            add("homepage", "Repository homepage must point to an Atlas Systems HTTPS surface.")
        elif not _homepage_allowed(homepage, cfg["allowed_homepage_domain"]):
            add("homepage-domain", f"Repository homepage must be on {cfg['allowed_homepage_domain']}.")

    topics = repository_data.get("topics")
    if not isinstance(topics, list):
        topics = []
    topic_set = {str(topic).lower() for topic in topics}
    for topic in cfg["required_topics"]:
        if topic.lower() not in topic_set:
            add("topic", f"Repository topics must include '{topic}'.")

    lifecycle = classification.get("lifecycle")
    should_be_archived = lifecycle in set(cfg["archived_lifecycles"])
    if bool(repository_data.get("archived")) != should_be_archived:
        expected = "archived" if should_be_archived else "not archived"
        add("archive-state", f"GitHub archive state must be {expected} for lifecycle '{lifecycle}'.")
    return findings


def label_findings(
    repository: str,
    labels: list[dict[str, Any]],
    policy: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    observed = {
        str(label.get("name")): label
        for label in labels
        if isinstance(label, dict) and isinstance(label.get("name"), str)
    }
    for expected in policy["pull_request_labels"]:
        name = expected["name"]
        actual = observed.get(name)
        if actual is None:
            findings.append(Finding(repository, "labels", "missing-label", f"Missing required label '{name}'."))
            continue
        color = str(actual.get("color", "")).lower()
        if color != expected["color"]:
            findings.append(Finding(repository, "labels", "label-color", f"Label '{name}' has the wrong color."))
        description = actual.get("description") or ""
        if description != expected["description"]:
            findings.append(Finding(repository, "labels", "label-description", f"Label '{name}' has the wrong description."))
    return findings


class GitHubClient:
    def __init__(self, token: str | None) -> None:
        self.token = token.strip() if token else None

    def get_json(self, path: str) -> Any:
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise HygieneError(f"GitHub HTTP {error.code} for {path}: {detail[:300]}") from error
        except urllib.error.URLError as error:
            raise HygieneError(f"GitHub request failed for {path}: {error.reason}") from error

    def get_optional_json(self, path: str) -> Any | None:
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            detail = error.read().decode("utf-8", errors="replace")
            raise HygieneError(f"GitHub HTTP {error.code} for {path}: {detail[:300]}") from error
        except urllib.error.URLError as error:
            raise HygieneError(f"GitHub request failed for {path}: {error.reason}") from error

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AtlasReaper311/atlas-infra-repository-hygiene",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def _decode_content(document: Any, repository: str, path: str) -> str:
    if not isinstance(document, dict) or document.get("encoding") != "base64":
        raise HygieneError(f"{repository}:{path} did not return base64 file content")
    encoded = document.get("content")
    if not isinstance(encoded, str):
        raise HygieneError(f"{repository}:{path} content is missing")
    try:
        return base64.b64decode(encoded).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise HygieneError(f"{repository}:{path} could not be decoded as UTF-8") from error


def audit_repository(
    client: GitHubClient,
    classification: dict[str, Any],
    policy: dict[str, Any],
) -> list[Finding]:
    repository = classification["repository"]
    owner, name = repository.split("/", 1)
    repo_path = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}"
    repository_data = client.get_json(repo_path)
    if not isinstance(repository_data, dict):
        raise HygieneError(f"GitHub repository response was not an object for {repository}")

    findings = metadata_findings(repository, repository_data, classification, policy)

    readme_document = client.get_optional_json(f"{repo_path}/contents/README.md")
    if readme_document is None:
        findings.append(Finding(repository, "readme", "missing-readme", "README.md is missing."))
    else:
        readme_text = _decode_content(readme_document, repository, "README.md")
        has_license = client.get_optional_json(f"{repo_path}/contents/LICENSE") is not None
        findings.extend(readme_findings(repository, readme_text, policy, has_license=has_license))

    labels = client.get_json(f"{repo_path}/labels?per_page=100")
    if not isinstance(labels, list):
        raise HygieneError(f"GitHub labels response was not an array for {repository}")
    findings.extend(label_findings(repository, labels, policy))
    return findings


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas Systems repository hygiene audit",
        "",
        f"Mode: `{report['mode']}`",
        f"Repositories checked: **{report['summary']['repositories_checked']}**",
        f"Findings: **{report['summary']['finding_count']}**",
        "",
    ]
    if not report["findings"]:
        lines.append("All approved public repositories satisfy the current hygiene policy.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(["| Repository | Category | Rule | Finding |", "|---|---|---|---|"])
    for finding in report["findings"]:
        message = finding["message"].replace("|", "\\|")
        lines.append(
            f"| `{finding['repository']}` | `{finding['category']}` | `{finding['rule_id']}` | {message} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_live_audit(
    policy_path: Path,
    projection_path: Path,
    *,
    token: str | None,
    mode: str,
) -> tuple[dict[str, Any], int]:
    policy = load_json(policy_path)
    if not isinstance(policy, dict):
        raise HygieneError("repository hygiene policy root must be an object")
    policy_errors = validate_policy_document(policy)
    if policy_errors:
        raise HygieneError("invalid repository hygiene policy: " + "; ".join(policy_errors))
    repositories = load_projection(projection_path)
    client = GitHubClient(token)
    findings: list[Finding] = []
    audit_errors: list[Finding] = []
    for classification in repositories:
        repository = classification["repository"]
        try:
            findings.extend(audit_repository(client, classification, policy))
        except HygieneError as error:
            audit_errors.append(Finding(repository, "audit", "provider-read-failed", str(error)))
    findings.extend(audit_errors)
    findings.sort(key=lambda item: (item.repository.lower(), item.category, item.rule_id, item.message))
    report = {
        "schema_version": "atlas-repository-hygiene/report/v1",
        "mode": mode,
        "authority": policy["authority"],
        "repository_projection": policy["repository_projection"],
        "summary": {
            "repositories_checked": len(repositories),
            "finding_count": len(findings),
            "repositories_with_findings": len({finding.repository for finding in findings}),
        },
        "findings": [finding.as_dict() for finding in findings],
    }
    exit_code = 1 if mode == "enforce" and findings else 0
    return report, exit_code


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and audit Atlas repository hygiene.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-policy", help="Validate policy and projection offline.")
    check.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    check.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)

    audit = subparsers.add_parser("audit-live", help="Audit approved public repositories through GitHub read APIs.")
    audit.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    audit.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    audit.add_argument("--mode", choices=("advisory", "enforce"), default="advisory")
    audit.add_argument("--json-out", type=Path, required=True)
    audit.add_argument("--markdown-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check-policy":
        try:
            errors = validate_policy_files(args.policy, args.projection)
        except (OSError, json.JSONDecodeError) as error:
            print(f"repository hygiene policy validation failed: {error}", file=sys.stderr)
            return 2
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("repository hygiene policy validation passed")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    try:
        report, status = run_live_audit(
            args.policy,
            args.projection,
            token=token,
            mode=args.mode,
        )
    except (OSError, json.JSONDecodeError, HygieneError) as error:
        print(f"repository hygiene audit failed: {error}", file=sys.stderr)
        return 2
    write_json(args.json_out, report)
    write_text(args.markdown_out, render_markdown(report))
    print(
        f"checked {report['summary']['repositories_checked']} repositories; "
        f"found {report['summary']['finding_count']} hygiene findings"
    )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
