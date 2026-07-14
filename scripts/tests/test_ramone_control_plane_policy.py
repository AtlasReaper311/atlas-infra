from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_OPERATIONS = {
    "GetEstateSummary",
    "GetServiceStatus",
    "GetReleaseStatus",
    "ListActiveFindings",
    "GetQuotaProjection",
    "GetBackupStatus",
    "ListGardenerProposals",
    "FindRunbook",
    "SearchEvidence",
}
EXPECTED_SENSORS = {
    "sensor.atlas_estate_health",
    "sensor.atlas_failed_journeys",
    "sensor.atlas_release_state",
    "sensor.atlas_contract_drift",
    "sensor.atlas_quota_level",
    "sensor.atlas_quota_projection",
    "sensor.atlas_open_gardener_prs",
    "sensor.atlas_secret_hygiene",
    "sensor.atlas_backup_freshness",
    "sensor.atlas_latest_evidence",
}


class RamoneControlPlanePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (ROOT / "policy" / "ramone-control-plane-tools.json").read_text(
                encoding="utf-8"
            )
        )

    def test_exact_nine_get_only_operations(self) -> None:
        operations = self.policy["operations"]
        self.assertEqual(EXPECTED_OPERATIONS, {item["operation_id"] for item in operations})
        self.assertEqual(9, len(operations))
        self.assertTrue(all(item["method"] == "GET" for item in operations))

    def test_exact_ten_sensor_names_and_no_service_calls(self) -> None:
        home_assistant = self.policy["home_assistant"]
        self.assertEqual(EXPECTED_SENSORS, set(home_assistant["entities"]))
        self.assertEqual(10, len(home_assistant["entities"]))
        self.assertTrue(home_assistant["sensor_only"])
        self.assertFalse(home_assistant["service_calls_allowed"])
        self.assertFalse(home_assistant["assist_exposure_automatic"])

    def test_bearer_name_is_documented_without_a_value(self) -> None:
        authentication = self.policy["authentication"]
        self.assertEqual("bearer", authentication["scheme"])
        self.assertEqual(
            "RAMONE_CONTROL_PLANE_READ_TOKEN", authentication["secret_name"]
        )
        self.assertFalse(authentication["model_receives_credentials"])
        self.assertEqual([], authentication["provider_permissions"])
        self.assertNotIn("value", authentication)
        self.assertNotIn("token_value", authentication)

    def test_write_and_passthrough_capabilities_are_blocked(self) -> None:
        blocked = set(self.policy["blocked_capabilities"])
        for capability in {
            "generic-shell",
            "arbitrary-http",
            "provider-api-proxy",
            "generic-home-assistant-service-call",
            "raw-evidence-blob-fetch",
            "write-methods",
            "deployment",
            "backup-restore",
        }:
            self.assertIn(capability, blocked)

    def test_protected_ramone_capabilities_remain_explicit(self) -> None:
        rendered = " ".join(self.policy["protected_capabilities"]).lower()
        for term in {
            "identity",
            "prompt",
            "model",
            "memory",
            "home assistant",
            "specular",
            "phone",
            "watch",
            "wake word",
            "wyoming",
            "stt",
            "tts",
            "openwebui",
        }:
            self.assertIn(term, rendered)


if __name__ == "__main__":
    unittest.main()
