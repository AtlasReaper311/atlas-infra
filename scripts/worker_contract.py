#!/usr/bin/env python3
"""Validate required Atlas Worker contracts in a Wrangler dry-run bundle.

The deploy workflow runs this against the exact bundle candidate produced by
`wrangler deploy --dry-run --outdir dist`. It is intentionally provider-free:
no live endpoint, Cloudflare credential, secret, or production mutation is
needed to prove that a declared public contract survived bundling.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEXT_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".json", ".map"}
MAX_FILE_BYTES = 8 * 1024 * 1024

META_MARKERS = (
    "/_meta",
    "name",
    "description",
    "version",
    "endpoints",
    "status",
    "source",
)

OPENAPI_MARKERS = (
    "/v1/openapi.json",
    "openapi",
    "paths",
)


class ContractError(RuntimeError):
    pass


def read_bundle_text(bundle_dir: Path) -> str:
    if not bundle_dir.is_dir():
        raise ContractError(f"bundle directory does not exist: {bundle_dir}")

    chunks: list[str] = []
    files_seen = 0
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError as error:
            raise ContractError(f"could not stat bundle file {path}: {error}") from error
        if size > MAX_FILE_BYTES:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as error:
            raise ContractError(f"could not read bundle file {path}: {error}") from error
        files_seen += 1

    if files_seen == 0:
        raise ContractError(f"no readable Worker bundle files found under {bundle_dir}")
    return "\n".join(chunks)


def missing_markers(bundle_text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in bundle_text]


def validate_contracts(
    bundle_dir: Path,
    *,
    require_meta: bool,
    require_openapi: bool,
) -> list[str]:
    if not require_meta and not require_openapi:
        raise ContractError("at least one contract requirement must be enabled")

    bundle_text = read_bundle_text(bundle_dir)
    errors: list[str] = []

    if require_meta:
        missing = missing_markers(bundle_text, META_MARKERS)
        if missing:
            errors.append(
                "required /_meta contract markers are missing from the deploy bundle: "
                + ", ".join(missing)
            )

    if require_openapi:
        missing = missing_markers(bundle_text, OPENAPI_MARKERS)
        if missing:
            errors.append(
                "required OpenAPI contract markers are missing from the deploy bundle: "
                + ", ".join(missing)
            )
        if "3.0." not in bundle_text and "3.1." not in bundle_text:
            errors.append("required OpenAPI document version marker is missing from the deploy bundle")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Atlas Worker deploy-bundle contracts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check")
    check.add_argument("--bundle-dir", type=Path, required=True)
    check.add_argument("--require-meta", action="store_true")
    check.add_argument("--require-openapi", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors = validate_contracts(
            args.bundle_dir,
            require_meta=args.require_meta,
            require_openapi=args.require_openapi,
        )
    except ContractError as error:
        print(f"Worker contract validation failed: {error}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    enabled = []
    if args.require_meta:
        enabled.append("/_meta")
    if args.require_openapi:
        enabled.append("OpenAPI")
    print("Worker contract validation passed: " + ", ".join(enabled))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
