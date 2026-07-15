# Repository instructions

## Chaos safety

- Scheduled chaos defaults to deterministic simulation.
- Do not enable scheduled live injection in code or change repository variables without explicit operator approval.
- Live mode must name one policy experiment and use the protected `production-chaos` environment.
- Keep targets allowlisted, durations bounded, and control leases self-expiring.
- Require a healthy baseline and an empty control lease before injection.
- Always attempt rollback and verify public recovery.
- Keep `CHAOS_FREEZE` as an immediate live-mode stop control.
- Publish source-linked, fingerprinted evidence for every completed run.
- Describe results as evidence for the named Atlas experiment, not universal reliability.

See `docs/chaos-assurance.md` and `policy/chaos-experiments.json` before changing the harness or workflow.
