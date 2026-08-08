# GitHub provider guard wider rollout: Wave 2 plan

Status: owner-authenticated inspection reviewed. Wave 2A apply source is prepared for `atlas-gardener` and `atlas-interface-kit` only. `atlas-journey-watch` is held for separate migration/reconciliation work. No Wave 2 provider write is authorised by this document alone.

## Scope

Wave 2 began with three specialist active public non-runtime repositories:

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`;
- `AtlasReaper311/atlas-journey-watch`.

After owner-authenticated inspection, the provider-write candidates are split:

### Wave 2A

- `AtlasReaper311/atlas-gardener` with required context `test`;
- `AtlasReaper311/atlas-interface-kit` with required context `Validate interface kit`.

### Wave 2B held

- `AtlasReaper311/atlas-journey-watch`.

Wave 3 and all later waves remain unstarted.

## Authority and classification

ADR-0004 authority in `policy/public-assurance-repositories.json` classifies all three repositories as active, public, original repositories. None is classified as a public runtime-service repository by `policy/estate-registry.json`.

The final Wave 1B scoreboard identified all three as failures of the qualifying `default_branch_guard` conformance check. The owner-authenticated Wave 2 inspection refined that result and proved that Journey Watch already has an active repository ruleset which does not satisfy the standard Atlas guard projection.

## Owner-authenticated inspection receipt

Inspection authority:

- source merge: `atlas-infra#133`;
- authority commit: `1a5be84456861e5d0cd09b13db207f2e81a1f007`;
- evidence run stamp: `20260808T005252Z`;
- uploaded archive SHA-256: `44cdbb9171c4cf9aaf0a3240836d744ec9ef5e19c1c9790ebc4c654e8b385b62`;
- `provider-baseline-summary.json` SHA-256: `f0c373e615c7d66aa6b94093807e715fa0201f6b86ebc9f60e9de0b75146713c`;
- evidence payloads covered by `SHA256SUMS.txt`: `40`;
- digest mismatches: `0`;
- provider writes performed: `false`.

The inspection did not read Actions secrets and did not mutate rulesets, branch protection, auto-merge, variables, workflows, releases, deployments, or runtime state.

## Wave 2A evidence

### atlas-gardener

Inspected repository state:

- default branch: `main`;
- current `main`: `319465dcea68a8fefead3e7d90e82b79078cb34d`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled;
- active branch rulesets: none;
- classic `main` protection: absent.

Native pull-request gate:

- context: `test`;
- GitHub Actions integration ID: `15368`;
- genuine Dependabot PR: `atlas-gardener#22`;
- PR state: open and mergeable;
- base SHA: `319465dcea68a8fefead3e7d90e82b79078cb34d`;
- head SHA: `5975733c5d4f05d66f957cb50a322905f7751d06`;
- native `test` check: completed successfully.

The owner-authenticated inspection also proved that the scheduled controller is currently live in a separately governed automation mode:

- `ATLAS_GARDENER_MODE`: `automerge-low-risk`;
- `ATLAS_GARDENER_WRITE_GATE`: `enabled`;
- `ATLAS_GARDENER_WRITE_TARGETS_JSON`: `["AtlasReaper311/atlas-doc-viewer","AtlasReaper311/atlas-quota-watch","AtlasReaper311/site-pulse","AtlasReaper311/specular-sonify","AtlasReaper311/status"]`.

Those five targets are later partial-protection repositories. A guard on Gardener's own `main` neither grants nor expands controller authority. The Wave 2A runner therefore pins the three observed variables and fails closed if any value changes before or during provider apply. It never writes an Actions variable, controller setting, GitHub App permission, schedule, target list, or secret.

### atlas-interface-kit

Inspected repository state:

- default branch: `main`;
- current `main`: `21a1a168e3b25e916555ce4edd4229bd7c061ecb`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled;
- active branch rulesets: none;
- classic `main` protection: absent.

Native pull-request gate:

- context: `Validate interface kit`;
- GitHub Actions integration ID: `15368`;
- current source/release candidate proof: `atlas-interface-kit#14`;
- reviewed head: `1f26360d938b589cf8a562ca308fd6ca3b4a2b3f`;
- merged commit: `21a1a168e3b25e916555ce4edd4229bd7c061ecb`;
- native `Validate interface kit` check: completed successfully.

