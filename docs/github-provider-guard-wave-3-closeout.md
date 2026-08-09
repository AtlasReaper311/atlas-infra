# GitHub provider guard Wave 3 closeout

Status: complete.

Wave 3 was limited to:

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

At the time of this Wave 3 closeout, Wave 4 and all later waves remained unstarted. Wave 4 later completed under a separate programme; see `docs/github-provider-guard-wave-4-closeout.md`.

## Source authority

- read-only inspection authority: `1cd123cafcaab0bb2736c1659e6f389922190c60` (`atlas-infra#140`);
- reviewed batch migration authority: `2edd65f4cc1b1e62c50630881ba7df42b8a2c0b7` (`atlas-infra#141`).

The reviewed inspection archive SHA-256 was:

`a18e383a80637dd742108c271b25e30d9cf607a495b9c5680ea20d9c3f7056d8`

It contained 64 manifest entries with zero missing payloads and zero digest mismatches.

## Provider migration result

The approved fail-closed migration created and verified all five replacement rulesets before removing any classic protection. After all five replacement rulesets were proven, the five superseded classic `main` protections were removed.

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

Every ruleset is active, targets `~DEFAULT_BRANCH`, has no bypass actors, and contains:

- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no required review-thread resolution;
- the repository-native required context under GitHub Actions integration `15368`;
- `Gardener native auto-merge barrier` under GitHub Actions integration `15368`.

Final read-back recorded classic branch protection absent on all five repositories.

## Automation preservation

The migration and finalization evidence records:

- repository auto-merge still enabled on all five repositories;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED=true` preserved on all five repositories;
- `DEPENDABOT_AUTOMERGE_ENABLED` absent on all five repositories;
- Gardener controller mode, write gate, and exact Wave 3 target set unchanged;
- no existing Dependabot pull request merged by Wave 3;
- no variable write during finalization;
- no workflow dispatch during finalization;
- no manual deployment;
- Wave 4 was not started by Wave 3.

## Owner-path validation

Each repository was validated through a documentation-only owner pull request. The exact reviewed heads passed both the repository-native required context and `Gardener native auto-merge barrier` before the owner-approved squash merge.

| Repository | PR | Reviewed head | Merge commit | Native context |
| --- | ---: | --- | --- | --- |
| `atlas-doc-viewer` | `#35` | `ca623d7e972abc868ce44fc59c1ae37d0686187c` | `7117eb333650d27c78ce612427cd729699985395` | `Static document validation` |
| `atlas-quota-watch` | `#15` | `2734a1c282fc4b63c63b9fb7ffb896a83dab9f64` | `f5425615a0ba5b042140bd1400680ec5963d32d3` | `validate` |
| `site-pulse` | `#17` | `f3fa1f3d2667f3ee122935d419cf371f5962c711` | `3bad42d3b3ce0dd787ad442874053d5e185409e1` | `Worker validation` |
| `specular-sonify` | `#20` | `29c1b1445820b4f16e140efb3aa5c0ff08f0f5ce` | `b08a9c411429fe47725a06cd3b4eb87b0ca14559` | `Worker configuration validation` |
| `status` | `#37` | `b10b39fb06129043e7e7571887dddb2a8beda4f0` | `6033f9f79e48462273a6fb19105a6df5ce31bff8` | `Status site validation` |

The final owner-authenticated evidence confirms each pull request closed at the reviewed head and each required context succeeded.

## Final scoreboard

The fresh owner-authenticated scoreboard was collected at `2026-08-08T20:57:32Z` from exact Atlas Infra authority commit `2edd65f4cc1b1e62c50630881ba7df42b8a2c0b7`.

Final policy summary:

- repositories checked: `33`;
- required passes: `245`;
- required failures: `15`;
- required unknowns: `0`;
- not applicable: `68`;
- approved exceptions: `1`;
- deferred: `1`;
- canonical fingerprint: `sha256:3a105c77e74827fd5a46e8cf89f59c0981422c4e7b071f1bf4a1dc314fab8e5b`.

All five Wave 3 `default_branch_guard` outcomes are `passed` with the message `An active default-branch ruleset was observed.`

This realizes the expected movement from `240 / 20 / 0` after Wave 2B to `245 / 15 / 0` after Wave 3.

The canonical scoreboard fingerprint was independently recomputed from the final JSON and matched exactly.

## Final evidence package

Final evidence archive SHA-256:

`b11c0f23f52dc26bcee5cf7436511ad97966aa1a8f1662207a4803c58fcda28b`

Its `SHA256SUMS.txt` contains 66 payload entries. All 66 referenced payloads are present and all 66 independently match their recorded SHA-256 values.

The permanent machine-readable receipt is `reports/github-provider-guard-wave-3-final-receipt.json`.

## Source-operator incident record

During preparation of the Wave 3 apply authority, two transient source-only placeholder writes were accidentally made directly to `atlas-infra/main` and immediately removed. The reviewed inspection receipt and migration plan already record the incident. It changed no Wave 3 target repository, provider setting, secret, runtime, workflow, deployment, release, or automation variable.

The final provider and scoreboard evidence confirms the incident had no effect on the completed Wave 3 result.

## Boundaries preserved

Wave 3 did not:

- change repository auto-merge;
- change Gardener or Dependabot automation variables;
- change Gardener controller authority;
- merge existing Dependabot pull requests;
- change secrets;
- dispatch workflows during provider finalization;
- create releases or tags;
- perform manual deployments or publication;
- modify runtime configuration;
- begin Wave 4 or any later wave.

Wave 3 requires no further provider work. Wave 4 later completed under a separate programme; see `docs/github-provider-guard-wave-4-closeout.md`.
