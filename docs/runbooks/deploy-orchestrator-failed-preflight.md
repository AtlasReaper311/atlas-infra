# Deploy orchestrator: failed preflight

## Trigger

A required registry, ref, workflow, commit-check, owner, rollback, or contract
preflight is missing or failed.

## Recover

Stop before dispatch. Preserve the dry-run plan and the exact failed check.
Correct the owning declaration or service workflow through a focused review,
then resolve the full commit and prove its required checks again. Missing or
unavailable data is not success and must not be waived with an input flag.

