# Chaos assurance

Atlas Systems uses bounded experiments to test one declared recovery claim at a time. The system separates deterministic simulations, isolated target-contract tests, and live fault injection.

## Cadence

- Every Wednesday, the workflow validates policy and runs all declared experiments in simulation mode.
- On the first Wednesday of each UTC month, a live 503 canary may run after simulation passes.
- Scheduled live execution also requires `CHAOS_SCHEDULE_ENABLED=true`.
- `CHAOS_FREEZE=true` blocks scheduled and manual live execution.
- Manual live execution requires one named experiment and the `production-chaos` environment.

Scheduled live execution remains disabled until the target control contract and one manual canary have both been verified.

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

1. Keep scheduled live execution disabled.
2. Merge and observe weekly simulations.
3. Verify the target control endpoint implements the live control contract.
4. Review source-only and non-production evidence.
5. Run `specular-route-503-v1` manually through the protected environment only after separate approval.
6. Confirm detection, notification, rollback, recovery, and published evidence.
7. Set `CHAOS_SCHEDULE_ENABLED=true` only after review.
8. Set `CHAOS_FREEZE=true` during incidents, deploy freezes, or target maintenance.

## Emergency response

If recovery fails, revoke the active lease through the control endpoint, set `CHAOS_FREEZE=true`, and investigate the failed workflow. The target-side logical expiry remains the final bound if the runner cannot complete rollback.
