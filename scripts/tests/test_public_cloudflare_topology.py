from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import public_cloudflare_topology as topology


class PublicCloudflareTopologyTests(unittest.TestCase):
    def test_current_policy_passes(self) -> None:
        report = topology.validate(ROOT)
        self.assertEqual([], report["errors"])
        self.assertEqual(14, report["workers"])
        self.assertEqual(3, report["pages_projects"])

    def test_worker_set_is_stable_and_sorted_by_declared_identity(self) -> None:
        document = topology.load(ROOT / topology.TOPOLOGY)
        scripts = [worker["script_name"] for worker in document["workers"]]
        self.assertEqual(len(scripts), len(set(scripts)))
        self.assertEqual(14, len(scripts))
        self.assertEqual(
            {
                "atlas-api-index",
                "atlas-api-public",
                "atlas-blackbox",
                "atlas-daily-digest",
                "atlas-dora",
                "atlas-notify",
                "atlas-quota-watch",
                "deploy-watch",
                "github-pulse",
                "ramone-edge",
                "ramone-trigger",
                "site-pulse",
                "specular-edge",
                "specular-sonify",
            },
            set(scripts),
        )

    def test_ramone_trigger_uses_current_trigger_route(self) -> None:
        document = topology.load(ROOT / topology.TOPOLOGY)
        worker = next(item for item in document["workers"] if item["script_name"] == "ramone-trigger")
        self.assertEqual("https://api.atlas-systems.uk/trigger/_meta", worker["metadata_url"])
        self.assertEqual(
            [{"pattern": "api.atlas-systems.uk/trigger*", "custom_domain": False}],
            worker["routes"],
        )

    def test_unknown_storage_reference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_inputs(root)
            document = topology.load(root / topology.TOPOLOGY)
            document["workers"][0]["storage_bindings"][0]["provider_id"] = "unknown-resource"
            (root / topology.TOPOLOGY).write_text(json.dumps(document), encoding="utf-8")
            report = topology.validate(root)
            self.assertTrue(any("absent from storage authority" in error for error in report["errors"]))

    def test_unknown_service_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_inputs(root)
            document = topology.load(root / topology.TOPOLOGY)
            document["workers"][0]["service_bindings"][0]["service"] = "not-a-service"
            (root / topology.TOPOLOGY).write_text(json.dumps(document), encoding="utf-8")
            report = topology.validate(root)
            self.assertTrue(any("unknown target service" in error for error in report["errors"]))

    def test_metadata_identity_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_inputs(root)
            document = topology.load(root / topology.TOPOLOGY)
            worker = next(item for item in document["workers"] if item["script_name"] == "ramone-trigger")
            worker["metadata_url"] = "https://api.atlas-systems.uk/ramone-trigger/_meta"
            (root / topology.TOPOLOGY).write_text(json.dumps(document), encoding="utf-8")
            report = topology.validate(root)
            self.assertTrue(any("metadata_url" in error and "service contract" in error for error in report["errors"]))

    def _copy_inputs(self, root: Path) -> None:
        for relative in (topology.TOPOLOGY, topology.SCHEMA, topology.STORAGE):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        target_contracts = root / topology.SERVICE_CONTRACTS
        target_contracts.mkdir(parents=True, exist_ok=True)
        for source in (ROOT / topology.SERVICE_CONTRACTS).glob("*.json"):
            (target_contracts / source.name).write_bytes(source.read_bytes())


if __name__ == "__main__":
    unittest.main()
