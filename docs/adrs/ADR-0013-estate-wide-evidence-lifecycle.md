+++
id = "ADR-0013"
date = 2026-09-07
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-infra"]
services = []
contracts = []
policies = []
+++

# ADR-0013: Source merge is not deployment, runtime, or live verification

## Context

Atlas Systems already separates some delivery concerns, but it does not yet own one estate-wide evidence lifecycle. Without that vocabulary, independent surfaces reuse overlapping English for different facts and treat a merged pull request as live proof.

Current accepted records do not fill this gap:

- ADR-0007 treats draft pull requests, previews, merges, and production rollouts as separate evidence stages. A green pull request is source validation only. That rule is local to the public-interface contract and is not a delivery chain.
- ADR-0008 distinguishes public terms including `merged`, `deployed`, `published`, `operational`, `degraded`, `unavailable`, and `unknown`. Those terms mix delivery, publication, and runtime health. They are not a SOURCE-to-LIVE evidence chain.
- ADR-0010 and ADR-0012 forbid treating Twin analysis, CI success, or source merge as deployment or live behaviour. Twin GitHub observation is additive inspection evidence and fails closed as `unavailable` when provider state is missing.
- ADR-0002 owns reliability objectives. ADR-0003 and ADR-0004 own the public/private boundary and classification authority. None of them owns rollout-state truth.

Current repository evidence still collides with those rules.

On `main` at inspection, `policy/estate-rollout-board.json` maps pull-request `merged` to Stage `Live / Verified`. `scripts/estate_rollout_board.py` derives Status and Stage from GitHub draft, gate, closed, and merged facts only. It does not observe deployment, runtime, or live verification. Pull request `#173` already mapped closed-unmerged work to Status `Not Shipped` and Stage `Closed - Not Merged`. The remaining board defect is specific: a merged change is still labelled live because it merged.

`policy/repository-hygiene.json` already keeps native GitHub draft, CI, and merge states out of labels. Atlas-specific labels include `status:rollout-pending` (source is merged or approved; live rollout is still pending) and `status:live-verified` (live state has been independently or owner-verified after rollout). Those labels are pull-request presentation. They are not the estate lifecycle model and are not deployment evidence by themselves.

Wave 3.1 Trace contracts connect existing evidence. They do not define delivery lifecycle authority. Node `evidence_state` is `verified`, `unverified`, `stale`, `unavailable`, or `unknown`. That is observation quality for one node, not a SOURCE-to-LIVE chain. Allowed edges include `SOURCE_OF`, `VALIDATED_BY`, `DEPLOYED_AS`, `VERIFIED_BY`, and `OBSERVED_BY`. Those relations may later attach evidence between stages. They must not collapse `MERGED` into `DEPLOYED` or `LIVE VERIFIED`.

Other evidence-state vocabularies remain valid in their own contracts and must not be silently replaced:

- retirement evidence: `verified`, `failed`, `unknown`, `unavailable`, `not-applicable`;
- evidence ledger allowed states: mixed health, release, and match vocabulary including `healthy`, `failed`, `stale`, `unavailable`, `unknown`, and `live`;
- public-interface evidence modes: `measured`, `stale-measured`, `recorded-replay`, `simulated`, `unavailable`, `unknown`, `not-applicable-unscored`.

Roadmap assertion-result values (`PASS`, `FAIL`, `UNKNOWN`, `NOT OBSERVED`, `NOT APPLICABLE`) are a later evidence-record field. They are not the delivery-stage axis defined here.

The source defect is the inference `MERGED` implies live or verified. This ADR forbids that inference for the estate. It does not rewrite the current rollout-board projection, hygiene labels, Trace contracts, or public-interface vocabulary.

## Decision

`AtlasReaper311/atlas-infra` owns one estate-wide delivery and evidence lifecycle. The Markdown ADR is the decision authority. Consumers may map into this vocabulary. They must not invent a parallel live-proof chain.

Keep two axes distinct. A subject always has a delivery or disposition stage. Independently, an observation at that stage has a result. Observation result is not a later delivery stage.

### Delivery or disposition

Ordered shipping stages:

1. `SOURCE`: a named change exists as repository source (branch, commit, or equivalent exact identity).
2. `CHECKED`: repository-native validation or required checks ran against that exact head. `CHECKED` does not mean review approval, merge, deployment, or live proof.
3. `MERGED`: the exact head is on the target default branch, or an equivalent accepted integration event has occurred. `MERGED` proves source integration only.
4. `DEPLOYMENT OBSERVED`: a named deployment event was seen (workflow run, provider deployment record, or equivalent named event) for a stated identity. Observation of some deployment is not proof that the expected identity is what was deployed.
5. `DEPLOYED`: the expected identity is the deployed identity. This is a stronger claim than `DEPLOYMENT OBSERVED`. The two labels are ordered strengths, not aliases.
6. `RUNTIME VERIFIED`: the deployed subject answered a stated runtime check (health, contract, probe, or equivalent) for the expected identity.
7. `LIVE VERIFIED`: an independent live check of the public or operator-facing behaviour succeeded for the expected identity after rollout. Browser, DNS, and owner live confirmation are methods that may satisfy this stage. They are not extra estate-wide stages.

