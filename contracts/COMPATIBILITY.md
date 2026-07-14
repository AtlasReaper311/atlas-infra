# Control-plane contract compatibility

The directory name is the major version. A v1 reader accepts only
`atlas-control-plane/*/v1` instances and rejects unknown major versions.

## Compatible within v1

- Add an optional property with a documented default or absence meaning.
- Relax a bound without changing the field's meaning or security boundary.
- Improve descriptions, examples, and negative fixtures.

Readers ignore unknown optional properties only after confirming the major
version. Canonical producer validation remains closed to undeclared properties;
the schema must first declare the additive field. Application readers then
ignore that optional field if they do not use it. Writers continue emitting the
oldest shape needed by active v1 consumers during a migration window.

The Phase 6 ServiceContract registry fields are additive optional properties.
Canonical registry policy requires them for its own records, but generic v1
readers and earlier producers are not required to emit them during migration.

The Phase 8 BackupEvidence fields are additive and optional within v1. The
Phase 8 producer requires them in its own output. `last_successful_backup_at`
and `evidence_ref` also accept `null` so missing evidence can be represented
honestly instead of fabricating a timestamp or URI. `json-export` and
`vector-store-export` are additive method values; consumers must retain an
unknown-method fallback during migration.

The Phase 9 ControlPlaneSummary `journeys` and `contract_registry` projections
and `gardener_proposals.open_pull_requests` property are additive and optional
within v1. The Phase 9 aggregator emits them, while earlier v1 summaries remain
valid. Missing projections are interpreted as `unknown`, never healthy.
ServiceContract route paths also accept OpenAPI-style `{parameter}` templates;
this relaxes the existing path character bound without changing route
ownership semantics.

## Requires a new major path

- Add a required property.
- Remove or rename a property.
- Remove a vocabulary value or change a field's meaning.
- Change an identifier format, required timestamp semantics, redaction rule,
  or additional-properties policy.
- Change any fingerprint field, array-order rule, canonicalisation rule, or
  digest target.

Vocabulary additions require consumer review. They are minor-compatible only
when every active reader explicitly tolerates unknown values for that field.

## Change procedure

1. Add the new schema path beside the old version.
2. Add positive, negative, compatibility, fingerprint, and idempotency tests.
3. Update producers first while preserving the previous writer shape.
4. Update readers to accept both major versions during a bounded migration.
5. Retire the old reader only after evidence shows no active producer emits it.

The machine-readable summary is `v1/compatibility-policy.json`. The validator's
compatibility helpers treat required-field additions, property removals, type
or const changes, enum removals, and fingerprint rule changes as breaking.
