from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_browser_icons import (
    git_blob_sha1,
    load_json,
    validate_authority,
    validate_local_package,
)

ROOT = Path(__file__).resolve().parents[2]


class BrowserIconAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = load_json(ROOT / "policy/browser-icons-v1.json")

    def test_committed_authority_is_valid(self) -> None:
        self.assertEqual(validate_authority(self.authority), [])

    def test_runtime_remote_dependency_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.authority)
        candidate["distribution"]["runtime"] = "remote-cdn"
        errors = validate_authority(candidate)
        self.assertIn("browser icons must be repository-local at runtime", errors)

    def test_missing_asset_target_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.authority)
        candidate["binary_assets"].pop()
        errors = validate_authority(candidate)
        self.assertIn("binary asset target set is incomplete", errors)

    def test_source_commit_must_be_immutable(self) -> None:
        candidate = copy.deepcopy(self.authority)
        candidate["source"]["commit"] = "main"
        errors = validate_authority(candidate)
        self.assertIn("canonical source commit must be a full Git SHA", errors)

    def test_git_blob_checksum_matches_git_object_semantics(self) -> None:
        self.assertEqual(
            git_blob_sha1(b"test\n"),
            "9daeafb9864cf43055ae93beb0afd6c7d144bfa4",
        )

    def test_local_package_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            package = root / "icons"
            package.mkdir()
            for asset in self.authority["binary_assets"]:
                (package / asset["target"]).write_bytes(b"not the canonical asset")
            manifest = root / "site.webmanifest"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "Fixture",
                        "short_name": "Fixture",
                        "icons": [
                            {"src": "/192.png", "sizes": "192x192", "type": "image/png"},
                            {"src": "/512.png", "sizes": "512x512", "type": "image/png"},
                        ],
                        "theme_color": "#0a0a0f",
                        "background_color": "#0a0a0f",
                        "display": "standalone",
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_local_package(self.authority, package, manifest)
            self.assertTrue(any("drift detected" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
