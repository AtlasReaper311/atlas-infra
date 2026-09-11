+++
id = "ADR-0016"
date = 2026-09-11
status = "accepted"
visibility = "public"
supersedes = "ADR-0015"
repositories = []
services = []
contracts = ["atlas-control-plane/gardener-automation-approval/v1", "atlas-control-plane/gardener-finding-bundle/v1"]
policies = ["policy/gardener-automation.json", "policy/gardener-github-app-coverage.json", "policy/gardener-target-readiness.json"]
+++

# ADR-0016: Gardener adds bounded npm graph remediation and explicit dispositions

## Context

ADR-0015 added safe direct dependency and container remediation after an earlier live controller run found seventeen non-actionable Findings. Its first live remediation proof on 10 September 2026 validated the end-to-end authority path but produced only two actionable container-digest proposals from seventeen current Findings. Fifteen dependency Findings remained observations.

The exact replay is recorded in `docs/gardener-remediation-coverage-2026-09-10.md`. It exposed two distinct problems.

First, Atlas Dep Audit used OSV `/v1/querybatch` entries as if they were complete vulnerability records. The resulting 52 vulnerability rows all reported unknown severity and no fixed version even where authoritative advisory records contain those fields. Producer correctness must be repaired before expanded remediation consumes fixed-version evidence.

Second, the npm vulnerabilities in the exact replay are transitive. Twelve source Findings include `sharp 0.35.2`, eight include `brace-expansion 5.0.7`, and seven contain both in the same lockfile. All twelve affected `sharp` repositories directly declare Wrangler, while `sharp` is introduced through Wrangler's Miniflare dependency. ADR-0015 intentionally required the vulnerable package itself to be direct, so it could not act on these graphs.

A safe response is not to make every observation eligible. Gardener needs a bounded graph-level candidate that can express an exact direct-parent update, an exact transitive lock target, or both, and then prove by deterministic regeneration that the claimed vulnerabilities disappear. Findings without a released non-affected target need a precise non-actionable disposition rather than a generic observation.

## Decision

ADR-0015 is superseded by this record. Its public-only attestation, exact snapshot, selected-repository GitHub App, repository classification, path authority, draft-PR dependency boundary, and housekeeping-only automatic merge rules remain in force unless explicitly changed here.

### Producer correctness gate

Atlas Dep Audit must hydrate OSV batch IDs to complete vulnerability records before severity or fixed-version data is used for remediation eligibility. It must follow OSV pagination, select the affected package/range corresponding to the exact scanned component, and treat `last_affected` without a published later non-affected release as no available fixed version.

A Gardener dependency candidate derived from shallow batch metadata is invalid.

### Explicit remediation dispositions

The Finding `remediation` object may carry an optional structured `disposition`. Atlas Dep Audit must populate it for dependency and container Findings produced by this programme.

The approved values are:

- `remediation-available`: a structured candidate is present and has passed the producer-side deterministic proof required by its class;
- `awaiting-upstream-release`: upstream source evidence identifies a remediation that has not yet been published as an acceptable package release;
- `awaiting-upstream-fix`: current authoritative advisory/package evidence exposes no released non-affected target;
- `manual-remediation-required`: remediation exists but is outside the deterministic Gardener boundary;
- `unsupported-remediation`: the packaging, registry, graph, or source form is outside current authority.

A disposition is evidence classification, not mutation authority. `remediation.eligible` remains the write eligibility gate.

### npm graph remediation candidate

The Finding and RemediationProposal contracts gain the `npm-lock-security-remediation` candidate kind. One candidate represents one exact npm manifest/lock graph and may contain both direct-parent and transitive operations so Gardener does not open competing pull requests against the same `package-lock.json` snapshot.

The candidate is limited to an exact `package.json` and matching lockfile-v3 `package-lock.json`. It carries:

- the manifest and lockfile paths;
- the exact npm version used for regeneration;
- zero or more direct dependency updates with dependency identity, manifest section, current/target versions, current/target manifest specs, and the vulnerability IDs associated with that operation;
- zero or more transitive dependency targets with dependency identity, exact lock-node path, current/target versions, every discovered parent package path/specifier constraining the target, and the vulnerability IDs associated with that operation;
- the complete vulnerability identifier set the regenerated graph proves absent;
- the expected target manifest and lockfile SHA-256 digests.

At least one direct or transitive operation is required.

A direct-parent operation is eligible only when:

- the dependency is uniquely declared in `dependencies`, `devDependencies`, or `optionalDependencies`;
- the installed direct version and declaration match the exact audited snapshot;
- the target is a released strict three-part version that is newer but remains in the same major version;
- producer regeneration proves the target graph removes at least one vulnerability identified by the Finding.

A transitive operation is eligible only when:

- the exact vulnerable lock node is uniquely identified;
- the target is a released strict three-part version that is newer and remains in the same major version;
- every dependency edge in the exact lock graph that constrains the target accepts that exact target version;
- no package manifest declaration or npm override is invented solely to force the target;
- producer regeneration proves the target graph removes the claimed vulnerability identifiers.

### Deterministic npm regeneration

Producer and controller implementations must use the same pinned npm toolchain and a repository-isolated disposable checkout. Npm lifecycle scripts must be disabled. Network access is limited to package metadata required for lockfile resolution; no package lifecycle code may execute.

