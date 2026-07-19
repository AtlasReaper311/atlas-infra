# Reliability: evidence is stale

Use this runbook when a service's reliability state is `stale_evidence`: a previously valid measurement exists but is older than the objective's freshness bound, so it may not be presented as current.

## Safe triage

1. Check `https://api.atlas-systems.uk/v1/reliability` and compare `evaluated_at` with `stale_after`. A whole-document stale means the evaluation cron has not completed recently.
2. Check whether `/v1/slo` itself is fresh. If the raw counters are current but the derived document is stale, the evaluation step inside the atlas-api-public cron is the fault; inspect its Worker logs through the Cloudflare dashboard.
3. If the raw counters are also old, the probe pass is not running: confirm the Worker cron trigger is enabled and the last scheduled invocation succeeded.
4. Do not treat stale numbers as either healthy or failed. The last-known values remain on display, labelled stale, and that labelling is the correct end state until measurement resumes.

## Recovery

Recovery is measurement resuming, not a manual edit. Once the cron writes fresh counters and the evaluation pass completes, the state clears on its own. No KV value should be hand-edited.

## Escalation and rollback

If a recent atlas-api-public deploy introduced the stall, the repository's own rollback path applies: redeploy the previous version through its deploy workflow. The reliability routes serve honest stale or unavailable states throughout and need no separate action.
