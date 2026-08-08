# GitHub provider guard wider rollout: Wave 2B plan

Status: owner-authenticated reconciliation inspection reviewed. A fail-closed in-place apply operator is prepared for existing ruleset `19154613`, but no Wave 2B provider mutation is authorised by this document alone.

## Scope

Wave 2B is limited to `AtlasReaper311/atlas-journey-watch`.

Wave 2A is closed. Wave 3 and all later waves remain unstarted.

## Current source and policy evidence

Current GitHub source remains pinned to:

- repository: `AtlasReaper311/atlas-journey-watch`;
- default branch: `main`;
- current `main`: `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- visibility: public;
- archived: false;
- repository auto-merge: enabled;
- ADR-0004 classification: active, public, original;
- native pull-request context: `Offline journey validation`;
- GitHub Actions integration ID: `15368`.

Current genuine Dependabot evidence remains PR `#12`:

- state: open;
- mergeable: true;
- base: `main` at `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- head: `acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`;
- `Offline journey validation`: completed successfully;
- Dependabot review policy: completed successfully;
- CodeQL: completed successfully;
- OpenSSF Scorecard: completed successfully.

The repository workflow `.github/workflows/dependabot-automerge.yml` calls the immutable reusable policy at `AtlasReaper311/atlas-infra/.github/workflows/dependabot-review.yml@8e6d08701823b02c4859bfc72af67fc8ace1f4b5` and passes:

`automerge_enabled: ${{ vars.DEPENDABOT_AUTOMERGE_ENABLED == 'true' }}`

The pinned policy enables auto-merge only when all of these conditions hold:

- repository opt-in is enabled;
- package ecosystem is `npm`;
- dependency type is `direct:development`;
- update type is `version-update:semver-patch`;
- the update is not grouped;
- maintainer changes are absent;
- exactly one dependency is present;
- old and new versions are stable semver;
- OSV lookup succeeds and reports no active advisory.

PR `#12` is a GitHub Actions update, so it is intentionally ineligible. Its owner-authenticated `autoMergeRequest` is `null`. That is expected fail-closed behavior, not evidence that the selective auto-merge pilot is broken.

## Owner-authenticated reconciliation receipt

Inspection authority merged through `atlas-infra#137` as `6c828ea1e98d4a731ffed3ee3def448212eb15df`.

Reviewed evidence archive:

- archive SHA-256: `abf7f135257a5b842188ea8ffae6cc9e2be28b0a0e60bbcba06d46c83bef0141`;
- `SHA256SUMS.txt`: 18 manifest entries;
- digest mismatches: zero;
- `wave-2b-inspection-summary.json` SHA-256: `40c0a8af72f1caca6a38fc1d273e9db1e92fed9fcb095350721560e33c1cae01`;
- ruleset payload SHA-256: `1a095f5f3aeaf0c7657ee092b909b9380f6594e308f31e0663d450cc9e3bebc3`;
- PR auto-merge projection SHA-256: `0603a9f976ee407624502e9fa1dae414e57ecd3f5686e7997fa65bc3edd2570c`;
- provider writes performed: false;
- variables written: false;
- secrets read: false;
- Wave 3 started: false.

The normalized inspection result records `qualifies_standard_guard_semantics: false`.

## Exact existing provider state

Ruleset `19154613` currently has:

- name: `Require native pull request validation`;
- target: branch;
- enforcement: active;
- bypass actors: none;
- ref include: `refs/heads/main`;
- ref excludes: none;
- effective rule types on `main`: `required_status_checks` only;
- required context: `Offline journey validation`;
- GitHub Actions integration ID: `15368`;
- `do_not_enforce_on_create`: false;
- `strict_required_status_checks_policy`: true.

Classic `main` protection is absent.

The existing ruleset therefore does not satisfy the Atlas default-branch guard contract because it does not require pull requests, does not block deletion, and does not block non-fast-forward updates. Its status-check policy also differs from the established Atlas guard shape by using strict branch-update enforcement.

## Reconciliation decision

Current evidence supports outcome 2 from the inspection plan: a narrow in-place reconciliation while preserving selective Dependabot auto-merge.

Replacement, deletion, disablement, or creation of a second overlapping ruleset is not an assumed outcome.

The ruleset identity and existing name are preserved. Only the deficient semantics are reconciled.

### Before

