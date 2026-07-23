#!/usr/bin/env python3
"""Validate the Atlas Systems browser-icon authority and local packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

SCHEMA = "atlas-control-plane/browser-icons/v1"
REQUIRED_TARGETS = {
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIGNATURE) or len(data) < 24:
        raise ValueError("invalid PNG signature or header")
    return struct.unpack(">II", data[16:24])


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def validate_authority(authority: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if authority.get("schema_version") != SCHEMA:
        errors.append("invalid browser-icon schema_version")
    if authority.get("status") != "accepted":
        errors.append("browser-icon authority is not accepted")
    source = authority.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if source.get("repository") != "AtlasReaper311/atlas-systems":
            errors.append("canonical icon repository must be AtlasReaper311/atlas-systems")
        commit = source.get("commit")
        if not isinstance(commit, str) or len(commit) != 40:
            errors.append("canonical source commit must be a full Git SHA")

    assets = authority.get("binary_assets")
    if not isinstance(assets, list):
        errors.append("binary_assets must be a list")
        return errors

    targets: list[str] = []
    paths: list[str] = []
    for index, asset in enumerate(assets):
        prefix = f"binary_assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        target = asset.get("target")
        source_path = asset.get("source_path")
        blob = asset.get("git_blob_sha1")
        content_type = asset.get("content_type")
        if not isinstance(target, str) or not target:
            errors.append(f"{prefix}.target is required")
        else:
            targets.append(target)
        if not isinstance(source_path, str) or not source_path:
            errors.append(f"{prefix}.source_path is required")
        else:
            paths.append(source_path)
        if not isinstance(blob, str) or len(blob) != 40 or any(c not in "0123456789abcdef" for c in blob):
            errors.append(f"{prefix}.git_blob_sha1 must be a lowercase SHA-1")
        if content_type not in {"image/x-icon", "image/png"}:
            errors.append(f"{prefix}.content_type is invalid")
        dimensions = asset.get("dimensions")
        if content_type == "image/png":
            if not (
                isinstance(dimensions, list)
                and len(dimensions) == 2
                and all(isinstance(value, int) and value > 0 for value in dimensions)
            ):
                errors.append(f"{prefix}.dimensions must contain positive width and height")

    if set(targets) != REQUIRED_TARGETS:
        errors.append("binary asset target set is incomplete")
    if len(targets) != len(set(targets)):
        errors.append("binary asset targets must be unique")
    if len(paths) != len(set(paths)):
        errors.append("binary asset source paths must be unique")

    manifest = authority.get("manifest_contract")
    if not isinstance(manifest, dict):
        errors.append("manifest_contract must be an object")
    else:
        if manifest.get("target") != "site.webmanifest":
            errors.append("manifest target must be site.webmanifest")
        if manifest.get("theme_color") != "#0a0a0f":
            errors.append("manifest theme colour must match the brand background")
        if manifest.get("background_color") != "#0a0a0f":
            errors.append("manifest background colour must match the brand background")
        if set(manifest.get("required_icon_sizes", [])) != {"192x192", "512x512"}:
            errors.append("manifest icon-size contract is incomplete")

    distribution = authority.get("distribution")
    if not isinstance(distribution, dict):
        errors.append("distribution must be an object")
    else:
        if distribution.get("runtime") != "repository-local":
            errors.append("browser icons must be repository-local at runtime")
        if distribution.get("remote_runtime_dependency_forbidden") is not True:
            errors.append("remote runtime icon dependency must remain forbidden")
    return errors


def validate_local_package(
    authority: dict[str, Any], package_dir: Path, manifest_path: Path
) -> list[str]:
    errors: list[str] = []
    for asset in authority.get("binary_assets", []):
        if not isinstance(asset, dict):
            continue
        target = asset.get("target")
        if not isinstance(target, str):
            continue
        path = package_dir / target
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            errors.append(f"missing local browser icon: {path}")
            continue
        if not data:
            errors.append(f"empty local browser icon: {path}")
            continue
        if git_blob_sha1(data) != asset.get("git_blob_sha1"):
            errors.append(f"browser icon drift detected: {path}")
        expected_dimensions = asset.get("dimensions")
        if expected_dimensions:
            try:
                actual = png_dimensions(data)
            except ValueError as exc:
                errors.append(f"{path}: {exc}")
            else:
                if list(actual) != expected_dimensions:
                    errors.append(
                        f"{path}: expected dimensions {expected_dimensions}, got {list(actual)}"
                    )

    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    contract = authority.get("manifest_contract", {})
    for field in contract.get("required_fields", []):
        if field not in manifest:
            errors.append(f"web manifest is missing {field}")
    if manifest.get("theme_color") != contract.get("theme_color"):
        errors.append("web manifest theme_color is invalid")
    if manifest.get("background_color") != contract.get("background_color"):
        errors.append("web manifest background_color is invalid")
    sizes = {
        icon.get("sizes")
        for icon in manifest.get("icons", [])
        if isinstance(icon, dict)
    }
    if not set(contract.get("required_icon_sizes", [])).issubset(sizes):
        errors.append("web manifest does not declare the required icon sizes")
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authority",
        type=Path,
        default=Path("policy/browser-icons-v1.json"),
    )
    parser.add_argument("--package-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        authority = load_json(args.authority)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_authority(authority)
    if args.package_dir or args.manifest:
        if not args.package_dir or not args.manifest:
            errors.append("--package-dir and --manifest must be supplied together")
        else:
            errors.extend(validate_local_package(authority, args.package_dir, args.manifest))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Browser icon contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
