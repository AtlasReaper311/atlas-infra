from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.worker_contract import ContractError, validate_contracts


META_MARKER_TEXT = """
/_meta
name
description
version
endpoints
status
source
"""

OPENAPI_MARKER_TEXT = """
/v1/openapi.json
openapi
paths
3.0.3
"""


class WorkerContractTests(unittest.TestCase):
    def write_bundle(self, text: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "worker.js").write_text(text, encoding="utf-8")
        return root

    def test_meta_contract_passes_with_required_markers(self) -> None:
        errors = validate_contracts(
            self.write_bundle(META_MARKER_TEXT),
            require_meta=True,
            require_openapi=False,
        )
        self.assertEqual([], errors)

    def test_meta_contract_fails_when_route_is_missing(self) -> None:
        errors = validate_contracts(
            self.write_bundle(META_MARKER_TEXT.replace("/_meta", "/meta")),
            require_meta=True,
            require_openapi=False,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("/_meta", errors[0])

    def test_openapi_contract_passes_with_required_markers(self) -> None:
        errors = validate_contracts(
            self.write_bundle(OPENAPI_MARKER_TEXT),
            require_meta=False,
            require_openapi=True,
        )
        self.assertEqual([], errors)

    def test_openapi_contract_requires_version_marker(self) -> None:
        errors = validate_contracts(
            self.write_bundle(OPENAPI_MARKER_TEXT.replace("3.0.3", "version")),
            require_meta=False,
            require_openapi=True,
        )
        self.assertIn("required OpenAPI document version marker", " ".join(errors))

    def test_both_contracts_can_be_required_together(self) -> None:
        errors = validate_contracts(
            self.write_bundle(META_MARKER_TEXT + OPENAPI_MARKER_TEXT),
            require_meta=True,
            require_openapi=True,
        )
        self.assertEqual([], errors)

    def test_at_least_one_contract_must_be_selected(self) -> None:
        with self.assertRaisesRegex(ContractError, "at least one"):
            validate_contracts(
                self.write_bundle(META_MARKER_TEXT),
                require_meta=False,
                require_openapi=False,
            )


if __name__ == "__main__":
    unittest.main()
