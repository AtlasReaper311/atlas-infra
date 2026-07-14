# Release watch runbook

Owner: `AtlasReaper311/atlas-infra` for policy and recovery guidance;
`AtlasReaper311/atlas-journey-watch` for verification execution.

## First checks

1. Open the exact `release-evidence-<run id>` artifact.
2. Confirm `repository`, full `commit`, `service_id`, `environment`, deployment
   target/ID, and timestamps match the deployment record.
3. Inspect `live_identity`, `journey_result`, and the three check records.
4. Do not deploy or roll back from the release-watch runner.

## Metadata mismatch

- Compare each explicit live field with the request. Do not compare display
  names or short SHAs.
- Confirm caches/CDN are not serving an older metadata document.
- Confirm the deployment workflow injected the full commit before retrying.
- Keep status `mismatch` until a fresh live response matches. A retry is safe;
  it performs reads and journeys only.

## Journey failure after deployment

- Open the Playwright report, trace, screenshot, and request evidence.
- Re-run only the service's mapped journey locally against fixtures first.
- If the failure is genuinely live, defer rollback to the owner and the target
  repository's rollback procedure. Release watch must not invoke it.

## Release evidence invalid

Run:

```bash
python3 scripts/validate_release_evidence.py --instance release-evidence.json
```

Fix the producer or request. Do not edit an evidence artifact after the run and
do not weaken the schema. Generate a new artifact from a new verification run.

## Live endpoint unavailable

- Confirm the request URL is the target's allowlisted Atlas hostname.
- Check DNS/service health outside this workflow only when separately approved.
- Leave `live_identity` as `unavailable` and release status as `unknown`.
  Cached or missing data is not proof of a live release.

## Rollback decision deferred

- Record the target repository's rollback reference and the owner decision.
- Leave the failed/mismatch/degraded evidence unchanged.
- Only a separate, human-controlled rollback may later produce
  `status: rolled-back`. Never add provider credentials to release watch.

## Baseline unavailable

- Confirm `baseline-comparison` has shared state `unavailable` and check status
  `unknown`, and that the run did not invent latency, error-rate, or threshold
  values. Expired supplied input uses shared state `stale`.
- This check alone does not block `live` when identity and journeys pass.
- Add a baseline only when an owning producer supplies recent baseline,
  observed values, freshness, and explicit thresholds.

## Disable and recover

Disable `.github/workflows/release-watch.yml` in `atlas-journey-watch` or stop
dispatching `release-watch` events. Existing deploy and scheduled estate
journey workflows continue independently. Reverting the Phase 3 commits removes
the CLI/workflow and policy/docs; no public route, deployment, or stored state
needs migration.
