# Atlas Systems control-plane contracts

`contracts/v1/` is the authoritative, versioned contract set for the Atlas
Systems control plane. It contains data contracts only. It does not create a
service, route, deployment, storage layer, remediation agent, or secret.

## Contract inventory

- `Finding`: redacted assurance output with a stable fingerprint.
- `RemediationProposal`: review-only proposal metadata and inert validation
  commands.
- `ServiceContract`: ownership, routes, dependencies, and separate lifecycle,
  scope, and provenance axes.
- `ReleaseEvidence`: bounded deployment and verification evidence. Phase 3
  producers include the optional `service_id` and `deployment_target` fields;
  checks may include an optional shared `state`. These additions remain
  compatible within v1 so older v1 readers may ignore them.
- `BackupEvidence`: backup freshness, retention, and disposable restore-test
  metadata without content. Phase 8 producers include optional service,
  repository, audit-state, digest/reference, warning/error, and runbook fields;
  missing timestamps or references may be explicit `null` and never healthy.
- `RunbookIndexEntry`: deterministic failure-to-runbook metadata.
- `EvidenceEnvelope`: one inline bounded payload or stable reference with a
  SHA-256 digest.
- `ControlPlaneSummary`: redacted aggregate projections and the shared six-value
  `ControlPlaneState` vocabulary. Phase 9 adds optional journey,
  contract-registry, and open-Gardener-PR projections for the bounded Home
  Assistant sensors; earlier v1 summaries remain valid.

Every schema uses JSON Schema Draft 2020-12, has a stable `$id`, requires an
explicit `schema_version`, rejects undeclared top-level properties, declares an
owner, and embeds an example. Canonical positive and negative examples are in
`v1/fixtures/`.

## Ownership and licence

`AtlasReaper311/atlas-infra` owns schema governance, fixtures, compatibility,
and the validator. `AtlasReaper311/atlas-dep-audit` owns scheduled assurance
invocation and provenance reporting. The machine-readable declaration is
`v1/ownership.json`.

These contracts are covered by the repository's MIT licence. They do not copy
implementation code from external-derived repositories.

## Validate

```bash
python3 scripts/validate_control_plane_contracts.py
python3 scripts/validate_release_evidence.py --instance path/to/release-evidence.json
python3 -m unittest discover -s scripts/tests -v
```

The validator is standard-library only. It checks schema inventory and
metadata, embedded examples, positive and negative fixtures, semantic rules,
fingerprints, payload digests, and deterministic second-run output.

## Stable identity

`v1/fingerprint-rules.json` is normative. Canonical JSON uses UTF-8, sorted
object keys, compact separators, and unescaped Unicode. Finding fingerprints
and proposal IDs hash an object whose keys are the declared dotted field paths
and whose values are the corresponding instance values. Arrays named in
`sort_arrays` are sorted by their canonical JSON before hashing. Evidence
payload digests hash the complete canonical inline payload. Changing an input
field or canonicalisation rule requires a new major contract path.

## Repository classification

`ServiceContract.classification` keeps `lifecycle`, `scope`, and `provenance`
as independent required axes. The `simple-proxy` invariant is encoded in the
schema and fixtures: it remains historically visible as deprecated, internal,
and external-derived, while route ownership, new features, default assurance,
Gardener remediation, and deployment orchestration are all disabled.

Phase 6 adds optional v1 fields for route origins, environments, explicit
health/metadata endpoint state, expected metadata shape, journey/quota/secret
links, backup relevance, release-watch eligibility, escalation, and approved
internal/public route exceptions. Existing v1 instances remain valid. The
canonical registry validator requires the extended fields only for records in
`policy/service-contracts/`.

See [COMPATIBILITY.md](COMPATIBILITY.md) and the validation
[runbook](../docs/runbooks/control-plane-contract-validation.md).
