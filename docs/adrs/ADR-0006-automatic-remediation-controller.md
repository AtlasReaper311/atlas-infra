+++
id = "ADR-0006"
date = 2026-07-22
status = "accepted"
visibility = "public"
repositories = []
services = []
contracts = ["atlas-control-plane/gardener-automation-approval/v1", "atlas-control-plane/gardener-finding-bundle/v1"]
policies = ["policy/gardener-automation.json", "policy/gardener-github-app-coverage.json", "policy/gardener-target-readiness.json"]
+++

# ADR-0006: automatic remediation separates detection, proposal writes, and merge authority

## Context

Atlas Gardener can already turn one validated Finding into one deterministic proposal, exact commit, branch, and draft pull request through a selected-repository GitHub App. That path is deliberately owner-run: a local operator supplies a reviewed digest, confirms an interactive prompt, and supplies a short-lived installation token. Atlas Dep Audit runs the weekly public assurance scan, but its report is not a canonical authenticated Finding handoff and it does not emit the low-risk housekeeping rules required for an initial automatic canary.

Removing the prompt without replacing it would convert an operator safeguard into an unauthenticated write path. Giving the central App merge, Actions, Checks, Administration, workflow-dispatch, settings, or deployment authority would combine proposal generation and final repository authority in one credential. Treating audit findings as executable instructions would also create a command-injection boundary.

## Decision

Atlas Infra owns a closed automatic-remediation policy, Finding bundle contract, automation approval contract, risk tiers, fixer-to-mode rules, public coverage dependency, path limits, expiry, evidence retention, notification cooldown, and rollout defaults.

Atlas Dep Audit remains the producer. It emits an attested public-only Finding bundle containing data, never commands. The bundle records its producer workflow, run identity, source commit, Atlas Infra authority commit, exact repository base snapshots, expiry, canonical Finding fingerprints, source report digest, policy digest, and bundle digest. Private findings remain in their authenticated source repository and are never copied into the public handoff.

Atlas Gardener remains the controller and GitHub App token broker. A non-interactive write requires an AutomationApproval bound to the policy digest, coverage digest, bundle digest, Finding fingerprint, proposal ID, plan digest, fixer ID and version, repository classification, exact base commit, expected head commit, exact files, patch digest, risk class, controller mode, source run, controller run, and expiry. Any mismatch fails closed. The existing manual CLI retains interactive confirmation.

The GitHub App permission boundary remains Metadata read, Contents write, and Pull requests write in selected-repository mode. The App creates exact Gardener pull requests but does not own the final merge decision.

Automatic merge is target-owned. A pinned reusable workflow runs with the target repository's ephemeral GITHUB_TOKEN, revalidates the approval and pull-request state, and enables GitHub native squash auto-merge only for exact approved low-risk `.gitignore` additions. Initial automatic merge permits only `macos-metadata-ignore` and `python-cache-ignore` when the complete patch changes one normal `.gitignore` file, adds no more than two allowlisted lines, deletes nothing, changes no existing line, and preserves exact base, head, and patch identities. Workflow, application source, dependency, lockfile, deployment, infrastructure, credential-like, binary, symlink, generated-output, unknown, stale, archived, deprecated, experimental, external-derived, unclassified, or out-of-coverage changes remain review-only or refused.

Source defaults to `disabled`. Runtime mode is the intersection of committed policy, the exact `ATLAS_GARDENER_MODE` repository variable, and the independent `ATLAS_GARDENER_WRITE_GATE=enabled` kill-switch gate. Unknown or missing values refuse writes.

Production scheduling follows the evidence lifetime. The public audit runs on Monday at `08:41 UTC` and the controller reconciles the resulting attested bundle on Monday at `10:15 UTC`. Manual dispatch remains available. A daily controller is not approved while Finding bundles expire after thirty-six hours because it would spend most of the week refusing stale evidence.

A repository is not production-ready merely because the target-owned caller exists. The default branch must require both its declared repository CI and `Gardener native auto-merge barrier`; squash merge must be available; repository native auto-merge and `ATLAS_GARDENER_AUTOMERGE_ENABLED` must be disabled at rest. The committed target-readiness policy declares the first bounded batch and its exact required checks. Provider configuration remains a separate owner-approved action.

Completed-rollout evidence must bind workflow jobs to the exact `run_attempt`. Deployment evidence is classified separately as `automatic`, `manual`, or `not-applicable`; a source-only housekeeping merge must not be reported as a deployment failure when the target has no push deployment contract.

## Consequences

Routine public housekeeping can proceed from scheduled detection to validated proposal, repository CI, native auto-merge, evidence, and notification without a local machine or per-PR confirmation. Higher-risk changes remain visible without being silently reported healthy.

The architecture adds target-owned workflow callers and requires GitHub native auto-merge to be enabled as a separate rollout action. It does not require a GitHub App permission expansion. A compromised Gardener workflow could still use the App's existing content and pull-request rights on selected repositories, so repository-restricted one-operation tokens, exact endpoint allowlists, short expiry, attested inputs, digest binding, concurrency, evidence, and the independent write gate remain mandatory.

Merging source does not enable live operation. Secrets, repository variables, auto-merge settings, branch protection, target workflow adoption, scheduling, canaries, and mode transitions remain separate owner-approved rollout actions.
