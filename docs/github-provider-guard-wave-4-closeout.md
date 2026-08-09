# GitHub provider guard Wave 4 closeout

Status: complete.

Wave 4 closed the remaining estate-wide `default_branch_guard` gap through:

- Wave 4A create-first rulesets on 13 reviewed repositories;
- Wave 4B in-place reconciliation of `AtlasReaper311/atlas-dora` ruleset `19581236`;
- a separately owner-operated final profile guard on `AtlasReaper311/AtlasReaper311` after the profile writer redesign;
- activation of the day-zero create-only reconciler as ongoing governance.

This document records source and evidence reconciliation only. Provider state was already complete before this closeout PR. No ruleset, classic protection, repository setting, variable, secret, workflow dispatch, merge, or deployment is authorised by this document.

## Accepted source authority

- Wave 4 source authority: `ae69babf02c79eb79ee8ba874027dc2c6df8f3c1` (`atlas-infra#143`)
- Day-zero reconciler source: `3ff1a72a9148e94d4e433cc787ffcad9ab8df10d` (`atlas-infra#144`)
- Current Atlas Infra main at final scoreboard collection: `217826b73e9dbbf8f0c3e4e9b0901860e7fbc4d4` (`atlas-infra#145`)

Wave 4A and Wave 4B local apply summaries did not embed the exact Atlas Infra SHA used at execution time. Recorded conservatively:

- accepted source authority: `ae69babf02c79eb79ee8ba874027dc2c6df8f3c1` (`#143`);
- execution-authority SHA inside apply receipt: not recorded;
- local historical evidence: consistent with execution after `#143`.

Do not treat the local historical association as a cryptographic claim.

## Wave 4A execution

Wave 4A used the reviewed one-shot operator `scripts/github-provider-guard-wave-4a.sh`.

Pre-apply inspection archive SHA-256:

`0abbd15869a96a8f38f7f7945a914277b7995924710e9eb0a0580478a289e884`

Apply evidence ZIP SHA-256:

`b7e6bcbe712ca0b2417753f18d35d937eeecca7594bff848cd4ef2fef12527bd`

All 287 evidence payload hashes verified. Summary records:

- `mode=apply`;
- `provider_writes_performed=true`;
- mutation `ruleset-create-only`;
- `variables_written=false`;
- `profile_repository_modified=false`;
- 13/13 rulesets created and read back.

Created rulesets:

| Repository | Ruleset ID |
| --- | ---: |
| `.github` | `20594949` |
| `atlas-api-index` | `20594950` |
| `atlas-blackbox` | `20594952` |
| `atlas-corpus` | `20594954` |
| `atlas-daily-digest` | `20594955` |
| `atlas-notify` | `20594956` |
| `deploy-watch` | `20594959` |
| `github-pulse` | `20594960` |
| `ramone-edge` | `20594961` |
| `ramone-memory` | `20594962` |
| `ramone-voice-trigger` | `20594963` |
| `specular-sentinel` | `20594965` |
| `specular-telemetry` | `20594968` |

## Wave 4B execution

Wave 4B used the reviewed one-shot operator `scripts/github-provider-guard-wave-4b-reconcile.sh`.

Apply evidence ZIP SHA-256:

`3ec75ed96dc15b045e879f100b3450bad4c2a1d7ba26520ef6c0d4329923b315`

All 28 evidence payload hashes verified. Summary records provider writes as an update-only mutation of ruleset `19581236`, with variables unchanged and the profile repository untouched.

| Field | Value |
| --- | --- |
| Ruleset | `19581236` |
| Before rule types | `required_status_checks` |
| After rule types | `deletion`, `non_fast_forward`, `pull_request`, `required_status_checks` |
| Preserved contexts | `check`, `Gardener native auto-merge barrier` |
| Live `updated_at` | `2026-08-08T23:43:46+01:00` |

## Profile writer redesign and final guard

Profile source repair merged as `AtlasReaper311/AtlasReaper311#8`:

`31a596cff8375072207635e0790578a8d6a2f9dc`

