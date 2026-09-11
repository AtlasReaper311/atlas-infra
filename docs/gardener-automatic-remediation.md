# Atlas Gardener automatic remediation authority

The automatic remediation programme is governed by [`policy/gardener-automation.json`](../policy/gardener-automation.json) and [ADR-0016](adrs/ADR-0016-gardener-npm-graph-remediation-and-dispositions.md). Source defaults to `disabled`; merging this authority does not store credentials, enable schedules, change GitHub App permissions, enable repository auto-merge, install target workflows, create target branches, publish a new Finding bundle, or perform a live remediation.

## Ownership

- Atlas Infra owns policy, contracts, risk tiers, fixer-specific path boundaries, public coverage, validation, and rollout boundaries.
- Atlas Dep Audit produces attested public-only Finding bundles and may attach bounded structured remediation candidates and evidence-backed dispositions.
- Atlas Gardener validates bundles, independently regenerates approved candidates, brokers repository-restricted App tokens, creates deterministic pull requests, reconciles outcomes, and writes bounded evidence.
- Target repositories own repository-native CI and any final automatic-merge gate through their repository-scoped `GITHUB_TOKEN`.
- Atlas Notify receives only the existing authenticated `alert` envelope; notification deduplication remains producer-owned.

## Remediation boundary

Automatic merge remains limited to `macos-metadata-ignore` and `python-cache-ignore`, and only when the complete patch is an additions-only edit to one normal `.gitignore` file containing no more than two approved lines.

Four dependency/container fixers are authorised only for review-required draft pull requests:

- `npm-security-update` for a direct npm dependency with a published patch or minor fixed version, updating the matching `package.json` and `package-lock.json`;
- `npm-lock-security-remediation` for one exact npm manifest/lock graph containing a bounded direct-parent update, bounded transitive lock target, or both, with deterministic producer and controller regeneration;
- `python-security-pin` for a direct exact pin in `requirements.txt` with a published patch or minor fixed version;
- `container-digest-pin` for externally resolvable Docker Hub base-image tags in Dockerfiles.

The npm graph fixer is limited to matching `package.json` and lockfile-v3 `package-lock.json` paths. Direct-parent targets must be released same-major versions. A transitive target is allowed only when every constraining parent range in the exact lock graph admits that exact target. No manifest dependency or npm `overrides` entry may be invented solely to force a transitive update. Producer and controller regeneration must run with lifecycle scripts disabled, must use the same pinned npm toolchain, must remain inside the approved manifest/lock paths, must reproduce the candidate target digests, and must prove the candidate vulnerability IDs are absent from the resulting graph.

Dependency and container Findings may carry one of these explicit dispositions:

- `remediation-available`;
- `awaiting-upstream-release`;
- `awaiting-upstream-fix`;
- `manual-remediation-required`;
- `unsupported-remediation`.

A disposition classifies evidence. It does not grant mutation authority; `remediation.eligible` and all existing controller/write gates remain authoritative.

Major dependency upgrades, unresolved fixed versions, unsupported Python packaging formats, unsupported container registries, graph ambiguity, parent-range conflicts, unpinned or unsupported package-manager execution, source changes, migrations, credentials, binaries, symlinks, generated application output, stale findings, unclassified repositories, non-original provenance, archived or deprecated repositories, and out-of-coverage work remain non-actionable or fail closed as defined by the accepted policy.

## Modes

The committed policy and repository variables are both required:

- `disabled`: no token minting or target writes;
- `observe`: validate and report only;
- `pr-only`: create deterministic draft pull requests;
- `automerge-low-risk`: automatically merge only the exact housekeeping boundary while dependency and container fixers remain draft-PR-only.

Writes additionally require `ATLAS_GARDENER_WRITE_GATE=enabled`. Missing or unknown values fail closed.

## Validation

```bash
python3 scripts/validate_gardener_automation.py
python3 -m unittest scripts.tests.test_validate_gardener_automation -v
python3 scripts/adr_trace.py check --root .
```

The validator checks the exact mode set, default-disabled state, write gate, producer workflow, attestation requirement, repository classification boundary, nine-fixer inventory, fixer-specific allowed paths, review-only dependency and container fixers, `.gitignore`-only automatic fixers, file and line limits, global forbidden paths, expiry, retention, weekly schedule relationship, selected-repository App mode, exact App permission contract, and all 20 verified public runtime repositories. Contract tests additionally prove that the v1 Finding and RemediationProposal schemas accept the bounded npm graph candidate and reject an empty graph candidate or unknown disposition.

The forensic basis for ADR-0016 is recorded in [`gardener-remediation-coverage-2026-09-10.md`](gardener-remediation-coverage-2026-09-10.md). It is evidence for authority design, not proof that a later implementation or rollout succeeded.
