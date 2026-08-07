# GitHub provider guard wider rollout

Status: canary, Wave 1A, and Wave 1B completed and evidenced. Wave 2 and all later waves remain unstarted.

## Purpose

Extend the proven default-branch PR guard pattern across the public Atlas estate without treating repositories with different runtime, release, automation, or existing-protection characteristics as interchangeable.

The programme began from the final `atlas-badges` canary receipt merged through `atlas-infra#124` as `72b85fe4a04598da20a1c10543dd24ed90e796a1`.

## Completed rollout

### Canary: `atlas-badges`

The canary established the standard pattern and proved both an Atlas owner path and a genuine Dependabot path before broader rollout.

### Wave 1A

Completed repositories:

- `AtlasReaper311/atlas-bootstrap`;
- `AtlasReaper311/atlas-resource-audit`.

Source authority merged through `atlas-infra#125` as `c84c4f4822ced17da79cba552def0eb9ada215a6`.

Final Wave 1A scoreboard:

- collected at: `2026-08-05T08:56:34Z`;
- fingerprint: `sha256:6838a900dbae4b2c1b4e218b2a5d02e9922649c5ea17e9740a402a145eb1c485`;
- required passes: `236`;
- required failures: `24`;
- required unknowns: `0`.

Permanent evidence:

- `docs/github-provider-guard-wave-1-closeout.md`;
- `docs/github-provider-guard-wave-1-final-receipt.json`.

### Wave 1B

Completed repository:

- `AtlasReaper311/ollama-rag-kit`.

Source authority merged through `atlas-infra#131` as `1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3`.

Provider outcome:

- ruleset ID: `20573090`;
- required context: `Build and smoke-check`;
- GitHub Actions integration ID: `15368`;
- repository auto-merge remained disabled.

Protected owner-path proof:

- `ollama-rag-kit#18` reviewed at `a46a83fd3a28807fbb9d3a2d5b4f96ae504a5e19`;
- merged as `e2cc5f4dadd3cc1bee5e8f72a6b710c8851c9657`.

Final Wave 1B scoreboard:

- collected at: `2026-08-07T23:29:47Z`;
- source: `AtlasReaper311/atlas-infra@1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3`;
- fingerprint: `sha256:16b63950fb860bb38fb8b4e7473b5ed8737b985f55d7a0024701d73e00b80322`;
- repositories checked: `33`;
- required checks: `260`;
- required passes: `237`;
- required failures: `23`;
- required unknowns: `0`;
- `ollama-rag-kit/default_branch_guard`: passed.

Permanent evidence:

- `docs/github-provider-guard-wave-1b-closeout.md`;
- `docs/github-provider-guard-wave-1b-final-receipt.json`.

## Remaining rollout groups

### Wave 2: specialist active non-runtime repositories

Not started.

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`;
- `AtlasReaper311/atlas-journey-watch`.

`atlas-gardener` is the dependency-remediation controller and requires a controller-specific protection review.

`atlas-interface-kit` owns immutable interface releases and requires release-path compatibility evidence.

`atlas-journey-watch` previously had repository auto-merge capability enabled and remains excluded until its automation authority and desired repository setting are reviewed together.

### Wave 3: partial classic-protection migrations

Not started.

- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-quota-watch`;
- `AtlasReaper311/site-pulse`;
- `AtlasReaper311/specular-sonify`;
- `AtlasReaper311/status`.

These are migrations rather than additions. Existing classic protection must be captured and deliberately preserved or replaced one repository at a time.

### Wave 4: production runtime repositories

Not started.

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

Not started.

- `AtlasReaper311/.github`;
- `AtlasReaper311/AtlasReaper311`.

These repositories lacked a meaningful recent repository-native pull-request gate during the original inspection and remain last until their special inheritance or profile behaviour is reviewed.

## Standard ruleset pattern

The default pattern proven by the canary and Wave 1 is:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- changes must pass through a pull request;
- required approving reviews: `0`;
- required review-thread resolution: false;
- repository-native required status check bound to the observed GitHub Actions integration;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch-update policy disabled;
- repository auto-merge unchanged unless separately authorised.

This pattern is not applied blindly. Each repository must first prove the exact native context, integration, automation compatibility, deployment/recovery boundary, and existing protection state.

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

No later wave begins implicitly from completion of an earlier wave.

Separate approval remains required for:

- each exact provider-write repository list;
- classic-protection migration;
- changing repository auto-merge;
- destructive direct-push, force-push, or deletion tests;
- merging Dependabot pull requests;
- workflow dispatches;
- releases, tags, deployments, publications, or secret changes.

The next optional stage is Wave 2. It must start with fresh current-state inspection before any source or provider change is proposed.
