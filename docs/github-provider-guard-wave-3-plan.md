# GitHub provider guard wider rollout: Wave 3 plan

Status: reviewed five-repository provider inspection complete; batch apply authority in review. No Wave 3 provider write is authorised by this document.

## Scope

Wave 3 is limited to:

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

Wave 2A and Wave 2B are closed. Wave 4 and all later waves remain unstarted.

## Current source authority

| Repository | `main` | Native PR context |
| --- | --- | --- |
| `atlas-doc-viewer` | `2b03d5843588f0415ecc735f6b33ca7527063137` | `Static document validation` |
| `atlas-quota-watch` | `97304b7df2489a881aca422e494063d62f034a55` | `validate` |
| `site-pulse` | `be661f348ce7bc96b98f868b9d0eb2c01fcc99af` | `Worker validation` |
| `specular-sonify` | `2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53` | `Worker configuration validation` |
| `status` | `4db1438b1a8859008461903105360a2f09376c02` | `Status site validation` |

All five are public, unarchived runtime repositories in `policy/estate-registry.json`, use `main`, and currently report repository-level auto-merge enabled.

## Reviewed owner-authenticated inspection

Inspection authority merged through `atlas-infra#140` as `1cd123cafcaab0bb2736c1659e6f389922190c60`.

Reviewed inspection archive:

- SHA-256: `a18e383a80637dd742108c271b25e30d9cf607a495b9c5680ea20d9c3f7056d8`;
- manifest entries: 64;
- missing payloads: zero;
- digest mismatches: zero;
- provider writes: zero;
- variable writes: zero;
- secret reads: zero;
- Wave 4 started: false.

All five repositories have the same migration class:

- classic `main` branch protection is present;
- repository ruleset count is zero;
- effective ruleset rule list on `main` is empty;
- repository auto-merge is enabled;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED=true`;
- `DEPENDABOT_AUTOMERGE_ENABLED` is absent, so the installed Dependabot auto-merge workflow is inert;
- the latest merged owner PR proves the repository-native context succeeds.

Gardener controller state remains:

- `ATLAS_GARDENER_MODE=automerge-low-risk`;
- `ATLAS_GARDENER_WRITE_GATE=enabled`;
- `ATLAS_GARDENER_WRITE_TARGETS_JSON=["AtlasReaper311/atlas-doc-viewer","AtlasReaper311/atlas-quota-watch","AtlasReaper311/site-pulse","AtlasReaper311/specular-sonify","AtlasReaper311/status"]`.

## Existing classic protection

Each repository currently blocks force pushes and deletion and requires two GitHub Actions checks:

1. its repository-native validation context;
2. `Gardener native auto-merge barrier`.

Both checks are pinned to GitHub Actions integration ID `15368`.

The reviewed strict status-check settings are:

| Repository | `strict` |
| --- | --- |
| `atlas-doc-viewer` | `true` |
| `atlas-quota-watch` | `true` |
| `site-pulse` | `true` |
| `specular-sonify` | `false` |
| `status` | `true` |

The original generic inspection-stage assumption included `strict_required_status_checks_policy: false`. Reviewed provider evidence supersedes that assumption for four repositories. Wave 3 will preserve the existing per-repository strict value instead of weakening protection for uniformity.

Classic protection does not currently expose a pull-request-review requirement, which is why `default_branch_guard` still fails despite the existing status/deletion/force-push controls.

## Reviewed migration target

Each repository will receive one active branch ruleset named `Atlas default branch PR guard` with:

- selector `~DEFAULT_BRANCH`;
- no bypass actors;
- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution;
- `required_status_checks` containing both the exact repository-native context and `Gardener native auto-merge barrier`, each under integration ID `15368`;
- the exact reviewed per-repository strict status-check value above.

Repository auto-merge, `ATLAS_GARDENER_AUTOMERGE_ENABLED`, absent `DEPENDABOT_AUTOMERGE_ENABLED`, Gardener controller authority, source, deployments, schedules, secrets, and runtime configuration are preservation boundaries.

## Fail-closed batch order

`scripts/github-provider-guard-wave-3-migrate.sh` is inspect-only by default. Apply mode requires the exact confirmation `APPLY GITHUB PROVIDER GUARD WAVE 3`.

The provider sequence is deliberately ordered so no repository becomes unprotected:

1. preflight all five exact source/provider baselines and Gardener controller state before the first write;
2. create all five replacement rulesets while every classic protection remains active;
3. re-read and verify every replacement ruleset and every still-present classic protection;
4. only after all five replacements are proven, remove the five superseded classic `main` protections;
5. verify final rulesets, classic-protection absence, unchanged `main`, repository auto-merge, Gardener variables, absent Dependabot variables, and Gardener controller state.

The batch must stop before the first write if any pinned baseline has drifted. If a failure occurs before classic removal, the original protection remains. If a failure occurs during classic removal, the affected repository already has a verified replacement ruleset. The operator has no automatic rollback or ruleset-deletion path.

## Existing pull requests

The inspection observed open Dependabot PRs in all five repositories. They are evidence only. The migration operator contains no PR-merge path and does not enable Dependabot auto-merge. Existing PRs may naturally become stale when later owner validation moves `main`; that is not a provider mutation.

## Source-operator incident note

While preparing the apply branch, two transient source-only placeholder writes were accidentally made directly to `atlas-infra/main` and immediately removed. They changed no Wave 3 target repository and no provider state, secret, runtime, workflow, deployment, release, or automation variable. The permanent inspection receipt records this as `source-operator-misfire-corrected`. No Wave 3 target repository or provider state was changed by that incident.

## Approval boundary

This source authority does not authorise provider mutation.

Any provider mutation requires a new explicit approval after the exact batch operator has passed Atlas Infra checks. No provider write should occur before that approval.

The proposed approval scope will be exactly ten ordered provider writes:

- five ruleset creations, one per Wave 3 repository;
- five classic branch-protection removals, executed only after all five replacement rulesets are verified.

## Explicit boundaries

Wave 3 does not authorise:

- changing repository auto-merge;
- changing Gardener or Dependabot variables;
- changing Gardener controller authority;
- merging existing dependency or Gardener pull requests;
- changing secrets;
- dispatching workflows;
- creating releases;
- deploying or publishing anything;
- modifying runtime configuration;
- beginning Wave 4 or any later wave.