Release compatibility remains unchanged. `.github/workflows/release.yml` operates on `v*` tags or explicit dispatch against an existing tag. A default-branch guard does not create a tag, publish a release, alter consumer adoption, or prove deployment.

## Journey Watch hold

The owner-authenticated inspection corrected the earlier coarse assumption about Journey Watch.

Current provider and automation state:

- repository auto-merge: enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED`: `true`;
- active repository ruleset ID: `19154613`;
- ruleset name: `Require native pull request validation`;
- target: branch;
- enforcement: active;
- classic `main` protection: absent;
- genuine Dependabot PR `atlas-journey-watch#12`: open and mergeable;
- native context `Offline journey validation`: successful under GitHub Actions integration ID `15368`.

Journey Watch is therefore not a fresh guard-addition candidate. It already combines provider protection with active selective Dependabot auto-merge. Its existing ruleset must be read back in full and reconciled deliberately against the Atlas default-branch guard contract before any provider mutation is proposed.

Wave 2A source and provider operations must not create, replace, update, disable, or delete Journey Watch ruleset `19154613`; must not change repository auto-merge; and must not change `DEPENDABOT_AUTOMERGE_ENABLED`.

## Wave 2A apply authority

`scripts/github-provider-guard-wave-2a.sh` is the only provider operator prepared by this stage.

Default mode is read-only `inspect`.

Provider apply is unreachable unless both conditions are true:

- `MODE=apply`;
- `ATLAS_PROVIDER_WRITE_CONFIRMATION="APPLY GITHUB PROVIDER GUARD WAVE 2A"`.

The exact repository map is limited to:

- `atlas-gardener`;
- `atlas-interface-kit`.

The runner pins:

- each current `main` SHA;
- Gardener PR `#22` and exact Dependabot head;
- Interface Kit PR `#14` and exact reviewed head/merged commit;
- the exact native required context for each repository;
- GitHub Actions integration ID `15368`;
- repository auto-merge disabled;
- absence of active branch rulesets and classic `main` protection;
- Gardener's three observed controller variables.

Any drift causes refusal before provider creation.

## Candidate ruleset shape

The Wave 2A ruleset matches the proven Atlas pattern:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- pull request required;
- required approving reviews: `0`;
- required review-thread resolution: false;
- exact repository-native status check bound to GitHub Actions integration ID `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch-update policy disabled.

Provider apply creates one ruleset per approved Wave 2A repository and then reads back:

- the created ruleset;
- effective `main` rules;
- repository settings;
- `main` identity;
- Gardener controller variables.

The runner records SHA-256 evidence and contains no rollback path.

## Validation after provider apply

Provider creation does not close Wave 2A.

After a separately approved provider apply:

1. review provider evidence and exact created ruleset IDs;
2. prove Gardener's genuine Dependabot path remains compatible through the new guard without merging it implicitly;
3. create a harmless owner validation PR for Interface Kit and prove its owner path through the new guard;
4. confirm repository auto-merge remains disabled on both Wave 2A repositories;
5. confirm Gardener controller variables remain byte-for-byte unchanged;
6. run a new owner-authenticated stamped scoreboard;
7. commit final machine-readable and human-readable Wave 2A receipts;
8. close Wave 2A before any Journey Watch provider mutation or Wave 3 work.

## Approval boundary

Merging Wave 2A apply source authority is not provider-write approval.

The exact provider-write list requiring explicit approval is:

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`.

`atlas-journey-watch`, Wave 3, and all later waves are excluded.

## Rollback

Rollback is not automatic.

If one approved ruleset blocks an intended path:

1. stop immediately;
2. do not touch the other repository if its write has not occurred;
3. identify only the affected ruleset ID from evidence;
4. obtain separate rollback approval;
5. delete or alter only the approved affected ruleset;
6. verify unrelated provider, automation, release, and repository state remains unchanged.

## Explicit boundaries

This stage does not:

- perform a provider write merely by merging source;
- alter Gardener controller mode, write gate, targets, schedule, GitHub App permissions, or secrets;
- alter Interface Kit tag/release authority;
- touch Journey Watch ruleset `19154613`;
- change Journey Watch auto-merge or `DEPENDABOT_AUTOMERGE_ENABLED`;
- merge Dependabot PRs;
- create or publish releases or tags;
- dispatch workflows;
- deploy, restart, publish, or roll back runtime services;
- begin Wave 3 or any later wave.
