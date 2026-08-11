#!/usr/bin/env python3
"""Synchronize the Atlas estate rollout GitHub Project."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("policy/estate-rollout-board.json")
DEFAULT_REPORT = Path("reports/estate-rollout-board-sync.json")
API_VERSION = "2022-11-28"
GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"
APPLY_CONFIRMATION = "SYNC ESTATE ROLLOUT BOARD"


class GitHubError(RuntimeError):
    """Describe a GitHub API failure without exposing credentials."""


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubClient:
    def __init__(self, token: str, *, api_url: str = REST_URL) -> None:
        self.token = token.strip()
        self.api_url = api_url.rstrip("/")

    def request_json(self, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "atlas-estate-rollout-board/1.0",
                "X-GitHub-Api-Version": API_VERSION,
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read()
                return json.loads(response_body) if response_body else None
        except urllib.error.HTTPError as error:
            message = "request failed"
            try:
                message = json.loads(error.read()).get("message", message)
            except (json.JSONDecodeError, AttributeError) as parse_error:
                message = f"{message} (unable to parse GitHub error response: {parse_error})"
            raise GitHubError(f"GitHub API {method} {url} returned {error.code}: {message}") from error
        except urllib.error.URLError as error:
            raise GitHubError(f"GitHub API {method} {url} failed: {error.reason}") from error

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = self.request_json("POST", GRAPHQL_URL, {"query": query, "variables": variables})
        if not isinstance(payload, dict):
            raise GitHubError("GitHub GraphQL returned a non-object payload")
        if payload.get("errors"):
            messages = "; ".join(str(error.get("message", "GraphQL error")) for error in payload["errors"])
            raise GitHubError(f"GitHub GraphQL error: {messages}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise GitHubError("GitHub GraphQL response did not include data")
        return data

    def rest_get(self, path: str) -> Any:
        return self.request_json("GET", self.api_url + "/" + path.lstrip("/"))

    def paginate(self, path: str) -> list[Any]:
        separator = "&" if "?" in path else "?"
        page = 1
        items: list[Any] = []
        while True:
            payload = self.rest_get(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(payload, list):
                raise GitHubError(f"Expected list payload from {path}")
            items.extend(payload)
            if len(payload) < 100:
                return items
            page += 1


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "owner",
        "project_number",
        "archive_after_done_days",
        "field_names",
        "repositories",
        "status_rules",
        "stage_rules",
    }
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"rollout board config missing keys: {', '.join(missing)}")
    return config


def label_names(pull: dict[str, Any]) -> set[str]:
    return {
        str(label.get("name", "")).strip().lower()
        for label in pull.get("labels", [])
        if isinstance(label, dict)
    }


def author_name(pull: dict[str, Any]) -> str:
    user = pull.get("user")
    if not isinstance(user, dict):
        return ""
    login = str(user.get("login", ""))
    user_type = str(user.get("type", "")).lower()
    return f"app/{login}" if user_type == "bot" else login


def is_excluded(pull: dict[str, Any], config: dict[str, Any]) -> bool:
    labels = label_names(pull)
    excluded_labels = {str(value).lower() for value in config.get("excluded_labels", [])}
    if labels & excluded_labels:
        return True
    excluded_prefixes = [
        str(value).lower() for value in config.get("excluded_label_prefixes", [])
    ]
    if any(label.startswith(prefix) for label in labels for prefix in excluded_prefixes):
        return True
    title = str(pull.get("title", "")).strip().lower()
    if any(
        title.startswith(str(prefix).lower())
        for prefix in config.get("excluded_title_prefixes", [])
    ):
        return True
    return author_name(pull).lower() in {
        str(value).lower() for value in config.get("excluded_authors", [])
    }


def body_text(pull: dict[str, Any]) -> str:
    return "\n".join(
        str(pull.get(key) or "") for key in ("title", "body")
    ).lower()


def is_gated(pull: dict[str, Any], config: dict[str, Any]) -> bool:
    text = body_text(pull)
    return any(str(marker).lower() in text for marker in config.get("gated_markers", []))


def status_for(pull: dict[str, Any], config: dict[str, Any]) -> str:
    rules = config["status_rules"]
    if pull.get("merged_at"):
        return rules["merged"]
    if pull.get("state") == "closed":
        return rules["closed"]
    if pull.get("draft"):
        return rules["open_draft"]
    return rules["open_ready"]


def stage_for(pull: dict[str, Any], config: dict[str, Any]) -> str:
    rules = config["stage_rules"]
    if pull.get("merged_at"):
        return rules["merged"]
    if pull.get("state") == "closed":
        return rules["closed"]
    if pull.get("draft"):
        return rules["open_draft"]
    if is_gated(pull, config):
        return rules["gated"]
    return rules["open_ready"]


def agent_for(pull: dict[str, Any], config: dict[str, Any]) -> str | None:
    labels = label_names(pull)
    for label, agent in config.get("agent_label_values", {}).items():
        if label.lower() in labels:
            return str(agent)
    prefix = str(config.get("agent_label_prefix", "")).lower()
    if not prefix:
        return None
    for label in labels:
        if label.startswith(prefix):
            candidate = label.removeprefix(prefix).strip().title()
            return candidate or None
    return None


def pillar_for(repository_name: str, config: dict[str, Any]) -> str:
    repositories = config["repositories"]
    if repository_name not in repositories:
        raise ValueError(f"repository {repository_name} has no pillar rule")
    pillar = repositories[repository_name].get("pillar")
    if not pillar:
        raise ValueError(f"repository {repository_name} has no pillar value")
    return str(pillar)


def should_archive(pull: dict[str, Any], config: dict[str, Any], *, now: dt.datetime) -> bool:
    closed_at = parse_time(pull.get("closed_at"))
    if pull.get("state") != "closed" or closed_at is None:
        return False
    grace = dt.timedelta(days=int(config["archive_after_done_days"]))
    return now - closed_at >= grace


def collect_open_pull_requests(client: GitHubClient, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    owner = config["owner"]
    pulls: dict[str, dict[str, Any]] = {}
    for repo_name in sorted(config["repositories"]):
        path = f"/repos/{owner}/{repo_name}/pulls?state=open&sort=updated&direction=desc"
        for pull in client.paginate(path):
            if not isinstance(pull, dict):
                continue
            if is_excluded(pull, config):
                continue
            url = str(pull.get("html_url", ""))
            if not url:
                continue
            pull["_atlas_repository_name"] = repo_name
            pulls[url] = pull
    return pulls


PROJECT_QUERY = """
query($login:String!,$number:Int!) {
  user(login:$login) {
    projectV2(number:$number) {
      id
      title
      fields(first:50) {
        nodes {
          __typename
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options { id name }
          }
        }
      }
      items(first:100, archivedStates:[NOT_ARCHIVED]) {
        nodes {
          id
          content {
            __typename
            ... on PullRequest {
              url
              number
              state
              title
              mergedAt
              closedAt
              repository { nameWithOwner }
            }
          }
        }
      }
    }
  }
}
"""


def project_state(client: GitHubClient, config: dict[str, Any]) -> dict[str, Any]:
    data = client.graphql(
        PROJECT_QUERY,
        {"login": config["owner"], "number": int(config["project_number"])},
    )
    project = data.get("user", {}).get("projectV2")
    if not isinstance(project, dict):
        raise GitHubError("configured project was not found")
    return project


def field_lookup(project: dict[str, Any], config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    wanted = set(config["field_names"].values())
    fields: dict[str, dict[str, Any]] = {}
    for field in project.get("fields", {}).get("nodes", []):
        if isinstance(field, dict) and field.get("name") in wanted:
            fields[str(field["name"])] = field
    missing = sorted(wanted - set(fields))
    if missing:
        raise GitHubError(f"project is missing required fields: {', '.join(missing)}")
    return fields


def option_id(field: dict[str, Any], value: str) -> str:
    for option in field.get("options", []):
        if option.get("name") == value:
            return str(option["id"])
    raise GitHubError(f"field {field.get('name')} has no option {value!r}")


def project_items_by_url(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for item in project.get("items", {}).get("nodes", []):
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, dict) and content.get("__typename") == "PullRequest":
            items[str(content.get("url"))] = item
    return items


def pull_from_project_item(item: dict[str, Any]) -> dict[str, Any] | None:
    content = item.get("content")
    if not isinstance(content, dict) or content.get("__typename") != "PullRequest":
        return None
    repository = str(content.get("repository", {}).get("nameWithOwner", ""))
    if "/" not in repository:
        return None
    state = str(content.get("state", "")).lower()
    if state == "merged":
        state = "closed"
    return {
        "html_url": content.get("url"),
        "state": state,
        "title": content.get("title") or "",
        "body": "",
        "draft": False,
        "merged_at": content.get("mergedAt"),
        "closed_at": content.get("closedAt"),
        "labels": [],
        "_atlas_repository_name": repository.split("/", 1)[1],
    }


def add_item(client: GitHubClient, project_id: str, content_id: str) -> str:
    query = """
    mutation($project:ID!,$content:ID!) {
      addProjectV2ItemById(input:{projectId:$project, contentId:$content}) {
        item { id }
      }
    }
    """
    data = client.graphql(query, {"project": project_id, "content": content_id})
    item = data.get("addProjectV2ItemById", {}).get("item")
    if not isinstance(item, dict) or not item.get("id"):
        raise GitHubError("addProjectV2ItemById did not return an item id")
    return str(item["id"])


def update_single_select(
    client: GitHubClient,
    project_id: str,
    item_id: str,
    field_id: str,
    option: str,
) -> None:
    query = """
    mutation($project:ID!,$item:ID!,$field:ID!,$option:String!) {
      updateProjectV2ItemFieldValue(
        input:{
          projectId:$project,
          itemId:$item,
          fieldId:$field,
          value:{singleSelectOptionId:$option}
        }
      ) { projectV2Item { id } }
    }
    """
    client.graphql(
        query,
        {"project": project_id, "item": item_id, "field": field_id, "option": option},
    )


def archive_item(client: GitHubClient, project_id: str, item_id: str) -> None:
    query = """
    mutation($project:ID!,$item:ID!) {
      archiveProjectV2Item(input:{projectId:$project,itemId:$item}) {
        item { id }
      }
    }
    """
    client.graphql(query, {"project": project_id, "item": item_id})


def delete_item(client: GitHubClient, project_id: str, item_id: str) -> None:
    query = """
    mutation($project:ID!,$item:ID!) {
      deleteProjectV2Item(input:{projectId:$project,itemId:$item}) {
        deletedItemId
      }
    }
    """
    client.graphql(query, {"project": project_id, "item": item_id})


def retention_action(config: dict[str, Any]) -> str:
    action = str(config.get("done_retention_action", "archive")).lower()
    if action not in {"archive", "delete"}:
        raise ValueError("done_retention_action must be archive or delete")
    return action


def pull_node_ids(client: GitHubClient, urls: list[str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for url in urls:
        parts = url.removeprefix("https://github.com/").split("/")
        if len(parts) < 4 or parts[2] != "pull":
            raise GitHubError(f"cannot parse pull request URL {url}")
        owner, repo, number = parts[0], parts[1], parts[3]
        data = client.graphql(
            """
            query($owner:String!,$repo:String!,$number:Int!) {
              repository(owner:$owner,name:$repo) {
                pullRequest(number:$number) { id }
              }
            }
            """,
            {"owner": owner, "repo": repo, "number": int(number)},
        )
        pull = data.get("repository", {}).get("pullRequest")
        if not isinstance(pull, dict) or not pull.get("id"):
            raise GitHubError(f"could not resolve GraphQL id for {url}")
        ids[url] = str(pull["id"])
    return ids


def build_plan(
    project: dict[str, Any],
    pulls: dict[str, dict[str, Any]],
    config: dict[str, Any],
    *,
    now: dt.datetime,
) -> dict[str, Any]:
    items = project_items_by_url(project)
    plan = {
        "project": {
            "id": project["id"],
            "title": project.get("title"),
            "number": config["project_number"],
        },
        "summary": {
            "pulls_considered": len(pulls),
            "items_present": len(items),
            "items_to_add": 0,
            "field_updates": 0,
            "items_to_archive": 0,
        },
        "actions": [],
    }
    for url, pull in sorted(pulls.items()):
        repo_name = str(pull["_atlas_repository_name"])
        item = items.get(url)
        item_id = item.get("id") if item else None
        if item_id is None:
            plan["actions"].append({"action": "add_item", "url": url})
            plan["summary"]["items_to_add"] += 1
            item_id = "<after-add>"
        desired = {
            "Status": status_for(pull, config),
            "Stage": stage_for(pull, config),
            "Pillar": pillar_for(repo_name, config),
        }
        agent = agent_for(pull, config)
        if agent:
            desired["Agent"] = agent
        for field, value in desired.items():
            plan["actions"].append(
                {
                    "action": "set_field",
                    "item_id": item_id,
                    "url": url,
                    "field": field,
                    "value": value,
                }
            )
            plan["summary"]["field_updates"] += 1
        if item and should_archive(pull, config, now=now):
            plan["actions"].append(
                {
                    "action": f"{retention_action(config)}_item",
                    "item_id": item["id"],
                    "url": url,
                    "reason": f"closed for at least {config['archive_after_done_days']} days",
                }
            )
            plan["summary"]["items_to_archive"] += 1
    for url, item in sorted(items.items()):
        if url in pulls:
            continue
        pull = pull_from_project_item(item)
        if pull is None:
            continue
        repo_name = str(pull.get("_atlas_repository_name", ""))
        if pull.get("state") != "closed":
            if repo_name in config["repositories"]:
                plan["actions"].append(
                    {
                        "action": "archive_item",
                        "item_id": item["id"],
                        "url": url,
                        "reason": "open item no longer matches rollout board rules",
                    }
                )
                plan["summary"]["items_to_archive"] += 1
            continue
        desired = {
            "Status": status_for(pull, config),
            "Stage": stage_for(pull, config),
        }
        for field, value in desired.items():
            plan["actions"].append(
                {
                    "action": "set_field",
                    "item_id": item["id"],
                    "url": url,
                    "field": field,
                    "value": value,
                }
            )
            plan["summary"]["field_updates"] += 1
        if should_archive(pull, config, now=now):
            plan["actions"].append(
                {
                    "action": f"{retention_action(config)}_item",
                    "item_id": item["id"],
                    "url": url,
                    "reason": f"closed for at least {config['archive_after_done_days']} days",
                }
            )
            plan["summary"]["items_to_archive"] += 1
    return plan


def apply_plan(
    client: GitHubClient,
    plan: dict[str, Any],
    fields: dict[str, dict[str, Any]],
) -> dict[str, str]:
    project_id = str(plan["project"]["id"])
    added: dict[str, str] = {}
    add_urls = [action["url"] for action in plan["actions"] if action["action"] == "add_item"]
    content_ids = pull_node_ids(client, add_urls) if add_urls else {}
    for action in plan["actions"]:
        if action["action"] == "add_item":
            added[action["url"]] = add_item(client, project_id, content_ids[action["url"]])
            continue
        if action["action"] == "set_field":
            item_id = action["item_id"]
            if item_id == "<after-add>":
                item_id = added[action["url"]]
            field = fields[action["field"]]
            update_single_select(
                client,
                project_id,
                item_id,
                field["id"],
                option_id(field, action["value"]),
            )
            continue
        if action["action"] == "archive_item":
            archive_item(client, project_id, action["item_id"])
            continue
        if action["action"] == "delete_item":
            delete_item(client, project_id, action["item_id"])
    return added


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true", help="Apply project changes")
    parser.add_argument(
        "--confirm",
        default=os.environ.get("ATLAS_ROLLOUT_BOARD_CONFIRMATION", ""),
        help="Required confirmation phrase for --apply",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit(
            "GITHUB_TOKEN or GH_TOKEN is required; scheduled sync expects "
            "the ATLAS_PROJECTS_TOKEN repository secret"
        )
    if args.apply and args.confirm != APPLY_CONFIRMATION:
        raise SystemExit(f"--apply requires confirmation phrase: {APPLY_CONFIRMATION}")

    config = load_config(args.config)
    client = GitHubClient(token)
    project = project_state(client, config)
    fields = field_lookup(project, config)
    pulls = collect_open_pull_requests(client, config)
    plan = build_plan(project, pulls, config, now=utcnow())
    report = {"mode": "apply" if args.apply else "dry-run", **plan}
    if args.apply:
        report["added_items"] = apply_plan(client, plan, fields)
    write_report(args.json_out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
