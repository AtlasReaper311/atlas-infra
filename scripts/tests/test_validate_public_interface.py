from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_public_interface import (
    REQUIRED_COMPONENT_ROLES,
    REQUIRED_ICON_FILES,
    REQUIRED_METADATA,
    load_json,
    validate_contract,
    validate_domains,
    validate_surface_manifest,
    validate_system,
)


ROOT = Path(__file__).resolve().parents[2]


class PublicInterfacePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "policy/public-interface-contract.json")
        self.system = load_json(ROOT / "policy/public-interface-system-v2.json")
        self.domains = load_json(ROOT / "policy/atlas-owned-domains.json")

    def test_committed_authority_is_valid(self) -> None:
        self.assertTrue(validate_contract(self.contract).ok)
        self.assertTrue(validate_system(self.system).ok)
        self.assertTrue(validate_domains(self.domains).ok)

    def test_remote_runtime_shell_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["estate_search"]["runtime_distribution"] = "remote-script"
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn("search assets must be local copies", result.errors)

    def test_status_source_cannot_drift_to_single_health_probe(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["status_indicator"]["source"] = (
            "https://api.atlas-systems.uk/notify/health"
        )
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn("status source must be /v1/stats", result.errors)

    def test_status_staleness_remains_explicit(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["status_indicator"]["stale_after_seconds"] = 0
        result = validate_contract(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "status stale threshold must remain 1200 seconds",
            result.errors,
        )

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
        self.assertIn(
            "external_rel must contain noopener and noreferrer",
            result.errors,
        )

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

    def test_v2_header_route_order_is_governed(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["navigation"]["global_routes"][3]["label"] = "About"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "v2 global routes must be Work, Writing, Lab, Systems, About in order",
            result.errors,
        )

    def test_v2_healthy_label_is_operational(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["navigation"]["desktop"]["status_healthy_label"] = "Nominal"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "healthy public label must be Operational",
            result.errors,
        )

    def test_v2_mobile_navigation_remains_bottom_navigation(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["navigation"]["mobile"]["primary_navigation"] = "drawer"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "mobile navigation must use the bottom navigation",
            result.errors,
        )

    def test_v2_maturity_and_runtime_state_cannot_be_merged(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["vocabulary"]["maturity_is_separate_from_runtime_state"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "maturity and runtime state must remain separate",
            result.errors,
        )

    def test_v2_systems_directory_does_not_promote_private_components(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["systems_directory"]["private_components_as_context_only"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "private components must remain context-only",
            result.errors,
        )

    def test_v2_system_symphony_remains_preview(self) -> None:
        candidate = copy.deepcopy(self.system)
        for item in candidate["lab"]["featured"]:
            if item["name"] == "System SYMPHONY":
                item["maturity"] = "Production"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "System SYMPHONY must remain Preview in the first migration",
            result.errors,
        )

    def test_v2_shape_detector_remains_experiment(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["lab"]["shape_detector_maturity"] = "Tool"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "Shape Detector must remain an Experiment",
            result.errors,
        )

    def test_v2_work_order_is_not_publication_order(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["work"]["display_order_independent_from_publication_order"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "Work display order must be independent from identifiers and publication",
            result.errors,
        )

    def test_v2_writing_scheduler_ownership_is_protected(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["writing"]["scheduler_owns_order_and_upcoming_visibility"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "scheduler must own Writing order and upcoming visibility",
            result.errors,
        )

    def test_v2_remote_interface_assets_are_rejected(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["distribution"]["runtime_assets"] = "remote"
        candidate["distribution"]["remote_runtime_dependency_forbidden"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "interface assets must remain repository-local",
            result.errors,
        )
        self.assertIn(
            "remote runtime interface dependencies must remain forbidden",
            result.errors,
        )

    def test_v2_visual_updates_cannot_auto_merge(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["distribution"]["visual_merge_approval"] = "automatic"
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "visual updates must require manual merge approval",
            result.errors,
        )

    def test_v2_component_contract_is_complete(self) -> None:
        self.assertEqual(
            set(self.system["components"]["roles"]),
            REQUIRED_COMPONENT_ROLES,
        )

    def test_v2_serious_accessibility_failures_block_merge(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["evidence"]["serious_accessibility_failures_block_merge"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "serious accessibility failures must block merge",
            result.errors,
        )

    def test_v2_live_data_is_separate_from_screenshot_fixtures(self) -> None:
        candidate = copy.deepcopy(self.system)
        candidate["evidence"]["live_data_contract_tests_are_separate"] = False
        result = validate_system(candidate)
        self.assertFalse(result.ok)
        self.assertIn(
            "visual fixtures and live-data contract tests must remain separate",
            result.errors,
        )


class SurfaceManifestTests(unittest.TestCase):
    def make_manifest(self, root: Path, kind: str = "standard") -> dict:
        source = root / "index.html"
        source.write_text(
            "<!doctype html><title>fixture</title>\n",
            encoding="utf-8",
        )
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
                    "link_policy": (
                        "atlas-owned-same-tab-external-safe-new-tab"
                    ),
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
            self.assertIn(
                "surfaces[0] homepage must own its status treatment",
                result.errors,
            )

    def test_cv_requires_noindex_follow(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root, kind="cv")
            result = validate_surface_manifest(manifest, root)
            self.assertFalse(result.ok)
            self.assertIn(
                "surfaces[0] CV indexing must be noindex, follow",
                result.errors,
            )

    def test_missing_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root)
            manifest["surfaces"][0]["source"] = "missing.html"
            result = validate_surface_manifest(manifest, root)
            self.assertFalse(result.ok)
            self.assertIn(
                "surfaces[0].source does not exist: missing.html",
                result.errors,
            )

    def test_manifest_json_is_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            manifest = self.make_manifest(root)
            json.dumps(manifest)


if __name__ == "__main__":
    unittest.main()
