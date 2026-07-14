from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts as contracts
import control_plane_summary as summary


class ControlPlaneSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_root = ROOT / "tests" / "fixtures" / "control-plane-summary"
        cls.sources = cls.fixture_root / "sources"
        cls.expected = contracts.load_json(cls.fixture_root / "expected-summary.json")
        cls.schema = contracts.load_json(
            ROOT / "contracts" / "v1" / "control-plane-summary.schema.json"
        )
        cls.now = datetime(2026, 7, 14, 10, 30, tzinfo=timezone.utc)

    def test_fixture_aggregation_matches_schema_and_expected_bytes(self) -> None:
        actual = summary.build_summary(self.sources, self.now)
        self.assertEqual(self.expected, actual)
        self.assertEqual([], contracts.validate_instance(actual, self.schema))
        self.assertEqual(1, actual["journeys"]["failed"])
        self.assertEqual(2, actual["contract_registry"]["drift_count"])

    def test_missing_sources_are_unknown_and_never_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            actual = summary.build_summary(Path(directory), self.now)
        self.assertEqual("unknown", actual["state"])
        for projection in summary.SOURCE_FILES:
            self.assertEqual("unknown", actual[projection]["state"])
            self.assertNotEqual("healthy", actual[projection]["state"])

    def test_expired_source_becomes_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(self.sources, target, dirs_exist_ok=True)
            actual = summary.build_summary(
                target, datetime(2026, 7, 16, 10, 30, tzinfo=timezone.utc)
            )
        self.assertEqual("stale", actual["health"]["state"])
        self.assertNotEqual("healthy", actual["state"])

    def test_malformed_source_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "health.json").write_text("{", encoding="utf-8")
            actual = summary.build_summary(target, self.now)
        self.assertEqual("unavailable", actual["health"]["state"])
        self.assertEqual("unavailable", actual["state"])

    def test_wrong_source_value_type_is_unavailable_not_zero_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(self.sources, target, dirs_exist_ok=True)
            health = contracts.load_json(target / "health.json")
            health["data"]["components_total"] = "34"
            (target / "health.json").write_text(
                json.dumps(health), encoding="utf-8"
            )
            actual = summary.build_summary(target, self.now)
        self.assertEqual("unavailable", actual["health"]["state"])
        self.assertNotEqual("healthy", actual["state"])

    def test_output_is_deterministic(self) -> None:
        first = summary.build_summary(self.sources, self.now)
        second = summary.build_summary(self.sources, self.now)
        self.assertEqual(first, second)
        self.assertEqual(first["request_id"], second["request_id"])

    def test_cli_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            command = [
                sys.executable,
                str(SCRIPTS / "control_plane_summary.py"),
                "--sources",
                str(self.sources),
                "--now",
                "2026-07-14T10:30:00Z",
                "--output",
                str(output),
            ]
            subprocess.run(command, check=True)
            first = output.read_bytes()
            subprocess.run(command, check=True)
            second = output.read_bytes()
        self.assertEqual(first, second)
        self.assertEqual(self.expected, json.loads(second))

    def test_phase9_fields_are_optional_for_earlier_v1_readers(self) -> None:
        earlier = dict(self.expected)
        earlier.pop("journeys")
        earlier.pop("contract_registry")
        earlier["gardener_proposals"] = dict(earlier["gardener_proposals"])
        earlier["gardener_proposals"].pop("open_pull_requests")
        self.assertEqual([], contracts.validate_instance(earlier, self.schema))


if __name__ == "__main__":
    unittest.main()
