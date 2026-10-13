#!/usr/bin/env python3
"""Validate the source-controlled Qdrant derivative inputs without building it."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "containers/qdrant/build-inputs.json"
DOCKERFILE = ROOT / "containers/qdrant/Dockerfile.qdrant-distroless"
HEALTHCHECK = ROOT / "containers/qdrant/qdrant-healthcheck.go"

def normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
    errors: list[str] = []

    expected_dockerfile = inputs["dockerfile"]["sha256_normalized_lf"]
    if normalized_sha256(DOCKERFILE) != expected_dockerfile:
        errors.append("Dockerfile content hash does not match the reviewed input")
    expected_healthcheck = inputs["healthcheck"]["sha256_normalized_lf"]
    if normalized_sha256(HEALTHCHECK) != expected_healthcheck:
        errors.append("healthcheck content hash does not match the reviewed input")

    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")
    actual_refs = re.findall(r"^FROM\s+([^\s]+)", dockerfile_text, flags=re.MULTILINE)
    expected_refs = [item["reference"] for item in inputs["base_images"]]
    if actual_refs != expected_refs:
        errors.append("Dockerfile FROM references do not match the pinned input list")
    if any("@sha256:" not in ref or not re.fullmatch(r".+@sha256:[0-9a-f]{64}", ref) for ref in actual_refs):
        errors.append("every base image must use a full immutable digest")
    if "latest" in dockerfile_text.lower():
        errors.append("mutable image tag marker found in Dockerfile")

    if errors:
        for error in errors:
            print(error)
        return 1

    print("qdrant derivative input validation passed")
    print(f"base_images={len(actual_refs)}")
    print(f"dockerfile_sha256={normalized_sha256(DOCKERFILE)}")
    print(f"healthcheck_sha256={normalized_sha256(HEALTHCHECK)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
