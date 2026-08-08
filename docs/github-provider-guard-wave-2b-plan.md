# GitHub provider guard wider rollout: Wave 2B plan

Status: Part 0 source inspection complete. Owner-authenticated provider reconciliation remains read-only and is not yet complete.

## Scope

Wave 2B is limited to `AtlasReaper311/atlas-journey-watch`.

Wave 2A is closed. Wave 3 and all later waves remain unstarted.

## Current source and policy evidence

Current GitHub source inspected on 2026-08-08 establishes:

- repository: `AtlasReaper311/atlas-journey-watch`;
- default branch: `main`;
- current `main`: `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- visibility: public;
- archived: false;
- repository auto-merge: enabled;
- ADR-0004 classification: active, public, original;
- native pull-request context: `Offline journey validation`;
- GitHub Actions integration ID used by the Atlas guard programme: `15368`.

Current genuine Dependabot evidence is PR `#12`:

- state: open;
- mergeable: true;
- base: `main` at `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- head: `acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`;
- `Offline journey validation`: completed successfully;
- Dependabot review policy: completed successfully;
- CodeQL: completed successfully;
- OpenSSF Scorecard: completed successfully.

The repository workflow `.github/workflows/dependabot-automerge.yml` calls the immutable reusable policy at `AtlasReaper311/atlas-infra/.github/workflows/dependabot-review.yml@8e6d08701823b02c4859bfc72af67fc8ace1f4b5` and passes:

`automerge_enabled: ${{ vars.DEPENDABOT_AUTOMERGE_ENABLED == 'true' }}`

That reusable workflow enables squash auto-merge only for policy-eligible Dependabot changes and revokes GitHub Actions-owned auto-merge when the change becomes ineligible.

## Last-observed provider state

The Wave 2 inspection and Wave 2A closeout last observed:

- repository auto-merge: enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED=true`;
- active ruleset ID: `19154613`;
- ruleset name: `Require native pull request validation`;
- target: branch;
- enforcement: active.

Those observations are navigation only. Wave 2B must re-read the provider state before deciding whether any mutation is necessary.

## Reconciliation question

Wave 2B is not a fresh ruleset-addition rollout. It must determine which of these outcomes current provider evidence supports:

1. the existing ruleset already satisfies the Atlas default-branch guard contract and only evidence/projection work is needed;
2. the existing ruleset needs a narrow in-place reconciliation while preserving selective Dependabot auto-merge;
3. an unexpected provider state requires a separate plan before any mutation.

Replacement, deletion, disablement, or creation of a second overlapping ruleset is not an assumed outcome.

## Read-only inspection authority

`scripts/github-provider-guard-wave-2b-inspect.sh` is inspection-only.

It pins the current repository and PR identities above and captures:

- repository settings;
- current `main` identity;
- all repository rulesets;
- full read-back of ruleset `19154613`;
- effective rules on `main`;
- classic branch-protection state;
- `DEPENDABOT_AUTOMERGE_ENABLED` without reading any secret;
- PR `#12` REST metadata and exact-head check runs;
- PR `#12` native auto-merge request state;
- current Journey Watch CI and Dependabot policy workflow bytes;
- the immutable reusable Dependabot workflow and its eligibility policy source.

The inspection writes evidence files locally only. It contains no GitHub provider mutation, variable write, PR merge, workflow dispatch, release, deployment, or rollback path.

## Decision gate after inspection

After the owner-authenticated evidence archive is reviewed, Atlas must receive an exact reconciliation proposal identifying:

- whether ruleset `19154613` changes at all;
- if so, the exact before/after semantic diff;
- how selective Dependabot auto-merge remains bounded;
- whether repository auto-merge or `DEPENDABOT_AUTOMERGE_ENABLED` changes at all;
- the exact provider endpoint and method, if any;
- owner and genuine Dependabot validation paths;
- scoreboard closure criteria.

Any provider mutation requires a new explicit approval after that proposal. Merging this inspection authority is not provider-write approval.

## Explicit boundaries

This stage does not:

- create, update, disable, replace, or delete ruleset `19154613`;
- create a second Journey Watch ruleset;
- change repository auto-merge;
- change `DEPENDABOT_AUTOMERGE_ENABLED`;
- merge Dependabot PR `#12`;
- change Journey Watch source, release behavior, schedules, secrets, or runtime configuration;
- dispatch workflows;
- deploy or publish anything;
- begin Wave 3 or any later wave.
