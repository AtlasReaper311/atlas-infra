# Chaos assurance

Atlas Systems uses bounded experiments to test one declared recovery claim at a time. The system separates deterministic simulations from live fault injection.

## Cadence

- Every Wednesday, the workflow validates policy and runs all experiments in simulation mode.
- On the first Wednesday of each UTC month, a live 503 canary may run after simulation passes.
- Scheduled live execution also requires `CHAOS_SCHEDULE_ENABLED=true`.
- `CHAOS_FREEZE=true` blocks scheduled and manual live execution.
- Manual live execution requires one named experiment and the `production-chaos` environment.

Scheduled live execution remains disabled until the target control contract and one manual canary have both been verified.

## Live control contract

Before injection, the harness requires the control endpoint to answer an authenticated `GET` request with JSON. The `active` field must be empty, and the public probe must return HTTP 200.

Activation uses an authenticated `POST`. A successful response must return HTTP 202 and an `active` lease with an `expires_at` timestamp. The target must enforce that expiry independently of the runner. The returned expiry cannot exceed the declared experiment duration plus 15 seconds of clock allowance.

Rollback uses an authenticated `DELETE`. The harness then waits for the public probe to return HTTP 200 within the declared recovery objective. Rollback runs from a `finally` path whenever activation succeeded.

## Published evidence

Each report records:

- experiment and policy versions
- simulation or live mode
- target and injected fault
- baseline health and control-plane availability
- bounded lease expiry verification
- detection latency
- notification latency
- rollback and recovery latency
- source repository, commit, workflow run, and report fingerprint
- an overall pass or fail verdict

This evidence supports only the named experiment, target, time, and recovery objectives. It does not claim that every outage mode is covered or that the estate cannot fail.

## Operating sequence

1. Keep scheduled live execution disabled.
2. Merge and observe weekly simulations.
3. Verify the target control endpoint implements the live control contract.
4. Run `specular-route-503-v1` manually through the protected environment.
5. Confirm detection, notification, rollback, recovery, and published evidence.
6. Set `CHAOS_SCHEDULE_ENABLED=true` only after review.
7. Set `CHAOS_FREEZE=true` during incidents, deploy freezes, or target maintenance.

## Emergency response

If recovery fails, revoke the active lease through the control endpoint, set `CHAOS_FREEZE=true`, and investigate the failed workflow. The target-side expiry remains the final bound if the runner cannot complete rollback.
