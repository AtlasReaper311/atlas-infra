+++
id = "ADR-0015"
date = 2026-09-10
status = "accepted"
visibility = "public"
supersedes = "ADR-0006"
repositories = []
services = []
contracts = ["atlas-control-plane/gardener-automation-approval/v1", "atlas-control-plane/gardener-finding-bundle/v1"]
policies = ["policy/gardener-automation.json", "policy/gardener-github-app-coverage.json", "policy/gardener-target-readiness.json"]
+++

# ADR-0015: Gardener adds bounded dependency and container remediation

## Context

ADR-0006 established the scheduled Atlas Gardener control plane with an attested public Finding bundle, exact repository snapshots, selected-repository GitHub App credentials, deterministic proposals, target-owned merge authority, and a default-disabled rollout. Its first automatic boundary intentionally permitted only tiny `.gitignore` housekeeping changes.

A live manual execution on 10 September 2026 proved that the corrected audit-to-controller path could validate and classify a fresh bundle without refusals, but all seventeen current findings were non-actionable. The dominant findings were dependency vulnerabilities and container base images without immutable digests. The controller therefore behaved correctly while providing no remediation for the work the assurance producer was actually detecting.

Expanding Gardener by treating audit prose as commands or by granting broad file authority would defeat the control-plane design. Dependency and container remediation instead needs structured candidate data, fixer-specific path constraints, exact source snapshots, deterministic regeneration, and a staged merge boundary.

## Decision

The separation of authority from ADR-0006 remains in force. Atlas Infra owns the closed policy and contracts. Atlas Dep Audit remains the attested public-only producer. Atlas Gardener remains the controller and repository-restricted GitHub App token broker. Target repositories remain responsible for repository CI and any final automatic merge. Provider and deployment authority remain separate.

The Finding contract may carry an optional structured `remediation.candidate`. Candidate data is bounded evidence, not a command. Supported candidate kinds are:

- `dependency-update`, containing ecosystem, direct dependency identity, current version, target version, source file, update class, and the vulnerability identifiers the target addresses;
- `container-digest-pin`, containing the source file, current external image reference, and resolved immutable `sha256` digest.

A dependency candidate is eligible only when Atlas Dep Audit can prove all of the following from the exact scanned repository snapshot:

- the dependency is a direct dependency;
- the current and target versions are parseable three-part versions;
- the target version is strictly newer;
- the update does not cross a major-version boundary;
- at least one affected vulnerability has a published fixed version at or below the selected target;
- the supported source is either an npm `package.json` plus matching `package-lock.json`, or an exact Python pin in `requirements.txt`;
- the candidate is emitted as structured data and can be regenerated from the exact snapshot.

Transitive-only npm vulnerabilities, major upgrades, unresolved fixed versions, unsupported Python packaging formats, ambiguous dependency declarations, and non-deterministic update plans remain observations.

Container digest candidates are limited initially to externally resolvable Docker Hub image tags in Dockerfiles. Named build stages and already digest-pinned images are not findings. Atlas Dep Audit resolves the immutable registry digest and records it as candidate evidence. Unsupported registries, ambiguous references, failed registry resolution, or malformed Dockerfiles remain observations.

Atlas Gardener gains three deterministic fixers:

- `npm-security-update`;
- `python-security-pin`;
- `container-digest-pin`.

Each fixer is constrained by an exact allowlisted path pattern in `policy/gardener-automation.json`. The controller must validate every planned file against the selected fixer's path patterns before minting a repository token or publishing a pull request. The existing sensitive-path and repository-classification controls remain in force.

The new fixers are review-required and `pr-only` at this stage. They may create deterministic draft pull requests when the controller is in `pr-only` or `automerge-low-risk`, but they are not eligible for native automatic merge. The only automatically mergeable fixers remain `macos-metadata-ignore` and `python-cache-ignore` within the existing one-file, two-line `.gitignore` boundary.

Automatic merge for dependency updates requires a separate later authority change and a target-gate revision that can revalidate manifest and lockfile bytes, exact required checks, and the resulting dependency graph. It must not be enabled merely because deterministic dependency PR creation works.

The GitHub App permission boundary remains Metadata read, Contents write, and Pull requests write in selected-repository mode. No Actions, Checks, Administration, workflow-dispatch, deployment, secret, or settings permission is added.

The production schedule remains the Monday public audit at `08:41 UTC` followed by Gardener reconciliation at `10:15 UTC`. Finding bundles remain valid for thirty-six hours. Manual dispatch remains available for separately authorised verification.

## Consequences

Gardener can progress from observing dependency and container findings to producing bounded, reviewable remediation pull requests without expanding its provider permissions or conflating source remediation with deployment.

Dependency and container changes can affect runtime behaviour, so they receive a stricter initial boundary than housekeeping. A successful Gardener PR does not prove that a deployment occurred or that a deployed service is healthy.

The extra structured candidate data and fixer-specific path validation increase implementation and test complexity. That cost is deliberate because it keeps audit text inert and prevents one fixer from inheriting another fixer's path authority.

ADR-0006 is superseded by this record. Its evidence-binding, credential, scheduling, target-ownership, and fail-closed principles remain unless this record explicitly changes them.
