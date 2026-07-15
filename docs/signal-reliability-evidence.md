# Signal and reliability evidence

This addition introduces two public evidence producers and one bounded fault-injection controller.

## Estate conformance

`scripts/estate_policy.py` now emits `atlas-estate-conformance-report/v1`. Each repository is scored from applicable weighted rules. Pass contributes the full rule weight, warning contributes half, error contributes zero, and rules that do not apply leave the denominator.

The weekly `estate-policy.yml` workflow continues to fail on blocking errors. It also publishes the validated JSON document to `atlas-api-public` when `EVIDENCE_REPORT_KEY` is configured.

## Chaos assurance

`policy/chaos-experiments.json` is the target allowlist and experiment catalogue. Scheduled runs execute the deterministic simulator only. Live mode requires all of the following:

1. a manual `workflow_dispatch`
2. `mode=live`
3. one explicit experiment id
4. approval through the `production-chaos` GitHub environment
5. the `ATLAS_CHAOS_TOKEN` environment secret
6. a target Worker with `CHAOS_ENABLED=true`

The harness activates a bounded lease, observes the declared fault, verifies notification evidence, deletes the lease, verifies recovery, and emits `atlas-chaos-report-set/v1`. Rollback is attempted in `finally` even when detection or notification fails.

The first target is `specular-edge`. Its control route remains hidden while `CHAOS_ENABLED=false`.
