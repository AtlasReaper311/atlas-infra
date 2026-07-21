from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import backup_audit  # noqa: E402
from control_plane_contracts import load_json, validate_instance  # noqa: E402


class BackupAuditTests(unittest.TestCase):
    NOW_TEXT = "2026-07-14T12:00:00Z"
    NOW = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "contracts", self.root / "contracts")
        (self.root / "policy").mkdir()
        for name in (
            "backup-audit.json",
            "backup-audit.schema.json",
            "backup-metadata.schema.json",
            "estate-registry.json",
            "estate-registry.schema.json",
        ):
            shutil.copy2(ROOT / "policy" / name, self.root / "policy" / name)
        shutil.copytree(
            ROOT / "policy" / "service-contracts",
            self.root / "policy" / "service-contracts",
        )
        shutil.copytree(
            ROOT / "tests" / "fixtures" / "backup-audit",
            self.root / "tests" / "fixtures" / "backup-audit",
        )
        shutil.copytree(
            ROOT / "docs" / "runbooks", self.root / "docs" / "runbooks"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def policy_path(self) -> Path:
        return self.root / "policy" / "backup-audit.json"

    @property
    def fixtures_dir(self) -> Path:
        return self.root / "tests" / "fixtures" / "backup-audit"

    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, path: Path, value: dict) -> None:
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def policy(self) -> dict:
        return self.load(self.policy_path)

    def write_policy(self, policy: dict) -> None:
        self.write(self.policy_path, policy)

    def target(self, target_id: str) -> dict:
        return next(
            target
            for target in self.policy()["targets"]
            if target["target_id"] == target_id
        )

    def metadata_path(self, target_id: str) -> Path:
        return self.fixtures_dir / self.target(target_id)["evidence_source"]

    def metadata(self, target_id: str) -> dict:
        return self.load(self.metadata_path(target_id))

    def write_metadata(self, target_id: str, metadata: dict) -> None:
        self.write(self.metadata_path(target_id), metadata)

    def refresh_digest(self, target_id: str) -> None:
        metadata = self.metadata(target_id)
        source = self.metadata_path(target_id).parent / metadata["digest"]["path"]
        metadata["digest"]["value"] = hashlib.sha256(source.read_bytes()).hexdigest()
        self.write_metadata(target_id, metadata)

    def audit(self) -> dict:
        return backup_audit.audit_backups(
            root=self.root,
            policy_path=self.policy_path,
            fixtures_dir=self.fixtures_dir,
            registry_path=self.root / "policy" / "estate-registry.json",
            contracts_dir=self.root / "policy" / "service-contracts",
            now=self.NOW,
        )

    def rules(self, report: dict) -> set[str]:
        return {finding["rule_id"] for finding in report["findings"]}

    def evidence(self, report: dict, target_id: str) -> dict:
        return next(
            item
            for item in report["backup_evidence"]
            if item["target_id"] == target_id
        )

    def test_valid_backup_policy(self) -> None:
        schema = load_json(self.root / "policy" / "backup-audit.schema.json")
        self.assertEqual([], validate_instance(self.policy(), schema))
        self.assertEqual([], self.audit()["policy_validation"]["errors"])

    def test_malformed_backup_policy(self) -> None:
        policy = self.policy()
        policy.pop("owner")
        self.write_policy(policy)
        report = self.audit()
        self.assertTrue(report["policy_validation"]["errors"])
        self.assertIn("malformed-backup-policy", self.rules(report))
        self.assertEqual("failed", report["result_state"])

    def test_malformed_restore_bounds_fail_closed(self) -> None:
        policy = self.policy()
        policy["guardrails"]["maximum_uncompressed_bytes"] = "unbounded"
        self.write_policy(policy)
        report = self.audit()
        self.assertIn("malformed-backup-policy", self.rules(report))
        self.assertEqual("failed", report["result_state"])

    def test_all_fixture_targets_validate(self) -> None:
        report = self.audit()
        self.assertEqual(6, len(report["backup_evidence"]))
        self.assertTrue(
            all(item["result_state"] == "healthy" for item in report["backup_evidence"])
        )
        self.assertTrue(
            all(
                item["restore_drill_state"] == "passed"
                for item in report["backup_evidence"]
            )
        )

    def test_owner_approved_recovery_targets(self) -> None:
        notify = self.target("atlas-notify-kv-export-fixture")
        self.assertEqual(6, notify["recovery_point_objective_hours"])
        self.assertEqual(4, notify["recovery_time_objective_hours"])
        self.assertEqual(30, notify["retention_expectation_days"])

        memory = self.target("ramone-memory-chroma-export-fixture")
        self.assertEqual(24, memory["recovery_point_objective_hours"])
        self.assertEqual(8, memory["recovery_time_objective_hours"])
        self.assertEqual(30, memory["retention_expectation_days"])

    def test_fresh_backup(self) -> None:
        evidence = self.evidence(self.audit(), "cloudflare-kv-export-fixture")
        self.assertEqual("fresh", evidence["freshness_state"])
        self.assertEqual("healthy", evidence["result_state"])

    def test_stale_backup(self) -> None:
        target_id = "cloudflare-kv-export-fixture"
        metadata = self.metadata(target_id)
        metadata["backup_at"] = "2026-07-10T09:30:00Z"
        metadata["observed_at"] = "2026-07-14T11:00:00Z"
        metadata["retention"]["retained_until"] = "2026-08-09T09:30:00Z"
        self.write_metadata(target_id, metadata)
        report = self.audit()
        evidence = self.evidence(report, target_id)
        self.assertEqual("stale", evidence["freshness_state"])
        self.assertEqual("stale", evidence["result_state"])
        self.assertIn("stale-backup", self.rules(report))

    def test_missing_evidence(self) -> None:
        self.metadata_path("incident-export-fixture").unlink()
        report = self.audit()
        evidence = self.evidence(report, "incident-export-fixture")
        self.assertEqual("unavailable", evidence["result_state"])
        self.assertNotEqual("healthy", evidence["status"])
        self.assertIn("missing-backup-evidence", self.rules(report))

    def test_retention_met(self) -> None:
        self.assertEqual(
            "met",
            self.evidence(self.audit(), "incident-export-fixture")["retention_state"],
        )

    def test_retention_violated(self) -> None:
        target_id = "incident-export-fixture"
        metadata = self.metadata(target_id)
        metadata["retention"]["retained_until"] = "2026-07-20T09:00:00Z"
        self.write_metadata(target_id, metadata)
        report = self.audit()
        self.assertEqual(
            "violated", self.evidence(report, target_id)["retention_state"]
        )
        self.assertIn("retention-policy-violated", self.rules(report))

    def test_retention_policy_missing(self) -> None:
        target_id = "incident-export-fixture"
        metadata = self.metadata(target_id)
        metadata.pop("retention")
        self.write_metadata(target_id, metadata)
        report = self.audit()
        self.assertIn("retention-policy-missing", self.rules(report))
        self.assertNotEqual(
            "healthy", self.evidence(report, target_id)["result_state"]
        )

    def test_restore_drill_success(self) -> None:
        evidence = self.evidence(self.audit(), "chroma-vector-store-export-fixture")
        self.assertEqual("passed", evidence["restore_drill_state"])
        self.assertEqual(self.NOW_TEXT, evidence["restore_tested_at"])

    def test_restore_drill_failure(self) -> None:
        target_id = "github-workflow-artifact-fixture"
        metadata = self.metadata(target_id)
        source = self.metadata_path(target_id).parent / metadata["restore_source"]["path"]
        document = self.load(source)
        document.pop("files")
        self.write(source, document)
        metadata["expected_total_size_bytes"] = source.stat().st_size
        self.write_metadata(target_id, metadata)
        self.refresh_digest(target_id)
        report = self.audit()
        self.assertIn("restore-drill-failed", self.rules(report))
        self.assertEqual(
            "failed", self.evidence(report, target_id)["restore_drill_state"]
        )

    def test_restore_drill_unavailable(self) -> None:
        policy = self.policy()
        target = next(
            item
            for item in policy["targets"]
            if item["target_id"] == "incident-export-fixture"
        )
        target["restore_drill_type"] = "archive-extraction"
        self.write_policy(policy)
        report = self.audit()
        self.assertIn("restore-drill-unavailable", self.rules(report))
        self.assertEqual(
            "unavailable",
            self.evidence(report, "incident-export-fixture")["restore_drill_state"],
        )

    def test_path_traversal_refusal(self) -> None:
        target_id = "incident-export-fixture"
        metadata = self.metadata(target_id)
        metadata["restore_source"]["path"] = "../outside.json"
        self.write_metadata(target_id, metadata)
        report = self.audit()
        self.assertIn("unsafe-restore-path", self.rules(report))
        self.assertEqual("failed", self.evidence(report, target_id)["result_state"])

    def test_symlink_escape_refusal(self) -> None:
        target_id = "incident-export-fixture"
        target_root = self.metadata_path(target_id).parent
        outside = self.fixtures_dir / "outside.json"
        outside.write_text("{}\n", encoding="utf-8")
        (target_root / "escape.json").symlink_to(outside)
        metadata = self.metadata(target_id)
        metadata["restore_source"]["path"] = "escape.json"
        self.write_metadata(target_id, metadata)
        self.assertIn("unsafe-restore-path", self.rules(self.audit()))

    def test_digest_mismatch(self) -> None:
        target_id = "cloudflare-kv-export-fixture"
        metadata = self.metadata(target_id)
        metadata["digest"]["value"] = "0" * 64
        self.write_metadata(target_id, metadata)
        report = self.audit()
        self.assertIn("digest-mismatch", self.rules(report))
        self.assertEqual("failed", self.evidence(report, target_id)["result_state"])

    def test_malformed_export(self) -> None:
        target_id = "cloudflare-kv-export-fixture"
        metadata = self.metadata(target_id)
        source = self.metadata_path(target_id).parent / metadata["restore_source"]["path"]
        source.write_text("{not-json}\n", encoding="utf-8")
        metadata["expected_total_size_bytes"] = source.stat().st_size
        self.write_metadata(target_id, metadata)
        self.refresh_digest(target_id)
        report = self.audit()
        self.assertIn("malformed-export", self.rules(report))
        self.assertIn("restore-drill-failed", self.rules(report))

    def test_unknown_service_id(self) -> None:
        policy = self.policy()
        target = next(
            item
            for item in policy["targets"]
            if item["target_id"] == "incident-export-fixture"
        )
        target["service_id"] = "unknown-service"
        self.write_policy(policy)
        report = self.audit()
        self.assertIn("unknown-service-id", self.rules(report))
        self.assertNotEqual(
            "healthy",
            self.evidence(report, "incident-export-fixture")["result_state"],
        )

    def test_target_owner_missing(self) -> None:
        policy = self.policy()
        policy["targets"][0].pop("owner")
        self.write_policy(policy)
        self.assertIn("missing-backup-target-owner", self.rules(self.audit()))

    def test_excluded_classification_refusal(self) -> None:
        policy = self.policy()
        target = policy["targets"][0]
        target["classification"] = {
            "lifecycle": "deprecated",
            "scope": "public",
            "provenance": "original",
        }
        self.write_policy(policy)
        self.assertIn("backup-classification-conflict", self.rules(self.audit()))

    def test_deprecated_repository_active_backup_refusal(self) -> None:
        registry_path = self.root / "policy" / "estate-registry.json"
        registry = self.load(registry_path)
        entry = next(
            item
            for item in registry["repositories"]
            if item["repository"] == "AtlasReaper311/atlas-api-public"
        )
        entry["lifecycle"] = "deprecated"
        self.write(registry_path, registry)
        self.assertIn("backup-classification-conflict", self.rules(self.audit()))

    def test_backup_coverage_is_complete_and_healthy(self) -> None:
        policy = self.policy()
        self.assertNotIn(
            "not-declared", {item["state"] for item in policy["service_coverage"]}
        )
        report = self.audit()
        self.assertNotIn("backup-coverage-not-declared", self.rules(report))
        self.assertEqual("healthy", report["result_state"])

    def test_backup_evidence_schema_validation(self) -> None:
        self.assertEqual([], self.audit()["backup_evidence_schema_errors"])

    def test_finding_schema_validation(self) -> None:
        self.assertEqual([], self.audit()["finding_schema_errors"])

    def test_deterministic_output(self) -> None:
        first = self.audit()
        self.assertEqual(first, self.audit())
        self.assertEqual(
            sorted(first["backup_evidence"], key=lambda item: item["target_id"]),
            first["backup_evidence"],
        )

    def test_policy_validation_is_idempotent(self) -> None:
        self.assertEqual(self.audit(), self.audit())

    def test_markdown_and_json_report_generation(self) -> None:
        output = self.root / "output"
        command = [
            sys.executable,
            str(SCRIPTS / "backup_audit.py"),
            "--root",
            str(self.root),
            "--policy",
            "policy/backup-audit.json",
            "--fixtures",
            "tests/fixtures/backup-audit",
            "--report",
            str(output / "backup-audit.json"),
            "--markdown",
            str(output / "backup-audit.md"),
            "--now",
            self.NOW_TEXT,
            "--quiet",
        ]
        subprocess.run(command, check=True)
        report = self.load(output / "backup-audit.json")
        self.assertEqual("healthy", report["result_state"])
        self.assertTrue(report["idempotent"])
        self.assertIn(
            "validates local fixtures only",
            (output / "backup-audit.md").read_text(encoding="utf-8"),
        )
        first_json = (output / "backup-audit.json").read_bytes()
        first_markdown = (output / "backup-audit.md").read_bytes()
        subprocess.run(command, check=True)
        self.assertEqual(first_json, (output / "backup-audit.json").read_bytes())
        self.assertEqual(first_markdown, (output / "backup-audit.md").read_bytes())

    def test_safe_archive_extraction(self) -> None:
        archive = self.root / "fixture.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("export/manifest.json", "{}\n")
        destination = self.root / "restored"
        files, size = backup_audit.safe_extract_zip(
            archive, destination, maximum_files=2, maximum_bytes=1024
        )
        self.assertEqual((1, 3), (files, size))
        self.assertEqual("{}\n", (destination / "export" / "manifest.json").read_text())

    def test_archive_path_traversal_refusal(self) -> None:
        archive = self.root / "traversal.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../escape.json", "{}\n")
        with self.assertRaises(backup_audit.UnsafeRestorePath):
            backup_audit.safe_extract_zip(
                archive, self.root / "restored", maximum_files=2, maximum_bytes=1024
            )

    def test_archive_symlink_refusal(self) -> None:
        archive = self.root / "symlink.zip"
        member = zipfile.ZipInfo("escape-link")
        member.create_system = 3
        member.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(member, "../outside")
        with self.assertRaises(backup_audit.UnsafeRestorePath):
            backup_audit.safe_extract_zip(
                archive, self.root / "restored", maximum_files=2, maximum_bytes=1024
            )

    def test_malformed_archive_refusal(self) -> None:
        archive = self.root / "malformed.zip"
        archive.write_text("not a zip\n", encoding="utf-8")
        with self.assertRaises(backup_audit.MalformedExport):
            backup_audit.safe_extract_zip(
                archive, self.root / "restored", maximum_files=2, maximum_bytes=1024
            )

    def test_archive_entry_count_bound(self) -> None:
        archive = self.root / "too-many.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("one.json", "{}\n")
            output.writestr("two.json", "{}\n")
        with self.assertRaises(backup_audit.MalformedExport):
            backup_audit.safe_extract_zip(
                archive, self.root / "restored", maximum_files=1, maximum_bytes=1024
            )

    def test_archive_uncompressed_size_bound(self) -> None:
        archive = self.root / "too-large.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("large.txt", "fixture-data")
        with self.assertRaises(backup_audit.MalformedExport):
            backup_audit.safe_extract_zip(
                archive, self.root / "restored", maximum_files=2, maximum_bytes=4
            )

    def test_unsafe_restore_location_refusal(self) -> None:
        policy = self.policy()
        policy["targets"][0]["disposable_restore_location"] = "/tmp/live-data"
        self.write_policy(policy)
        self.assertIn("unsafe-restore-path", self.rules(self.audit()))


if __name__ == "__main__":
    unittest.main()
