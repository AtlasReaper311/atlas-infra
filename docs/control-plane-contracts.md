# Shared control-plane contracts

## Architecture and ownership

`atlas-infra` is the schema authority because the contracts cross repository
and runtime boundaries. Producers own their evidence contents, but they do not
fork the common envelopes or identity rules. `atlas-dep-audit` is the assurance
consumer: it invokes the canonical validator against the allowlisted
`AtlasReaper311/atlas-infra` checkout and records the result in build
provenance.

This separation avoids a circular ownership model. The policy repository owns
meaning and versioning; the assurance repository proves the published set can
be consumed. Neither repository stores evidence or performs remediation.

## Phase 1 boundary

This phase adds contracts and validation only. It does not implement
atlas-gardener, a gateway, a dashboard, orchestration, cost changes, backup
drills, runbook matching, evidence storage, or any deployment behavior.

Classification is three-dimensional. Lifecycle, scope, and provenance are
never inferred from one another. `simple-proxy` remains in the contract model
for historical and dependency visibility, with every new-feature and automated
control-plane policy disabled.

## Producer example

Use a positive fixture as the configuration example, replace only the
instance-specific values, calculate the declared fingerprint or digest, then
run:

```bash
python3 scripts/validate_control_plane_contracts.py
```

Do not add undeclared fields for credentials, authorization headers, cookies,
private keys, or token-bearing URLs. Evidence summaries must already be
redacted before validation.

## Assurance integration

The `atlas-infra` estate-policy workflow validates schemas and fixtures before
running the wider policy audit. The `atlas-dep-audit` audit path invokes the
same canonical validator for the allowlisted contract owner, with credential
environment variables removed from the subprocess, and records the stable
validation report in provenance.

## Migration order

1. Review and merge the `atlas-infra` contract branch.
2. Rebase the `atlas-dep-audit` integration branch on its current main.
3. Run the dependency audit with `--skip-osv` against a local manifest when a
   network-free clone set is available, or let the scheduled workflow consume
   `atlas-infra/main` after merge.
4. Adopt individual contracts in later approved phases without changing v1
   identity inputs.

No estate manifest registration is added in Phase 1 because this contract set
does not introduce a deployed service or public endpoint.
