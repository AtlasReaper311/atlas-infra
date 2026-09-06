# Evidence lifecycle architecture task

Status: queued Phase 1 architecture task. Captured during Atlas Systems 2026
Completion Roadmap Phase 0 item 0.2. This is not accepted architecture, not
rollout-board authority, and not implementation authority.

This record exists so Phase 0 can state that the merged-versus-live follow-up is
formally captured in repository source. It does not authorise an ADR, a contract
change, a rollout-board edit, a merge, a workflow dispatch, a provider change, or
any live mutation.

Inspection date: 2026-09-06. This capture used `origin/main` commit
`2219be3a0e07cf574415c5bbc17452a844883c5a`, which added
`docs/2026-completion-roadmap.md` through `atlas-infra#178`, plus current
GitHub state for draft `atlas-infra#173` at
`9a2a1392130c88fa93373d35d951fa17b940712c`. Reverify those heads before Phase 1
implementation.

## Purpose

Keep `MERGED` from implying `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`.

`atlas-infra#173` is a bounded closed-unmerged board fix and is out of scope.
The missing follow-up is an estate-wide evidence lifecycle vocabulary owned by
`atlas-infra`, so later control-plane, Trace, and Evidence Console work can share
one rule: source merge is not live proof.

## Current authority inspected

### Accepted ADRs

Current accepted records already separate some of these concerns, but they do not
define one estate-wide delivery lifecycle:

- `ADR-0007` treats draft pull requests, previews, merges, and production
  rollouts as separate evidence stages. A green pull request is source
  validation only.
- `ADR-0008` distinguishes public terms including `merged`, `deployed`,
  `published`, `operational`, `degraded`, `unavailable`, and `unknown`. Those
  terms mix delivery, publication, and runtime health. They are not a delivery
  evidence chain.
- `ADR-0010` and `ADR-0012` forbid treating Twin analysis, CI success, or source
  merge as deployment or live behaviour. Twin GitHub observation is additive
  inspection evidence and fails closed as `unavailable` when provider state is
  missing.
- `ADR-0002` owns reliability objectives, not delivery lifecycle.
- `ADR-0003` and `ADR-0004` own public/private and classification authority, not
  rollout-state truth.

Historical `docs/decisions.md` already says merged code does not prove
deployment. That log is not current architecture authority.

### Estate rollout board

`policy/estate-rollout-board.json` on `main` still maps both `closed` and
`merged` to Stage `Live / Verified`. `scripts/estate_rollout_board.py` derives
Status and Stage from GitHub pull-request draft, gate, closed, and merged
facts only. It does not observe deployment, runtime, or live verification.

`atlas-infra#173` (draft, head `9a2a1392130c88fa93373d35d951fa17b940712c`)
changes closed-unmerged mapping to Status `Not Shipped` and Stage
`Closed - Not Merged`, and adds `atlas-systems` to the tracked repository map.
It leaves `merged` mapped to `Live / Verified` on purpose. That remaining
conflation is this follow-up. Do not modify that pull request. Do not change
rollout-board behaviour in the Phase 1 architecture task named here.

### Repository hygiene vocabulary

`policy/repository-hygiene.json` already keeps native GitHub draft, CI, and merge
states out of labels. Atlas-specific labels include:

- `status:rollout-pending`: source is merged or approved; live rollout is still
  pending;
- `status:live-verified`: live state has been independently or owner-verified
  after rollout.

Those labels are pull-request presentation. They are not the estate lifecycle
model and must not be treated as deployment evidence by themselves.

### Atlas Trace relationships

Wave 3.1 Trace contracts connect existing evidence. They do not define delivery
lifecycle authority.

Node `evidence_state` is `verified`, `unverified`, `stale`, `unavailable`, or
`unknown`. That is observation quality for one node, not a SOURCE-to-LIVE chain.

Allowed edges include `SOURCE_OF`, `VALIDATED_BY`, `DEPLOYED_AS`, `VERIFIED_BY`,
and `OBSERVED_BY`. Those relations can later attach evidence between stages.
They must not collapse `MERGED` into `DEPLOYED` or `LIVE VERIFIED`. Missing
evidence stays `unverified`, `stale`, `unavailable`, or `unknown`. It must not
become healthy or live.

### Other evidence-state vocabularies

These remain valid in their own contracts and must not be silently replaced by
the delivery lifecycle:

- retirement evidence: `verified`, `failed`, `unknown`, `unavailable`,
  `not-applicable`;
- evidence ledger allowed states: mixed health, release, and match vocabulary
  including `healthy`, `failed`, `stale`, `unavailable`, `unknown`, `live`;
- public-interface evidence modes: `measured`, `stale-measured`,
  `recorded-replay`, `simulated`, `unavailable`, `unknown`,
  `not-applicable-unscored`.

Phase 1.2 evidence-record Result values in the roadmap (`PASS`, `FAIL`,
`UNKNOWN`, `NOT OBSERVED`, `NOT APPLICABLE`) are assertion outcomes. They are
not the same axis as delivery stage.

## Collision to resolve

The board, hygiene labels, public-interface vocabulary, Trace node states, and
ledger states all use overlapping English for different facts. The source defect
is specific:

On current `main`, a merged pull request is labelled `Live / Verified` because
it merged. PR `#173` stops closed-unmerged work from sharing that label, but a
merged change would still be labelled live without deployment, runtime, or
browser evidence.

That violates standing ADR and contract language: merge is not rollout, and a
green pull request is not production proof.

## Smallest correct Phase 1 architecture task

Write and accept one `atlas-infra` ADR that formalises the estate-wide evidence
lifecycle vocabulary and the non-implication rules below.

