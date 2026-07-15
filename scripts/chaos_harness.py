#!/usr/bin/env python3
"""Bounded chaos experiment runner for Atlas Systems.

Scheduled runs use the deterministic simulator. Live mode talks only to targets
declared in policy/chaos-experiments.json, requires an explicit confirmation
flag, requires a short-lived bearer token, and always attempts rollback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_FAULTS = {
    "status_503",
    "latency",
    "stale_response",
    "kv_write_reject",
    "webhook_drop",
}
MAX_DURATION_SECONDS = 300
MAX_DETECTION_SECONDS = 300
ALLOWED_HOST_SUFFIXES = ("atlas-systems.uk", "workers.dev", "localhost", "127.0.0.1")


def canonical_json_value(value):
    """Match JSON.stringify number semantics before cross-runtime hashing."""
    if isinstance(value, dict):
        return {
            key: canonical_json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [canonical_json_value(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def canonical_json_bytes(value) -> bytes:
    normalized = canonical_json_value(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_url(value: str, field: str) -> None:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    host = parsed.hostname.lower()
    if not any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_HOST_SUFFIXES):
        raise ValueError(f"{field} host is outside the Atlas allowlist: {host}")


def validate_experiment(experiment: dict[str, Any]) -> list[str]:
    errors = []
    identifier = str(experiment.get("id", ""))
    if not identifier or len(identifier) > 80:
        errors.append("id is required and must be at most 80 characters")
    fault = str(experiment.get("fault", ""))
    if fault not in ALLOWED_FAULTS:
        errors.append(f"unsupported fault: {fault}")
    duration = experiment.get("duration_seconds")
    if not isinstance(duration, int) or not 10 <= duration <= MAX_DURATION_SECONDS:
        errors.append(f"duration_seconds must be 10-{MAX_DURATION_SECONDS}")
    detection = experiment.get("expectations", {}).get("detect_within_seconds")
    if not isinstance(detection, int) or not 1 <= detection <= MAX_DETECTION_SECONDS:
        errors.append(f"expectations.detect_within_seconds must be 1-{MAX_DETECTION_SECONDS}")
    recovery = experiment.get("expectations", {}).get("recover_within_seconds")
    if not isinstance(recovery, int) or not 1 <= recovery <= MAX_DETECTION_SECONDS:
        errors.append(f"expectations.recover_within_seconds must be 1-{MAX_DETECTION_SECONDS}")
    if experiment.get("rollback", {}).get("method") != "delete_control_lease":
        errors.append("rollback.method must be delete_control_lease")
    for field in ("control_url", "probe_url", "notification_url"):
        try:
            validate_url(str(experiment.get(field, "")), field)
        except ValueError as error:
            errors.append(str(error))
    return errors


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors = []
    if policy.get("schema") != "atlas-chaos-policy/v1":
        errors.append("schema must be atlas-chaos-policy/v1")
    experiments = policy.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        errors.append("experiments must be a non-empty list")
        return errors
    identifiers = set()
    for index, experiment in enumerate(experiments):
        if not isinstance(experiment, dict):
            errors.append(f"experiments[{index}] must be an object")
            continue
        identifier = experiment.get("id")
        if identifier in identifiers:
            errors.append(f"duplicate experiment id: {identifier}")
        identifiers.add(identifier)
        errors.extend(f"{identifier or index}: {error}" for error in validate_experiment(experiment))
    return errors


@dataclass
class Observation:
    observed: bool
    detail: str
    status: int | None = None
    latency_ms: int | None = None


class SimulatedAdapter:
    def __init__(self) -> None:
        self.active: dict[str, dict[str, Any]] = {}

    def activate(self, experiment: dict[str, Any], _token: str) -> dict[str, Any]:
        record = {
            "experiment_id": experiment["id"],
            "fault": experiment["fault"],
            "activated_at": utc_now(),
            "expires_at": utc_now(),
        }
        self.active[experiment["id"]] = record
        return record

    def probe_fault(self, experiment: dict[str, Any]) -> Observation:
        fault = experiment["fault"]
        if experiment["id"] not in self.active:
            return Observation(False, "fault lease is not active")
        if fault == "status_503":
            return Observation(True, "controlled 503 observed", status=503, latency_ms=4)
        if fault == "latency":
            return Observation(True, "latency budget exceeded", status=200, latency_ms=2000)
        if fault == "stale_response":
            return Observation(True, "stale sampled_at marker observed", status=200, latency_ms=5)
        if fault == "kv_write_reject":
            return Observation(True, "x-atlas-chaos write rejection marker observed", status=200, latency_ms=5)
        if fault == "webhook_drop":
            return Observation(True, "notification intentionally absent", status=200, latency_ms=5)
        return Observation(False, "unsupported simulated fault")

    def notification_seen(self, experiment: dict[str, Any]) -> bool:
        return experiment["fault"] != "webhook_drop"

    def rollback(self, experiment: dict[str, Any], _token: str) -> None:
        self.active.pop(experiment["id"], None)

    def probe_recovery(self, experiment: dict[str, Any]) -> Observation:
        return Observation(
            experiment["id"] not in self.active,
            "healthy response restored",
            status=200,
            latency_ms=5,
        )


class LiveAdapter:
    def _request(
        self,
        url: str,
        *,
        method: str = "GET",
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: float = 10,
    ) -> tuple[int, bytes, dict[str, str], int]:
        headers = {"User-Agent": "atlas-chaos-harness/1.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        started = monotonic_ms()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return (
                    response.status,
                    response.read(),
                    {key.lower(): value for key, value in response.headers.items()},
                    monotonic_ms() - started,
                )
        except urllib.error.HTTPError as error:
            return (
                error.code,
                error.read(),
                {key.lower(): value for key, value in error.headers.items()},
                monotonic_ms() - started,
            )

    def activate(self, experiment: dict[str, Any], token: str) -> dict[str, Any]:
        payload = {
            "experiment_id": experiment["id"],
            "fault": experiment["fault"],
            "duration_seconds": experiment["duration_seconds"],
            "latency_ms": experiment.get("latency_ms"),
        }
        status, body, _, _ = self._request(
            experiment["control_url"],
            method="POST",
            token=token,
            payload=payload,
        )
        if status != 202:
            raise RuntimeError(f"activation failed with HTTP {status}: {body.decode(errors='replace')}")
        return json.loads(body).get("active", {})

    def probe_fault(self, experiment: dict[str, Any]) -> Observation:
        status, body, headers, latency_ms = self._request(
            experiment["probe_url"],
            timeout=max(10, experiment.get("latency_ms", 0) / 1000 + 5),
        )
        fault = experiment["fault"]
        text = body.decode("utf-8", errors="replace")
        if fault == "status_503":
            return Observation(status == 503, f"HTTP {status}", status, latency_ms)
        if fault == "latency":
            threshold = int(experiment.get("latency_ms", 1000) * 0.8)
            return Observation(latency_ms >= threshold, f"{latency_ms}ms >= {threshold}ms", status, latency_ms)
        if fault == "stale_response":
            try:
                payload = json.loads(text)
                sampled = payload.get("telemetry", {}).get("sampled_at")
                age = time.time() - datetime.fromisoformat(sampled.replace("Z", "+00:00")).timestamp()
                return Observation(age >= 1800, f"sample age {int(age)}s", status, latency_ms)
            except (ValueError, TypeError, AttributeError, json.JSONDecodeError):
                return Observation(False, "stale marker could not be parsed", status, latency_ms)
        if fault == "kv_write_reject":
            marker = headers.get("x-atlas-chaos")
            return Observation(bool(marker), f"x-atlas-chaos={marker}", status, latency_ms)
        if fault == "webhook_drop":
            return Observation(True, "target surface remained reachable while webhook was suppressed", status, latency_ms)
        return Observation(False, "unsupported fault", status, latency_ms)

    def notification_seen(self, experiment: dict[str, Any]) -> bool:
        status, body, _, _ = self._request(
            f"{experiment['notification_url']}?limit=50",
            timeout=10,
        )
        if status != 200:
            return False
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return False
        identifier = experiment["id"]
        return any(
            identifier in f"{item.get('title', '')} {item.get('message', '')}"
            for item in payload.get("events", [])
        )

    def rollback(self, experiment: dict[str, Any], token: str) -> None:
        status, body, _, _ = self._request(
            experiment["control_url"],
            method="DELETE",
            token=token,
        )
        if status != 200:
            raise RuntimeError(f"rollback failed with HTTP {status}: {body.decode(errors='replace')}")

    def probe_recovery(self, experiment: dict[str, Any]) -> Observation:
        status, _, _, latency_ms = self._request(experiment["probe_url"], timeout=10)
        return Observation(status == 200, f"HTTP {status}", status, latency_ms)


def wait_until(deadline_seconds: int, action, *, interval: float = 2.0):
    started = monotonic_ms()
    last = None
    while monotonic_ms() - started <= deadline_seconds * 1000:
        last = action()
        if getattr(last, "observed", last):
            return last, monotonic_ms() - started
        time.sleep(interval)
    return last, monotonic_ms() - started


def build_report(experiment: dict[str, Any], mode: str, stages: dict[str, Any], passed: bool) -> dict[str, Any]:
    report = {
        "schema": "atlas-chaos-report/v1",
        "experiment_id": experiment["id"],
        "experiment_version": str(experiment.get("version", "1.0.0")),
        "mode": mode,
        "target": experiment.get("target"),
        "fault": experiment["fault"],
        "generated_at": utc_now(),
        "passed": passed,
        "expectations": experiment["expectations"],
        "stages": stages,
        "safety": {
            "duration_seconds": experiment["duration_seconds"],
            "rollback_method": experiment["rollback"]["method"],
            "allowlisted_target": True,
        },
        "source": {
            "repository": os.getenv("GITHUB_REPOSITORY", "AtlasReaper311/atlas-infra"),
            "commit": os.getenv("GITHUB_SHA", "local"),
            "run_url": (
                f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/"
                f"{os.getenv('GITHUB_RUN_ID')}"
                if os.getenv("GITHUB_RUN_ID")
                else None
            ),
        },
    }
    canonical = canonical_json_bytes(report)
    report["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    return report


def run_experiment(experiment: dict[str, Any], mode: str, token: str) -> dict[str, Any]:
    adapter = SimulatedAdapter() if mode == "simulate" else LiveAdapter()
    stages: dict[str, Any] = {}
    rollback_error = None
    activated = False
    try:
        activated_at = monotonic_ms()
        lease = adapter.activate(experiment, token)
        activated = True
        stages["injection"] = {
            "ok": True,
            "at": utc_now(),
            "latency_ms": monotonic_ms() - activated_at,
            "lease": lease,
        }

        observation, detection_ms = wait_until(
            experiment["expectations"]["detect_within_seconds"],
            lambda: adapter.probe_fault(experiment),
            interval=0.1 if mode == "simulate" else 2.0,
        )
        stages["detection"] = {
            "ok": bool(observation and observation.observed),
            "at": utc_now(),
            "latency_ms": detection_ms,
            "detail": observation.detail if observation else "no observation",
            "status": observation.status if observation else None,
            "probe_latency_ms": observation.latency_ms if observation else None,
        }

        expected_notification = experiment["fault"] != "webhook_drop"
        if expected_notification:
            notification, notification_ms = wait_until(
                experiment["expectations"]["detect_within_seconds"],
                lambda: adapter.notification_seen(experiment),
                interval=0.1 if mode == "simulate" else 2.0,
            )
            notification_ok = bool(notification)
        else:
            notification_started = monotonic_ms()
            notification = adapter.notification_seen(experiment)
            notification_ms = monotonic_ms() - notification_started
            notification_ok = not bool(notification)
        stages["notification"] = {
            "ok": notification_ok,
            "at": utc_now(),
            "latency_ms": notification_ms,
            "expected": expected_notification,
        }
    finally:
        if activated:
            rollback_started = monotonic_ms()
            try:
                adapter.rollback(experiment, token)
                recovery, recovery_ms = wait_until(
                    experiment["expectations"]["recover_within_seconds"],
                    lambda: adapter.probe_recovery(experiment),
                    interval=0.1 if mode == "simulate" else 2.0,
                )
                stages["recovery"] = {
                    "ok": bool(recovery and recovery.observed),
                    "at": utc_now(),
                    "latency_ms": recovery_ms,
                    "detail": recovery.detail if recovery else "no recovery observation",
                    "rollback_latency_ms": monotonic_ms() - rollback_started,
                }
            except Exception as error:  # noqa: BLE001
                rollback_error = str(error)
                stages["recovery"] = {
                    "ok": False,
                    "at": utc_now(),
                    "latency_ms": None,
                    "detail": rollback_error,
                }

    passed = all(stages.get(name, {}).get("ok") for name in ("injection", "detection", "notification", "recovery"))
    if rollback_error:
        passed = False
    return build_report(experiment, mode, stages, passed)


def write_reports(reports: list[dict[str, Any]], output: Path, markdown: Path) -> None:
    document = {
        "schema": "atlas-chaos-report-set/v1",
        "generated_at": utc_now(),
        "passed": all(item["passed"] for item in reports),
        "summary": {
            "experiments": len(reports),
            "passed": sum(item["passed"] for item in reports),
            "failed": sum(not item["passed"] for item in reports),
        },
        "experiments": reports,
    }
    canonical = canonical_json_bytes(document)
    document["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Atlas Systems chaos assurance",
        "",
        f"Mode: **{reports[0]['mode'] if reports else 'none'}**  ",
        f"Experiments: **{document['summary']['experiments']}**  ",
        f"Passed: **{document['summary']['passed']}**  ",
        f"Failed: **{document['summary']['failed']}**",
        "",
        "| Experiment | Fault | Detection | Notification | Recovery | Verdict |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in reports:
        stages = item["stages"]
        lines.append(
            f"| `{item['experiment_id']}` | `{item['fault']}` | "
            f"{stages.get('detection', {}).get('latency_ms', 'n/a')}ms | "
            f"{stages.get('notification', {}).get('latency_ms', 'n/a')}ms | "
            f"{stages.get('recovery', {}).get('latency_ms', 'n/a')}ms | "
            f"{'pass' if item['passed'] else 'fail'} |"
        )
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate")
    validate.add_argument("--policy", required=True)

    run = subcommands.add_parser("run")
    run.add_argument("--policy", required=True)
    run.add_argument("--experiment", action="append")
    run.add_argument("--mode", choices=("simulate", "live"), default="simulate")
    run.add_argument("--confirm-live", action="store_true")
    run.add_argument("--output", default="reports/chaos-report.json")
    run.add_argument("--markdown", default="reports/chaos-report.md")

    args = parser.parse_args()
    policy = load_json(args.policy)
    errors = validate_policy(policy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(f"Validated {len(policy['experiments'])} chaos experiments.")
        return 0

    if args.mode == "live" and not args.confirm_live:
        print("Live mode requires --confirm-live.", file=sys.stderr)
        return 2
    token = os.getenv("ATLAS_CHAOS_TOKEN", "")
    if args.mode == "live" and not token:
        print("ATLAS_CHAOS_TOKEN is required for live mode.", file=sys.stderr)
        return 2

    selected = set(args.experiment or [])
    experiments = [
        item for item in policy["experiments"] if not selected or item["id"] in selected
    ]
    missing = selected - {item["id"] for item in experiments}
    if missing:
        print(f"Unknown experiment ids: {', '.join(sorted(missing))}", file=sys.stderr)
        return 2

    reports = []
    for experiment in experiments:
        print(f"Running {experiment['id']} in {args.mode} mode", flush=True)
        try:
            reports.append(run_experiment(experiment, args.mode, token))
        except Exception as error:  # noqa: BLE001
            reports.append(
                build_report(
                    experiment,
                    args.mode,
                    {
                        "injection": {
                            "ok": False,
                            "at": utc_now(),
                            "latency_ms": None,
                            "detail": str(error),
                        }
                    },
                    False,
                )
            )

    write_reports(reports, Path(args.output), Path(args.markdown))
    return 0 if all(item["passed"] for item in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
