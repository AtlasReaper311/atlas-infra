# GitHub provider guard wider rollout

Status: Wave 1A completed and evidenced. Wave 1B and all later waves remain unstarted.

## Purpose

Extend the proven `atlas-badges` default-branch guard pattern across the remaining public estate without treating repositories with different runtime, release, automation, or existing-protection characteristics as interchangeable.

The programme began from the final canary receipt merged in `atlas-infra#124` as `72b85fe4a04598da20a1c10543dd24ed90e796a1`.

The canary-closeout scoreboard collected on `2026-08-04T23:22:02Z` recorded:

- report fingerprint: `sha256:cfb03af45343602dfa5bcc1c6180d2e054242a14a6295695ffda99d7ae5427bd`;
- repositories checked: 33;
- required checks passed: 234;
- required checks failed: 26;
- required checks unknown: 0.

All 26 failures were readable `default_branch_guard` findings.

## Rollout groups

### Wave 1A: completed

Active public non-runtime repositories with genuine Dependabot proof available:

- `AtlasReaper311/atlas-bootstrap`;
- `AtlasReaper311/atlas-resource-audit`.

Wave 1A source authority was merged in `atlas-infra#125` as `c84c4f4822ced17da79cba552def0eb9ada215a6`.

Final evidence is recorded in:

- `docs/github-provider-guard-wave-1-closeout.md`;
- `docs/github-provider-guard-wave-1-final-receipt.json`.

### Wave 1B: not started

Active public non-runtime repository requiring a fresh owner validation pull request:

- `AtlasReaper311/ollama-rag-kit`.

Wave 1B requires a fresh Part 0 inspection, repository-native required-check discovery, and separate provider-write approval.

### Wave 2: specialist active non-runtime repositories

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`;
- `AtlasReaper311/atlas-journey-watch`.

`atlas-gardener` is the dependency-remediation controller and requires a controller-specific protection review.

`atlas-interface-kit` owns immutable interface releases and requires release-path compatibility evidence.

`atlas-journey-watch` had repository auto-merge capability enabled during the Wave 1 inspection and remains excluded until its automation authority and desired repository setting are reviewed together.

### Wave 3: partial classic-protection migrations

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

These are migrations rather than additions. Existing classic protection must be captured and deliberately preserved or replaced one repository at a time.

### Wave 4: production runtime repositories

- `AtlasReaper311/atlas-api-index`;
- `AtlasReaper311/atlas-blackbox`;
- `AtlasReaper311/atlas-corpus`;
- `AtlasReaper311/atlas-daily-digest`;
- `AtlasReaper311/atlas-dora`;
- `AtlasReaper311/atlas-notify`;
- `AtlasReaper311/deploy-watch`;
- `AtlasReaper311/github-pulse`;
- `AtlasReaper311/ramone-edge`;
- `AtlasReaper311/ramone-memory`;
- `AtlasReaper311/ramone-voice-trigger`;
- `AtlasReaper311/specular-sentinel`;
- `AtlasReaper311/specular-telemetry`.

Each runtime repository requires deployment, publication, emergency-recovery, and required-check inspection before a provider write.

### Wave 5: owner-wide special repositories

- `AtlasReaper311/.github`;
- `AtlasReaper311/AtlasReaper311`.

These repositories did not provide a recent repository-native pull-request gate during the Wave 1 inspection. They remain last until their special inheritance or profile behaviour is reviewed and a meaningful native check exists.

## Standard ruleset pattern

The default pattern proven by the canary and Wave 1A is:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- changes must pass through a pull request;
- required approving reviews: 0;
- required review thread resolution: false;
- repository-native required status check bound to GitHub Actions integration ID `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch update policy disabled;
- repository auto-merge unchanged unless separately authorised.

This pattern is not applied blindly. Each repository must first prove the exact native context, integration, automation compatibility, and recovery boundary.

## Wave 1A outcome

Provider results:

| Repository | Ruleset | Required context |
| --- | ---: | --- |
| `atlas-bootstrap` | `20443224` | `build` |
| `atlas-resource-audit` | `20443225` | `Offline resource audit` |

Both rulesets were created through the approved fail-closed runner, read back from GitHub, and independently observed through the active-rules endpoint. Both retained repository auto-merge disabled.

Protected owner-path proof:

- `atlas-bootstrap#10` passed at `1bb61ab660fd987625bee83b57ed71caefd0da1f` and merged as `c4da05eb850ec9dffa8cf84e98d33f0b8d4aaa22`;
- `atlas-resource-audit#13` passed at `9d44d8b4ef417fa92ef29d5e7481bdb0990ea839` and merged as `76ec572239a35c7f8a00111801e1aaebd1dc1b27`.

The final owner-authenticated scoreboard collected at `2026-08-05T08:56:34Z` recorded:

- report fingerprint: `sha256:6838a900dbae4b2c1b4e218b2a5d02e9922649c5ea17e9740a402a145eb1c485`;
- repositories checked: 33;
- required checks passed: 236;
- required checks failed: 24;
- required checks unknown: 0;
- both Wave 1A repositories passed `default_branch_guard`.

Wave 1A is closed and requires no further work.

## Per-wave execution contract

Every later wave must follow this sequence:

1. inspect current repository, ruleset, classic-protection, auto-merge, pull-request, workflow, release, deployment, and recovery state;
2. discover the exact repository-native required check and GitHub App integration;
3. prepare source authority and a fail-closed inspection-first runner;
4. merge source authority after exact-head validation;
5. obtain separate provider-write approval for an exact repository list;
6. run read-only inspection from the approved authority commit;
7. review pre-write evidence and digests;
8. perform only the approved provider writes;
9. verify provider create responses, read-backs, active rules, and unchanged unrelated settings;
10. prove genuine automation compatibility;
11. open and merge harmless owner validation pull requests through the new guards;
12. run a stamped owner-authenticated scoreboard;
13. commit a final machine-readable receipt and human-readable closeout record.

Expected count movement is planning arithmetic, not evidence. Only the stamped report closes a wave.

## Rollback

When a new rule blocks an intended owner or automation path:

1. stop the wave immediately;
2. do not touch repositories whose approved write has not occurred;
3. identify only the affected ruleset ID from the evidence directory;
4. obtain separate rollback approval;
5. disable or delete only that ruleset;
6. verify repository auto-merge and unrelated settings remain unchanged;
7. rerun the owner-authenticated scoreboard;
8. record the failure and do not begin the next wave.

Rollback is a provider write and is never implied by rollout approval.

## Boundaries

No later wave may begin implicitly from completion of Wave 1A.

Separate approval remains required for:

- each exact provider-write repository list;
- classic-protection migration;
- changing repository auto-merge;
- destructive direct-push, force-push, or deletion tests;
- merging Dependabot pull requests;
- workflow dispatches;
- releases, tags, deployments, publications, or secret changes.

The shared `docs/work-allocation.md` remains untouched because public-interface Phase 15 coordination is independent of this provider programme.
