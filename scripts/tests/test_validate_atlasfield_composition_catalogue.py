from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.validate_atlasfield_composition_catalogue import (
    EXPECTED_COMPOSITIONS,
    catalogue_fingerprint,
    load_json,
    validate_catalogue,
)


ROOT = Path(__file__).resolve().parents[2]


class AtlasFieldCompositionCatalogueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalogue = load_json(ROOT / "policy/atlasfield-composition-catalogue.json")

    def test_committed_catalogue_is_valid(self) -> None:
        result = validate_catalogue(self.catalogue)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(
            self.catalogue["catalogue_fingerprint"],
            catalogue_fingerprint(self.catalogue),
        )

    def test_compositions_are_currently_bounded(self) -> None:
        self.assertEqual(
            tuple(item["name"] for item in self.catalogue["compositions"]),
            EXPECTED_COMPOSITIONS,
        )
        self.assertEqual(len(self.catalogue["compositions"]), 5)

    def test_new_route_without_catalogue_revision_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.catalogue)
        candidate["compositions"].append(copy.deepcopy(candidate["compositions"][0]))
        candidate["compositions"][-1]["name"] = "unbounded-new-field"
        candidate["compositions"][-1]["route"] = "/new/"
        candidate["catalogue_fingerprint"] = catalogue_fingerprint(candidate)

        result = validate_catalogue(candidate)

        self.assertFalse(result.ok)
        self.assertIn("composition names are invalid or out of order", result.errors)

    def test_runtime_or_provider_scope_change_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.catalogue)
        candidate["scope"]["product_runtime_changed"] = True
        candidate["catalogue_fingerprint"] = catalogue_fingerprint(candidate)

        result = validate_catalogue(candidate)

        self.assertFalse(result.ok)
        self.assertIn("scope.product_runtime_changed must be false", result.errors)

    def test_fingerprint_drift_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.catalogue)
        candidate["compositions"][0]["selector"] = ".changed"

        result = validate_catalogue(candidate)

        self.assertFalse(result.ok)
        self.assertIn("catalogue_fingerprint does not match canonical content", result.errors)


if __name__ == "__main__":
    unittest.main()
