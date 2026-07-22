# Atlas Gardener automatic remediation authority

The automatic remediation programme is governed by [`policy/gardener-automation.json`](../policy/gardener-automation.json) and ADR-0003. Source defaults to `disabled`; merging this authority does not store credentials, enable schedules, change GitHub App permissions, enable repository auto-merge, install target workflows, create target branches, or perform a live remediation.

## Ownership

- Atlas Infra owns policy, contracts, risk tiers, public coverage, validation, and rollout boundaries.
- Atlas Dep Audit produces attested public-only Finding bundles.
- Atlas Gardener validates bundles, brokers repository-restricted App tokens, creates deterministic pull requests, reconciles outcomes, and writes bounded evidence.
- Target repositories own the native CI and final automatic-merge gate through their repository-scoped `GITHUB_TOKEN`.
- Atlas Notify receives only the existing authenticated `alert` envelope; notification deduplication remains producer-owned.

## Initial automatic boundary

Only `macos-metadata-ignore` and `python-cache-ignore` can be automatically merged, and only when the complete patch is an additions-only edit to one normal `.gitignore` file containing no more than two approved lines. Tracked metadata or cache-file deletion is review-only. Workflow, source, dependency, lockfile, deployment, infrastructure, credential-like, binary, symlink, generated-output, stale, unclassified, non-original, experimental, archived, deprecated, or out-of-coverage work is refused or review-only.

## Modes

The committed policy and repository variables are both required:

- `disabled`: no token minting or target writes;
- `observe`: validate and report only;
- `pr-only`: create deterministic draft pull requests;
- `automerge-low-risk`: create ready pull requests only for the exact low-risk `.gitignore` boundary.

Writes additionally require `ATLAS_GARDENER_WRITE_GATE=enabled`. Missing or unknown values fail closed.

## Validation

```bash
python3 scripts/validate_gardener_automation.py
python3 -m unittest scripts.tests.test_validate_gardener_automation -v
python3 scripts/adr_trace.py check --root .
```

The validator checks the exact mode set, default-disabled state, write gate, producer workflow, attestation requirement, repository classification boundary, five-fixer inventory, review-only workflow fixers, `.gitignore`-only automatic fixers, file and line limits, forbidden paths, expiry, retention, schedule relationship, selected-repository App mode, exact App permission contract, and all 20 verified public runtime repositories.
