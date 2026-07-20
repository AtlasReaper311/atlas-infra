from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts import control_plane_contracts as contracts
from scripts.control_plane_io import load_json
from scripts.reliability_evaluator import (
    build_release_baseline,
    evaluate,
    from_slo_response,
    round_places,
)

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "tests/fixtures/reliability/vectors"
RESULT_SCHEMA = load_json(ROOT / "contracts/v1/reliability-result.schema.json")
FINGERPRINT_RULES = load_json(ROOT / "contracts/v1/fingerprint-rules.json")


def run_vector(name: str) -> tuple[dict, dict]:
    payload = load_json(VECTORS / name / "input.json")
    expected = load_json(VECTORS / name / "expected.json")
    actual = evaluate(
        payload["policy"],
        payload["uptime"],
        payload["now"],
        payload["source_checked_at"],
    )
    return actual, expected


class VectorTests(unittest.TestCase):
    """The vectors are the cross-language contract: exact equality only."""

    def test_every_vector_matches_expected_exactly(self) -> None:
        names = sorted(path.name for path in VECTORS.iterdir() if path.is_dir())
        self.assertGreaterEqual(len(names), 14)
        for name in names:
            with self.subTest(vector=name):
                actual, expected = run_vector(name)
                self.assertEqual(expected, actual)

    def test_every_vector_output_is_contract_valid(self) -> None:
        for path in sorted(VECTORS.iterdir()):
            expected = load_json(path / "expected.json")
            errors = contracts.validate_instance(expected, RESULT_SCHEMA)
            errors += contracts.semantic_errors(
                "reliability-result.schema.json", expected, FINGERPRINT_RULES
            )
            self.assertEqual([], errors, path.name)

    def test_evaluation_is_deterministic(self) -> None:
        payload = load_json(VECTORS / "mixed-states" / "input.json")
        first = evaluate(
            payload["policy"], payload["uptime"], payload["now"],
            payload["source_checked_at"],
        )
        second = evaluate(
            payload["policy"], payload["uptime"], payload["now"],
            payload["source_checked_at"],
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_states_cover_the_failure_matrix(self) -> None:
        observed = set()
        for path in sorted(VECTORS.iterdir()):
            expected = load_json(path / "expected.json")
            observed.update(entry["state"] for entry in expected["results"])
        self.assertEqual(
            {
                "objective_met",
                "budget_at_risk",
                "budget_exhausted",
                "insufficient_evidence",
                "stale_evidence",
                "unavailable_source",
                "malformed_evidence",
            },
            observed,
        )


class BehaviourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = load_json(VECTORS / "healthy" / "input.json")

    def test_missing_measurement_never_becomes_success(self) -> None:
        broken = copy.deepcopy(self.payload)
        broken["uptime"]["components"] = {}
        result = evaluate(
            broken["policy"], broken["uptime"], broken["now"],
            broken["source_checked_at"],
        )
        entry = result["results"][0]
        self.assertEqual("unavailable_source", entry["state"])
        self.assertIsNone(entry["availability_pct"])
        self.assertEqual(0, entry["samples"]["total"])

    def test_out_of_order_days_do_not_change_the_result(self) -> None:
        shuffled = copy.deepcopy(self.payload)
        component = shuffled["uptime"]["components"]["alpha"]
        shuffled["uptime"]["components"]["alpha"] = dict(
            reversed(list(component.items()))
        )
        baseline = evaluate(
            self.payload["policy"], self.payload["uptime"], self.payload["now"],
            self.payload["source_checked_at"],
        )
        reordered = evaluate(
            shuffled["policy"], shuffled["uptime"], shuffled["now"],
            shuffled["source_checked_at"],
        )
        self.assertEqual(baseline, reordered)

    def test_duplicate_windows_prune_outside_objective_window(self) -> None:
        aged = copy.deepcopy(self.payload)
        aged["uptime"]["components"]["alpha"]["2026-06-01"] = {
            "ok": 100,
            "total": 144,
        }
        result = evaluate(
            aged["policy"], aged["uptime"], aged["now"], aged["source_checked_at"]
        )
        entry = result["results"][0]
        self.assertEqual("2026-07-13", entry["window"]["start_day"])
        self.assertEqual(936, entry["samples"]["total"])

    def test_counter_reset_shape_is_visible_not_hidden(self) -> None:
        reset = copy.deepcopy(self.payload)
        reset["uptime"]["components"]["alpha"]["2026-07-19"] = {"ok": 1, "total": 1}
        result = evaluate(
            reset["policy"], reset["uptime"], reset["now"],
            reset["source_checked_at"],
        )
        entry = result["results"][0]
        self.assertEqual(865, entry["samples"]["total"])
        self.assertLess(entry["coverage"]["fraction"], 1)

    def test_hundred_percent_target_has_no_burn_allowance(self) -> None:
        strict = copy.deepcopy(self.payload)
        strict["policy"]["objectives"][0]["target_pct"] = 100
        result = evaluate(
            strict["policy"], strict["uptime"], strict["now"],
            strict["source_checked_at"],
        )
        entry = result["results"][0]
        self.assertIsNone(entry["burn"]["fast"]["rate"])
        self.assertIn("no burn allowance", entry["burn"]["fast"]["reason"])

    def test_round_places_normalises_integral_floats(self) -> None:
        self.assertEqual(1, round_places(1.0, 4))
        self.assertIsInstance(round_places(1.0, 4), int)
        self.assertEqual(0.86, round_places(0.855, 2))
        self.assertEqual(-0.86, round_places(-0.855, 2))

    def test_slo_response_adapter_matches_kv_shape(self) -> None:
        response = {
            "measuring_since": "2026-07-13T00:00:00Z",
            "window_days": 30,
            "components": {
                "alpha": {
                    "days": {"2026-07-19": {"ok": 5, "total": 6}},
                    "ok": 5,
                    "total": 6,
                }
            },
        }
        adapted = from_slo_response(response)
        self.assertEqual(
            {"2026-07-19": {"ok": 5, "total": 6}}, adapted["components"]["alpha"]
        )
        self.assertEqual("2026-07-13T00:00:00Z", adapted["started_at"])


class BaselineTests(unittest.TestCase):
    def test_healthy_history_produces_a_valid_baseline(self) -> None:
        payload = load_json(VECTORS / "healthy" / "input.json")
        baseline = build_release_baseline(
            payload["policy"], payload["uptime"], payload["now"],
            "service-a", payload["source_checked_at"],
        )
        self.assertIsNotNone(baseline)
        self.assertEqual(
            "atlas-journey-watch/release-baseline/v1", baseline["schema_version"]
        )
        self.assertEqual("avg", baseline["latency_metric"])
        self.assertEqual(180, baseline["baseline"]["latency_ms_avg"])
        self.assertEqual(180, baseline["observed"]["latency_ms_avg"])
        self.assertEqual(0, baseline["baseline"]["error_rate"])
        self.assertEqual(25, baseline["thresholds"]["latency_regression_percent"])

    def test_insufficient_evidence_yields_no_baseline(self) -> None:
        payload = load_json(VECTORS / "insufficient" / "input.json")
        self.assertIsNone(
            build_release_baseline(
                payload["policy"], payload["uptime"], payload["now"],
                "service-a", payload["source_checked_at"],
            )
        )

    def test_stale_evidence_yields_no_baseline(self) -> None:
        payload = load_json(VECTORS / "stale-checked-at" / "input.json")
        self.assertIsNone(
            build_release_baseline(
                payload["policy"], payload["uptime"], payload["now"],
                "service-a", payload["source_checked_at"],
            )
        )


if __name__ == "__main__":
    unittest.main()
