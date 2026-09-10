# Atlas Gardener automatic remediation authority

The automatic remediation programme is governed by [`policy/gardener-automation.json`](../policy/gardener-automation.json) and [ADR-0015](adrs/ADR-0015-gardener-bounded-dependency-container-remediation.md). Source defaults to `disabled`; merging this authority does not store credentials, enable schedules, change GitHub App permissions, enable repository auto-merge, install target workflows, create target branches, publish a new Finding bundle, or perform a live remediation.

## Ownership

- Atlas Infra owns policy, contracts, risk tiers, fixer-specific path boundaries, public coverage, validation, and rollout boundaries.
- Atlas Dep Audit produces attested public-only Finding bundles and may attach bounded structured remediation candidates.
- Atlas Gardener validates bundles, brokers repository-restricted App tokens, creates deterministic pull requests, reconciles outcomes, and writes bounded evidence.
- Target repositories own repository-native CI and any final automatic-merge gate through their repository-scoped `GITHUB_TOKEN`.
- Atlas Notify receives only the existing authenticated `alert` envelope; notification deduplication remains producer-owned.

## Remediation boundary

Automatic merge remains limited to `macos-metadata-ignore` and `python-cache-ignore`, and only when the complete patch is an additions-only edit to one normal `.gitignore` file containing no more than two approved lines.

Three additional deterministic fixers are authorised for review-required draft pull requests:

- `npm-security-update` for direct npm dependencies with a published patch or minor fixed version, updating the matching `package.json` and `package-lock.json`;
- `python-security-pin` for direct exact pins in `requirements.txt` with a published patch or minor fixed version;
- `container-digest-pin` for externally resolvable Docker Hub base-image tags in Dockerfiles.

Each fixer has an exact allowlisted path-pattern boundary. Major dependency upgrades, transitive-only npm findings, unresolved fixed versions, unsupported Python packaging formats, unsupported container registries, source changes, migrations, credentials, binaries, symlinks, generated application output, stale findings, unclassified repositories, non-original provenance, archived or deprecated repositories, and out-of-coverage work remain observations, review-required work, or refusals.

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

The validator checks the exact mode set, default-disabled state, write gate, producer workflow, attestation requirement, repository classification boundary, eight-fixer inventory, fixer-specific allowed paths, review-only dependency and container fixers, `.gitignore`-only automatic fixers, file and line limits, global forbidden paths, expiry, retention, weekly schedule relationship, selected-repository App mode, exact App permission contract, and all 20 verified public runtime repositories.