The producer may emit a graph candidate only when regeneration results in changes to the declared `package.json` and/or matching `package-lock.json` paths, the manifest changes exactly match the structured direct-update list, and the resulting digests match the candidate's target digests.

Atlas Gardener must independently regenerate the candidate from the exact base snapshot before publishing a pull request. Any difference in structured operations, changed path set, target digests, or post-regeneration vulnerability state fails closed.

The controller must rerun the bounded vulnerability check over the resulting graph and require every vulnerability ID claimed by the candidate to be absent. A version-string change alone is not sufficient proof.

### Fixer authority

Atlas Gardener gains one additional review-required fixer:

- `npm-lock-security-remediation`.

Its write boundary is limited to `package.json` and `package-lock.json` beneath the repository root. It may create deterministic draft pull requests in `pr-only` or `automerge-low-risk` mode when all existing repository/write gates also pass.

It is never automatically mergeable under this ADR. Existing `npm-security-update`, `python-security-pin`, and `container-digest-pin` also remain review-required. `macos-metadata-ignore` and `python-cache-ignore` remain the only automatically mergeable fixers.

### Closed-unmerged proposal replacement

The remediation key remains the stable semantic identity for one repository, rule, Finding fingerprint, fixer version, and exact target base SHA. It does not change merely because the deterministic implementation of the reviewed patch is corrected.

The primary Gardener branch derived from that remediation key remains authoritative for the first proposal. Gardener may inspect pull requests on that branch but must not force-push, reopen, edit, delete, or otherwise reuse a closed proposal branch.

A matching open pull request is idempotent only when its signed approval marker binds the exact current plan digest and patch digest. A matching merged pull request is already remediated only under the same exact-plan and exact-patch condition. An open or merged pull request carrying the same remediation key but a different current plan or patch must fail closed.

A matching closed, unmerged pull request has two cases:

- when its approval marker binds the exact current plan and patch, Gardener must respect the owner closure and must not recreate the proposal;
- when its approval marker binds an obsolete plan or patch for the same remediation key, Gardener may create one replacement draft pull request on a new deterministic replacement branch.

The replacement branch must be derived only from the existing remediation key, fixer ID, and the current patch digest. Its branch name is `gardener/<fixer-id>-<first-12-key-hex>-r-<first-12-patch-hex>`. The replacement plan digest must be recomputed after that branch is selected, and the resulting approval must bind the replacement branch, current plan digest, current patch digest, exact base SHA, and expected head SHA.

If a replacement branch or pull request already exists, the same exact-state rules apply: an exact open proposal is idempotent, an exact merged proposal is already remediated, and an exact closed-unmerged proposal remains closed. Any conflicting state, duplicate matching pull request, unexplained branch, or approval mismatch fails closed.

This recovery path does not expand mutation or merge authority. Replacement dependency and container proposals remain review-required draft pull requests. Gardener gains no force-push, branch deletion, pull-request reopen/update, merge, Actions, Administration, or settings permission.

### Current replay decisions

The exact 10 September replay establishes the following design targets, not pre-authorised output:

- the two Docker tag Findings remain actionable under `container-digest-pin`;
- the thirteen npm source Findings may become one graph-remediation proposal per source only when exact regeneration proves the claimed vulnerability set absent;
- `sharp 0.35.2` has an upstream remediation path through the published Wrangler/Miniflare line containing `sharp 0.35.4`, but each Atlas repository still requires exact graph regeneration proof before candidate emission;
- `brace-expansion 5.0.7` has a patched 5.x target, but a lock-only operation is permitted only where every current parent constraint accepts it and post-regeneration evidence clears both current advisory IDs;
- the two ChromaDB source Findings remain `awaiting-upstream-fix` while the latest stable package release remains inside current advisory affected ranges.

The controller is therefore measured on complete evidence-backed accounting, not on fabricating a pull request for every Finding. For this replay the upper bound from current upstream evidence is fifteen remediation proposals and two explicit upstream-blocked dispositions. The exact count must be recomputed from every fresh audit snapshot.

## Consequences

Gardener can address security findings caused by an otherwise safe direct toolchain update or an already-permitted transitive lock target without granting arbitrary dependency mutation authority.

Mixed lockfiles can be handled as one deterministic source proposal instead of multiple conflicting Gardener branches. The post-regeneration vulnerability proof makes graph state, rather than a guessed package-name mapping, the acceptance criterion.

A deliberately closed proposal remains closed unless the reviewed deterministic patch itself changes. A corrected patch may be proposed exactly once on a replacement branch without mutating or reusing the obsolete branch, preserving both owner intent and auditable history.

The controller gains a tightly bounded package-manager execution path. That raises implementation complexity and requires strong regression coverage for lifecycle-script suppression, toolchain pinning, network/package-resolution errors, graph ambiguity, parent-range validation, changed-path containment, output digest agreement, stale snapshots, vulnerability postconditions, and closed-proposal replacement identity.

Findings with no released non-affected target remain visible and specifically classified. Gardener must not invent replacement versions, use prereleases without separate authority, or suppress advisories simply to improve remediation counts.

The GitHub App permission boundary remains Metadata read, Contents write, and Pull requests write in selected-repository mode. No Actions, Checks, Administration, deployment, secret, settings, or merge permission is added.

Merge, workflow dispatch, target remediation, dependency pull-request merge, deployment, and live verification remain separate authority gates.
