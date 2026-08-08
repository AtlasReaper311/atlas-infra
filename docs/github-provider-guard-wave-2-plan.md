# GitHub provider guard wider rollout: Wave 2 plan

Status: Part 0 complete. Source authority is inspection-only; no Wave 2 provider write is authorised by this document.

## Scope

Wave 2 is limited to three specialist active public non-runtime repositories:

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`;
- `AtlasReaper311/atlas-journey-watch`.

The `atlas-badges` canary, Wave 1A, and Wave 1B are complete. Wave 3 and all later waves remain unstarted.

## Authority and classification

Part 0 was refreshed against current GitHub state on 2026-08-08.

ADR-0004 authority in `policy/public-assurance-repositories.json` classifies all three repositories as:

- lifecycle: `active`;
- scope: `public`;
- provenance: `original`.

None is classified as a public runtime-service repository by `policy/estate-registry.json`.

The final Wave 1B owner-authenticated scoreboard recorded all three as readable `default_branch_guard` failures: no active default-branch ruleset or classic pull-request guard was observed.

## Part 0 repository evidence

### atlas-gardener

Current repository state:

- default branch: `main`;
- current `main`: `319465dcea68a8fefead3e7d90e82b79078cb34d`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled.

Current `.github/workflows/ci.yml` defines the repository-native pull-request context:

- workflow: `CI`;
- job/context: `test`;
- GitHub Actions integration ID: `15368`.

The `test` job validates immutable Atlas Infra automation authority, target-readiness policy, repository tests, write-target scope, automatic controller modes, auto-merge refusal cases, shell syntax, and whitespace.

Current genuine Dependabot PR `atlas-gardener#22` provides exact-head automation compatibility evidence:

- state: open;
- mergeable: true;
- base: `main`;
- base SHA: `319465dcea68a8fefead3e7d90e82b79078cb34d`;
- head SHA: `5975733c5d4f05d66f957cb50a322905f7751d06`;
- `CI` run `30681523307`: success;
- native `test` job: success;
- `Dependabot review policy` run `30681523278`: success;
- `OpenSSF Scorecard` run `30681523274`: success;
- `CodeQL` run `30681523302`: success.

Gardener is not an ordinary library. Its scheduled controller can operate in `disabled`, `observe`, `pr-only`, or `automerge-low-risk` modes and has separately gated GitHub App write seams. Current source defaults mode and write gate to disabled, but repository variables can override those defaults. Therefore the provider inspection must capture the current non-secret values or absence of:

- `ATLAS_GARDENER_MODE`;
- `ATLAS_GARDENER_WRITE_GATE`;
- `ATLAS_GARDENER_WRITE_TARGETS_JSON`.

A branch guard on Gardener's own `main` must not be treated as authority to enable or alter its controller, GitHub App, target repository auto-merge, schedules, variables, secrets, or write scope.

### atlas-interface-kit

Current repository state:

- default branch: `main`;
- current `main`: `21a1a168e3b25e916555ce4edd4229bd7c061ecb`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled.

Current `.github/workflows/ci.yml` defines the repository-native pull-request context:

- workflow: `CI`;
- job/context: `Validate interface kit`;
- GitHub Actions integration ID: `15368`.

The gate compiles tooling, validates the deterministic bundle, runs unit tests, performs a release-artifact dry run, checks generated-file cleanliness, and checks whitespace.

There is no current open Dependabot pull request. Recent genuine Dependabot PR `atlas-interface-kit#11` merged successfully from exact head `ed0d59e6fa902854c50de61941a588128b471966` after CI, CodeQL, and OpenSSF Scorecard passed.

The current `0.5.0` owner change was validated on `atlas-interface-kit#14` at exact head `1f26360d938b589cf8a562ca308fd6ca3b4a2b3f` and merged as current `main` `21a1a168e3b25e916555ce4edd4229bd7c061ecb`. Its CI, CodeQL, Scorecard, deterministic rebuild, and release-artifact dry run all passed.

Release compatibility is explicit:

- source merge does not deploy a public interface;
- `.github/workflows/release.yml` runs on `v*` tags or explicit workflow dispatch against an existing tag;
- release validation is tag/version-bound and read-only apart from uploading the workflow artifact;
- creating a tag, publishing a GitHub Release, consumer adoption, and consumer production rollout remain separate owner-approved actions.

A default-branch branch ruleset therefore must not be represented as release publication evidence and must not alter tag or release authority.

### atlas-journey-watch

Current repository state:

- default branch: `main`;
- current `main`: `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- visibility: public;
- archived: false;
- repository auto-merge: **enabled**.

Current `.github/workflows/ci.yml` defines the repository-native pull-request context:

- workflow: `Pull request CI`;
- job/context: `Offline journey validation`;
- GitHub Actions integration ID: `15368`.

Current genuine Dependabot PR `atlas-journey-watch#12` provides exact-head automation compatibility evidence:

- state: open;
- mergeable: true;
- base: `main`;
- base SHA: `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- head SHA: `acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`;
- `Pull request CI` run `30681495858`: success;
- native `Offline journey validation` job: success;
- `Dependabot review policy` run `30681496052`: success;
- `OpenSSF Scorecard` run `30681495821`: success;
- `CodeQL` run `30681495823`: success.

Journey Watch contains a selective Dependabot auto-merge caller. The caller passes:

```text
automerge_enabled = vars.DEPENDABOT_AUTOMERGE_ENABLED == 'true'
```

into the pinned reusable Atlas Infra policy. The reusable policy can enable native squash auto-merge only when its fail-closed eligibility decision returns true, and can revoke a policy-created auto-merge request when eligibility later becomes false.

Repository-level auto-merge capability is currently enabled. The current value or absence of `DEPENDABOT_AUTOMERGE_ENABLED` is not exposed by the connected GitHub tool, so it must be captured through the owner-authenticated read-only inspection before any Journey Watch provider write is considered.

Journey Watch itself deploys nothing. Its scheduled journeys and release-watch workflow create assurance evidence and notifications; release-watch performs no deploy or rollback. Those facts do not remove the need to reconcile branch protection with selective Dependabot auto-merge.

## Wave split

Part 0 supports the following provisional split.

### Wave 2A candidates

- `AtlasReaper311/atlas-gardener` with required context `test`;
- `AtlasReaper311/atlas-interface-kit` with required context `Validate interface kit`.

Both currently have repository auto-merge disabled. They remain candidates, not approved provider writes, until the owner-authenticated Wave 2 inspection proves current provider state and Gardener controller-variable state.

### Wave 2B held pending automation-state evidence

- `AtlasReaper311/atlas-journey-watch` with required context `Offline journey validation`.

Journey Watch is held because repository auto-merge is enabled and the current non-secret `DEPENDABOT_AUTOMERGE_ENABLED` value is not yet observed. The inspection must establish whether selective auto-merge is active, inactive, or absent and whether the intended branch guard is compatible with that state.

No source plan may silently disable repository auto-merge. Changing that setting would be a separate provider mutation and requires explicit approval.

## Inspection-only operator

`scripts/github-provider-guard-wave-2-inspect.sh` is the only operator path authorised by this source stage.

It is read-only and pinned to:

- the three exact repositories above;
- their exact current `main` SHAs;
- the exact PR/check evidence listed above;
- the native contexts `test`, `Validate interface kit`, and `Offline journey validation`;
- GitHub Actions integration ID `15368`;
- current expected repository auto-merge values.

It collects and verifies:

- authenticated owner identity;
- repository identity, visibility, archival state, default branch, current `main`, and auto-merge capability;
- existing repository rulesets;
- classic `main` branch protection;
- exact PR and check-run evidence;
- current specialist workflow bytes;
- Gardener controller variables named above;
- Journey Watch `DEPENDABOT_AUTOMERGE_ENABLED` variable;
- SHA-256 evidence digests.

It does not read GitHub Actions secrets and must never request or print secret values.

The script contains no provider apply mode and no POST, PUT, PATCH, or DELETE GitHub API operation.

## Decision after inspection

After the owner-authenticated inspection archive is reviewed:

1. determine whether `atlas-gardener` is safe to enter Wave 2A without altering controller authority;
2. determine whether `atlas-interface-kit` is safe to enter Wave 2A without altering release authority;
3. determine the exact current Journey Watch selective auto-merge state;
4. prepare a separate fail-closed provider apply runner only for repositories that remain compatible;
5. merge that provider-apply source authority after exact-head validation;
6. request separate approval for the exact provider-write repository list;
7. perform provider writes one bounded wave at a time;
8. prove genuine automation compatibility and owner PR paths;
9. run a stamped owner-authenticated scoreboard;
10. close the wave through permanent receipts.

No provider-write approval is implied by approval to merge this inspection authority.

## Candidate ruleset shape

If later evidence supports a provider write, the candidate default pattern remains:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- pull request required;
- required approving reviews: `0`;
- required review-thread resolution: false;
- exact repository-native required status bound to GitHub Actions integration ID `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch-update policy disabled.

This shape is a candidate only. The inspection evidence must prove repository-specific compatibility before an apply runner is authored.

## Rollback boundary

No rollback is needed for this inspection-only stage because it performs no provider mutation.

Any later ruleset rollback remains a provider write and must receive separate approval. A rollback must identify only the affected ruleset ID from provider evidence and must preserve unrelated repository settings and automation state.

## Explicit boundaries

This stage does not:

- create, update, disable, or delete a ruleset;
- edit classic branch protection;
- enable or disable repository auto-merge;
- create, update, or delete an Actions variable;
- read or change an Actions secret;
- change Gardener controller mode, write gate, targets, GitHub App permissions, or schedule;
- enable or disable Journey Watch selective Dependabot auto-merge;
- merge a Dependabot pull request;
- create a release or tag;
- dispatch a workflow;
- deploy, restart, publish, or roll back anything;
- begin Wave 3 or any later wave.
