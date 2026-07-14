# Deploy orchestrator: partial deployment

## Trigger

At least one target completed and a later preflight, dispatch, timeout, release
identity check, or journey failed.

## Recover

1. Stop every pending dependant.
2. Preserve the plan, completed and failed workflow URLs, exact commits, and
   available ReleaseEvidence.
3. Run release watch for completed services when safe; do not infer state.
4. Assess whether the completed services are backwards compatible with the
   still-old dependants.
5. Let each service owner choose its repository-owned rollback or forward fix.
6. Record any deferred rollback decision explicitly.
7. Generate and review a new dry-run plan before resuming.

No automatic rollback, merge, provider write, or secret access is permitted.

