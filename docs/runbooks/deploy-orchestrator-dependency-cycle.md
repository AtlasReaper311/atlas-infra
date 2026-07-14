# Deploy orchestrator: dependency cycle

## Trigger

The planner emits `dependency-cycle` and no dispatch order.

## Diagnose

1. Run the same plan with JSON and Markdown output.
2. Inspect `dependencies` for every service named by the finding.
3. Compare the deployment dependency with the Phase 6 runtime graph. They are
   related but not necessarily identical.

## Recover

Remove the incorrect deployment edge or split the coupled change into explicit
owner-approved stages. Re-run policy validation and the plan twice. Do not
force an order by bypassing the graph and do not dispatch any target while the
cycle exists.

