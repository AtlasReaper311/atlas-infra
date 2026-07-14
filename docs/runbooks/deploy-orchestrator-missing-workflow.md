# Deploy orchestrator: missing deploy workflow

## Trigger

The planner emits `missing-deploy-workflow` for a policy target.

## Diagnose

Confirm the target repository still owns the named workflow and that the
workflow still supports manual dispatch. Inspection is read-only; do not add a
caller to a service repository without separate approval.

## Recover

Correct stale policy when an existing workflow was renamed. If no manual
workflow exists, disable the target and request a focused service-repository
change. Do not point policy at a push-only workflow or reimplement deployment
inside `atlas-infra`.

