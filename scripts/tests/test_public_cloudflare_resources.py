from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from control_plane_contracts import load_json  # noqa: E402
from validate_public_cloudflare_resources import validate_resource_registry  # noqa: E402


class PublicCloudflareResourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_json(ROOT / "policy" / "public-cloudflare-resources.json")
        cls.schema = load_json(ROOT / "policy" / "public-cloudflare-resources.schema.json")
        cls.estate_registry = load_json(ROOT / "policy" / "estate-registry.json")

    def validate(self, document: dict) -> list[str]:
        return validate_resource_registry(document, self.schema, self.estate_registry)

    def test_canonical_registry_passes(self) -> None:
        self.assertEqual([], self.validate(self.document))
        self.assertEqual(9, len(self.document["resources"]))

    def test_resources_are_sorted_by_owner_service(self) -> None:
        owners = [item["owner"]["service_id"] for item in self.document["resources"]]
        self.assertEqual(sorted(owners), owners)

    def test_provider_identity_is_unique(self) -> None:
        keys = [(item["kind"], item["provider_id"]) for item in self.document["resources"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_telemetry_namespace_has_one_owner_and_read_only_consumer(self) -> None:
        item = next(
            resource
            for resource in self.document["resources"]
            if resource["display_label"] == "TELEMETRY_KV"
        )
        self.assertEqual("specular-edge", item["owner"]["service_id"])
        self.assertEqual(
            [
                {
                    "service_id": "specular-sonify",
                    "repository": "AtlasReaper311/specular-sonify",
                    "access": "read-only",
                    "source_ref": "AtlasReaper311/specular-sonify:wrangler.toml",
                }
            ],
            item["consumers"],
        )

    def test_duplicate_provider_identity_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        duplicate = copy.deepcopy(document["resources"][0])
        duplicate["owner"] = copy.deepcopy(document["resources"][1]["owner"])
        document["resources"].insert(1, duplicate)
        errors = self.validate(document)
        self.assertTrue(any("duplicate provider identity" in error for error in errors))

    def test_unknown_consumer_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["resources"][0]["consumers"] = [
            {
                "service_id": "unknown-service",
                "repository": "AtlasReaper311/atlas-api-index",
                "access": "read-only",
                "source_ref": "AtlasReaper311/atlas-api-index:wrangler.toml",
            }
        ]
        errors = self.validate(document)
        self.assertTrue(any("unknown public service_id" in error for error in errors))

    def test_document_serialisation_is_deterministic(self) -> None:
        first = json.dumps(self.document, indent=2, sort_keys=True) + "\n"
        second = json.dumps(self.document, indent=2, sort_keys=True) + "\n"
        self.assertEqual(first.encode(), second.encode())


if __name__ == "__main__":
    unittest.main()
