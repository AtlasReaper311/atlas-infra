#!/usr/bin/env python3
"""Stamp GitHub conformance reports with reproducible evidence identity."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

AUTHORITY = "AtlasReaper311/atlas-infra"
SCHEMA_VERSION = "atlas-github-conformance-scoreboard/report/v2"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class StampError(RuntimeError):
    """Raised when a report cannot be stamped safely."""


def canonical_fingerprint(document: Any) -> str:
    candidate = copy.deepcopy(document)
    if isinstance(candidate, dict):
        candidate.pop("fingerprint", None)
    encoded = json.dumps(
        candidate,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_source_commit(value: str) -> str:
    if not FULL_SHA.fullmatch(value):
        raise StampError("source commit must be a lowercase 40-character Git SHA")
    return value


def validate_collected_at(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise StampError("collected_at must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise StampError("collected_at must include a UTC offset")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def stamp_report(
    report: dict[str, Any],
    *,
    source_commit: str,
    collected_at: str | None = None,
) -> dict[str, Any]:
    if report.get("schema_version") != SCHEMA_VERSION:
        raise StampError("unexpected GitHub conformance report schema_version")
    stamped = copy.deepcopy(report)
    stamped.pop("fingerprint", None)
    stamped["collected_at"] = validate_collected_at(collected_at or utc_now())
    stamped["source"] = {
        "repository": AUTHORITY,
        "commit": validate_source_commit(source_commit),
    }
    stamped["fingerprint"] = canonical_fingerprint(stamped)
    return stamped


def render_markdown_identity(report: dict[str, Any], markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise StampError("scoreboard markdown must begin with a level-one heading")
    rest = lines[1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    identity = [
        "## Evidence identity",
        "",
        f"- Collected at: `{report['collected_at']}`",
        f"- Source: `{report['source']['repository']}@{report['source']['commit']}`",
        f"- Report fingerprint: `{report['fingerprint']}`",
        "",
    ]
    return "\n".join([lines[0], "", *identity, *rest]).rstrip() + "\n"


def stamp_files(
    json_path: Path,
    markdown_path: Path,
    *,
    source_commit: str,
    collected_at: str | None = None,
) -> dict[str, Any]:
    try:
        report = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StampError(f"could not read scoreboard JSON: {error}") from error
    if not isinstance(report, dict):
        raise StampError("scoreboard JSON root must be an object")
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
    except OSError as error:
        raise StampError(f"could not read scoreboard Markdown: {error}") from error

    stamped = stamp_report(
        report,
        source_commit=source_commit,
        collected_at=collected_at,
    )
    json_path.write_text(
        json.dumps(stamped, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown_identity(stamped, markdown),
        encoding="utf-8",
    )
    return stamped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stamp a GitHub conformance scoreboard with evidence identity."
    )
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--collected-at")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = stamp_files(
            args.json,
            args.markdown,
            source_commit=args.source_commit,
            collected_at=args.collected_at,
        )
    except StampError as error:
        print(f"github conformance stamping failed: {error}", file=sys.stderr)
        return 2
    print(
        f"stamped {report['source']['commit']} at {report['collected_at']} "
        f"with {report['fingerprint']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
