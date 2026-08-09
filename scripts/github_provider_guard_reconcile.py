#!/usr/bin/env python3
"""Create missing Atlas default-branch guards without rewriting existing protection.

The reconciler is deliberately create-only. It reads the authoritative public
repository projection and GitHub conformance requirements, identifies repositories
where ``default_branch_guard`` is required, and creates the baseline Atlas ruleset
only when the repository has no ruleset, no classic branch protection, and no
other effective branch rule on its default branch.

Existing rulesets and classic protection are never modified or removed. Repositories
with unexpected provider state fail closed for human review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTION = ROOT / "policy" / "public-repository-classifications.json"
DEFAULT_REQUIREMENTS = ROOT / "policy" / "github-conformance-requirements.json"
AUTHORITY = "AtlasReaper311/atlas-infra"
OWNER = "AtlasReaper311"
PROJECTION_SCHEMA = "atlas-public-repository-classifications/projection/v1"
REQUIREMENTS_SCHEMA = "atlas-github-conformance-requirements/v1"
REPORT_SCHEMA = "atlas-github-provider-guard-reconciler/report/v1"
RULESET_NAME = "Atlas default branch PR guard"
API_VERSION = "2022-11-28"
APPLY_CONFIRMATION = "APPLY MISSING BASELINE GUARDS"
REQUIRED_RULES = {"deletion", "non_fast_forward", "pull_request"}


class ReconcileError(RuntimeError):
    """Raised when provider state cannot be reconciled safely."""


class GitHubApiError(ReconcileError):
    """Describe a failed GitHub API call without exposing credentials."""

    def __init__(self, status: int, method: str, path: str, message: str) -> None:
        super().__init__(f"GitHub API {method} {path} returned {status}: {message}")
        self.status = status
        self.method = method
        self.path = path


class GitHubClient:
    """Small GitHub REST client supporting only the reads and create used here."""

    def __init__(self, token: str, *, api_url: str = "https://api.github.com") -> None:
        self.token = token.strip()
        self.api_url = api_url.rstrip("/")

    def _url(self, path: str) -> str:
        if path.startswith("https://"):
            return path
        return self.api_url + "/" + path.lstrip("/")

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "atlas-provider-guard-reconciler/1.0",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self._url(path),
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as error:
            try:
                body = error.read()
                parsed = json.loads(body) if body else {}
                message = str(parsed.get("message", "request failed"))
            except (json.JSONDecodeError, AttributeError):
                message = "request failed"
            raise GitHubApiError(error.code, method, path, message) from error
        except urllib.error.URLError as error:
            raise ReconcileError(
                f"GitHub API request failed for {path}: {error.reason}"
            ) from error

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def get_optional(self, path: str) -> Any | None:
        try:
            return self.get(path)
        except GitHubApiError as error:
            if error.status == 404:
                return None
            raise

    def post(self, path: str, payload: Any) -> Any:
        return self.request("POST", path, payload)


@dataclass(frozen=True)
class RepositoryPlan:
    repository: str
    default_branch: str | None
    action: str
    reason: str
    ruleset_id: int | None = None


def canonical_fingerprint(document: Any) -> str:
    encoded = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_projection(path: Path) -> dict[str, Any]:
    projection = load_json(path)
    if not isinstance(projection, dict):
        raise ReconcileError("repository projection root must be an object")
    if projection.get("schema_version") != PROJECTION_SCHEMA:
        raise ReconcileError("unexpected repository projection schema_version")
    if projection.get("authority") != AUTHORITY:
        raise ReconcileError("repository projection authority must be Atlas Infra")
    repositories = projection.get("repositories")
    if not isinstance(repositories, list):
        raise ReconcileError("repository projection repositories must be an array")
    if projection.get("repository_count") != len(repositories):
        raise ReconcileError("repository projection count does not match entries")
    identities: set[str] = set()
    for item in repositories:
        if not isinstance(item, dict):
            raise ReconcileError("repository projection entry must be an object")
        repository = item.get("repository")
        if not isinstance(repository, str) or not repository.startswith(f"{OWNER}/"):
            raise ReconcileError("repository projection contains an invalid identity")
        if repository in identities:
            raise ReconcileError(f"repository projection duplicates {repository}")
        identities.add(repository)
    return projection


def load_requirements(path: Path, projection: dict[str, Any]) -> dict[str, Any]:
    requirements = load_json(path)
    if not isinstance(requirements, dict):
        raise ReconcileError("requirements root must be an object")
    if requirements.get("schema_version") != REQUIREMENTS_SCHEMA:
        raise ReconcileError("unexpected requirements schema_version")
    if requirements.get("authority") != AUTHORITY:
        raise ReconcileError("requirements authority must be Atlas Infra")
    defaults = requirements.get("defaults")
    if not isinstance(defaults, dict) or defaults.get("default_branch_guard") not in {
        "required",
        "not_applicable",
        "exception",
        "deferred",
    }:
        raise ReconcileError("requirements must define default_branch_guard")
    overrides = requirements.get("repositories")
    if not isinstance(overrides, dict):
        raise ReconcileError("requirements repositories must be an object")
    projected = {item["repository"] for item in projection["repositories"]}
    unknown = sorted(set(overrides) - projected)
    if unknown:
        raise ReconcileError(
            "requirements reference repositories outside the projection: "
            + ", ".join(unknown)
        )
    return requirements


def guard_is_required(requirements: dict[str, Any], repository: str) -> bool:
    disposition = requirements["defaults"]["default_branch_guard"]
    override = requirements["repositories"].get(repository, {}).get(
        "default_branch_guard"
    )
    if isinstance(override, dict):
        disposition = override.get("disposition")
    return disposition == "required"


def repo_api_path(repository: str) -> str:
    owner, name = repository.split("/", 1)
    return "/repos/{}/{}".format(
        urllib.parse.quote(owner, safe=""),
        urllib.parse.quote(name, safe=""),
    )


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


def rule_types(rules: Any) -> set[str]:
    if not isinstance(rules, list):
        return set()
    return {
        str(item.get("type"))
        for item in rules
        if isinstance(item, dict) and isinstance(item.get("type"), str)
    }


def ruleset_has_guard(ruleset: dict[str, Any], default_branch: str) -> bool:
    return (
        ruleset.get("target") == "branch"
        and ruleset.get("enforcement") == "active"
        and ruleset_targets_default_branch(ruleset, default_branch)
        and REQUIRED_RULES.issubset(rule_types(ruleset.get("rules")))
    )


def hydrate_rulesets(
    client: GitHubClient, repository: str, payload: Any
) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ReconcileError(f"ruleset list for {repository} was not an array")
    base = repo_api_path(repository)
    hydrated: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ReconcileError(f"ruleset list for {repository} contained a non-object")
        candidate = item
        if "conditions" not in item or "rules" not in item:
            ruleset_id = item.get("id")
            if not isinstance(ruleset_id, int):
                raise ReconcileError(f"ruleset summary for {repository} lacked an id")
            detail = client.get(f"{base}/rulesets/{ruleset_id}")
            if not isinstance(detail, dict):
                raise ReconcileError(f"ruleset detail for {repository} was not an object")
            candidate = detail
        hydrated.append(candidate)
    return hydrated


def classic_pull_request_guard(protection: Any) -> bool:
    return isinstance(protection, dict) and protection.get(
        "required_pull_request_reviews"
    ) is not None


def active_rules_have_guard(active_rules: Any) -> bool:
    return isinstance(active_rules, list) and REQUIRED_RULES.issubset(
        rule_types(active_rules)
    )


def inspect_repository(client: GitHubClient, repository: str) -> RepositoryPlan:
    base = repo_api_path(repository)
    metadata = client.get(base)
    if not isinstance(metadata, dict):
        raise ReconcileError(f"repository metadata for {repository} was not an object")
    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise ReconcileError(f"repository {repository} has no readable default branch")
    if metadata.get("visibility") != "public":
        return RepositoryPlan(
            repository,
            default_branch,
            "blocked",
            "projected repository is no longer public",
        )
    if metadata.get("archived") is True:
        return RepositoryPlan(
            repository,
            default_branch,
            "blocked",
            "projected repository is archived; automatic provider writes are forbidden",
        )

    rulesets = hydrate_rulesets(
        client,
        repository,
        client.get(f"{base}/rulesets?per_page=100"),
    )
    for ruleset in rulesets:
        if ruleset_has_guard(ruleset, default_branch):
            ruleset_id = ruleset.get("id")
            return RepositoryPlan(
                repository,
                default_branch,
                "compliant",
                "active default-branch ruleset already satisfies the Atlas guard",
                ruleset_id if isinstance(ruleset_id, int) else None,
            )

    quoted_branch = urllib.parse.quote(default_branch, safe="")
    protection = client.get_optional(f"{base}/branches/{quoted_branch}/protection")
    if classic_pull_request_guard(protection):
        return RepositoryPlan(
            repository,
            default_branch,
            "compliant",
            "classic branch protection already requires pull requests",
        )

    active_rules = client.get(f"{base}/rules/branches/{quoted_branch}")
    if active_rules_have_guard(active_rules):
        return RepositoryPlan(
            repository,
            default_branch,
            "compliant",
            "effective branch rules already satisfy the Atlas guard",
        )

    if rulesets:
        return RepositoryPlan(
            repository,
            default_branch,
            "blocked",
            "repository has rulesets but none satisfy the guard; automatic migration is forbidden",
        )
    if protection is not None:
        return RepositoryPlan(
            repository,
            default_branch,
            "blocked",
            "classic protection exists without a pull-request guard; automatic migration is forbidden",
        )
    if isinstance(active_rules, list) and active_rules:
        return RepositoryPlan(
            repository,
            default_branch,
            "blocked",
            "effective branch rules exist but do not satisfy the guard",
        )
    if not isinstance(active_rules, list):
        raise ReconcileError(f"active rules for {repository} were not an array")

    return RepositoryPlan(
        repository,
        default_branch,
        "create",
        "repository is governed and has no existing branch-protection mechanism",
    )


def baseline_ruleset_payload() -> dict[str, Any]:
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": ["~DEFAULT_BRANCH"],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": False,
                },
            },
        ],
    }


def verify_created_ruleset(
    client: GitHubClient,
    repository: str,
    default_branch: str,
    ruleset_id: int,
) -> None:
    base = repo_api_path(repository)
    detail = client.get(f"{base}/rulesets/{ruleset_id}")
    if not isinstance(detail, dict):
        raise ReconcileError(f"created ruleset detail for {repository} was not an object")
    if detail.get("id") != ruleset_id:
        raise ReconcileError(f"created ruleset id changed for {repository}")
    if detail.get("name") != RULESET_NAME:
        raise ReconcileError(f"created ruleset name changed for {repository}")
    if detail.get("target") != "branch" or detail.get("enforcement") != "active":
        raise ReconcileError(f"created ruleset target/enforcement invalid for {repository}")
    bypass = detail.get("bypass_actors")
    if not isinstance(bypass, list) or bypass:
        raise ReconcileError(f"created ruleset unexpectedly has bypass actors for {repository}")
    if not ruleset_targets_default_branch(detail, default_branch):
        raise ReconcileError(f"created ruleset does not target default branch for {repository}")
    if rule_types(detail.get("rules")) != REQUIRED_RULES:
        raise ReconcileError(f"created ruleset rule set changed for {repository}")
    pull_rules = [
        item
        for item in detail.get("rules", [])
        if isinstance(item, dict) and item.get("type") == "pull_request"
    ]
    if len(pull_rules) != 1:
        raise ReconcileError(f"created ruleset pull-request rule invalid for {repository}")
    parameters = pull_rules[0].get("parameters")
    if not isinstance(parameters, dict):
        raise ReconcileError(f"created pull-request parameters missing for {repository}")
    expected = {
        "dismiss_stale_reviews_on_push": False,
        "require_code_owner_review": False,
        "require_last_push_approval": False,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": False,
    }
    for key, value in expected.items():
        if parameters.get(key) != value:
            raise ReconcileError(
                f"created pull-request parameter {key} changed for {repository}"
            )

    quoted_branch = urllib.parse.quote(default_branch, safe="")
    active_rules = client.get(f"{base}/rules/branches/{quoted_branch}")
    if not isinstance(active_rules, list):
        raise ReconcileError(f"active rule readback for {repository} was not an array")
    created_types = {
        str(item.get("type"))
        for item in active_rules
        if isinstance(item, dict) and item.get("ruleset_id") == ruleset_id
    }
    if created_types != REQUIRED_RULES:
        raise ReconcileError(f"created rules are not effective on {repository}")


def build_plan(
    client: GitHubClient,
    projection: dict[str, Any],
    requirements: dict[str, Any],
) -> list[RepositoryPlan]:
    plans: list[RepositoryPlan] = []
    for classification in projection["repositories"]:
        repository = classification["repository"]
        if not guard_is_required(requirements, repository):
            plans.append(
                RepositoryPlan(
                    repository,
                    None,
                    "skipped",
                    "default_branch_guard is not required by current policy",
                )
            )
            continue
        try:
            plans.append(inspect_repository(client, repository))
        except (GitHubApiError, ReconcileError) as error:
            plans.append(RepositoryPlan(repository, None, "blocked", str(error)))
    return plans


def summarize(plans: list[RepositoryPlan]) -> dict[str, int]:
    actions = ("compliant", "create", "blocked", "skipped", "created")
    return {action: sum(1 for plan in plans if plan.action == action) for action in actions}


def write_report(
    path: Path,
    *,
    mode: str,
    projection: dict[str, Any],
    requirements: dict[str, Any],
    plans: list[RepositoryPlan],
    provider_writes_performed: bool,
) -> None:
    document = {
        "schema_version": REPORT_SCHEMA,
        "authority": AUTHORITY,
        "mode": mode,
        "ruleset_name": RULESET_NAME,
        "provider_writes_performed": provider_writes_performed,
        "projection_fingerprint": projection.get("source_fingerprint"),
        "requirements_fingerprint": canonical_fingerprint(requirements),
        "summary": summarize(plans),
        "repositories": [asdict(plan) for plan in plans],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def reconcile(
    client: GitHubClient,
    projection: dict[str, Any],
    requirements: dict[str, Any],
    *,
    mode: str,
    confirmation: str,
) -> tuple[list[RepositoryPlan], bool]:
    plans = build_plan(client, projection, requirements)
    blocked = [plan for plan in plans if plan.action == "blocked"]
    if blocked:
        names = ", ".join(plan.repository for plan in blocked)
        raise ReconcileError(f"provider preflight blocked reconciliation: {names}")

    if mode == "inspect":
        return plans, False
    if mode != "apply":
        raise ReconcileError("mode must be inspect or apply")
    if confirmation != APPLY_CONFIRMATION:
        raise ReconcileError("exact provider-guard apply confirmation is required")

    mutable = list(plans)
    writes = False
    for index, plan in enumerate(plans):
        if plan.action != "create":
            continue
        if plan.default_branch is None:
            raise ReconcileError(f"missing default branch for {plan.repository}")
        base = repo_api_path(plan.repository)
        response = client.post(f"{base}/rulesets", baseline_ruleset_payload())
        if not isinstance(response, dict) or not isinstance(response.get("id"), int):
            raise ReconcileError(f"GitHub did not return a ruleset id for {plan.repository}")
        ruleset_id = int(response["id"])
        verify_created_ruleset(client, plan.repository, plan.default_branch, ruleset_id)
        mutable[index] = RepositoryPlan(
            plan.repository,
            plan.default_branch,
            "created",
            "baseline Atlas default-branch guard created and verified",
            ruleset_id,
        )
        writes = True
    return mutable, writes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or create missing baseline Atlas default-branch guards."
    )
    parser.add_argument("--mode", choices=("inspect", "apply"), default="inspect")
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--json-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        projection = load_projection(args.projection)
        requirements = load_requirements(args.requirements, projection)
        client = GitHubClient(os.environ.get("GITHUB_TOKEN", ""))
        plans, writes = reconcile(
            client,
            projection,
            requirements,
            mode=args.mode,
            confirmation=os.environ.get("ATLAS_PROVIDER_GUARD_CONFIRMATION", ""),
        )
        write_report(
            args.json_out,
            mode=args.mode,
            projection=projection,
            requirements=requirements,
            plans=plans,
            provider_writes_performed=writes,
        )
    except (OSError, json.JSONDecodeError, ReconcileError) as error:
        print(f"provider guard reconciliation failed: {error}", file=sys.stderr)
        return 2

    summary = summarize(plans)
    print(
        "provider guard reconciliation: "
        f"{summary['compliant']} compliant, "
        f"{summary['created']} created, "
        f"{summary['create']} pending creation, "
        f"{summary['blocked']} blocked, "
        f"{summary['skipped']} skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