Terminal disposition, not a shipping stage:

- `CLOSED / NOT SHIPPED`: the change was closed without becoming the shipped identity. This disposition is not live.

A subject remains at the last stage for which evidence exists. Later stages are not inferred.

### Observation result

Usable at any delivery or disposition stage:

- `FAILED`: the check or observation for the claimed stage was performed and did not hold.
- `UNKNOWN / NOT OBSERVED`: required later or current-stage evidence is missing. This is the required label when later evidence is absent. It is never promoted to a live or verified label.
- `NOT APPLICABLE`: the subject has no deployment, runtime, publication, or public surface at which the stage could apply. Examples include a library with no release, documentation that is not published, or a source-only policy change with no runtime.

`FAILED` and `UNKNOWN / NOT OBSERVED` do not move the subject forward. `NOT APPLICABLE` skips a stage that cannot exist for that subject. It does not skip a stage that can exist but was not checked.

### Non-implication rules

These inferences are forbidden:

- `CHECKED` does not imply `MERGED`.
- `MERGED` does not imply `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`.
- `DEPLOYMENT OBSERVED` does not imply `DEPLOYED`. Seeing a named deployment event is not proof that the expected identity is the deployed identity.
- `DEPLOYMENT OBSERVED` or `DEPLOYED` does not imply `RUNTIME VERIFIED`.
- `RUNTIME VERIFIED` does not imply `LIVE VERIFIED`.
- Missing later evidence remains `UNKNOWN / NOT OBSERVED`. It must not be inferred as deployed, runtime-verified, or live-verified.
- `NOT APPLICABLE` is valid only where the stage cannot apply. It is not a substitute for an unobserved stage that does apply.
- `CLOSED / NOT SHIPPED` is not live, not deployed, and not verified.

A merged pull request with no named deployment event is `MERGED` with observation `UNKNOWN / NOT OBSERVED`. The required public reading is that deployment was not observed and the change is not live-verified. Labelling that subject `Live / Verified` is an illegal inference under this ADR.

### How to classify a change

For an arbitrary Atlas repository or change:

1. Name the exact identity (repository, pull request, commit SHA, or equivalent).
2. Assign the latest delivery or disposition stage that current evidence actually proves.
3. Assign an observation result for that stage, and for any later stage that the subject could have.
4. Name the next required evidence as the next applicable stage that is still `UNKNOWN / NOT OBSERVED`.
5. When later evidence is absent, keep the proven stage and report `UNKNOWN / NOT OBSERVED`. Do not fill the gap with merge, CI, or board labels.

CI success, review approval, Twin observation, Motion output, hygiene labels, and rollout-board Stage values do not by themselves prove `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`.

## Consequences

Reviewers gain one estate-wide rule: source merge is insufficient proof of deployment, runtime verification, or live verification. A later Evidence Console, generated estate snapshot, or control-plane consumer can ask the same four questions of any change: current delivery stage, required next evidence, what to show when later evidence is absent, and why `MERGED` is not live.

Existing Trace, ledger, retirement, hygiene, and public-interface vocabularies are not rewritten by this ADR. Those contracts keep their current enums and meanings. Consumers may map them onto this lifecycle later. They must not treat this ADR as a silent schema change.

The Estate Rollout Board remains a GitHub Project projection over pull-request state until a later separately authorised implementation slice. Accepting this ADR does not edit `policy/estate-rollout-board.json`, `scripts/estate_rollout_board.py`, hygiene labels, or Trace contract versions. The current board mapping of `merged` to `Live / Verified` remains a known projection that this ADR forbids as an inference. Changing that mapping is later work.

Lifecycle profiles (runtime Worker, static site, library, documentation, model promotion, article), generated estate snapshots, drift validation, and Evidence Console work depend on this ADR. They remain later Phase 1 and Phase 2 tasks. This record does not authorise those implementations.

Any Trace `GOVERNED_BY` projection of this ADR is a generated relationship from frontmatter, not a second decision authority.

Costs: operators and automations must stop using merge, board Stage, or a green pull request as live language. Surfaces that currently print `Live / Verified` from merge facts will disagree with this ADR until a later authorised mapping change. That disagreement is expected. It is not proof that the merged subject is live.