This is roadmap Phase 1 item 1.2 only: the shared lifecycle model. It is not
Phase 1.3 profiles, 1.4 snapshot generation, 1.5 drift detection, Phase 2
Evidence Console, or any rollout-board rewrite.

Prefer an ADR because the model is estate-wide. Do not start that work by
editing `policy/estate-rollout-board.json`. The board is a GitHub Project
projection over pull-request state. It may later consume the ADR; it must not
define it.

### Vocabulary the ADR must define

Keep two axes distinct.

Delivery or disposition:

- `SOURCE`
- `CHECKED`
- `MERGED`
- `DEPLOYMENT OBSERVED` / `DEPLOYED`
- `RUNTIME VERIFIED`
- `LIVE VERIFIED`
- `CLOSED` / `NOT SHIPPED`

Observation result, usable at any stage:

- `FAILED`
- `UNKNOWN` / `NOT OBSERVED`
- `NOT APPLICABLE`

The ADR must say whether `DEPLOYMENT OBSERVED` and `DEPLOYED` are aliases or
ordered strengths. Current source uses both: the rollout-state follow-up needs
an explicit observed-deployment claim, while Worker profiles use `DEPLOYED`.
The smallest honest rule is: `DEPLOYMENT OBSERVED` means a named deployment
event was seen; `DEPLOYED` means the expected identity is the deployed
identity. Neither is implied by `MERGED`. If the ADR keeps both labels, it
must forbid treating observation of some deployment as proof of the expected
version.

`CHECKED` means repository-native validation or required checks on an exact
head. It does not mean review approval, merge, or live proof.

### Non-implication rules

The ADR must make these inferences illegal:

- `MERGED` does not imply `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`,
  or `LIVE VERIFIED`.
- `DEPLOYMENT OBSERVED` or `DEPLOYED` does not imply `RUNTIME VERIFIED`.
- `RUNTIME VERIFIED` does not imply `LIVE VERIFIED`.
- `CHECKED` does not imply `MERGED`.
- Missing later evidence is `UNKNOWN` / `NOT OBSERVED`, never an inferred live
  or verified label.
- `NOT APPLICABLE` is valid for subjects with no runtime, no deployment, or no
  public surface, such as a library with no release, or documentation that is
  not published.
- `CLOSED` / `NOT SHIPPED` is not live. PR `#173` is the bounded board
  expression of that rule and stays out of this ADR's implementation slice.

### Required ADR contents

1. Context naming the current collision: board `merged` -> `Live / Verified`,
   hygiene `status:rollout-pending` versus `status:live-verified`, ADR-0007 and
   ADR-0008 stage language, and Trace observation states.
2. Decision stating the vocabulary, the two axes, and the non-implication
   rules.
3. Consequences stating:
   - consumers may map into this vocabulary;
   - existing Trace, ledger, retirement, hygiene, and public-interface
     contracts are not rewritten by this ADR;
   - the Estate Rollout Board remains a pull-request projection until a later
     authorised change;
   - Evidence Console and generated estate snapshots depend on this ADR and
     remain later Phase 1 and Phase 2 work.

Declare only repositories, services, contracts, and policies that current
Atlas authority can prove at implementation time. The Markdown ADR remains the
decision authority. Any Trace `GOVERNED_BY` projection is generated later and
is not this task.

## Owner

`AtlasReaper311/atlas-infra` owns the ADR, as it owns estate architecture
decisions.

Accepting owner: Atlas Reaper.

No other repository is required for this task. `atlas-api-public`,
`atlas-systems`, Atlas Trace runtime, and the Evidence Console are later
consumers.

## Dependencies

Required before the ADR is written:

- fresh Part 0 inspection of current `atlas-infra` ADRs, rollout-board policy
  and implementation, hygiene policy, Trace contracts, and evidence-state
  documents;
- this capture record, or current GitHub state that supersedes it.

Not dependencies, and not blockers:

- merge of `atlas-infra#173`;
- rollout-board Project field options;
- Evidence Console implementation;
- estate snapshot generation;
- Trace contract version changes;
- provider, workflow, or live evidence.

Later work that depends on the accepted ADR, and must not start inside this
task:

- lifecycle profiles (roadmap 1.3);
- generated estate snapshot (roadmap 1.4);
- drift detection (roadmap 1.5);
- Evidence Console v1 (Phase 2);
- any later authorised board mapping away from `merged` -> `Live / Verified`.

## Exit condition

Phase 1 may close this task when all of the following are true:

1. An ADR is accepted on `atlas-infra` `main`.
2. A reviewer can take any repository or change and name its current delivery
   stage, required next evidence, and the label to show when later evidence is
   missing, without using merge as live proof.
3. The ADR text makes `MERGED` -> `DEPLOYED`, `RUNTIME VERIFIED`, or
   `LIVE VERIFIED` an explicit forbidden inference.
4. The same change does not edit rollout-board policy, board sync behaviour,
   PR `#173`, Trace contracts, hygiene labels, or live systems.

Source merge of that ADR is still only `MERGED`. It does not prove the board,
Trace, or Evidence Console already consume the vocabulary.

## Boundaries for this capture

This file:

- captures the Phase 0 item 0.2 follow-up in repository source;
- names the smallest Phase 1 architecture task;
- does not propose ADR body text as accepted decision;
- does not change `policy/estate-rollout-board.json` or
  `scripts/estate_rollout_board.py`;
- does not modify `atlas-infra#173`;
- does not implement evidence records, profiles, snapshot tooling, or the
  Evidence Console.

The 2026 Completion Roadmap remains a planning artifact. Current repository
files, accepted ADRs, and current GitHub state override it.
