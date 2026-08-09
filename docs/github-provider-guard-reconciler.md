# GitHub provider guard reconciler

Status: source design for maintaining the Atlas default-branch guard after the completed provider-guard rollout. Provider activation remains separate from source merge.

## Purpose

The reconciler turns `default_branch_guard` from a point-in-time estate correction into a maintained governance invariant for repositories admitted to the public Atlas classification authority.

It reads only:

- `policy/public-repository-classifications.json`, the deterministic ADR-0004 projection; and
- `policy/github-conformance-requirements.json`, which decides whether `default_branch_guard` is required for a projected repository.

It does not discover repositories from account membership or visibility. A repository becomes eligible only after Atlas Infra governance admits it to the projection.

## Create-only contract

`scripts/github_provider_guard_reconcile.py` is inspect-only by default.

For each projected repository where `default_branch_guard` is currently required, it inspects:

- repository metadata and default branch;
- repository rulesets and ruleset details;
- classic default-branch protection; and
- effective rules on the default branch.

The reconciler takes one of four read-only decisions:

- `compliant`: an active ruleset or classic pull-request guard already satisfies the Atlas requirement;
- `create`: the repository has no ruleset, no classic protection, and no effective default-branch rule;
- `blocked`: provider state is unreadable, archived/private drift is present, or an existing protection mechanism would require migration or reconciliation;
- `skipped`: current conformance policy does not require `default_branch_guard` for the repository.

Apply mode performs a full estate preflight before the first write. Any `blocked` repository prevents all writes.

For `create` repositories, apply mode may create exactly one active repository ruleset named `Atlas default branch PR guard` with:

- target `branch`;
- selector `~DEFAULT_BRANCH`;
- no bypass actors;
- deletion protection;
- non-fast-forward protection; and
- pull-request requirement with zero approvals, no code-owner requirement, no last-push approval requirement, no stale-review dismissal, and no required review-thread resolution.

The reconciler immediately reads the created ruleset and effective default-branch rules back and fails if the result differs from that contract.

It never:

- updates or deletes a ruleset;
- changes classic branch protection;
- changes repository settings, Actions permissions, variables, or secrets;
- invents or adds a required status context;
- changes repository auto-merge;
- merges or closes pull requests;
- dispatches another workflow;
- creates a release;
- deploys or publishes anything.

Existing stronger rulesets, including current native required-status checks, are left untouched.

## Why baseline guards do not invent CI requirements

A newly governed repository may not yet have a successful native CI context. Requiring an assumed check name can deadlock the first protected pull request.

The day-zero invariant is therefore the three-rule baseline guard: pull requests, deletion protection, and non-fast-forward protection. Native required-status checks remain an explicit evidence-backed strengthening step once a real repository-owned check has been observed. Existing status requirements are preserved because the reconciler never updates an existing ruleset.

## Workflow

`.github/workflows/github-provider-guard-reconcile.yml` runs a read-only inspection daily and on manual dispatch.

Provider writes are disabled unless repository variable:

`ATLAS_PROVIDER_GUARD_RECONCILE_ENABLED=true`

is present.

A manual dispatch with `apply=false` is always inspection-only. A manual dispatch with `apply=true` can write only when the provider gate variable is also enabled. Scheduled runs can write only while the same variable is enabled.

The apply job mints a short-lived GitHub App installation token, runs the create-only reconciler, then runs a second inspection and requires zero remaining `create` or `blocked` outcomes. JSON evidence is retained as a workflow artifact.

## Dedicated provider identity

The built-in workflow `GITHUB_TOKEN` is not the provider-write identity. Creating repository rulesets requires repository Administration write permission, and the existing Atlas Gardener App deliberately excludes Administration.

Use a separate GitHub App dedicated to this reconciler. Do not widen Atlas Gardener.

Required GitHub App repository permission:

- Administration: read and write.

No webhook is required. The App must not request Contents write, Pull requests write, Actions write, Secrets, Variables, Deployments, or other unrelated mutation permissions.

For automatic coverage of future Atlas repositories, install the dedicated App on the `AtlasReaper311` personal account with **All repositories**. Each workflow run then mints an installation token scoped down to the repository names in the current Atlas Infra projection, so the active token does not receive an unbounded all-repository target. The reconciler still writes only to projected identities requiring `default_branch_guard`.

Configure only these Atlas Infra workflow inputs:

- repository variable `ATLAS_PROVIDER_GUARD_APP_CLIENT_ID` containing the App client ID;
- repository secret `ATLAS_PROVIDER_GUARD_APP_PRIVATE_KEY` containing the App private key; and
- repository variable `ATLAS_PROVIDER_GUARD_RECONCILE_ENABLED`, initially `false` and changed to `true` only at the separate rollout gate.

Never place the private key in source, shell history, logs, issue text, pull requests, or chat.

## New-repository lifecycle

The intended path is:

1. create and initialise a repository;
2. classify it in the appropriate ADR-0004 Atlas Infra authority input;
3. regenerate and merge `public-repository-classifications.json`;
4. the reconciler observes the newly governed repository;
5. if the repository has no protection mechanism, the reconciler creates the baseline guard;
6. the reconciler reads the provider state back and records evidence;
7. repository-native CI may later be added as a separately evidenced required-status strengthening.

Classification remains the admission gate. Account membership alone never authorises a provider write.

## Failure handling

If inspection reports `blocked`, do not broaden the reconciler. Inspect the repository-specific provider state and prepare a separate migration or reconciliation plan.

If a create request fails after an earlier repository was successfully protected, keep the successfully created additive guard. Do not automatically delete it. Begin recovery from a fresh inspection.

If the dedicated App is suspended, uninstalled, loses Administration write, or its credentials are unavailable, the inspect job remains useful but the apply job must fail or skip rather than falling back to another credential.
