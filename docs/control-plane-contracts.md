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

Phase 3 adds optional, minor-compatible `ReleaseEvidence` properties:
`service_id`, `deployment_target`, and a shared `state` on each check. The
release-watch producer always emits them, while older v1 readers may continue
to ignore them. The canonical single-instance validator remains in this
repository.

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

## Phase 6 follow-on

Phase 6 adds the canonical repository catalogue and ServiceContract instances
under `policy/`, plus an offline validator and generated graph/catalogue. The
v1 schema additions are optional and minor-compatible; the registry validator
applies the stricter canonical-instance policy without breaking older v1
producers.
