#!/usr/bin/env python3
"""Deterministic reliability evaluator: the canonical reference implementation.

Input is the published ``atlas-reliability-policy/v1`` document plus the
per-day probe counters that ``atlas-api-public`` accrues (the KV
``uptime:days:v1`` shape: ``{started_at, window_days, components: {name:
{"YYYY-MM-DD": {ok, total, ms_sum, ms_count}}}}``). Output is one
``atlas-control-plane/reliability-result/v1`` document.

Honesty rules enforced here:

- missing, malformed, stale or insufficient evidence is a stated condition,
  never health;
- burn windows are day-granular because the source is day-granular; sub-day
  windows are not claimed;
- percentiles are structurally impossible from ``ms_sum``/``ms_count``
  aggregates and are always reported unsupported with the reason;
- evaluation is a pure function of (policy, counters, now, source_checked_at):
  identical inputs produce byte-identical output.

The runtime consumer in ``atlas-api-public`` (``src/lib/reliability.js``)
mirrors these formula sequences exactly; the shared vectors under
``tests/fixtures/reliability/vectors/`` pin both implementations to identical
canonical output. Numbers are normalised to integers whenever integral so
Python and JavaScript serialise them identically.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
from typing import Any

try:
    from .control_plane_io import digest_json, load_json
except ImportError:  # direct script execution
    from control_plane_io import digest_json, load_json

ROOT = Path(__file__).resolve().parents[1]
DAY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

STATE_TO_CONTROL_PLANE = {
    "objective_met": "healthy",
    "budget_at_risk": "warning",
    "budget_exhausted": "failed",
    "insufficient_evidence": "unknown",
    "stale_evidence": "stale",
    "unavailable_source": "unavailable",
    "malformed_evidence": "unavailable",
    "unmeasured": "unknown",
}


def _normalise_number(value: float) -> int | float:
    """Return an int when integral so Python and JavaScript serialise alike."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def round_places(value: float, places: int) -> int | float:
    """Round half away from zero using the shared cross-language sequence."""
    factor = 10 ** places
    scaled = math.floor(abs(value) * factor + 0.5) / factor
    result = scaled if value >= 0 else -scaled
    return _normalise_number(result)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def utc_day(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _bucket_errors(day: str, bucket: Any, today: str) -> list[str]:
    """Structural validation for one day bucket."""
    if not DAY_PATTERN.match(day):
        return [f"day key {day!r} is not a UTC date"]
    if day > today:
        return [f"day {day} is in the future"]
    if not isinstance(bucket, dict):
        return [f"day {day} bucket is not an object"]
    problems: list[str] = []
    ok = bucket.get("ok")
    total = bucket.get("total")
    for name, value in (("ok", ok), ("total", total)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            problems.append(f"day {day} {name} is not a non-negative integer")
    if not problems and ok > total:
        problems.append(f"day {day} counts ok above total")
    for name in ("ms_sum", "ms_count"):
        if name in bucket:
            value = bucket[name]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                problems.append(f"day {day} {name} is not a non-negative number")
    if (
        not problems
        and isinstance(bucket.get("ms_count"), int)
        and bucket["ms_count"] > ok
    ):
        problems.append(f"day {day} ms_count exceeds ok samples")
    return problems


def _burn(
    window_days: list[str],
    days: dict[str, dict[str, Any]],
    bucket_days: int,
    minimum_samples: int,
    allowed_fraction: float,
) -> dict[str, Any]:
    """Day-granular burn rate over the newest ``bucket_days`` buckets."""
    recent = window_days[-bucket_days:]
    ok = sum(days[day].get("ok", 0) for day in recent)
    total = sum(days[day].get("total", 0) for day in recent)
    if total < minimum_samples:
        return {
            "rate": None,
            "samples": total,
            "bucket_days": bucket_days,
            "reason": f"insufficient samples for burn window ({total} of {minimum_samples})",
        }
    if allowed_fraction <= 0:
        return {
            "rate": None,
            "samples": total,
            "bucket_days": bucket_days,
            "reason": "a 100 percent target has no burn allowance",
        }
    rate = ((total - ok) / total) / allowed_fraction
    return {
        "rate": round_places(rate, 2),
        "samples": total,
        "bucket_days": bucket_days,
        "reason": None,
    }


def evaluate(
    policy: dict[str, Any],
    uptime: Any,
    now_iso: str,
    source_checked_at: str | None = None,
) -> dict[str, Any]:
    """Evaluate every objective in ``policy`` against ``uptime`` counters."""
    config = policy["evaluator_config"]
    now = parse_utc(now_iso)
    today = utc_day(now)
    stale_seconds = int(config["result_stale_after_seconds"])
    stale_after = (now + timedelta(seconds=stale_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    percentile_reason = str(config["percentile_reason"])
    expected_per_day = int(config["expected_samples_per_day"])

    uptime_valid = isinstance(uptime, dict) and isinstance(uptime.get("components"), dict)
    measuring_since = None
    window_days_count = None
    if uptime_valid:
        raw_since = uptime.get("started_at")
        if isinstance(raw_since, str):
            try:
                parse_utc(raw_since)
                measuring_since = raw_since
            except ValueError:
                measuring_since = None
        raw_window = uptime.get("window_days")
        if isinstance(raw_window, int) and not isinstance(raw_window, bool) and 1 <= raw_window <= 90:
            window_days_count = raw_window

    results = []
    for objective in policy["objectives"]:
        results.append(
            _evaluate_objective(
                objective,
                uptime if uptime_valid else None,
                config,
                now,
                today,
                measuring_since,
                source_checked_at,
                percentile_reason,
                expected_per_day,
            )
        )

    document: dict[str, Any] = {
        "schema_version": "atlas-control-plane/reliability-result/v1",
        "evaluated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale_after": stale_after,
        "policy_fingerprint": policy["fingerprint"],
        "source": {
            "provider": "atlas-api-public/v1/slo",
            "window_days": window_days_count if window_days_count is not None else 30,
            "measuring_since": measuring_since,
            "checked_at": source_checked_at,
        },
        "results": results,
        "unmeasured": [
            {"service_id": item["service_id"], "reason": item["reason"]}
            for item in policy.get("unmeasured", [])
        ],
    }
    document["fingerprint"] = digest_json(document)
    return document


def _evaluate_objective(
    objective: dict[str, Any],
    uptime: dict[str, Any] | None,
    config: dict[str, Any],
    now: datetime,
    today: str,
    measuring_since: str | None,
    source_checked_at: str | None,
    percentile_reason: str,
    expected_per_day: int,
) -> dict[str, Any]:
    target = objective["target_pct"]
    allowed_fraction = (100 - target) / 100
    reasons: list[str] = []
    window_days_limit = int(objective["window_days"])
    cutoff = utc_day(now - timedelta(days=window_days_limit))

    result: dict[str, Any] = {
        "service_id": objective["service_id"],
        "objective_id": objective["objective_id"],
        "indicator": objective["indicator"],
        "target_pct": _normalise_number(float(target)),
        "state": "unavailable_source",
        "control_plane_state": "unavailable",
        "reasons": reasons,
        "window": {"start_day": None, "end_day": None, "days_observed": 0},
        "samples": {"ok": 0, "failed": 0, "total": 0},
        "availability_pct": None,
        "coverage": {"fraction": None, "observed": 0, "expected": 0},
        "latency": {
            "avg_ms": None,
            "percentiles_supported": False,
            "percentile_reason": percentile_reason,
        },
        "budget": {
            "allowed_failures": None,
            "remaining_fraction": None,
            "consumed_fraction": None,
        },
        "burn": {
            "fast": {
                "rate": None,
                "samples": 0,
                "bucket_days": int(config["fast_burn"]["bucket_days"]),
                "reason": "source unavailable",
            },
            "slow": {
                "rate": None,
                "samples": 0,
                "bucket_days": int(config["slow_burn"]["bucket_days"]),
                "reason": "source unavailable",
            },
        },
        "freshness": {
            "evidence_stale_after_seconds": int(
                objective["freshness"]["evidence_stale_after_seconds"]
            ),
        },
    }

    def finish(state: str) -> dict[str, Any]:
        result["state"] = state
        result["control_plane_state"] = STATE_TO_CONTROL_PLANE[state]
        return result

    if uptime is None:
        reasons.append("probe counters document is missing or malformed")
        return finish("unavailable_source")

    component_name = objective["measurement_source"]["component"]
    component = uptime["components"].get(component_name)
    if not isinstance(component, dict):
        reasons.append(f"component {component_name} has no counters")
        return finish("unavailable_source")

    structural: list[str] = []
    for day in sorted(component):
        structural.extend(_bucket_errors(day, component[day], today))
    if structural:
        reasons.extend(structural[:8])
        return finish("malformed_evidence")

    window_days = sorted(day for day in component if day >= cutoff)
    ok = sum(component[day]["ok"] for day in window_days)
    total = sum(component[day]["total"] for day in window_days)
    failed = total - ok

    result["window"] = {
        "start_day": window_days[0] if window_days else None,
        "end_day": window_days[-1] if window_days else None,
        "days_observed": len(window_days),
    }
    result["samples"] = {"ok": ok, "failed": failed, "total": total}

    if total > 0:
        result["availability_pct"] = round_places((ok / total) * 100, 2)

    ms_sum = sum(component[day].get("ms_sum", 0) for day in window_days)
    ms_count = sum(component[day].get("ms_count", 0) for day in window_days)
    if ms_count > 0:
        result["latency"]["avg_ms"] = round_places(ms_sum / ms_count, 0)

    # Expected sample volume: full cadence for every elapsed day in the
    # window since measurement effectively began, plus today's elapsed
    # portion at one probe per 600 seconds.
    effective_start = cutoff
    if measuring_since is not None:
        since_day = utc_day(parse_utc(measuring_since))
        if since_day > effective_start:
            effective_start = since_day
    if effective_start <= today:
        start_date = datetime.strptime(effective_start, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        today_date = datetime.strptime(today, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        full_days = max((today_date - start_date).days, 0)
        seconds_today = (
            (now - today_date).total_seconds()
            if effective_start < today or effective_start == today
            else 0
        )
        expected = full_days * expected_per_day + math.floor(seconds_today / 600)
    else:
        expected = 0
    result["coverage"]["observed"] = total
    result["coverage"]["expected"] = expected
    if expected > 0:
        fraction = total / expected
        result["coverage"]["fraction"] = round_places(min(fraction, 1), 4)

    fast = _burn(
        window_days,
        component,
        int(config["fast_burn"]["bucket_days"]),
        int(config["fast_burn"]["minimum_samples"]),
        allowed_fraction,
    )
    slow = _burn(
        window_days,
        component,
        int(config["slow_burn"]["bucket_days"]),
        int(config["slow_burn"]["minimum_samples"]),
        allowed_fraction,
    )
    result["burn"] = {"fast": fast, "slow": slow}

    # Staleness beats budget maths: old numbers presented as current would
    # be the exact dishonesty this system exists to prevent.
    evidence_stale_seconds = int(objective["freshness"]["evidence_stale_after_seconds"])
    if source_checked_at is not None:
        age = (now - parse_utc(source_checked_at)).total_seconds()
        if age > evidence_stale_seconds:
            reasons.append(
                f"counters were last confirmed {math.floor(age)} seconds ago,"
                f" past the {evidence_stale_seconds} second bound"
            )
            return finish("stale_evidence")
    elif window_days and window_days[-1] < utc_day(now - timedelta(days=1)):
        reasons.append(
            f"newest counters day {window_days[-1]} is older than one day"
        )
        return finish("stale_evidence")

    minimum = int(config["minimum_evaluation_samples"])
    if total < minimum:
        reasons.append(f"only {total} samples of the {minimum} required")
        return finish("insufficient_evidence")

    allowed = total * allowed_fraction
    result["budget"]["allowed_failures"] = round_places(allowed, 2)
    if allowed > 0:
        remaining = (allowed - failed) / allowed
        result["budget"]["remaining_fraction"] = round_places(remaining, 4)
        result["budget"]["consumed_fraction"] = round_places(failed / allowed, 4)
    else:
        remaining = 0 if failed == 0 else -1
        result["budget"]["remaining_fraction"] = remaining
        result["budget"]["consumed_fraction"] = 0 if failed == 0 else 1
        reasons.append("a 100 percent target leaves no failure allowance")

    coverage_fraction = result["coverage"]["fraction"]
    if (
        coverage_fraction is not None
        and coverage_fraction < config["coverage_confidence_floor"]
    ):
        reasons.append(
            f"coverage {coverage_fraction} is below the confidence floor"
        )

    if result["budget"]["remaining_fraction"] is not None and (
        result["budget"]["remaining_fraction"] <= 0
    ):
        reasons.append("the error budget for the window is exhausted")
        return finish("budget_exhausted")

    at_risk = False
    if fast["rate"] is not None and fast["rate"] >= config["fast_burn"]["at_risk_threshold"]:
        reasons.append(f"fast burn rate {fast['rate']} is at or above the risk threshold")
        at_risk = True
    if slow["rate"] is not None and slow["rate"] >= config["slow_burn"]["at_risk_threshold"]:
        reasons.append(f"slow burn rate {slow['rate']} is at or above the risk threshold")
        at_risk = True
    if (
        result["budget"]["remaining_fraction"] is not None
        and result["budget"]["remaining_fraction"]
        <= config["remaining_budget_at_risk_fraction"]
    ):
        reasons.append(
            f"remaining budget {result['budget']['remaining_fraction']} is at or below the risk fraction"
        )
        at_risk = True
    if at_risk:
        return finish("budget_at_risk")
    return finish("objective_met")


def from_slo_response(document: dict[str, Any]) -> dict[str, Any]:
    """Adapt a live /v1/slo response to the KV counters shape."""
    return {
        "started_at": document.get("measuring_since"),
        "window_days": document.get("window_days"),
        "components": {
            name: entry.get("days", {})
            for name, entry in (document.get("components") or {}).items()
            if isinstance(entry, dict)
        },
    }


def build_release_baseline(
    policy: dict[str, Any],
    uptime: Any,
    now_iso: str,
    service_id: str,
    source_checked_at: str | None = None,
) -> dict[str, Any] | None:
    """Render an atlas-journey-watch release-baseline document.

    Baseline is the objective window excluding the fast-burn buckets;
    observed is the fast-burn buckets. At verification time shortly after a
    deploy the observed window necessarily holds mostly pre-release samples,
    so this gates on the service being within its measured norms; genuine
    post-release regression detection needs later full-day evidence.
    Returns None when evidence cannot support an honest comparison.
    """
    result = evaluate(policy, uptime, now_iso, source_checked_at)
    entry = next(
        (item for item in result["results"] if item["service_id"] == service_id),
        None,
    )
    if entry is None or entry["state"] in {
        "unavailable_source",
        "malformed_evidence",
        "stale_evidence",
        "insufficient_evidence",
    }:
        return None

    objective = next(
        item for item in policy["objectives"] if item["service_id"] == service_id
    )
    config = policy["evaluator_config"]
    thresholds = config.get("release_baseline", {})
    component = uptime["components"][objective["measurement_source"]["component"]]
    now = parse_utc(now_iso)
    cutoff = utc_day(now - timedelta(days=int(objective["window_days"])))
    window_days = sorted(day for day in component if day >= cutoff)
    fast_days = window_days[-int(config["fast_burn"]["bucket_days"]):]
    base_days = [day for day in window_days if day not in fast_days]

    def window_stats(day_list: list[str]) -> dict[str, Any] | None:
        ok = sum(component[day]["ok"] for day in day_list)
        total = sum(component[day]["total"] for day in day_list)
        ms_sum = sum(component[day].get("ms_sum", 0) for day in day_list)
        ms_count = sum(component[day].get("ms_count", 0) for day in day_list)
        if total == 0 or ms_count == 0:
            return None
        return {
            "latency_ms_avg": round_places(ms_sum / ms_count, 0),
            "error_rate": round_places((total - ok) / total, 4),
        }

    baseline = window_stats(base_days)
    observed = window_stats(fast_days)
    if baseline is None or observed is None or baseline["latency_ms_avg"] == 0:
        return None
    stale_seconds = int(thresholds.get("stale_after_seconds", 1800))
    return {
        "schema_version": "atlas-journey-watch/release-baseline/v1",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale_after": (now + timedelta(seconds=stale_seconds)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "service_id": service_id,
        "latency_metric": "avg",
        "baseline": baseline,
        "observed": observed,
        "thresholds": {
            "latency_regression_percent": thresholds.get(
                "latency_regression_percent", 25
            ),
            "error_rate_increase": thresholds.get("error_rate_increase", 0.02),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evaluate", "emit-baseline"))
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--uptime", type=Path, required=True)
    parser.add_argument("--now", required=True, help="UTC RFC 3339 evaluation instant")
    parser.add_argument("--checked-at", help="when the counters were last confirmed")
    parser.add_argument("--service-id", help="required for emit-baseline")
    parser.add_argument("--slo-response", action="store_true",
                        help="treat --uptime as a live /v1/slo response body")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    policy = load_json(args.policy)
    uptime = load_json(args.uptime)
    if args.slo_response:
        uptime = from_slo_response(uptime)

    if args.command == "evaluate":
        document = evaluate(policy, uptime, args.now, args.checked_at)
    else:
        if not args.service_id:
            parser.error("emit-baseline requires --service-id")
        document = build_release_baseline(
            policy, uptime, args.now, args.service_id, args.checked_at
        )
        if document is None:
            print(
                "baseline unavailable: evidence cannot support an honest comparison",
            )
            return 1

    rendered = json.dumps(document, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