It replaced the direct-main six-hour writer with:

- one-use automation branch;
- pull request;
- exact-head validation dispatch;
- exact-head validation wait;
- squash merge;
- branch deletion.

The redesigned path successfully executed before final guard installation as `AtlasReaper311/AtlasReaper311#9` by `github-actions[bot]`, merged as:

`57d0844f1fb55901715210b91d72bbc7905bf525`

Final profile ruleset:

| Field | Value |
| --- | --- |
| ID | `20595678` |
| Created at | `2026-08-09T01:00:35+01:00` |
| Actor | not exposed |
| Provenance | reconstructed, not provider-audit-attributed |

This ruleset is not attributed to Wave 4A, Wave 4B, or the day-zero reconciler. The creation path is reconstructed from available local evidence as a separate owner-operated provider action. GitHub ruleset APIs do not expose the creating actor.

### Profile post-guard execution limitation

The guarded automation path is structurally compatible with the final pull-request guard: the direct-main writer was removed before guard installation; the replacement branch/PR/exact-head/squash path was successfully exercised before installation; and subsequent scheduled runs execute successfully under the guard but have so far been no-op because the generated README has not changed.

A post-guard content-changing scheduled refresh has not yet been observed. This is an evidence limitation, not a known live failure.

Do not claim that a post-guard genuine-change refresh is proven.

## Day-zero reconciler

Current repository variable:

`ATLAS_PROVIDER_GUARD_RECONCILE_ENABLED=true`

Observed post-source runs:

| Run | Event | Result |
| ---: | --- | --- |
| `31286612623` | `workflow_dispatch` | inspect success / apply skipped |
| `31286729796` | `workflow_dispatch` | inspect success / apply success |
| `31302475134` | `schedule` | inspect success / apply success |

Successful apply evidence reports 33 compliant, 0 create, 0 blocked, and `provider_writes_performed=false`.

The reconciler is therefore:

- enabled;
- scheduled;
- healthy;
- create-only;
- ongoing governance.

GitHub does not expose the exact variable-mutation audit timestamp. Do not invent it.

The reconciler never updates or deletes existing rulesets. Stronger existing guards remain untouched.

## Final scoreboard

Fresh owner-authenticated scoreboard:

| Field | Value |
| --- | --- |
| Collected at | `2026-08-09T20:37:29Z` |
| Atlas Infra authority | `217826b73e9dbbf8f0c3e4e9b0901860e7fbc4d4` |
| Repositories checked | `33` |
| Required passed | `260` |
| Required failed | `0` |
| Required unknown | `0` |
| Fingerprint | `sha256:34265f801dfcd5ca1d24d93b0041aa707a8746d01879f3da8bab30df053ed5fe` |

No live provider drift exists against this closeout.

## One-shot operator retirement

Disposition A:

- retain unchanged `scripts/github-provider-guard-wave-4a.sh`;
- retain unchanged `scripts/github-provider-guard-wave-4b-reconcile.sh`.

Their rollout authority is exhausted. They are retained as historical fail-closed execution evidence. Their embedded pre-apply baselines intentionally no longer match live state. They are not the current provider-maintenance mechanism and must not be reused for future rollout work.

The ongoing maintenance mechanism is the day-zero create-only reconciler.

## Permanent receipts

- historical pre-apply inspection receipt: `reports/github-provider-guard-wave-4-inspection-receipt.json`
- final machine-readable receipt: `reports/github-provider-guard-wave-4-final-receipt.json`
- historical plan (superseded): `docs/github-provider-guard-wave-4-plan.md`
- reconciler standing governance: `docs/github-provider-guard-reconciler.md`

## Boundaries preserved

This closeout source PR does not:

- create, update, or delete rulesets;
- change classic branch protection;
- change repository settings, variables, or secrets;
- dispatch workflows;
- modify the profile repository or `atlas-dora`;
- merge pull requests;
- deploy or publish anything.

Provider Guard Wave 4 programme provider work is complete. Day-zero create-only reconciliation remains standing governance for newly admitted projected repositories.
