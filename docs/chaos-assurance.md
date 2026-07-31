# Chaos assurance

Atlas Systems uses bounded experiments to test one declared recovery claim at a time. The system separates deterministic simulations, isolated target-contract tests, and live fault injection.

## Cadence

- Every Wednesday, the workflow validates policy and runs all declared experiments in simulation mode.
- On the first Wednesday of each UTC month, a live 503 canary may run after simulation passes.
- Scheduled live execution also requires `CHAOS_SCHEDULE_ENABLED=true`.
- `CHAOS_FREEZE=true` blocks scheduled and manual live execution.
- Manual live execution requires one named experiment and the `production-chaos` environment.

Scheduled live execution is enabled after the target control contract and a protected manual live canary were both verified.

## Current rollout state

Phase I chaos assurance is complete.

The source contract, target-side control contract, protected manual `specular-route-503-v1` canary, and first scheduled workflow proof have all been verified. The weekly schedule remains responsible for deterministic simulation evidence. The first Wednesday of each UTC month remains the only scheduled live-eligible window, subject to the enabled schedule, freeze gate, successful simulation, and protected environment.

The first monthly live-eligible date after Phase I closure is Wednesday, 5 August 2026. That run is ongoing operational assurance and is not a remaining Phase I closure gate.

## Phase I scheduled proof

The scheduled workflow run on Wednesday, 29 July 2026 completed successfully:

- workflow run: [`30446405193`](https://github.com/AtlasReaper311/atlas-infra/actions/runs/30446405193)
- source branch: `main`
- source commit: `138bbbc3e7cb396c4acca856a401757305a1c804`
- policy version: `1.1.0`
- simulation job: passed
- scheduled live-window check: passed
- approved live experiment job: skipped as expected
- monthly canary job: skipped as expected because 29 July was not the first Wednesday of the UTC month
- report verdict: passed
- report fingerprint: `e02f96099b63af6863728cf1e4281d39cbe0d9c188f5b17e4e178c1f77dca838`
- retained artifact: `chaos-simulation-30446405193`, artifact ID `8721598950`
- artifact digest: `sha256:7072308b0f30ae3a7b35ee08456a77709dbb8590f8aa6b3724f4ee24cae6730b`
- artifact expiry: 27 October 2026

The scheduled simulation passed all three declared experiments:

- `specular-route-503-v1` using `status_503`
- `specular-latency-v1` using `latency`
- `specular-kv-reject-v1` using `kv_write_reject`

The workflow also published the stamped chaos evidence successfully. This proves the weekly scheduled simulation and gating path against the hardened source without claiming that a live fault ran on 29 July.

## Capability classes

`policy/chaos-experiments.json` records target capabilities separately from experiment declarations.

For `specular-edge`, the live policy-authorised faults are:

- `status_503`
- `latency`
- `kv_write_reject`

The target also contains `stale_response` and `webhook_drop` as test-only hooks. They cannot enter the live policy and the Worker rejects them unless an explicit non-production switch is present. This keeps their contract coverage without silently broadening the production fault surface.

The policy validator requires every harness fault to have exactly one capability class and rejects experiments that use a test-only or undeclared target fault.

## Live control contract

Before injection, the harness requires the control endpoint to answer an authenticated `GET` request with JSON. The `active` field must be empty, and the public probe must return HTTP 200.

Activation uses an authenticated `POST`. A successful response must return HTTP 202 and an `active` lease with an `expires_at` timestamp. The target must enforce that expiry independently of the runner. The returned expiry cannot exceed the declared experiment duration plus 15 seconds of clock allowance.

Only one lease may be active. The target returns HTTP 409 rather than replacing an existing lease, and serialises activation inside one Worker isolate. Cloudflare KV is not a linearizable lock, so the current design also relies on the bearer-token boundary and the single `chaos-assurance` workflow concurrency group. A future multi-controller design would require a Durable Object or another linearizable coordinator.

Rollback uses an authenticated `DELETE`. The harness then waits for the public probe to return HTTP 200 within the declared recovery objective. Rollback runs from a `finally` path whenever activation succeeded.

Passive expiry is event-driven. The first control or telemetry request after `expires_at` removes the logical lease and emits recovered evidence with reason `lease_expired`. Explicit deletion uses reason `explicit_delete`. An invalid stored expiry is removed fail-closed.

## Published evidence

Each final report records:

- policy and experiment versions
- policy path and capability class
- simulation or live mode
- target and injected fault
- baseline health and control-plane availability
- bounded lease expiry verification
- detection latency
- notification latency
- rollback and recovery latency
- source repository, commit, workflow run, and report fingerprint
- an overall pass or fail verdict

`chaos_harness.py` produces the bounded experiment result. `chaos_evidence.py` validates the target capability contract, stamps policy provenance into every experiment and report set, and recalculates the fingerprints before publication.

This evidence supports only the named experiment, target, time, and recovery objectives. It does not claim that every outage mode is covered or that the estate cannot fail.

## Source-only and non-production validation

The source validation path does not contact the production hostname or dispatch a workflow.

```bash
python3 scripts/chaos_evidence.py validate \
  --policy policy/chaos-experiments.json

python3 scripts/chaos_harness.py validate \
  --policy policy/chaos-experiments.json

python3 scripts/chaos_harness.py run \
  --policy policy/chaos-experiments.json \
  --mode simulate \
  --output reports/chaos-report.json \
  --markdown reports/chaos-report.md

python3 scripts/chaos_evidence.py stamp \
  --policy policy/chaos-experiments.json \
  --report reports/chaos-report.json \
  --markdown reports/chaos-report.md
```

The `specular-telemetry` Worker tests separately prove disabled mode, authentication failure, unsupported faults, duration bounds, active-lease rejection, same-isolate concurrent activation, passive expiry, and explicit rollback. Its CI also performs linting, Node tests, and a Wrangler dry-run without deployment.

## Operating sequence

1. Run all declared experiments in simulation mode on the weekly schedule.
2. Permit the monthly live canary only when simulation passes, `CHAOS_SCHEDULE_ENABLED=true`, `CHAOS_FREEZE` is not `true`, and the date is the first Wednesday of the UTC month.
3. Keep scheduled live execution limited to the policy-authorised `specular-route-503-v1` experiment and the protected `production-chaos` environment.
4. Review detection, notification, rollback, recovery, provenance, and report fingerprints after every live run.
5. Set `CHAOS_FREEZE=true` during incidents, deploy freezes, or target maintenance.
6. Treat failed or missing scheduled evidence as an incomplete assurance cycle rather than a successful run.

## Emergency response

If recovery fails, revoke the active lease through the control endpoint, set `CHAOS_FREEZE=true`, and investigate the failed workflow. The target-side logical expiry remains the final bound if the runner cannot complete rollback.
