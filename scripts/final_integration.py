#!/usr/bin/env python3
"""Final deterministic integration and readiness gate for Atlas control plane."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    from .control_plane_io import digest_json, load_json, write_json
    from .runbook_bot import validate_index
    from .evidence_ledger import validate_policy as validate_evidence_policy
except ImportError:  # direct script execution
    from control_plane_io import digest_json, load_json, write_json
    from runbook_bot import validate_index
    from evidence_ledger import validate_policy as validate_evidence_policy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy/final-integration.json"
ACTION_USE_RE = re.compile(r"uses:\s*([^\s#]+)")
SHA_RE = re.compile(r"^[^@]+@[0-9a-fA-F]{40}$")
RETENTION_RE = re.compile(r"retention-days:\s*(\d+)")
CRON_RE = re.compile(r"cron:\s*['\"]?([^'\"\n]+)")
TIMEOUT_RE = re.compile(r"timeout-minutes:\s*(\d+)")


def validate_policy(policy: dict[str, Any]) -> list[str]:
    required = {
        "schema_version", "required_files", "optional_files", "deferred_cutovers",
        "expected_warning_ids", "allowed_action_permissions", "max_artifact_retention_days",
        "test_timeout_seconds", "execute_repository_tests",
    }
    errors = [f"missing policy field: {name}" for name in sorted(required - set(policy))]
    if policy.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    return errors


def workflow_inventory(root: Path, max_retention: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    inventory: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    workflow_dir = root / ".github/workflows"
    if not workflow_dir.is_dir():
        return inventory, findings
    for path in sorted(list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        actions = ACTION_USE_RE.findall(text)
        unpinned = sorted(action for action in actions if not action.startswith("./") and not action.startswith("docker://") and not SHA_RE.match(action))
        retention = [int(value) for value in RETENTION_RE.findall(text)]
        timeouts = [int(value) for value in TIMEOUT_RE.findall(text)]
        crons = CRON_RE.findall(text)
        rel = path.relative_to(root).as_posix()
        if unpinned:
            findings.append({"id": "workflow-unpinned-action", "path": rel, "detail": ", ".join(unpinned)})
        if any(value > max_retention for value in retention):
            findings.append({"id": "workflow-retention-too-long", "path": rel, "detail": str(max(retention))})
        if "jobs:" in text and not timeouts:
            findings.append({"id": "workflow-timeout-missing", "path": rel, "detail": "no timeout-minutes found"})
        if "permissions:" not in text:
            findings.append({"id": "workflow-permissions-missing", "path": rel, "detail": "no explicit permissions block"})
        if "concurrency:" not in text:
            findings.append({"id": "workflow-concurrency-missing", "path": rel, "detail": "no concurrency block"})
        inventory.append({"path": rel, "actions": actions, "retention_days": retention, "timeouts": timeouts, "crons": crons})
    return inventory, findings


def backup_gap_count(root: Path) -> int | None:
    policy_path = root / "policy/backup-audit.json"
    if not policy_path.is_file():
        return None
    payload = load_json(policy_path)
    text = json.dumps(payload).lower()
    # Count explicit not-declared declarations without assuming the exact policy shape.
    return text.count('"not-declared"')


def validate(root: Path, policy_path: Path) -> dict[str, Any]:
    policy = load_json(policy_path)
    policy_errors = validate_policy(policy)
    checks: list[dict[str, Any]] = []
    for rel in policy.get("required_files", []):
        exists = (root / rel).is_file()
        checks.append({"id": f"required:{rel}", "status": "passed" if exists else "failed", "path": rel})
    for rel in policy.get("optional_files", []):
        exists = (root / rel).is_file()
        checks.append({"id": f"optional:{rel}", "status": "passed" if exists else "warning", "path": rel})

    runbook_errors: list[str] = []
    runbook_path = root / "policy/runbook-index.json"
    routing_path = root / "policy/runbook-routing.json"
    if runbook_path.is_file() and routing_path.is_file():
        runbook_errors = validate_index(load_json(runbook_path), load_json(routing_path), root)
        checks.append({"id": "runbook-index", "status": "passed" if not runbook_errors else "failed", "errors": runbook_errors})
    elif runbook_path.is_file() or routing_path.is_file():
        runbook_errors = ["runbook index and routing policy must be present together"]
        checks.append({"id": "runbook-index", "status": "failed", "errors": runbook_errors})

    evidence_errors: list[str] = []
    evidence_path = root / "policy/evidence-ledger.json"
    if evidence_path.is_file():
        evidence_errors = validate_evidence_policy(load_json(evidence_path))
        checks.append({"id": "evidence-ledger-policy", "status": "passed" if not evidence_errors else "failed", "errors": evidence_errors})

    workflows, workflow_findings = workflow_inventory(root, int(policy.get("max_artifact_retention_days", 90)))
    checks.append({"id": "workflow-hardening", "status": "passed" if not workflow_findings else "warning", "findings": workflow_findings})

    backup_gaps = backup_gap_count(root)
    if backup_gaps:
        checks.append({"id": "backup-coverage-not-declared", "status": "warning", "count": backup_gaps})

    for deferred in policy.get("deferred_cutovers", []):
        checks.append({"id": deferred["id"], "status": "warning", "state": deferred["state"], "reason": deferred["reason"]})

    statuses = Counter(check["status"] for check in checks)
    overall = "failed" if statuses["failed"] else "warning" if statuses["warning"] else "passed"
    report = {
        "schema_version": "1.0.0",
        "status": overall,
        "policy_errors": policy_errors,
        "summary": dict(sorted(statuses.items())),
        "checks": checks,
        "workflow_inventory": workflows,
        "safety": {
            "deployments": 0,
            "provider_mutations": 0,
            "secrets_created": 0,
            "live_assistant_changes": 0,
        },
    }
    if policy_errors:
        report["status"] = "failed"
    report["report_digest"] = digest_json(report)
    return report


def run_checks(root: Path, policy_path: Path) -> dict[str, Any]:
    policy = load_json(policy_path)
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"],
        [sys.executable, "scripts/validate_control_plane_contracts.py", "--quiet"],
    ]
    results: list[dict[str, Any]] = []
    if not policy.get("execute_repository_tests", True):
        return {"schema_version": "1.0.0", "status": "skipped", "results": []}
    timeout = int(policy.get("test_timeout_seconds", 420))
    for command in commands:
        start = time.monotonic()
        completed = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout, check=False)
        results.append({
            "command": command,
            "exit_code": completed.returncode,
            "duration_seconds": round(time.monotonic() - start, 3),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    report = {"schema_version": "1.0.0", "status": "passed" if all(item["exit_code"] == 0 for item in results) else "failed", "results": results}
    report["report_digest"] = digest_json(report)
    return report


def markdown(report: dict[str, Any], title: str) -> str:
    lines = [f"# {title}", "", f"Overall status: **{report['status']}**", ""]
    for check in report.get("checks", []):
        lines.append(f"- `{check['status']}` {check['id']}")
        if check.get("reason"):
            lines.append(f"  - {check['reason']}")
    for result in report.get("results", []):
        command = " ".join(result["command"])
        lines.append(f"- `{result['exit_code']}` `{command}` ({result['duration_seconds']}s)")
    return "\n".join(lines).rstrip() + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("validate", "checks"):
        command = sub.add_parser(name)
        command.add_argument("--root", type=Path, default=ROOT)
        command.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
        command.add_argument("--report", type=Path)
        command.add_argument("--markdown", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report = validate(args.root, args.policy) if args.command == "validate" else run_checks(args.root, args.policy)
    if args.report:
        write_json(args.report, report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report, "Atlas final integration" if args.command == "validate" else "Atlas final checks"), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
