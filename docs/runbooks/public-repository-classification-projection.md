# Public repository classification projection

## Purpose

Use this runbook when a public repository lifecycle, scope, or provenance changes, when a public non-runtime repository enters or leaves assurance scope, or when a downstream projection reports classification drift.

## Authority

Public runtime repository classification is authored in `policy/estate-registry.json`.

Public non-runtime repository classification is authored in `policy/public-assurance-repositories.json`.

The two source sets must not overlap. `policy/public-repository-classifications.json` is generated evidence only and must never be edited as the source of a classification decision.

Private repository governance is source-owned in the authenticated private repository and is outside this public projection.

## Change procedure

1. Update the applicable Atlas Infra authority input.
2. Run:

   ```bash
   python3 scripts/public_repository_classifications.py
   ```

3. Review the generated `policy/public-repository-classifications.json` diff.
4. Run:

   ```bash
   python3 scripts/public_repository_classifications.py --check
   python3 -m unittest discover -s scripts/tests -v
   git diff --check
   ```

5. Open a reviewed pull request. Do not edit a downstream copy before the Atlas Infra authority change is accepted.
6. After the Atlas Infra change is merged, refresh downstream verified copies and let their CI compare the copied projection with current Atlas Infra `main`.

## Failure modes

`--check` fails when the generated projection is missing or differs from the authoritative inputs.

Generation fails when runtime and non-runtime authority sets overlap, when a classification axis is invalid, when a public non-runtime repository is not public scope, or when an input schema version is unsupported.

A downstream mismatch means the downstream projection is stale. Do not make the downstream value authoritative and do not repair the mismatch by changing both sides independently.

## Rollback

Before merge, discard the branch or restore the authority input and regenerate the projection.

After merge, revert the classification authority change through a reviewed pull request and regenerate the projection. Downstream copies are then refreshed from the reverted Atlas Infra projection.

No step in this runbook deploys a service, modifies provider state, or changes repository settings.
