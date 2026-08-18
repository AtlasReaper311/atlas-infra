# Repository instructions

## Estate-wide conventions

For anything beyond this repository's own chaos-safety rules below, read
`docs/agent-conventions.md` and `docs/model-policy.md` in this repository
first. They are the estate-wide source of truth for architecture, workflow,
model policy, and source-of-truth ordering across all of Atlas Systems, not
just `atlas-infra`.

If you are working in a different repository and this file is not present
there, those two documents may not be linked from where you are. Ask the
person whether they should be, rather than assuming their absence means they
don't apply.

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
