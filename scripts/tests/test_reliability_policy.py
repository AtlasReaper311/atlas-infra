from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import control_plane_contracts as contracts
from scripts.control_plane_io import load_json
from scripts.reliability_policy import (
    build_policy_document,
    build_status_slo,
    build_unmeasured,
    validate_policy,
)

ROOT = Path(__file__).resolve().parents[2]


def temp_root() -> tempfile.TemporaryDirectory:
    """Copy the policy-relevant subset of the repository for mutation tests."""
    holder = tempfile.TemporaryDirectory()
    target = Path(holder.name)
    for relative in (
        "policy/reliability",
        "policy/service-contracts",
        "policy/schemas",
        "contracts/v1",
    ):
        shutil.copytree(ROOT / relative, target / relative)
    shutil.copy(
        ROOT / "policy/estate-registry.json", target / "policy/estate-registry.json"
    )
    return holder


class PolicyValidationTests(unittest.TestCase):
    def test_repository_policy_is_valid(self) -> None:
        self.assertEqual([], validate_policy(ROOT))

    def test_deprecated_service_may_not_carry_an_objective(self) -> None:
        holder = temp_root()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        registry_path = root / "policy/estate-registry.json"
        registry = load_json(registry_path)
        entry = next(
            item
            for item in registry["repositories"]
            if item["repository"] == "AtlasReaper311/atlas-api-public"
        )
        entry["lifecycle"] = "deprecated"
        registry_path.write_text(
            json.dumps(registry, indent=2) + "\n", encoding="utf-8"
        )

        template = load_json(root / "policy/reliability/objectives/atlas-notify.json")
        template["service_id"] = "atlas-api-public"
        template["objective_id"] = "atlas-api-public-availability-30d"
        path = root / "policy/reliability/objectives/atlas-api-public.json"
        path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
        errors = validate_policy(root)
        self.assertTrue(
            any("deprecated service 'atlas-api-public'" in error for error in errors),
            errors,
        )

    def test_duplicate_objective_ids_are_rejected(self) -> None:
        holder = temp_root()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        clone = load_json(root / "policy/reliability/objectives/atlas-notify.json")
        clone["service_id"] = "deploy-watch"
        path = root / "policy/reliability/objectives/deploy-watch.json"
        path.write_text(json.dumps(clone, indent=2) + "\n")
        errors = validate_policy(root)
        self.assertTrue(any("duplicate objective_id" in error for error in errors), errors)

    def test_slo_ref_targets_must_exist(self) -> None:
        holder = temp_root()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "policy/reliability/objectives/atlas-notify.json").unlink()
        errors = validate_policy(root)
        self.assertTrue(any("slo_refs target missing" in error for error in errors), errors)

    def test_active_unmeasured_service_requires_reviewed_reason(self) -> None:
        holder = temp_root()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        path = root / "policy/reliability/unmeasured.json"
        document = load_json(path)
        document["services"] = [
            item
            for item in document["services"]
            if item["service_id"] != "atlas-api-public"
        ]
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        errors = validate_policy(root)
        self.assertTrue(
            any("atlas-api-public" in error and "needs an owner-reviewed" in error for error in errors),
            errors,
        )

    def test_measured_service_may_not_also_be_unmeasured(self) -> None:
        holder = temp_root()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        path = root / "policy/reliability/unmeasured.json"
        document = load_json(path)
        document["services"].append(
            {
                "service_id": "atlas-notify",
                "reason": "Invalid duplicate classification for mutation testing only.",
            }
        )
        document["services"].sort(key=lambda item: item["service_id"])
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        errors = validate_policy(root)
        self.assertTrue(
            any("measured service 'atlas-notify'" in error for error in errors), errors
        )


class ProjectionTests(unittest.TestCase):
    def test_policy_document_is_deterministic_and_schema_valid(self) -> None:
        first = build_policy_document(ROOT)
        second = build_policy_document(ROOT)
        self.assertEqual(first, second)
        schema = load_json(ROOT / "policy/schemas/reliability-policy.schema.json")
        self.assertEqual([], contracts.validate_instance(first, schema))

    def test_policy_fingerprint_tracks_content(self) -> None:
        document = build_policy_document(ROOT)
        without = {key: value for key, value in document.items() if key != "fingerprint"}
        from scripts.control_plane_io import digest_json

        self.assertEqual(digest_json(without), document["fingerprint"])

    def test_generated_at_derives_from_approvals_not_wall_time(self) -> None:
        document = build_policy_document(ROOT)
        approvals = {
            objective["provenance"]["approved_at"]
            for objective in document["objectives"]
        }
        self.assertIn(document["generated_at"], approvals)

    def test_status_slo_projection_satisfies_the_status_contract(self) -> None:
        projection = build_status_slo(ROOT)
        self.assertIsInstance(projection["window_days"], int)
        self.assertGreater(projection["window_days"], 0)
        services = projection["services"]
        self.assertTrue(services)
        ids: set[str] = set()
        components: set[str] = set()
        for service in services:
            for key in ("id", "component", "target_pct", "sub", "domain"):
                self.assertIn(key, service)
            self.assertNotIn(service["id"], ids)
            self.assertNotIn(service["component"], components)
            ids.add(service["id"])
            components.add(service["component"])
            self.assertIn(service["domain"], {"edge", "machine"})
            self.assertTrue(0 < service["target_pct"] <= 100)
        self.assertEqual(
            build_policy_document(ROOT)["fingerprint"],
            projection["policy_fingerprint"],
        )

    def test_status_slo_preserves_the_approved_presentation_order(self) -> None:
        projection = build_status_slo(ROOT)
        self.assertEqual(
            [
                "ramone-memory",
                "atlas-corpus",
                "specular-telemetry",
                "atlas-api-index",
                "ramone-trigger",
                "specular-edge",
                "atlas-notify",
                "github-pulse",
                "site-pulse",
                "deploy-watch",
                "atlas-systems",
                "atlas-doc-viewer",
                "status",
            ],
            [service["id"] for service in projection["services"]],
        )

    def test_unmeasured_has_exact_reviewed_runtime_coverage(self) -> None:
        unmeasured = build_unmeasured(ROOT)
        by_id = {item["service_id"]: item["reason"] for item in unmeasured}
        self.assertEqual(
            {
                "atlas-api-public",
                "atlas-blackbox",
                "atlas-daily-digest",
                "atlas-dora",
                "atlas-quota-watch",
                "ramone-edge",
                "specular-sentinel",
                "specular-sonify",
            },
            set(by_id),
        )
        self.assertIn("self-probing", by_id["atlas-api-public"])
        self.assertIn("owner-approved", by_id["atlas-blackbox"])
        self.assertIn("scheduled delivery", by_id["atlas-daily-digest"])
        self.assertIn("not yet probe", by_id["atlas-dora"])
        self.assertIn("not a pure availability indicator", by_id["atlas-quota-watch"])
        self.assertIn("sleeping local AI is intentionally healthy", by_id["ramone-edge"])
        self.assertIn("no independent sentinel probe", by_id["specular-sentinel"])
        self.assertIn("No dedicated uptime probe", by_id["specular-sonify"])
        for measured in ("atlas-notify", "deploy-watch", "ramone-memory"):
            self.assertNotIn(measured, by_id)


if __name__ == "__main__":
    unittest.main()
