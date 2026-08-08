# GitHub provider guard wider rollout: Wave 3 plan

Status: complete. Final provider, owner-path, and stamped scoreboard evidence is recorded in `docs/github-provider-guard-wave-3-closeout.md` and `reports/github-provider-guard-wave-3-final-receipt.json`.

## Scope

Wave 3 was limited to:

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

Wave 2A and Wave 2B were already closed before this work. Wave 4 and all later waves remain unstarted and separately approval gated.

## Source authority

Inspection authority merged through `atlas-infra#140` as `1cd123cafcaab0bb2736c1659e6f389922190c60`.

Batch migration authority merged through `atlas-infra#141` as `2edd65f4cc1b1e62c50630881ba7df42b8a2c0b7`.

The original reviewed source baselines were:

| Repository | Initial `main` | Native PR context |
| --- | --- | --- |
| `atlas-doc-viewer` | `2b03d5843588f0415ecc735f6b33ca7527063137` | `Static document validation` |
| `atlas-quota-watch` | `97304b7df2489a881aca422e494063d62f034a55` | `validate` |
| `site-pulse` | `be661f348ce7bc96b98f868b9d0eb2c01fcc99af` | `Worker validation` |
| `specular-sonify` | `2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53` | `Worker configuration validation` |
| `status` | `4db1438b1a8859008461903105360a2f09376c02` | `Status site validation` |

All five are public, unarchived runtime repositories in the accepted public estate authority, use `main`, and reported repository-level auto-merge enabled throughout the reviewed migration.

## Reviewed owner-authenticated inspection

The inspection archive SHA-256 was:

`a18e383a80637dd742108c271b25e30d9cf607a495b9c5680ea20d9c3f7056d8`

It contained 64 manifest entries with zero missing payloads and zero digest mismatches.

The inspection proved the common migration class:

- classic `main` branch protection present;
- repository ruleset count zero;
- repository auto-merge enabled;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED=true`;
- `DEPENDABOT_AUTOMERGE_ENABLED` absent;
- repository-native validation successful;
- classic protection requiring the repository-native context plus `Gardener native auto-merge barrier`, both under GitHub Actions integration `15368`.

The reviewed strict required-status settings were:

| Repository | `strict` |
| --- | --- |
| `atlas-doc-viewer` | `true` |
| `atlas-quota-watch` | `true` |
| `site-pulse` | `true` |
| `specular-sonify` | `false` |
| `status` | `true` |

Classic protection did not expose the pull-request requirement expected by the Atlas `default_branch_guard` contract, so all five remained readable guard failures before migration.

## Migration contract

The reviewed migration target for every repository was one active branch ruleset named `Atlas default branch PR guard` with:

- selector `~DEFAULT_BRANCH`;
- no bypass actors;
- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution;
- the exact repository-native required status context;
- `Gardener native auto-merge barrier`;
- GitHub Actions integration ID `15368` for both required contexts;
- the existing repository-specific strict required-status value preserved.

Repository auto-merge, Gardener and Dependabot variables, Gardener controller authority, source, deployments, schedules, secrets, and runtime configuration were preservation boundaries.

## Completed fail-closed provider migration

The approved batch followed the reviewed ordering:

1. preflight all five source and provider baselines before the first write;
2. create all five replacement rulesets while every classic protection remained active;
3. verify every replacement ruleset and every still-present classic protection;
4. remove classic protection only after all five replacements were proven;
5. verify final rulesets, classic-protection absence, source identity, repository auto-merge, Gardener variables, absent Dependabot variables, and Gardener controller state.

Provider evidence archive SHA-256:

`c6356e72680cfa130fa4b622cf8a30d63fe96b2e3d79dcecb2c778d0fb2be2e2`

Final rulesets:

| Repository | Ruleset ID | Strict required-status policy |
| --- | ---: | --- |
| `atlas-doc-viewer` | `20586980` | `true` |
| `atlas-quota-watch` | `20586981` | `true` |
| `site-pulse` | `20586982` | `true` |
| `specular-sonify` | `20586983` | `false` |
| `status` | `20586984` | `true` |

Final provider read-back proves the expected four rule types on all five repositories and classic branch protection absent on all five.

## Owner-path validation

Documentation-only owner validation exercised every replacement ruleset through the normal protected path.

| Repository | PR | Reviewed head | Merge commit |
| --- | ---: | --- | --- |
| `atlas-doc-viewer` | `#35` | `ca623d7e972abc868ce44fc59c1ae37d0686187c` | `7117eb333650d27c78ce612427cd729699985395` |
| `atlas-quota-watch` | `#15` | `2734a1c282fc4b63c63b9fb7ffb896a83dab9f64` | `f5425615a0ba5b042140bd1400680ec5963d32d3` |
| `site-pulse` | `#17` | `f3fa1f3d2667f3ee122935d419cf371f5962c711` | `3bad42d3b3ce0dd787ad442874053d5e185409e1` |
| `specular-sonify` | `#20` | `29c1b1445820b4f16e140efb3aa5c0ff08f0f5ce` | `b08a9c411429fe47725a06cd3b4eb87b0ca14559` |
| `status` | `#37` | `b10b39fb06129043e7e7571887dddb2a8beda4f0` | `6033f9f79e48462273a6fb19105a6df5ce31bff8` |

Each exact reviewed head passed its repository-native context and `Gardener native auto-merge barrier`. The user then explicitly approved those five exact heads, and each squash merge used the reviewed head SHA as a merge guard.

No existing Dependabot pull request was merged by Wave 3.

## Final owner-authenticated scoreboard

The final scoreboard was collected at `2026-08-08T20:57:32Z` from exact Atlas Infra source authority `2edd65f4cc1b1e62c50630881ba7df42b8a2c0b7`.

- repositories checked: `33`;
- required passes: `245`;
- required failures: `15`;
- required unknowns: `0`;
- canonical fingerprint: `sha256:3a105c77e74827fd5a46e8cf89f59c0981422c4e7b071f1bf4a1dc314fab8e5b`.

All five Wave 3 `default_branch_guard` checks are `passed` with an active default-branch ruleset observed.

This is the expected movement from the Wave 2B result of `240 / 20 / 0` to `245 / 15 / 0`.

The scoreboard fingerprint was independently recomputed from the canonical final JSON and matched exactly.

## Final evidence package

Final evidence archive SHA-256:

`b11c0f23f52dc26bcee5cf7436511ad97966aa1a8f1662207a4803c58fcda28b`

The archive manifest contains 66 payload entries. Every referenced payload is present and every digest matches.

Permanent evidence is recorded in:

- `docs/github-provider-guard-wave-3-closeout.md`;
- `reports/github-provider-guard-wave-3-final-receipt.json`.

## Source-operator incident note

While preparing the apply authority, two transient source-only placeholder writes were accidentally made directly to `atlas-infra/main` and immediately removed. The reviewed inspection receipt records the incident as corrected.

No Wave 3 target repository or provider state was changed by that incident. Final provider and scoreboard evidence confirms the completed migration state is unaffected.

## Boundaries preserved

Wave 3 did not:

- change repository auto-merge;
- change Gardener or Dependabot variables;
- change Gardener controller authority;
- merge existing dependency or Gardener pull requests;
- change secrets;
- dispatch workflows during provider finalization;
- create releases or tags;
- perform manual deployment or publication;
- modify runtime configuration;
- begin Wave 4 or any later wave.

Wave 3 requires no further provider work. Any Wave 4 activity requires fresh current-state inspection and separate approval.
