#!/usr/bin/env python3
"""Audit public source for protected private repository identities without publishing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Iterable

from github_api import GitHubApiError, GitHubClient


SCHEMA_VERSION = "atlas-public-boundary/audit/v1"
MAX_LOCAL_FILE_BYTES = 1_048_576
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


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _identity_fingerprint(identity: str) -> str:
    return "sha256:" + _sha256(identity)


def _finding_fingerprint(
    identity_fingerprint: str,
    repository: str,
    path: str,
    line: int | None,
) -> str:
    material = json.dumps(
        {
            "identity_fingerprint": identity_fingerprint,
            "repository": repository,
            "path": path,
            "line": line,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + _sha256(material)


def _redacted_finding(
    identity: str,
    repository: str,
    path: str,
    *,
    line: int | None = None,
) -> dict[str, Any]:
    identity_fingerprint = _identity_fingerprint(identity)
    return {
        "fingerprint": _finding_fingerprint(
            identity_fingerprint,
            repository,
            path,
            line,
        ),
        "identity_fingerprint": identity_fingerprint,
        "repository": repository,
        "path": path,
        "line": line,
    }


def load_protected_identities(path: Path) -> list[str]:
    """Load a protected identity set from JSON or newline-delimited local input."""

    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        raise BoundaryAuditError("protected identity input is empty")

    identities: list[str]
    if stripped.startswith("["):
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as error:
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
    """Scan one current source tree and return only redacted identity findings."""

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
            errors.append(f"unable to read public source path: {relative}")
            continue
        if len(data) > MAX_LOCAL_FILE_BYTES:
            errors.append(f"public source path exceeds audit size bound: {relative}")
            continue
        if b"\x00" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue

        files_checked += 1
        for identity in identities:
            if identity not in text:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if identity in line:
                    findings.append(
                        _redacted_finding(
                            identity,
                            repository_label,
                            relative,
                            line=line_number,
                        )
                    )

    findings.sort(
        key=lambda item: (
            item["repository"],
            item["path"],
            item["line"] or 0,
            item["identity_fingerprint"],
        )
    )
    errors = sorted(set(errors))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "local",
        "protected_identity_count": len(identities),
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
        if repository_owner.get("login") != owner or repository.get("private") is not True:
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


def _code_search_page(
    client: GitHubClient,
    owner: str,
    identity: str,
    page: int,
) -> dict[str, Any]:
    query = f'"{identity}" user:{owner}'
    path = "/search/code?" + urllib.parse.urlencode(
        {"q": query, "per_page": "100", "page": str(page)}
    )
    try:
        payload = client.get(path)
    except (GitHubApiError, RuntimeError):
        fingerprint = _identity_fingerprint(identity)
        raise BoundaryAuditError(
            f"GitHub code search failed for protected identity {fingerprint}"
        ) from None
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        fingerprint = _identity_fingerprint(identity)
        raise BoundaryAuditError(
            f"GitHub code search returned an invalid result for protected identity {fingerprint}"
        )
    return payload


def audit_github_public_source(
    client: GitHubClient,
    owner: str,
    identities: list[str],
) -> dict[str, Any]:
    """Search current indexed GitHub source and retain only public-repository matches."""

    findings_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    searches_performed = 0

    for identity in identities:
        page = 1
        while True:
            payload = _code_search_page(client, owner, identity, page)
            searches_performed += 1
            items = payload["items"]
            for item in items:
                if not isinstance(item, dict):
                    continue
                repository = item.get("repository")
                if not isinstance(repository, dict):
                    continue
                repository_owner = repository.get("owner")
                if not isinstance(repository_owner, dict):
                    continue
                if repository_owner.get("login") != owner:
                    continue
                if repository.get("private") is not False:
                    continue
                full_name = repository.get("full_name")
                path = item.get("path")
                if not isinstance(full_name, str) or not isinstance(path, str):
                    continue
                finding = _redacted_finding(identity, full_name, path)
                key = (
                    finding["identity_fingerprint"],
                    finding["repository"],
                    finding["path"],
                )
                findings_by_key[key] = finding

            if len(items) < 100:
                break
            page += 1
            if page > 10:
                fingerprint = _identity_fingerprint(identity)
                raise BoundaryAuditError(
                    f"GitHub code search exceeded the bounded result window for protected identity {fingerprint}"
                )

    findings = sorted(
        findings_by_key.values(),
        key=lambda item: (
            item["repository"],
            item["path"],
            item["identity_fingerprint"],
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "github",
        "owner": owner,
        "protected_identity_count": len(identities),
        "searches_performed": searches_performed,
        "findings": findings,
        "errors": [],
        "status": "failed" if findings else "passed",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Public/private source boundary audit",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Protected identities evaluated: {report['protected_identity_count']}",
    ]
    if report.get("mode") == "local":
        lines.append(f"UTF-8 source files checked: {report.get('files_checked', 0)}")
    else:
        lines.append(f"Bounded GitHub searches performed: {report.get('searches_performed', 0)}")

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
                "| Public repository | Path | Line | Protected identity fingerprint | Finding fingerprint |",
                "|---|---|---:|---|---|",
            ]
        )
        for finding in findings:
            line = finding.get("line") or ""
            lines.append(
                "| {repository} | `{path}` | {line} | `{identity}` | `{fingerprint}` |".format(
                    repository=finding["repository"],
                    path=finding["path"],
                    line=line,
                    identity=finding["identity_fingerprint"],
                    fingerprint=finding["fingerprint"],
                )
            )
    else:
        lines.extend(["", "No protected repository identities were found in public source."])
    lines.append("")
    return "\n".join(lines)


def write_report(report: dict[str, Any], json_path: Path | None, markdown_path: Path | None) -> None:
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
        description="Audit public source for protected private repository identities."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--root", type=Path, help="Local public source root to scan.")
    mode.add_argument(
        "--github-owner",
        help="GitHub owner whose authenticated private identities and public source are audited.",
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
            report = audit_github_public_source(client, args.github_owner, identities)
    except (BoundaryAuditError, OSError) as error:
        print(f"public boundary audit failed: {error}", file=sys.stderr)
        return 2

    write_report(report, args.report, args.markdown)
    if not args.quiet:
        print(render_markdown(report), end="")
    return 1 if report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