Ruleset `19154613`:

- condition: `refs/heads/main`;
- rule types: `required_status_checks`;
- strict required-status policy: true.

### After

The same ruleset `19154613`:

- name remains `Require native pull request validation`;
- target remains branch;
- enforcement remains active;
- no bypass actors;
- condition becomes `~DEFAULT_BRANCH`;
- add `deletion`;
- add `non_fast_forward`;
- add `pull_request`;
- required approving reviews: `0`;
- required review-thread resolution: false;
- preserve required context `Offline journey validation`;
- preserve GitHub Actions integration ID `15368`;
- preserve `do_not_enforce_on_create: false`;
- set `strict_required_status_checks_policy: false`.

Repository auto-merge remains enabled and `DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged.

The change makes the ruleset resilient to a future default-branch rename while preserving the native validation and selective auto-merge authority already present in Journey Watch.

## Apply authority

`scripts/github-provider-guard-wave-2b-reconcile.sh` is the only provider operator prepared by this stage.

Default mode is read-only `inspect`.

Provider apply is unreachable unless both conditions are true:

- `MODE=apply`;
- `ATLAS_PROVIDER_WRITE_CONFIRMATION="APPLY GITHUB PROVIDER GUARD WAVE 2B"`.

Before any write it fails closed unless all reviewed identities remain exact:

- current `main`;
- sole active branch ruleset ID `19154613`;
- exact current ruleset name and one-rule baseline;
- absence of classic protection;
- repository auto-merge enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED=true`;
- PR `#12` open, mergeable and on the reviewed head;
- native `Offline journey validation` uniquely successful under integration `15368`;
- PR `#12` auto-merge request remains null.

The only provider mutation in the runner is:

`PUT /repos/AtlasReaper311/atlas-journey-watch/rulesets/19154613`

The runner contains no ruleset create, delete or second-ruleset path. It does not write repository auto-merge, Actions variables, secrets, PR state, releases, workflows, deployments, or runtime state.

After the update it re-reads the same ruleset ID and effective `main` rules, then proves:

- all four Atlas guard rule types are effective;
- required native context remains exact;
- repository auto-merge remains enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged;
- current `main` remains unchanged;
- PR `#12` remains open, mergeable and without an auto-merge request.

## Validation and closeout after provider apply

Provider reconciliation does not itself close Wave 2B.

After separately approved apply:

1. verify the provider receipt and exact in-place ruleset read-back;
2. create a harmless owner documentation PR and merge it through ruleset `19154613`;
3. confirm PR `#12` remains a genuine ineligible Dependabot specimen, open and unmerged with the native check passing;
4. confirm repository auto-merge remains enabled;
5. confirm `DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged;
6. run a fresh owner-authenticated stamped scoreboard;
7. expect planning movement from 239 required passes / 21 required failures / 0 unknowns to 240 / 20 / 0 if unrelated estate state does not move;
8. commit final human and machine-readable Wave 2B receipts;
9. close Wave 2B before beginning Wave 3.

No artificial eligible dependency update is required solely to prove this provider reconciliation. The immutable selective auto-merge policy remains separately bounded, and this change does not expand its eligibility.

## Approval boundary

Any provider mutation requires a new explicit approval after this proposal is reviewed.

Merging the Wave 2B apply authority is source work only and does not authorise the provider update.

The exact provider mutation requiring approval is the single in-place update of Journey Watch ruleset `19154613` described above.

## Rollback

Rollback is not automatic.

If the in-place reconciliation blocks an intended path:

1. stop;
2. preserve the provider evidence;
3. identify the exact ruleset version/state involved;
4. obtain separate rollback approval;
5. alter only ruleset `19154613`;
6. verify repository auto-merge, `DEPENDABOT_AUTOMERGE_ENABLED`, source, workflows, and Wave 3 state remain unchanged.

## Explicit boundaries

This stage does not:

- create a second Journey Watch ruleset;
- delete or disable ruleset `19154613`;
- change repository auto-merge;
- change `DEPENDABOT_AUTOMERGE_ENABLED`;
- enable auto-merge on PR `#12`;
- merge Dependabot PR `#12`;
- change Journey Watch source, release behavior, schedules, secrets, or runtime configuration;
- dispatch workflows;
- deploy or publish anything;
- begin Wave 3 or any later wave.
