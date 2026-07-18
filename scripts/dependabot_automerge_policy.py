#!/usr/bin/env python3
"""Evaluate narrow, fail-closed Dependabot auto-merge eligibility."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


OSV_QUERY_URL = "https://api.osv.dev/v1/query"
SEMVER = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


@dataclass(frozen=True)
class Decision:
    eligible: bool
    reason: str


def _enabled(value: str) -> bool:
    return value.strip().lower() == "true"


def _stable_semver(value: str) -> bool:
    match = SEMVER.fullmatch(value.strip())
    return bool(match and int(match.group("major")) > 0)


def metadata_decision(
    *,
    enabled: str,
    dependency_name: str,
    dependency_type: str,
    update_type: str,
    package_ecosystem: str,
    previous_version: str,
    new_version: str,
    dependency_group: str,
    maintainer_changes: str,
) -> Decision:
    if not _enabled(enabled):
        return Decision(False, "repository-opt-in-disabled")
    if package_ecosystem != "npm":
        return Decision(False, "ecosystem-not-eligible")
    if dependency_type != "direct:development":
        return Decision(False, "dependency-type-not-eligible")
    if update_type != "version-update:semver-patch":
        return Decision(False, "update-type-not-eligible")
    if dependency_group.strip():
        return Decision(False, "grouped-update-not-eligible")
    if maintainer_changes.strip().lower() == "true":
        return Decision(False, "maintainer-changes-present")
    if not dependency_name.strip() or "," in dependency_name:
        return Decision(False, "single-dependency-required")
    if not _stable_semver(previous_version) or not _stable_semver(new_version):
        return Decision(False, "stable-semver-required")
    return Decision(True, "metadata-eligible")


def query_osv(
    dependency_name: str,
    new_version: str,
    *,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> tuple[bool | None, str]:
    body = json.dumps(
        {
            "package": {"ecosystem": "npm", "name": dependency_name},
            "version": new_version,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OSV_QUERY_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "atlas-infra-dependabot-policy/1",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None, "osv-unavailable"
    if not isinstance(payload, dict) or not isinstance(payload.get("vulns", []), list):
        return None, "osv-invalid-response"
    active = [
        item
        for item in payload.get("vulns", [])
        if isinstance(item, dict) and not item.get("withdrawn")
    ]
    if active:
        return True, "osv-active-advisory"
    return False, "osv-clear"


def evaluate_policy(
    *,
    osv_lookup: Callable[[str, str], tuple[bool | None, str]] = query_osv,
    **metadata: str,
) -> Decision:
    decision = metadata_decision(**metadata)
    if not decision.eligible:
        return decision
    vulnerable, reason = osv_lookup(
        metadata["dependency_name"], metadata["new_version"]
    )
    if vulnerable is None:
        return Decision(False, reason)
    if vulnerable:
        return Decision(False, reason)
    return Decision(True, "eligible")


def _write_github_output(path: Path, decision: Decision) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"eligible={'true' if decision.eligible else 'false'}\n")
        handle.write(f"reason={decision.reason}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enabled", required=True)
    parser.add_argument("--dependency-name", required=True)
    parser.add_argument("--dependency-type", required=True)
    parser.add_argument("--update-type", required=True)
    parser.add_argument("--package-ecosystem", required=True)
    parser.add_argument("--previous-version", required=True)
    parser.add_argument("--new-version", required=True)
    parser.add_argument("--dependency-group", default="")
    parser.add_argument("--maintainer-changes", default="false")
    parser.add_argument("--github-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = {
        "enabled": args.enabled,
        "dependency_name": args.dependency_name,
        "dependency_type": args.dependency_type,
        "update_type": args.update_type,
        "package_ecosystem": args.package_ecosystem,
        "previous_version": args.previous_version,
        "new_version": args.new_version,
        "dependency_group": args.dependency_group,
        "maintainer_changes": args.maintainer_changes,
    }
    try:
        decision = evaluate_policy(**metadata)
    except Exception:
        decision = Decision(False, "policy-error")
    if args.github_output is not None:
        _write_github_output(args.github_output, decision)
    print(json.dumps({"eligible": decision.eligible, "reason": decision.reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
