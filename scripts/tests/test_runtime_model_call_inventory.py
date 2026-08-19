import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import runtime_model_call_inventory


class RuntimeModelCallInventoryTests(unittest.TestCase):
    def load_inventory(self):
        return json.loads(
            (ROOT / "policy" / "runtime-model-call-inventory.json").read_text(
                encoding="utf-8"
            )
        )

    def load_coverage(self):
        return json.loads(
            (ROOT / "policy" / "model-promotion-coverage.json").read_text(
                encoding="utf-8"
            )
        )

    def test_inventory_has_unique_valid_call_sites(self):
        inventory = self.load_inventory()

        call_sites = runtime_model_call_inventory.validate_inventory(inventory)

        self.assertGreaterEqual(len(call_sites), 10)
        self.assertEqual(len(call_sites), len({item["id"] for item in call_sites}))

    def test_ramone_memory_live_chat_is_not_session_summary(self):
        inventory = self.load_inventory()
        call_sites = runtime_model_call_inventory.validate_inventory(inventory)

        live_chat = next(item for item in call_sites if item["id"] == "ramone-memory-api-chat")
        summary = next(
            item for item in call_sites if item["id"] == "ramone-memory-session-summary"
        )

        self.assertEqual("interactive-live", live_chat["classification"])
        self.assertEqual("ramone-live-chat", live_chat["capability_id"])
        self.assertEqual("async-summary", summary["classification"])
        self.assertEqual("session-summarisation", summary["capability_id"])

    def test_interactive_live_override_is_flagged(self):
        call_sites = [
            {
                "id": "bad-live",
                "classification": "interactive-live",
                "capability_id": "session-summarisation",
            }
        ]
        coverage = self.load_coverage()

        issues = runtime_model_call_inventory.analyse(call_sites, coverage)

        self.assertTrue(
            any(item["code"] == "interactive-live-covered-by-override" for item in issues)
        )

    def test_missing_harness_paths_are_reported_without_runtime_calls(self):
        inventory = self.load_inventory()
        coverage = self.load_coverage()
        report = runtime_model_call_inventory.build_report(
            ROOT / "policy" / "runtime-model-call-inventory.json",
            ROOT / "policy" / "model-promotion-coverage.json",
            harness_root=ROOT / "__missing_harness__",
        )

        self.assertGreater(report["summary"]["warnings"], 0)
        self.assertTrue(
            any(item["code"].endswith("-path-missing") for item in report["issues"])
        )
        self.assertEqual(
            len(inventory["call_sites"]),
            report["summary"]["call_sites"],
        )

    def test_real_harness_origin_main_evidence_has_expected_open_gaps(self):
        harness = ROOT.parent / "atlas-eval-harness"
        if not harness.exists():
            self.skipTest("atlas-eval-harness checkout not present next to atlas-infra")

        report = runtime_model_call_inventory.build_report(
            ROOT / "policy" / "runtime-model-call-inventory.json",
            ROOT / "policy" / "model-promotion-coverage.json",
            harness_root=harness,
        )

        self.assertTrue(
            any(
                item["call_site"] == "ollama-rag-kit-ask"
                and item["code"] == "promotion-record-path-missing"
                for item in report["issues"]
            )
        )
        self.assertTrue(
            any(
                item["call_site"] == "ramone-memory-api-chat"
                and item["code"] == "interactive-live-without-eval-case"
                for item in report["issues"]
            )
        )


if __name__ == "__main__":
    unittest.main()
