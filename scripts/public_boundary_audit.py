#!/usr/bin/env python3
"""Audit governed public projections for protected private repository identities."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Iterable

from github_api import GitHubApiError, GitHubClient


SCHEMA_VERSION = "atlas-public-boundary/audit/v2"
PROJECTION_POLICY_SCHEMA = "atlas-public-boundary/projections/v1"
DEFAULT_PROJECTION_POLICY = (
    Path(__file__).resolve().parents[1] / "policy" / "public-boundary-projections.json"
)
MAX_LOCAL_FILE_BYTES = 1_048_576
MAX_PROJECTION_FILE_BYTES = 2_097_152
SKIP_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "vendor",
}
BINARY_SUFFIXES = {
    ".7z",
    ".avif",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dylib",
    ".eot",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".o",
    ".pdf",
    ".png",
    ".so",
    ".tar",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}


class BoundaryAuditError(RuntimeError):
    """Describe a boundary-audit failure without exposing a protected identity."""


def _finding_fingerprint(repository: str, path: str, line: int | None) -> str:
    """Create a stable fingerprint from public finding coordinates only."""

    material = json.dumps(
        {
            "repository": repository,
            "path": path,
            "line": line,
            "rule": "protected-private-identity-in-public-projection",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return "sha256:" + digest


def _redacted_finding(
    repository: str,
    path: str,
    *,
    line: int | None = None,
) -> dict[str, Any]:
    return {
        "fingerprint": _finding_fingerprint(repository, path, line),
        "repository": repository,
        "path": path,
        "line": line,
    }


def load_protected_identities(path: Path) -> list[str]:
    """Load a protected identity set from local JSON or newline-delimited input."""

    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        raise BoundaryAuditError("protected identity input is empty")

    identities: list[str]
    if stripped.startswith("["):
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            raise BoundaryAuditError("protected identity JSON is malformed") from None
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise BoundaryAuditError(
                "protected identity JSON must be a non-empty string array"
            )
        identities = [item.strip() for item in value]
    else:
        identities = [line.strip() for line in text.splitlines() if line.strip()]

    normalized = sorted(set(identities))
    if not normalized:
        raise BoundaryAuditError("protected identity input contains no usable values")
    return normalized


def _iter_local_files(root: Path, excluded_paths: set[str]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRECTORIES for part in relative.parts):
            continue
        relative_text = relative.as_posix()
        if relative_text in excluded_paths:
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        yield path


def audit_local_tree(
    root: Path,
    identities: list[str],
    *,
    repository: str | None = None,
    excluded_paths: Iterable[str] = (),
) -> dict[str, Any]:
    """Scan one explicitly selected local tree and return redacted coordinates."""

    root = root.resolve(strict=True)
    repository_label = repository or root.name
    exclusions = {Path(value).as_posix() for value in excluded_paths}
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    files_checked = 0

    for path in _iter_local_files(root, exclusions):
        relative = path.relative_to(root).as_posix()
        try:
            data = path.read_bytes()
        except OSError:
            errors.append(f"unable to read selected source path: {relative}")
            continue
        if len(data) > MAX_LOCAL_FILE_BYTES:
            errors.append(f"selected source path exceeds audit size bound: {relative}")
            continue
        if b"\x00" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue

        files_checked += 1
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(identity in line for identity in identities):
                findings.append(
                    _redacted_finding(
                        repository_label,
                        relative,
                        line=line_number,
                    )
                )

    findings = sorted(
        {
            (item["repository"], item["path"], item["line"]): item
            for item in findings
        }.values(),
        key=lambda item: (
            item["repository"],
            item["path"],
            item["line"] or 0,
        ),
    )
    errors = sorted(set(errors))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "local-selected-source",
        "files_checked": files_checked,
        "findings": findings,
        "errors": errors,
        "status": "failed" if findings or errors else "passed",
    }


def discover_private_identities(client: GitHubClient, owner: str) -> list[str]:
    """Derive protected repository identities inside authenticated GitHub context."""

    try:
        repositories = client.paginate(
            "/user/repos?affiliation=owner&visibility=private"
        )
    except Exception:
        raise BoundaryAuditError(
            "cannot discover protected repository identities from authenticated GitHub context"
        ) from None

    identities: set[str] = set()
    for repository in repositories:
        if not isinstance(repository, dict):
            continue
        repository_owner = repository.get("owner")
        if not isinstance(repository_owner, dict):
            continue
        if repository_owner.get("login") != owner:
            continue
        if repository.get("private") is not True:
            continue
        name = repository.get("name")
        full_name = repository.get("full_name")
        if isinstance(name, str) and name:
            identities.add(name)
        if isinstance(full_name, str) and full_name:
            identities.add(full_name)

    if not identities:
        raise BoundaryAuditError(
            "authenticated GitHub context returned no protected repository identities"
        )
    return sorted(identities)


def load_projection_targets(path: Path, owner: str) -> list[dict[str, str]]:
    """Load the explicit public projection coordinates governed by the boundary."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BoundaryAuditError(f"cannot load public projection policy: {error}") from None

    if not isinstance(document, dict):
        raise BoundaryAuditError("public projection policy root must be an object")
    if document.get("schema_version") != PROJECTION_POLICY_SCHEMA:
        raise BoundaryAuditError("unsupported public projection policy schema")
    if document.get("owner") != owner:
        raise BoundaryAuditError("public projection policy owner does not match audit owner")

    raw_targets = document.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise BoundaryAuditError("public projection policy targets must be a non-empty list")

    targets: list[dict[str, str]] = []
    for item in raw_targets:
        if not isinstance(item, dict) or set(item) != {"repository", "path"}:
            raise BoundaryAuditError(
                "public projection targets must contain only repository and path"
            )
        repository = item.get("repository")
        source_path = item.get("path")
        if not isinstance(repository, str) or not repository.startswith(owner + "/"):
            raise BoundaryAuditError("public projection target repository is outside audit owner")
        if not isinstance(source_path, str) or not source_path or source_path.startswith("/"):
            raise BoundaryAuditError("public projection target path is invalid")
        if ".." in Path(source_path).parts:
            raise BoundaryAuditError("public projection target path may not traverse parents")
        targets.append({"repository": repository, "path": source_path})

    normalized = sorted(targets, key=lambda item: (item["repository"], item["path"]))
    if targets != normalized:
        raise BoundaryAuditError("public projection targets must be sorted")
    coordinates = [(item["repository"], item["path"]) for item in targets]
    if len(coordinates) != len(set(coordinates)):
        raise BoundaryAuditError("public projection targets must be unique")
    return targets


