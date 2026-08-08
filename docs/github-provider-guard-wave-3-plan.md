# GitHub provider guard wider rollout: Wave 3 plan

Status: Part 0 inspection authority in preparation. No Wave 3 provider write is authorised by this document.

## Scope

Wave 3 is the five-repository migration batch:

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

Wave 2A and Wave 2B are closed. Wave 4 and all later waves remain unstarted.

## Current source authority

Current GitHub source is pinned to:

| Repository | `main` | Native PR context |
| --- | --- | --- |
| `atlas-doc-viewer` | `2b03d5843588f0415ecc735f6b33ca7527063137` | `Static document validation` |
| `atlas-quota-watch` | `97304b7df2489a881aca422e494063d62f034a55` | `validate` |
| `site-pulse` | `be661f348ce7bc96b98f868b9d0eb2c01fcc99af` | `Worker validation` |
| `specular-sonify` | `2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53` | `Worker configuration validation` |
| `status` | `4db1438b1a8859008461903105360a2f09376c02` | `Status site validation` |

All five repositories are public, unarchived, use `main` as the default branch, and currently report repository-level auto-merge enabled.

All five are authoritative runtime entries in `policy/estate-registry.json`. They are not non-runtime entries in `policy/public-assurance-repositories.json`.

Current repository source also contains both maintenance paths:

- `.github/workflows/gardener-remediation-gate.yml`, scoped to `gardener/` branches and gated by `ATLAS_GARDENER_AUTOMERGE_ENABLED`;
- `.github/workflows/dependabot-automerge.yml`, gated by `DEPENDABOT_AUTOMERGE_ENABLED`.

The Gardener gates pin the native contexts listed above and use GitHub native auto-merge as the final merge mechanism.

## Why Wave 3 is a migration

The final Wave 2B scoreboard records 240 policy-required passes, 20 policy-required failures, and zero unknowns across 33 repositories.

Wave 3 was previously classified as partial classic-protection migration work. Current provider state must be re-read before relying on that classification. The batch must not assume that classic protection, repository rulesets, or automation variables are unchanged.

The migration goal is one understandable default-branch guard model per repository without weakening any existing protection or breaking Gardener or Dependabot automation.

## Part 0 owner-authenticated inspection

`scripts/github-provider-guard-wave-3-inspect.sh` is read-only. It will inspect all five repositories in one run and capture:

- repository metadata and repository auto-merge;
- exact current `main` commit;
- classic `main` branch protection, including an explicit absent/present result;
- all repository rulesets;
- effective rules on `main`;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED` without writing it;
- `DEPENDABOT_AUTOMERGE_ENABLED` without writing it;
- recent pull-request evidence and exact native check results;
- current Gardener remediation gate source;
- current Dependabot auto-merge workflow source;
- the three Gardener controller variables that bound `automerge-low-risk` write authority.

The inspection does not read any secret endpoint.

## Expected migration shape, not yet authorised

If provider evidence confirms that a repository still has partial classic branch protection and no equivalent Atlas ruleset, the likely target semantics are:

- active branch ruleset;
- selector `~DEFAULT_BRANCH`;
- no bypass actors;
- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution;
- `required_status_checks` using the exact repository-native context under GitHub Actions integration `15368`;
- `strict_required_status_checks_policy: false`.

Repository auto-merge, `ATLAS_GARDENER_AUTOMERGE_ENABLED`, `DEPENDABOT_AUTOMERGE_ENABLED`, source, deployments, schedules, secrets, and runtime configuration are preservation boundaries, not rollout targets.

Classic protection must not be removed until the replacement ruleset is proven equivalent or stronger and the owner and automation paths have been validated. Any classic-protection removal is a separate provider mutation within the reviewed migration plan, not an implicit cleanup.

If a repository already has an equivalent ruleset or materially different protection, it will be reconciled from evidence rather than forced into the assumed path.

## Batch strategy

To finish Wave 3 quickly without weakening controls:

1. run one five-repository read-only inspection;
2. normalize the exact per-repository migration decision in `atlas-infra`;
3. prepare one fail-closed batch apply operator where repository states are sufficiently uniform;
4. obtain one explicit provider-write approval covering the exact reviewed five-repository mutation set;
5. apply and verify the provider batch;
6. validate one harmless owner documentation PR per repository through the resulting guard;
7. separately validate Gardener/Dependabot behavior when current evidence requires it;
8. run one owner-authenticated stamped estate scoreboard;
9. close Wave 3 in one Atlas Infra closeout PR.

The batch operator must stop before the first write if any pinned repository identity or provider baseline has drifted. It must not silently skip or improvise a changed repository.

## Approval boundary

This inspection and its source PR do not authorise provider mutation.

After the read-only evidence is reviewed, the exact ruleset creation/update and any classic-protection removal will be presented as one explicit Wave 3 provider-write gate. No provider write should occur before that approval.

## Explicit boundaries

Wave 3 does not by itself authorise:

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
