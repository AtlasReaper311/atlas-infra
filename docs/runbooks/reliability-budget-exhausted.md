# Reliability: error budget at risk or exhausted

Use this runbook when a service's reliability state is `budget_at_risk` or `budget_exhausted`: the measured failure count over the objective window has approached or passed the allowance the approved target grants.

## Safe triage

1. Read the service entry at `https://api.atlas-systems.uk/v1/reliability/services/<service_id>` and note the burn rates, their sample counts, and the reasons array. Fast burn implicates the last two UTC days; slow burn implicates the last eight.
2. Check `https://api.atlas-systems.uk/notify/recent?level=failure` for the events across the burn window, and `/dora/releases` for a release inside it. A `suspected_regression` there is correlation evidence, not proof.
3. Confirm the counters are honest before acting on them: coverage well below one, or a `machine` domain service, can mean the machine slept, which is measured downtime by design for the 75 percent tier.
4. Compare against the component's raw day buckets at `/v1/slo` if the derived numbers look surprising; the derivation is deterministic, so a disagreement means stale caching, not different truths.

## Recovery

Fix the underlying service fault through its own repository and deployment path. Nothing in the reliability pipeline restarts, rolls back, or mutates a service. Recovery is confirmed only by measurement: the state returns to `objective_met` and the recovery notification fires after the improved state has held for six consecutive evaluation passes.

## Escalation and rollback

The owner is `AtlasReaper311` for every estate service. If the target itself is wrong rather than the service, change the objective in `atlas-infra/policy/reliability/objectives/` through a reviewed pull request; never edit targets in a consumer surface. Roll back a bad policy change by reverting its commit and re-running the publish workflow.
