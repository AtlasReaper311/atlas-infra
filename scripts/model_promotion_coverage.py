#!/usr/bin/env python3
"""Synchronize the Atlas model promotion and eval coverage Project."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("policy/model-promotion-coverage.json")
DEFAULT_REPORT = Path("reports/model-promotion-coverage-sync.json")
API_VERSION = "2022-11-28"
REST_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
APPLY_CONFIRMATION = "SYNC MODEL PROMOTION COVERAGE"


class GitHubError(RuntimeError):
    """Describe a GitHub API failure without exposing credentials."""


def quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="/")


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
                "User-Agent": "atlas-model-promotion-coverage/1.0",
                "X-GitHub-Api-Version": API_VERSION,
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                return json.loads(data) if data else None
        except urllib.error.HTTPError as error:
            message = "request failed"
            try:
                message = json.loads(error.read()).get("message", message)
            except (json.JSONDecodeError, AttributeError):
                pass
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

    def rest_get_optional(self, path: str) -> Any | None:
        url = self.api_url + "/" + path.lstrip("/")
        try:
            return self.request_json("GET", url)
        except GitHubError as error:
            if " returned 404:" in str(error):
                return None
            raise


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {"owner", "project_number", "field_names", "capabilities", "eval_harness_repository"}
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"model promotion coverage config missing keys: {', '.join(missing)}")
    return config


def decode_content(payload: Any) -> str | None:
    if not isinstance(payload, dict) or payload.get("type") != "file":
        return None
    if payload.get("encoding") != "base64":
        raise GitHubError("unsupported GitHub content encoding")
    return base64.b64decode(payload["content"]).decode("utf-8")


def fetch_text(client: GitHubClient, owner: str, repository: str, path: str) -> str | None:
    payload = client.rest_get_optional(
        f"/repos/{owner}/{repository}/contents/{quote_path(path)}"
    )
    return decode_content(payload)


def resolve_live_model(
    client: GitHubClient, capability: dict[str, Any], owner: str
) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    for source in capability.get("live_model_sources", []):
        repo = source["repository"]
        path = source["path"]
        text = fetch_text(client, owner, repo, path)
        evidence = f"{owner}/{repo}:{path}"
        if text is None:
            errors.append(f"missing live model source {evidence}")
            continue
        match = re.search(source["pattern"], text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"'), evidence, errors
        errors.append(f"pattern did not match {evidence}")
    return "", "", errors


def eval_case_count(client: GitHubClient, config: dict[str, Any], capability: dict[str, Any]) -> tuple[int, list[str]]:
    owner = config["owner"]
    harness = config["eval_harness_repository"]
    found: list[str] = []
    for path in capability.get("eval_case_paths", []):
        text = fetch_text(client, owner, harness, path)
        if text is not None:
            found.append(path)
    return len(found), found


def promotion_model(
    client: GitHubClient, config: dict[str, Any], capability: dict[str, Any]
) -> tuple[str, str, list[str]]:
    owner = config["owner"]
    harness = config["eval_harness_repository"]
    missing: list[str] = []
    for path in capability.get("promotion_record_paths", []):
        text = fetch_text(client, owner, harness, path)
        if text is None:
            missing.append(path)
            continue
        payload = json.loads(text)
        model = payload.get("model", {})
        if isinstance(model, dict) and model.get("name"):
            return str(model["name"]), f"{owner}/{harness}:{path}", missing
        missing.append(f"{path} has no model.name")
    return "", "", missing


def coverage_status(
    capability: dict[str, Any],
    *,
    live_model: str,
    eval_cases: int,
    promoted_model: str,
    missing_promotions: list[str],
) -> str:
    if capability.get("coverage_override"):
        return str(capability["coverage_override"])
    if not live_model:
        return "Live model unverified"
    if eval_cases == 0:
        return "No eval case"
    if missing_promotions:
        return "Promotion record missing"
    if not promoted_model:
        return "Eval case exists - no promotion"
    if promoted_model == live_model:
        return "Promoted - matches live"
    return "Promoted - does not match live"


def status_for(action_needed: str, coverage: str) -> str:
    if action_needed in {"No action", "Monitor only"} or coverage == "Promoted - matches live":
        return "Done"
    return "Todo"


def action_for(capability: dict[str, Any], coverage: str) -> str:
    if coverage == "Live model unverified":
        return "Confirm live model"
    if coverage == "No eval case":
        return "Add eval case"
    if coverage in {"Eval case exists - no promotion", "Promotion record missing"}:
        return "Create promotion record"
    if coverage == "Promoted - does not match live":
        return "Decide live/promoted mismatch"
    if coverage == "Promoted - matches live":
        return "No action"
    if coverage == "Exempt - low risk":
        return "Monitor only"
    return str(capability["action_needed"])


def item_body(row: dict[str, Any]) -> str:
    lines = [
        f"Capability: {row['capability_id']}",
        f"Source: {row['source']}",
        f"Risk: {row['risk']}",
        f"Coverage: {row['coverage_status']}",
        f"Live model: {row['live_model'] or 'unverified'}",
        f"Promoted model: {row['promoted_model'] or 'none verified'}",
        f"Eval cases: {row['eval_case_count']}",
        f"Next step: {row['next_step']}",
    ]
    if row["live_evidence"]:
        lines.append(f"Live evidence: {row['live_evidence']}")
    if row["promotion_evidence"]:
        lines.append(f"Promotion evidence: {row['promotion_evidence']}")
    if row["eval_case_paths"]:
        lines.append("Eval case paths: " + ", ".join(row["eval_case_paths"]))
    if row["missing_promotion_paths"]:
        lines.append("Missing promotion paths: " + ", ".join(row["missing_promotion_paths"]))
    if row["notes"]:
        lines.append("")
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in row["notes"])
    if row["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in row["warnings"])
    return "\n".join(lines)


def build_rows(client: GitHubClient, config: dict[str, Any], *, today: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    owner = config["owner"]
    for capability in config["capabilities"]:
        live_model, live_evidence, warnings = resolve_live_model(client, capability, owner)
        case_count, case_paths = eval_case_count(client, config, capability)
        promoted, promotion_evidence, missing_promotions = promotion_model(
            client, config, capability
        )
        coverage = coverage_status(
            capability,
            live_model=live_model,
            eval_cases=case_count,
            promoted_model=promoted,
            missing_promotions=missing_promotions,
        )
        action = action_for(capability, coverage)
        row = {
            "title": str(capability["title"]),
            "capability_id": str(capability["id"]),
            "source": str(capability["source"]),
            "risk": str(capability["risk"]),
            "action_needed": action,
            "next_step": str(capability["next_step"]),
            "live_model": live_model,
            "live_evidence": live_evidence,
            "promoted_model": promoted,
            "promotion_evidence": promotion_evidence,
            "eval_case_count": case_count,
            "eval_case_paths": case_paths,
            "coverage_status": coverage,
            "status": status_for(action, coverage),
            "last_verified": today,
            "missing_promotion_paths": missing_promotions,
            "notes": list(capability.get("notes", [])),
            "warnings": warnings,
        }
        row["body"] = item_body(row)
        rows.append(row)
    return rows


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
            ... on DraftIssue { id title body }
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


def fields_by_name(project: dict[str, Any], config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    wanted = set(config["field_names"].values())
    fields: dict[str, dict[str, Any]] = {}
    for field in project.get("fields", {}).get("nodes", []):
        if isinstance(field, dict) and field.get("name") in wanted:
            fields[str(field["name"])] = field
    missing = sorted(wanted - set(fields))
    if missing:
        raise GitHubError(f"project is missing fields: {', '.join(missing)}")
    return fields


def option_id(field: dict[str, Any], name: str) -> str:
    for option in field.get("options", []):
        if option.get("name") == name:
            return str(option["id"])
    raise GitHubError(f"field {field.get('name')} has no option {name!r}")


def items_by_title(project: dict[str, Any]) -> dict[str, dict[str, str]]:
    items: dict[str, dict[str, str]] = {}
    for item in project.get("items", {}).get("nodes", []):
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, dict) and content.get("__typename") == "DraftIssue":
            items[str(content["title"])] = {
                "item_id": str(item["id"]),
                "draft_id": str(content["id"]),
                "body": str(content.get("body", "")),
            }
    return items


def add_draft_item(client: GitHubClient, project_id: str, title: str, body: str) -> tuple[str, str]:
    query = """
    mutation($project:ID!,$title:String!,$body:String!) {
      addProjectV2DraftIssue(input:{projectId:$project,title:$title,body:$body}) {
        projectItem {
          id
          content {
            ... on DraftIssue { id }
          }
        }
      }
    }
    """
    data = client.graphql(query, {"project": project_id, "title": title, "body": body})
    item = data.get("addProjectV2DraftIssue", {}).get("projectItem")
    if not isinstance(item, dict):
        raise GitHubError("addProjectV2DraftIssue did not return a project item")
    content = item.get("content")
    if not isinstance(content, dict):
        raise GitHubError("addProjectV2DraftIssue did not return draft content")
    return str(item["id"]), str(content["id"])


def update_draft_item(client: GitHubClient, draft_id: str, title: str, body: str) -> None:
    query = """
    mutation($draft:ID!,$title:String!,$body:String!) {
      updateProjectV2DraftIssue(input:{draftIssueId:$draft,title:$title,body:$body}) {
        draftIssue { id }
      }
    }
    """
    client.graphql(query, {"draft": draft_id, "title": title, "body": body})


def update_field(
    client: GitHubClient,
    project_id: str,
    item_id: str,
    field: dict[str, Any],
    value: str | int,
) -> None:
    data_type = field.get("dataType")
    if field.get("__typename") == "ProjectV2SingleSelectField":
        field_value = {"singleSelectOptionId": option_id(field, str(value))}
    elif data_type == "NUMBER":
        field_value = {"number": float(value)}
    elif data_type == "DATE":
        field_value = {"date": str(value)}
    else:
        field_value = {"text": str(value)}
    query = """
    mutation($project:ID!,$item:ID!,$field:ID!,$value:ProjectV2FieldValue!) {
      updateProjectV2ItemFieldValue(
        input:{projectId:$project,itemId:$item,fieldId:$field,value:$value}
      ) { projectV2Item { id } }
    }
    """
    client.graphql(
        query,
        {
            "project": project_id,
            "item": item_id,
            "field": field["id"],
            "value": field_value,
        },
    )


def build_plan(project: dict[str, Any], rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    existing = items_by_title(project)
    actions: list[dict[str, Any]] = []
    for row in rows:
        current = existing.get(row["title"])
        if current is None:
            actions.append({"action": "add_item", "title": row["title"]})
            item_id = "<after-add>"
        else:
            item_id = current["item_id"]
            draft_id = current["draft_id"]
            if current.get("body") != row["body"]:
                actions.append(
                    {
                        "action": "update_item_body",
                        "draft_id": draft_id,
                        "title": row["title"],
                    }
                )
        for key, field_name in config["field_names"].items():
            if key == "status":
                value = row["status"]
            elif key in row:
                value = row[key]
            else:
                continue
            actions.append(
                {
                    "action": "set_field",
                    "item_id": item_id,
                    "title": row["title"],
                    "field": field_name,
                    "value": value,
                }
            )
    return {
        "project": {
            "id": project["id"],
            "title": project.get("title"),
            "number": config["project_number"],
        },
        "summary": {
            "capabilities": len(rows),
            "items_present": len(existing),
            "items_to_add": sum(1 for action in actions if action["action"] == "add_item"),
            "items_to_update": sum(1 for action in actions if action["action"] == "update_item_body"),
            "field_updates": sum(1 for action in actions if action["action"] == "set_field"),
        },
        "actions": actions,
        "rows": rows,
    }


def apply_plan(
    client: GitHubClient,
    plan: dict[str, Any],
    fields: dict[str, dict[str, Any]],
) -> dict[str, str]:
    project_id = str(plan["project"]["id"])
    rows = {row["title"]: row for row in plan["rows"]}
    item_ids: dict[str, str] = {}
    draft_ids: dict[str, str] = {}
    for action in plan["actions"]:
        title = action["title"]
        row = rows[title]
        if action["action"] == "add_item":
            item_id, draft_id = add_draft_item(client, project_id, title, row["body"])
            item_ids[title] = item_id
            draft_ids[title] = draft_id
        elif action["action"] == "update_item_body":
            update_draft_item(client, action["draft_id"], title, row["body"])
        elif action["action"] == "set_field":
            item_id = action["item_id"]
            if item_id == "<after-add>":
                item_id = item_ids[title]
            update_field(client, project_id, item_id, fields[action["field"]], action["value"])
    return item_ids


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--confirm",
        default=os.environ.get("ATLAS_MODEL_COVERAGE_CONFIRMATION", ""),
        help="Required confirmation phrase for --apply",
    )
    parser.add_argument("--today", default=dt.datetime.now(dt.UTC).date().isoformat())
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
    rows = build_rows(client, config, today=args.today)
    project = project_state(client, config)
    fields = fields_by_name(project, config)
    plan = build_plan(project, rows, config)
    report = {"mode": "apply" if args.apply else "dry-run", **plan}
    if args.apply:
        report["added_items"] = apply_plan(client, plan, fields)
    write_report(args.json_out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
