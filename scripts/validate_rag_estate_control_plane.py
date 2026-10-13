"""Static, secret-free checks for the staged RAG deployment control plane."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "deployments" / "rag-estate"
IMMUTABLE_REF = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?!(?:RAG_SECRET_ROOT|RAG_TLS_ROOT)\s*=)(?:[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)\s*=\s*[^$\s#].+"
)


def validate() -> list[str]:
    errors: list[str] = []
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    freeze = (ROOT / "compose.freeze.yaml").read_text(encoding="utf-8")
    runtime_example = (ROOT / "runtime.env.example").read_text(encoding="utf-8")

    if ":latest" in compose or ":latest" in freeze:
        errors.append("mutable latest image tag present")
    if "internal: true" not in compose:
        errors.append("private Docker network is not marked internal")
    if "QDRANT_IMAGE_REF:?" not in compose:
        errors.append("QDRANT_IMAGE_REF is not fail-closed")
    for name in (
        "RAMONE_MEMORY_IMAGE_REF:?",
        "ATLAS_CORPUS_IMAGE_REF:?",
        "OLLAMA_RAG_KIT_IMAGE_REF:?",
    ):
        if name not in compose:
            errors.append(f"{name} is not fail-closed")
    if "ports:" in compose and re.search(r"(?ms)\n  qdrant:.*?\n  [a-z]", compose):
        qdrant_block = compose.split("\n  qdrant:", 1)[1].split("\n  ramone-memory:", 1)[0]
        if "ports:" in qdrant_block:
            errors.append("Qdrant publishes a host port")
    if "WRITE_FREEZE" not in compose or 'WRITE_FREEZE: "true"' not in freeze:
        errors.append("write-freeze contract is incomplete")
    if "MIGRATION" in compose.upper():
        errors.append("migration controls must remain outside steady-state Compose")
    if SECRET_ASSIGNMENT.search(runtime_example):
        errors.append("secret-like value found in runtime example")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".yaml", ".yml", ".env", ".toml"}:
            text = path.read_text(encoding="utf-8")
            if ":latest" in text:
                errors.append(f"mutable latest tag in {path.relative_to(ROOT)}")
            if SECRET_ASSIGNMENT.search(text):
                errors.append(f"secret-like assignment in {path.relative_to(ROOT)}")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        raise SystemExit("\n".join(problems))
    print("rag-estate control plane static checks passed")
