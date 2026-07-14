# Deploy orchestrator: rollback decision deferred

## Trigger

A deployment or verification failed and the owner has not chosen rollback or a
forward fix.

## Recover

Keep remaining targets stopped, preserve evidence and current service state,
and record the decision as deferred. Do not automatically compensate, merge,
or redeploy. The target repository's rollback runbook and blast radius guide
the owner decision. Resume only from a new approved dry-run plan.

