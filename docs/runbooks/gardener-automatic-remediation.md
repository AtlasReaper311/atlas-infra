# Atlas Gardener automatic remediation

Use this runbook when the automatic remediation controller opens an unexpected pull request, refuses eligible work, reports stale evidence, or must be stopped immediately.

## Immediate stop

Set the `ATLAS_GARDENER_WRITE_GATE` repository variable in `AtlasReaper311/atlas-gardener` to any value other than `enabled`, preferably `disabled`. The controller must refuse token minting and target writes before it evaluates a Finding bundle. Do not delete the GitHub App or rotate its key as the first response unless credential compromise is suspected.

Then set `ATLAS_GARDENER_MODE=disabled`. Disable the scheduled controller workflow only when the workflow itself is causing repeated failures; disabled mode should continue producing bounded evidence that the kill switch is active.

## Triage

Review the latest controller evidence artifact and identify:

- controller run ID and mode;
- policy, coverage, and Finding bundle digests;
- Finding fingerprint, remediation disposition, and remediation key;
- repository, base SHA, expected head SHA, and patch digest;
- structured remediation candidate kind for dependency or container work;
- for npm graph work, exact manifest/lock paths, pinned npm version, target digests, direct/transitive operations, parent constraints, and vulnerability IDs;
- refusal code, observation reason, or pull-request URL;
- installation-token mint and revoke status without token values;
- target-gate, CI, merge, and notification outcomes.

Treat any private key, JWT, installation token, notification token, or secret value exposed in logs, artifacts, issues, pull requests, or chat as compromised. Revoke or replace it through the provider interface and do not paste it into a remediation record.

## Dependency and container proposals

`npm-security-update`, `npm-lock-security-remediation`, `python-security-pin`, and `container-digest-pin` are review-required fixers. They may create deterministic draft pull requests, but they are not authorised for native automatic merge.

For a direct dependency proposal, confirm that the Finding candidate identifies a direct dependency, the source file matches the fixer-specific policy boundary, the selected target version is a patch or minor update within the current major version, and every vulnerability identifier recorded by the candidate is represented in the audit evidence.

For an npm graph proposal, additionally confirm all of the following:

- the candidate binds exactly one `package.json` and matching lockfile-v3 `package-lock.json` from the audited snapshot;
- the npm toolchain version is explicit and identical between producer and controller regeneration;
- lifecycle scripts are disabled during regeneration;
- every direct update matches one unique existing manifest declaration and remains in the current major version;
- every transitive update identifies one exact lock node and records every parent package path/specifier constraining that node;
- every recorded parent range accepts the selected transitive target;
- no direct dependency or npm `overrides` entry was invented merely to force a transitive version;
- changed paths are confined to the candidate manifest/lock pair and manifest edits exactly match the structured direct-update list;
- regenerated manifest and lock digests exactly match the candidate target digests;
- the bounded post-regeneration vulnerability check no longer reports every vulnerability ID claimed by the candidate.

If any of those checks cannot be reproduced from the exact base snapshot, refuse the proposal. A package version changing is not proof that a vulnerability is remediated.

For a container proposal, confirm that the candidate binds one external Docker Hub tag to one immutable `sha256` digest and that the Dockerfile change preserves the original tag while adding the digest. Named build stages, already digest-pinned bases, unsupported registries, and ambiguous references must not be rewritten.

For non-actionable dependency/container Findings, require a specific disposition rather than treating every result as a generic observation:

- `awaiting-upstream-release` when upstream source evidence exists but the acceptable package release is not yet published;
- `awaiting-upstream-fix` when no released non-affected target exists;
- `manual-remediation-required` when a real remediation exists outside deterministic Gardener authority;
- `unsupported-remediation` when the source, graph, package form, or registry is outside current authority.

`remediation-available` must correspond to an eligible structured candidate. Do not reinterpret a non-actionable disposition as write authority.

Major upgrades, missing or contradictory fixed-version evidence, ambiguous declarations, unsupported Python package formats, unsupported npm graph forms, non-deterministic lockfile changes, package-manager lifecycle execution, and parent-range conflicts must remain non-actionable or fail closed.

Do not treat a passing pull request as deployment evidence. Dependency and container changes can affect runtime behaviour, so merge, deployment, and live verification remain separate authority and evidence steps.

## Unexpected pull request

Confirm that the head branch begins with `gardener/`, the pull-request body contains the machine approval marker, and the exact head SHA matches the controller evidence. Confirm that every changed file matches the selected fixer's `allowed_path_patterns` from the committed Atlas Infra authority. For npm graph proposals, confirm the exact manifest/lock pair and target digests agree with the controller evidence. Disable native auto-merge on the pull request before further inspection. Close the pull request if the approval, patch, actor, repository classification, base SHA, policy digest, structured candidate, fixer path boundary, regenerated dependency graph, or vulnerability postcondition does not match.

Do not force-push or reuse an owner-authored branch. Gardener branches are deterministic per repository, rule, Finding fingerprint, fixer version, and target base state.

## Closed obsolete Gardener proposal

A closed, unmerged Gardener pull request is not automatically reusable. Inspect its signed approval marker and compare its plan digest and patch digest with the current deterministic plan for the same remediation key.