def _repository_is_public(client: GitHubClient, repository: str) -> bool:
    owner, name = repository.split("/", 1)
    path = "/repos/{}/{}".format(
        urllib.parse.quote(owner, safe=""),
        urllib.parse.quote(name, safe=""),
    )
    try:
        payload = client.get(path)
    except (GitHubApiError, RuntimeError):
        raise BoundaryAuditError(
            f"cannot verify public projection repository visibility: {repository}"
        ) from None
    return isinstance(payload, dict) and payload.get("private") is False


def _projection_text(client: GitHubClient, repository: str, source_path: str) -> str:
    owner, name = repository.split("/", 1)
    api_path = "/repos/{}/{}/contents/{}".format(
        urllib.parse.quote(owner, safe=""),
        urllib.parse.quote(name, safe=""),
        urllib.parse.quote(source_path, safe="/"),
    )
    try:
        payload = client.get(api_path)
    except (GitHubApiError, RuntimeError):
        raise BoundaryAuditError(
            f"cannot read governed public projection: {repository}:{source_path}"
        ) from None
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise BoundaryAuditError(
            f"governed public projection is not a file: {repository}:{source_path}"
        )
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise BoundaryAuditError(
            f"governed public projection has unsupported encoding: {repository}:{source_path}"
        )
    try:
        data = base64.b64decode(payload["content"], validate=False)
    except (ValueError, TypeError):
        raise BoundaryAuditError(
            f"governed public projection content is malformed: {repository}:{source_path}"
        ) from None
    if len(data) > MAX_PROJECTION_FILE_BYTES:
        raise BoundaryAuditError(
            f"governed public projection exceeds audit size bound: {repository}:{source_path}"
        )
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise BoundaryAuditError(
            f"governed public projection is not UTF-8: {repository}:{source_path}"
        ) from None


