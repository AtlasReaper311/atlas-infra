# Atlas Gardener automatic remediation

Use this runbook when the automatic remediation controller opens an unexpected pull request, refuses eligible work, reports stale evidence, or must be stopped immediately.

## Immediate stop

Set the `ATLAS_GARDENER_WRITE_GATE` repository variable in `AtlasReaper311/atlas-gardener` to any value other than `enabled`, preferably `disabled`. The controller must refuse token minting and target writes before it evaluates a Finding bundle. Do not delete the GitHub App or rotate its key as the first response unless credential compromise is suspected.

Then set `ATLAS_GARDENER_MODE=disabled`. Disable the scheduled controller workflow only when the workflow itself is causing repeated failures; disabled mode should continue producing bounded evidence that the kill switch is active.

## Triage

Review the latest controller evidence artifact and identify:

- controller run ID and mode;
- policy, coverage, and Finding bundle digests;
- Finding fingerprint and remediation key;
- repository, base SHA, expected head SHA, and patch digest;
- refusal code or pull-request URL;
- installation-token mint and revoke status without token values;
- target-gate, CI, merge, and notification outcomes.

Treat any private key, JWT, installation token, notification token, or secret value exposed in logs, artifacts, issues, pull requests, or chat as compromised. Revoke or replace it through the provider interface and do not paste it into a remediation record.

## Unexpected pull request

Confirm that the head branch begins with `gardener/`, the pull-request body contains the machine approval marker, and the exact head SHA matches the controller evidence. Disable native auto-merge on the pull request before further inspection. Close the pull request if the approval, patch, actor, repository classification, base SHA, or policy digest does not match.

Do not force-push or reuse an owner-authored branch. Gardener branches are deterministic per repository, rule, Finding fingerprint, fixer version, and target base state.

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

This proves the GitHub control path from attested Finding through controller approval, App-authored pull request, repository CI, target-owned validation, native auto-merge, exact merge result, and disabled cleanup. It does not prove a deployment, live service health, notification delivery, or any non-GitHub provider state.

Future canaries must use the structured verifier in `AtlasReaper311/atlas-gardener` rather than matching exact strings in aggregated workflow logs.

## Recovery

Restore service in stages:

1. validate source with mode `disabled`;
2. run `observe` and inspect one complete evidence artifact;
3. run `pr-only` against one harmless eligible Finding;
4. enable `automerge-low-risk` for the canary repository;
5. expand to a limited repository batch;
6. expand to the verified 20-repository public runtime set.

A merged source change, successful dry run, target workflow installation, or enabled repository setting does not prove live automatic operation. Live completion requires one real eligible Finding, automatic pull-request creation, required target CI, automatic squash merge, result notification, and bounded evidence.