- If the closed pull request binds the exact current plan and patch, treat the closure as deliberate owner intent. Do not reopen it and do not create another pull request for that exact plan.
- If the closed pull request binds an obsolete plan or patch while the remediation key and exact target base are unchanged, Gardener may create one replacement draft using the ADR-0016 replacement branch form `gardener/<fixer-id>-<first-12-key-hex>-r-<first-12-patch-hex>`.
- Leave the obsolete pull request and branch unchanged. Never force-push, delete, reopen, or retarget them.
- Recompute the replacement plan digest after selecting the replacement branch and require the new approval marker to bind the current plan digest, patch digest, exact base SHA, and expected head SHA.
- If the replacement branch already has an exact open pull request, treat it as idempotent. If it has an exact merged pull request, treat it as already remediated. If it has an exact closed-unmerged pull request, respect that closure. Any conflicting approval, duplicate pull request, unexplained branch, or mismatched open/merged proposal must fail closed.

This recovery path does not expand automatic merge. Dependency and container replacements remain review-required draft pull requests.

## Unexpected merge

Disable the write gate and controller mode before reverting. Revert the squash merge through a reviewed pull request in the target repository. Do not edit the default branch directly. Record the original remediation key, merge commit, revert pull request, cause, and policy change required to prevent recurrence.

## Credential compromise

Disable the write gate, replace the GitHub App private key, remove affected repositories from the selected-repository installation when containment requires it, and review all Gardener-authored branches and pull requests created after the suspected compromise time. The App permission boundary must remain Metadata read, Contents write, and Pull requests write. Any permission expansion requires a separate accepted ADR and owner approval.

## Verified autonomous canary

The first complete autonomous canary was verified on 22 July 2026 against `AtlasReaper311/atlas-dora`.

Evidence:

- attested audit run: `AtlasReaper311/atlas-dep-audit` run `29962518596`;
- controller run: `AtlasReaper311/atlas-gardener` run `29962590660`;
- target pull request: `AtlasReaper311/atlas-dora#30`;
- reviewed head: `2d24e6450f45869835c9694b940018bb5b54a48b`;
- target gate run: `29964113312`;
- automatic squash merge: `542e1647698c07e1fcdc83d84b4b508298f071d1`;
- exact result: one `.DS_Store` addition to `.gitignore`;
- final safety state: controller mode disabled, write gate disabled, write targets empty, audit handoff disabled, target auto-merge variable false, and repository native auto-merge false.

The target gate and independent native auto-merge barrier both completed successfully. The refusal cleanup step was skipped, and GitHub merged the exact Gardener App proposal without a manual merge action.

## Verified bounded production proof

The first bounded batch-one `automerge-low-risk` proof was verified on 23 July 2026 against `AtlasReaper311/specular-sonify`.

Evidence:

- controller run: `AtlasReaper311/atlas-gardener` run `29972373628`;
- target pull request: `AtlasReaper311/specular-sonify#9`;
- reviewed head: `2daa1b41a2aa832dba1e8260cc8febac32d8d3d9`;
- target gate run: `29972390426`;
- automatic squash merge: `33ebfca292c6a099f3face8b04f244942d19f2dc`;
- exact result: a blank separator and `.DS_Store` added to `.gitignore`;
- deployment classification: `not-applicable`, because the repository has no push-to-main deployment workflow and the patch changes no runtime source or configuration;
- final safety state: controller mode disabled, write gate disabled, write targets empty, audit handoff disabled, target auto-merge variable false, and repository native auto-merge false.

The proof exposed three permanent verification requirements: bind jobs to the exact Actions `run_attempt`, accept both authority-approved `.DS_Store` patch forms, and classify deployment evidence rather than assuming every merge deploys.

## ADR-0015 remediation proof and ADR-0016 correction

The first ADR-0015 live dependency/container execution on 10 September 2026 produced two bounded container-digest draft pull requests and fifteen dependency observations from seventeen Findings. It proved the write path but exposed insufficient dependency coverage and an Atlas Dep Audit OSV enrichment defect. The exact replay and corrected design target are recorded in `docs/gardener-remediation-coverage-2026-09-10.md`.

ADR-0016 does not retroactively classify those fifteen dependency observations as eligible. Producer correctness, exact graph regeneration, parent-range checks, target digest binding, and vulnerability postconditions must all pass before a fresh Finding may become `remediation-available`.

## Production readiness

Before enabling a target batch, run the committed source-policy validator and the read-only target-readiness verifier. Every target used for automatic housekeeping merge must have:

- the pinned target-owned Gardener caller;
- its declared repository CI check required on `main`;
- `Gardener native auto-merge barrier` required on `main`;
- squash merge enabled;
- repository native auto-merge disabled at rest;
- `ATLAS_GARDENER_AUTOMERGE_ENABLED=false` at rest.

All four dependency and container fixers remain draft-PR-only even when the controller mode is `automerge-low-risk`. Automatic merge for those fixers requires a later accepted authority change and a target-gate implementation capable of revalidating their complete output. ADR-0016 does not grant that authority.

The scheduled production cadence is Monday audit ingestion at `08:41 UTC`, followed by controller reconciliation at `10:15 UTC`. Manual dispatch remains available. Do not enable a daily controller against a thirty-six-hour Finding lifetime.

## Recovery

Restore service in stages:

1. validate source with mode `disabled`;
2. run `observe` and inspect one complete evidence artifact, including dispositions;
3. for npm graph work, reproduce one candidate independently against its exact base without any target write;
4. run `pr-only` against one eligible dependency or container Finding and inspect the exact draft;
5. verify repository-native CI against the exact draft head;
6. retain manual review for dependency and container proposals;
7. use `automerge-low-risk` only for the separately authorised housekeeping boundary.

A merged source change, successful dry run, target workflow installation, or enabled repository setting does not prove live automatic operation. Live completion for dependency and container remediation requires one real eligible Finding, deterministic pull-request creation, repository-native validation, an owner-authorised merge, explicit deployment classification, and live verification where deployment occurs.
