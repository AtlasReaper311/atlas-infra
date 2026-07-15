import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chaos_harness


class ChaosHarnessTests(unittest.TestCase):
    def experiment(self):
        return {
            "id": "specular-route-503-v1",
            "version": "1.0.0",
            "target": "specular-edge",
            "control_url": "https://api.atlas-systems.uk/specular/__chaos",
            "probe_url": "https://api.atlas-systems.uk/specular",
            "notification_url": "https://api.atlas-systems.uk/notify/recent",
            "fault": "status_503",
            "duration_seconds": 45,
            "expectations": {
                "detect_within_seconds": 30,
                "recover_within_seconds": 60,
            },
            "rollback": {"method": "delete_control_lease"},
        }

    def test_valid_experiment(self):
        self.assertEqual([], chaos_harness.validate_experiment(self.experiment()))

    def test_lease_must_be_bounded(self):
        experiment = self.experiment()
        lease = {
            "expires_at": (
                chaos_harness.datetime.now(chaos_harness.timezone.utc)
                + chaos_harness.timedelta(seconds=45)
            ).isoformat().replace("+00:00", "Z")
        }
        result = chaos_harness.validate_lease(experiment, lease)
        self.assertLessEqual(result["remaining_seconds"], 45)

    def test_lease_without_expiry_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "expires_at"):
            chaos_harness.validate_lease(self.experiment(), {})

    def test_unbounded_duration_is_rejected(self):
        experiment = self.experiment()
        experiment["duration_seconds"] = 301
        self.assertTrue(
            any("duration_seconds" in item for item in chaos_harness.validate_experiment(experiment))
        )

    def test_simulation_closes_the_loop(self):
        report = chaos_harness.run_experiment(self.experiment(), "simulate", "")
        self.assertTrue(report["passed"])
        self.assertTrue(report["stages"]["preflight"]["ok"])
        self.assertTrue(report["stages"]["injection"]["lease_ttl_verified"])
        self.assertTrue(report["stages"]["detection"]["ok"])
        self.assertTrue(report["stages"]["notification"]["ok"])
        self.assertTrue(report["stages"]["recovery"]["ok"])

    def test_webhook_drop_expects_absence(self):
        experiment = self.experiment()
        experiment["id"] = "specular-webhook-drop-v1"
        experiment["fault"] = "webhook_drop"
        report = chaos_harness.run_experiment(experiment, "simulate", "")
        self.assertTrue(report["passed"])
        self.assertFalse(report["stages"]["notification"]["expected"])

    def test_report_set_is_machine_readable(self):
        report = chaos_harness.run_experiment(self.experiment(), "simulate", "")
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "report.json"
            markdown_path = Path(tmp) / "report.md"
            chaos_harness.write_reports([report], json_path, markdown_path)
            document = json.loads(json_path.read_text())
            self.assertEqual("atlas-chaos-report-set/v1", document["schema"])
            self.assertEqual(1, document["summary"]["passed"])


if __name__ == "__main__":
    unittest.main()
