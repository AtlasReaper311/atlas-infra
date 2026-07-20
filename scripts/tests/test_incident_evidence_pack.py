from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import unittest

from scripts import control_plane_contracts as contracts
from scripts.control_plane_io import load_json
from scripts.incident_evidence_pack import build_pack, main

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "tests/fixtures/reliability/vectors"
PACK_SCHEMA = load_json(ROOT / "policy/schemas/incident-evidence-pack.schema.json")


def make_args(**overrides) -> argparse.Namespace:
    values = {
        "service_id": "service-a",
        "reliability_result": VECTORS / "exhausted" / "expected.json",
        "generated_at": "2026-07-19T13:00:00Z",
        "first_detected_at": "2026-07-19T11:40:00Z",
        "last_healthy_at": "2026-07-18T23:50:00Z",
        "incident": None,
        "release_evidence": None,
        "no_related_release": False,
        "notify_events": None,
        "recovery_result": None,
        "correlation": None,
        "chaos_report": None,
        "output": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class PackTests(unittest.TestCase):
    def test_minimal_pack_is_schema_valid_and_honest(self) -> None:
        pack = build_pack(make_args())
        self.assertEqual([], contracts.validate_instance(pack, PACK_SCHEMA))
        self.assertEqual("budget_exhausted", pack["reliability"]["state"])
        self.assertEqual("unknown", pack["release"]["related"])
        self.assertEqual("unknown", pack["recovery"]["state"])
        self.assertEqual(
            "docs/runbooks/reliability-budget-exhausted.md", pack["runbook_ref"]
        )
        self.assertEqual("unavailable", pack["dora_correlation"]["state"])
        self.assertIsNone(pack["chaos_experiment_id"])

    def test_identical_inputs_produce_identical_packs(self) -> None:
        first = build_pack(make_args())
        second = build_pack(make_args())
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_full_pack_links_references_with_digests(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        base = Path(holder.name)
        incident = base / "incident.json"
        incident.write_text(json.dumps({"id": "inc-42", "trigger": {"ts": 1}}))
        release = base / "release.json"
        release.write_text(
            json.dumps(
                {
                    "repository": "AtlasReaper311/atlas-notify",
                    "deployment_id": "deploy-7",
                    "completed_at": "2026-07-19T11:30:00Z",
                    "journey_result": "failed",
                }
            )
        )
        events = base / "events.json"
        events.write_text(json.dumps({"events": [{"level": "failure"}] * 3}))
        recovery = base / "recovery.json"
        recovery.write_text(
            json.dumps(
                {
                    "evaluated_at": "2026-07-19T15:00:00Z",
                    "results": [
                        {"service_id": "service-a", "state": "objective_met"}
                    ],
                }
            )
        )
        chaos = base / "chaos.json"
        chaos.write_text(
            json.dumps({"reports": [{"experiment_id": "specular-route-503-v1"}]})
        )
        pack = build_pack(
            make_args(
                incident=incident,
                release_evidence=release,
                notify_events=events,
                recovery_result=recovery,
                chaos_report=chaos,
            )
        )
        self.assertEqual([], contracts.validate_instance(pack, PACK_SCHEMA))
        self.assertEqual("inc-42", pack["detection"]["incident_id"])
        self.assertEqual("linked", pack["release"]["related"])
        self.assertEqual("failed", pack["journey"]["state"])
        self.assertEqual(3, pack["notifications"]["delivered_count"])
        self.assertEqual("confirmed", pack["recovery"]["state"])
        self.assertEqual("specular-route-503-v1", pack["chaos_experiment_id"])
        kinds = sorted(reference["kind"] for reference in pack["references"])
        self.assertEqual(
            [
                "chaos-report",
                "incident",
                "notify-events",
                "recovery-result",
                "release-evidence",
                "reliability-result",
            ],
            kinds,
        )
        for reference in pack["references"]:
            self.assertRegex(reference["digest"], r"^[0-9a-f]{64}$")

    def test_recovery_below_objective_is_not_confirmed(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        recovery = Path(holder.name) / "recovery.json"
        recovery.write_text(
            json.dumps(
                {
                    "evaluated_at": "2026-07-19T15:00:00Z",
                    "results": [
                        {"service_id": "service-a", "state": "budget_at_risk"}
                    ],
                }
            )
        )
        pack = build_pack(make_args(recovery_result=recovery))
        self.assertEqual("not-confirmed", pack["recovery"]["state"])
        self.assertIsNone(pack["recovery"]["confirmed_at"])

    def test_unknown_service_fails_loudly(self) -> None:
        with self.assertRaises(SystemExit):
            build_pack(make_args(service_id="service-nope"))

    def test_cli_writes_a_valid_pack(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        output = Path(holder.name) / "pack.json"
        code = main(
            [
                "--service-id", "service-a",
                "--reliability-result", str(VECTORS / "exhausted" / "expected.json"),
                "--generated-at", "2026-07-19T13:00:00Z",
                "--first-detected-at", "2026-07-19T11:40:00Z",
                "--output", str(output),
            ]
        )
        self.assertEqual(0, code)
        pack = load_json(output)
        self.assertEqual([], contracts.validate_instance(pack, PACK_SCHEMA))
        self.assertIsNone(pack["detection"]["last_healthy_at"])


if __name__ == "__main__":
    unittest.main()
