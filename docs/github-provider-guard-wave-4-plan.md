# GitHub provider guard Wave 4 plan

Status: reviewed owner-authenticated Wave 4 inspection complete; source authority in review. No Wave 4 provider write is authorised by this document.

## Scope

Wave 4 is split by observed provider shape rather than repository count.

Wave 4A is a create-first batch of 13 repositories:

- `AtlasReaper311/.github`;
- `AtlasReaper311/atlas-api-index`;
- `AtlasReaper311/atlas-blackbox`;
- `AtlasReaper311/atlas-corpus`;
- `AtlasReaper311/atlas-daily-digest`;
- `AtlasReaper311/atlas-notify`;
- `AtlasReaper311/deploy-watch`;
- `AtlasReaper311/github-pulse`;
- `AtlasReaper311/ramone-edge`;
- `AtlasReaper311/ramone-memory`;
- `AtlasReaper311/ramone-voice-trigger`;
- `AtlasReaper311/specular-sentinel`;
- `AtlasReaper311/specular-telemetry`;

Wave 4B is limited to in-place reconciliation of `AtlasReaper311/atlas-dora` ruleset `19581236`.

`AtlasReaper311/AtlasReaper311` is explicitly held. Its scheduled profile refresh writes directly to `main`; Wave 4A and Wave 4B must not modify that repository or its rules until the writer is redesigned or separately approved.

## Source and inspection authority

The reviewed inspection was taken from `atlas-infra` authority `ce709204e735bbf30f9479f354dacdd602b6a65f`.

Inspection archive SHA-256:

`0abbd15869a96a8f38f7f7945a914277b7995924710e9eb0a0580478a289e884`

The archive contains 171 manifest payloads. All 171 are present and independently match their recorded SHA-256 values. It records zero provider writes, zero variable writes, zero workflow dispatches, zero secret reads, and `wave_4_provider_apply_started: false`.

The permanent normalized receipt is `reports/github-provider-guard-wave-4-inspection-receipt.json`.

Wave 3 closed at 245 required passes, 15 required failures, and zero required unknowns. All 15 remaining required failures are `default_branch_guard`.

## Wave 4A reviewed baselines

| Repository | Reviewed `main` | Native required context |
| --- | --- | --- |
| `.github` | `dd3818eeae486c95e1a1fc0860786db5c24308fa` | `none` |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | `build` |
| `atlas-blackbox` | `e0c3ac7cdb2438a13a7ec71a02f7ac86aeed4223` | `Offline Worker validation` |
| `atlas-corpus` | `faa0690f5f1e58fa97c1839d6f320e00512ecdd1` | `build` |
| `atlas-daily-digest` | `125e4872b90227c4cf72f33f953308e99ddd027b` | `Worker validation` |
| `atlas-notify` | `9efeb709cd86f4b7bb7e6910d55a6155eb7e79f0` | `Test (Vitest)` |
| `deploy-watch` | `72513e434a7b68bdba4e8c181b536b92da6f2b17` | `Worker validation` |
| `github-pulse` | `8f1435e9302cf9006d9ab8a2cc2a9702c460cad6` | `Worker validation` |
| `ramone-edge` | `3830dd3839847187e0b5ac6c837a5658f5f47341` | `Worker validation` |
| `ramone-memory` | `7b983cd4df1435ea0962ff3179d8570ec8dc0e71` | `build` |
| `ramone-voice-trigger` | `6e3273330e531b936553b34243ed5ee6141ba614` | `build` |
| `specular-sentinel` | `8dfe8c4274fc278855bcd4658cdb4866d3c29d3f` | `build` |
| `specular-telemetry` | `0a0a930abaa104e6da5c9ad2da57e78eb0fbec80` | `build` |

All 13 Wave 4A repositories share the create-first provider shape:

- public, unarchived repository with default branch `main`;
- repository auto-merge disabled;
- classic `main` protection absent;
- zero repository rulesets and zero effective rules on `main`;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED` absent;
- `DEPENDABOT_AUTOMERGE_ENABLED` absent.

The 12 runtime repositories have a reviewed successful repository-native GitHub Actions context under integration ID `15368`. `.github` has no repository-native CI context and therefore receives no invented required-status rule.

### Wave 4A target contract

`scripts/github-provider-guard-wave-4a.sh` is inspect-only by default. Apply mode requires the exact confirmation `APPLY GITHUB PROVIDER GUARD WAVE 4A`.

For each of the 12 runtime repositories it may create exactly one active ruleset named `Atlas default branch PR guard` with:

- selector `~DEFAULT_BRANCH`;
- no bypass actors;
- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution;
- `required_status_checks` containing only the reviewed repository-native context under GitHub Actions integration ID `15368`;
- `strict_required_status_checks_policy: false`.

For `.github` the ruleset contains only `deletion`, `non_fast_forward`, and `pull_request`; there is no required-status rule because the reviewed repository has no native CI context.

Wave 4A is additive. Its provider mutation surface is repository-ruleset creation only. It must not delete or update classic protection, update an existing ruleset, change repository settings, change Actions variables, merge or close pull requests, dispatch workflows, create releases, or deploy anything.

The operator preflights all 13 reviewed baselines before the first provider write and verifies each newly created ruleset immediately. If a later creation fails, already-created rulesets remain additive protection; recovery must begin with a fresh read-only inspection rather than blind retry or deletion.

Successful Wave 4A readback is expected to move the scoreboard from `245 / 15 / 0` to `258 / 2 / 0`.

## Wave 4B reviewed baseline

`atlas-dora` is not a create-first repository. The reviewed state is:

- `main`: `fff7c2c5453240dafd693e8a4de645beab523031`;
- classic protection absent;
- exactly one active repository ruleset, ID `19581236`;
- ruleset name `Atlas Gardener native auto-merge barrier`;
- selector `refs/heads/main`;
- no bypass actors;
- only one rule type, `required_status_checks`;
- required contexts `check` and `Gardener native auto-merge barrier`;
- `strict_required_status_checks_policy: false`;
- repository auto-merge disabled;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED=false`;
- `DEPENDABOT_AUTOMERGE_ENABLED` absent.

Gardener controller authority remains `automerge-low-risk`, write gate `enabled`, with write targets limited to the five completed Wave 3 repositories. DORA is not a controller write target.

### Wave 4B target contract

`scripts/github-provider-guard-wave-4b-reconcile.sh` is inspect-only by default. Apply mode requires the exact confirmation `APPLY GITHUB PROVIDER GUARD WAVE 4B`.

The operator may update ruleset `19581236` in place. It preserves the existing ruleset identity, name, `refs/heads/main` selector, no-bypass state, both required-status contexts, and non-strict required-status policy, and adds only:

- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution.

It must not create or delete a DORA ruleset, change repository auto-merge, change Gardener or Dependabot variables, change Gardener controller authority, merge a pull request, dispatch a workflow, or deploy anything.

Wave 4B remains separately provider-write gated after Wave 4A evidence is reviewed. Successful Wave 4B readback is expected to move the scoreboard from `258 / 2 / 0` to `259 / 1 / 0`.

## Held profile repository

`AtlasReaper311/AtlasReaper311` remains the final known `default_branch_guard` failure after Wave 4B by design. The reviewed repository has no current ruleset or classic protection, but `.github/workflows/update-readme.yml` has `contents: write` and commits/pushes refreshed profile data directly to `main` with `github-actions[bot]`.

Wave 4A and Wave 4B contain no profile-repository mutation. Reaching `260 / 0 / 0` requires a later, separately inspected redesign or explicit compatibility decision for that direct-main writer.

## Validation and rollout gates

Source preparation and provider rollout remain separate:

1. merge this source authority only after exact-head Atlas Infra checks and review;
2. separately approve Wave 4A provider creation;
3. collect owner-authenticated Wave 4A readback and a fresh scoreboard;
4. separately approve Wave 4B DORA reconciliation;
5. collect owner-authenticated Wave 4B readback and a fresh scoreboard;
6. treat the profile writer redesign as a later programme.

The provider operators do not create or merge owner-validation pull requests. If owner-path validation is later requested, it is a separate source-write gate. Any merge in a repository whose `main` path deploys is also a separate deployment action and must not be inferred from ruleset success.

Any provider mutation requires a new explicit approval after this source authority is reviewed and merged.
