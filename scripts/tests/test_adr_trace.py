from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import adr_trace


class AdrTraceTests(unittest.TestCase):
    def test_current_adr_set_is_valid_and_deterministic(self) -> None:
        first, first_errors = adr_trace.build_index(ROOT)
        second, second_errors = adr_trace.build_index(ROOT)
        self.assertEqual([], first_errors)
        self.assertEqual([], second_errors)
        self.assertEqual(6, len(first["relationships"]))
        self.assertEqual(
            adr_trace.canonical_bytes(first),
            adr_trace.canonical_bytes(second),
        )
        self.assertEqual(
            ["ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004", "ADR-0006", "ADR-0007"],
            [item["adr"]["id"] for item in first["relationships"]],
        )

    def test_legacy_slug_keeps_existing_authority_path_valid(self) -> None:
        parsed = adr_trace.parse_adr(
            ROOT / "docs" / "adrs" / "public-private-estate-boundary.md"
        )
        self.assertEqual("ADR-0003", parsed["adr"]["id"])

    def test_legacy_filename_without_matching_slug_fails(self) -> None:
        text = """+++
id = "ADR-0099"
date = 2026-07-21
status = "accepted"
visibility = "public"
repositories = []
services = []
contracts = []
policies = []
+++

# ADR-0099: Example

## Context
x

## Decision
y

## Consequences
z
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-name.md"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(adr_trace.AdrTraceError, "legacy ADR filename"):
                adr_trace.parse_adr(path)

    def test_unknown_scope_references_fail_closed(self) -> None:
        parsed = adr_trace.parse_adr(
            ROOT / "docs" / "adrs" / "ADR-0001-worker-to-worker-service-bindings.md"
        )
        parsed["affects"]["repositories"].append("AtlasReaper311/not-approved")
        parsed["affects"]["services"].append("not-approved")
        parsed["affects"]["contracts"].append("atlas-control-plane/not-approved/v1")
        parsed["affects"]["policies"].append("policy/not-approved.json")
        errors = adr_trace.scope_errors(parsed, adr_trace.authorities(ROOT))
        self.assertEqual(4, len(errors))
        self.assertTrue(all("unknown public" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