def audit_github_public_projections(
    client: GitHubClient,
    owner: str,
    identities: list[str],
    targets: list[dict[str, str]],
) -> dict[str, Any]:
    """Scan only reviewed public projection coordinates for protected identities."""

    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    verified_repositories: dict[str, bool] = {}

    for target in targets:
        repository = target["repository"]
        source_path = target["path"]
        try:
            if repository not in verified_repositories:
                verified_repositories[repository] = _repository_is_public(client, repository)
            if not verified_repositories[repository]:
                raise BoundaryAuditError(
                    f"governed projection repository is not public: {repository}"
                )
            text = _projection_text(client, repository, source_path)
        except BoundaryAuditError as error:
            errors.append(str(error))
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(identity in line for identity in identities):
                findings.append(
                    _redacted_finding(
                        repository,
                        source_path,
                        line=line_number,
                    )
                )

    findings = sorted(
        {
            (item["repository"], item["path"], item["line"]): item
            for item in findings
        }.values(),
        key=lambda item: (
            item["repository"],
            item["path"],
            item["line"] or 0,
        ),
    )
    errors = sorted(set(errors))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "github-public-projections",
        "projection_targets_checked": len(targets),
        "findings": findings,
        "errors": errors,
        "status": "failed" if findings or errors else "passed",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Public/private projection boundary audit",
        "",
        f"Status: **{report['status']}**",
    ]
    if report.get("mode") == "local-selected-source":
        lines.extend(
            [
                "",
                f"UTF-8 source files checked: {report.get('files_checked', 0)}",
            ]
        )
    elif report.get("mode") == "github-public-projections":
        lines.extend(
            [
                "",
                f"Governed public projections checked: {report.get('projection_targets_checked', 0)}",
            ]
        )

    errors = report.get("errors", [])
    findings = report.get("findings", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    if findings:
        lines.extend(
            [
                "",
                "## Redacted findings",
                "",
                "| Public repository | Projection path | Line | Finding fingerprint |",
                "|---|---|---:|---|",
            ]
        )
        for finding in findings:
            line = finding.get("line") or ""
            lines.append(
                "| {repository} | `{path}` | {line} | `{fingerprint}` |".format(
                    repository=finding["repository"],
                    path=finding["path"],
                    line=line,
                    fingerprint=finding["fingerprint"],
                )
            )
    else:
        lines.extend(
            [
                "",
                "No protected repository identities were found in governed public projections.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def write_report(
    report: dict[str, Any],
    json_path: Path | None,
    markdown_path: Path | None,
) -> None:
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(report), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit explicit public projection files for protected private repository identities."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--root", type=Path, help="Explicit local source root to scan.")
    mode.add_argument(
        "--github-owner",
        help="GitHub owner whose private identities are checked against governed projections.",
    )
    parser.add_argument(
        "--protected-identities-file",
        type=Path,
        help="Local JSON or newline-delimited protected identity input. Required with --root.",
    )
    parser.add_argument(
        "--repository",
        help="Public repository label for local mode. Defaults to the root directory name.",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        help="Exact repository-relative path excluded from local scanning. Repeat as needed.",
    )
    parser.add_argument(
        "--projection-policy",
        type=Path,
        default=DEFAULT_PROJECTION_POLICY,
        help="Reviewed public projection coordinates used by GitHub mode.",
    )
    parser.add_argument(
        "--token-env",
        default="GH_DIGEST_PAT",
        help="Environment variable containing the read token for GitHub mode.",
    )
    parser.add_argument("--report", type=Path, help="Optional JSON report path.")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown report path.")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.root is not None:
            if args.protected_identities_file is None:
                raise BoundaryAuditError(
                    "--protected-identities-file is required with --root"
                )
            identities = load_protected_identities(args.protected_identities_file)
            report = audit_local_tree(
                args.root,
                identities,
                repository=args.repository,
                excluded_paths=args.exclude_path,
            )
        else:
            if args.protected_identities_file is not None:
                raise BoundaryAuditError(
                    "--protected-identities-file cannot be used with --github-owner"
                )
            token = os.environ.get(args.token_env, "").strip()
            if not token:
                raise BoundaryAuditError(
                    f"authenticated GitHub token is unavailable in environment variable {args.token_env}"
                )
            client = GitHubClient(token)
            identities = discover_private_identities(client, args.github_owner)
            targets = load_projection_targets(args.projection_policy, args.github_owner)
            report = audit_github_public_projections(
                client,
                args.github_owner,
                identities,
                targets,
            )
    except (BoundaryAuditError, OSError) as error:
        print(f"public boundary audit failed: {error}", file=sys.stderr)
        return 2

    write_report(report, args.report, args.markdown)
    if not args.quiet:
        print(render_markdown(report), end="")
    return 1 if report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
