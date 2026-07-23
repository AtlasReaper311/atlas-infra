from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_public_interface import (
    REQUIRED_ICON_FILES,
    REQUIRED_METADATA,
    load_json,
    validate_contract,
    validate_domains,
    validate_surface_manifest,
)


ROOT = Path(__file__).resolve().parents[2]


class PublicInterfacePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "policy/public-interface-contract.json")
        self.domains = load_json(ROOT / "policy/atlas-owned-domains.json")

    def test_committed_contract_is_valid(self) -> None:
        self.assertTrue(validate_contract(self.contract).ok)
        self.assertTrue(validate_domains(self.domains).ok)

    def test_remote_runtime_shell_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["estate_search"]["runtime_distribution"] = "remote-script"
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn("search assets must be local copies", result.errors)

    def test_status_source_cannot_drift_to_single_health_probe(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["status_indicator"]["source"] = "https://api.atlas-systems.uk/notify/health"
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn("status source must be /v1/stats", result.errors)

    def test_status_staleness_remains_explicit(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["status_indicator"]["stale_after_seconds"] = 0
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn("status stale threshold must remain 1200 seconds", result.errors)

    def test_atlas_owned_links_must_remain_same_tab(self) -> None:
        candidate = copy.deepcopy(self.domains)
        candidate["rules"]["atlas_owned_html_target"] = "new-tab"
        result = validate_domains(candidate)
        self.assertFalse(result.ok)
        self.assertIn("Atlas-owned HTML must remain same-tab", result.errors)

    def test_external_links_require_both_safety_relations(self) -> None:
        candidate = copy.deepcopy(self.domains)
        candidate["rules"]["external_rel"] = ["noopener"]
        result = validate_domains(candidate)
        self.assertFalse(result.ok)
        self.assertIn("external_rel must contain noopener and noreferrer", result.errors)

    def test_icon_contract_is_complete(self) -> None:
        self.assertEqual(
            set(self.contract["browser_icons"]["required_files"]),
            REQUIRED_ICON_FILES,
        )

    def test_metadata_contract_is_complete(self) -> None:
        self.assertEqual(
            set(self.contract["metadata"]["required"]),
            REQUIRED_METADATA,
        )


class SurfaceManifestTests(unittest.TestCase):
    def make_manifest(self, root: Path, kind: str = "standard") -> dict:
        source = root / "index.html"
        source.write_text("<!doctype html><title>fixture</title>\n", encoding="utf-8")
        return {
            "schema_version": "atlas-control-plane/public-interface-surface/v1",
            "repository": "AtlasReaper311/example",
            "surfaces": [
                {
                    "url": "https://example.atlas-systems.uk/",
                    "source": "index.html",
                    "kind": kind,
                    "indexing": "index",
                    "global_header": True,
                    "search": True,
                    "status_indicator": "aggregate-link",
                    "contextual_navigation": False,
                    "icons": sorted(REQUIRED_ICON_FILES),
                    "metadata": sorted(REQUIRED_METADATA),
                    "footer": "product",
                    "link_policy": "atlas-owned-same-tab-external-safe-new-tab",
                    "generated_owner": None,
                    "notes": [],
                }
            ],
            "machine_surface_exclusions": [],
        }

    def test_valid_standard_surface_passes(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root)
            self.assertTrue(validate_surface_manifest(manifest, root).ok)

    def test_homepage_cannot_duplicate_header_status(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root, kind="homepage")
            result = validate_surface_manifest(manifest, root)
            self.assertFalse(result.ok)
            self.assertIn("surfaces[0] homepage must own its status treatment", result.errors)

    def test_cv_requires_noindex_follow(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root, kind="cv")
            result = validate_surface_manifest(manifest, root)
            self.assertFalse(result.ok)
            self.assertIn("surfaces[0] CV indexing must be noindex, follow", result.errors)

    def test_missing_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root)
            manifest["surfaces"][0]["source"] = "missing.html"
            result = validate_surface_manifest(manifest, root)
            self.assertFalse(result.ok)
            self.assertIn("surfaces[0].source does not exist: missing.html", result.errors)

    def test_manifest_json_is_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root)
            json.dumps(manifest)


if __name__ == "__main__":
    unittest.main()
