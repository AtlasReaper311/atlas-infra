# Backup audit

## Architecture and ownership

`AtlasReaper311/atlas-infra` owns the backup policy, fixture metadata, offline
validator, disposable restore adapters, BackupEvidence production, Finding
production, documentation, and runbooks.

Backup producers retain their data and provider credentials. This public control
plane does not enumerate source-owned private repositories, does not modify
backup producers, and does not mutate GitHub, Cloudflare, local data stores, or
any backup destination.

The current assurance flow is deliberately local and fixture-only:

1. Load the versioned backup policy and public runtime registry.
2. Resolve each enabled target to a public ServiceContract and repository entry.
3. Load one redacted local metadata fixture.
4. Calculate freshness and validate retention metadata.
5. Verify the declared SHA-256 digest.
6. Copy or extract synthetic content into a newly created system temporary
   directory.
7. Validate the restored fixture shape, count, and byte size.
8. Delete the temporary directory and emit redacted BackupEvidence and Finding
   records.

No step has a provider client, network fallback, shell-command adapter, live
destination, or deletion API.

## Licence and registration

The implementation, policy, tests, and synthetic fixtures are covered by this
repository's MIT licence. They contain no copied provider export or
external-derived implementation code.

The backup auditor is a control-plane capability, not a deployed service. It
therefore does not add a runtime repository or service entry to the public
estate registry.

## Policy and target declaration

`policy/backup-audit.json` conforms to `policy/backup-audit.schema.json`. Its
schema version is `atlas-backup-audit/policy/v1` and its current mode is
`fixture-only`.

Each target declares:

- stable target and service IDs;
- exact public source repository;
- data and storage types;
- accountable owner;
- lifecycle, scope, and provenance classifications;
- backup frequency and maximum allowed age;
- recovery point and recovery time intent in hours;
- retention expectation in days;
- one allowlisted restore drill type;
- `system-temporary-directory` as the only destination class;
- repository-relative metadata fixture path;
- required metadata fields;
- repository-relative runbook;
- criticality;
- enabled and fixture-only flags;
- notes that distinguish fixture assurance from live backup proof.

The four current enabled fixture targets are:

| Target | Public registry service | Storage shape | Drill |
|---|---|---|---|
| `github-workflow-artifact-fixture` | `atlas-blackbox` | GitHub artifact metadata | artifact metadata validation |
| `cloudflare-kv-export-fixture` | `atlas-api-public` | Cloudflare KV-shaped JSON export | JSON export validation |
| `incident-export-fixture` | `atlas-blackbox` | bounded incident JSON export | JSON export validation |
| `chroma-vector-store-export-fixture` | `atlas-corpus` | Chroma-shaped manifest, collections, and JSONL records | vector-store fixture validation |

These targets are synthetic. They prove the auditor's mechanics, not the
existence, freshness, or recoverability of provider data.

## Service coverage and registry rules

The policy contains sorted `service_coverage` records for public runtime
services and ServiceContracts already marked backup-relevant.

Each coverage record has one of these states:

- `target`: one or more declared fixture or live target IDs;
- `no-backup-rationale`: an owner-reviewable reason the service is
  reconstructable and owns no mutable data under its current contract;
- `not-declared`: no target or no-backup decision is currently proven;
- `excluded`: lifecycle or provenance policy prohibits default active
  assurance.

`not-declared` emits a warning and cannot make the aggregate healthy. It is used
rather than inventing provider targets where evidence is unknown.

Every enabled target must:

- use a service ID present in `policy/service-contracts/`;
- map to the same repository in `policy/estate-registry.json`;
- match lifecycle, scope, and provenance independently;
- reference an existing runbook;
- avoid archived, deprecated, and external-derived active ownership.

Source-owned private repository governance is outside this public policy and is
never enumerated here.

## Backup metadata fixtures

`policy/backup-metadata.schema.json` defines the redacted local metadata shape.
Metadata records include target, service, and public repository identity;
backup and observation timestamps; a redacted HTTPS evidence reference;
SHA-256 digest; retention metadata; restore source; and bounded file and byte
expectations.

Metadata absence, parse failure, identity mismatch, unsafe path, future or
misordered timestamp, missing retention, expired retention, digest mismatch, or
restore failure is explicit non-healthy evidence. The auditor never fills an
unknown backup timestamp with the audit time.

## BackupEvidence

Every enabled target produces a record conforming to
`contracts/v1/backup-evidence.schema.json`.

The producer output includes:

- target ID, service ID, and public repository;
- backup and audit timestamps;
- freshness, retention, and restore-drill states;
- SHA-256 digest and redacted evidence reference when available;
- source type and aggregate result state;
- bounded sorted errors and warnings;
- runbook reference.

Missing evidence uses explicit `null` timestamps and references plus an
`unknown` or `unavailable` result. It never uses fabricated success data.

State meanings are:

| Dimension | States |
|---|---|
| Freshness | `fresh`, `stale`, `unknown`, `unavailable` |
| Retention | `met`, `violated`, `missing`, `unknown` |
| Restore drill | `passed`, `failed`, `unavailable`, `not-run` |
| Result | `healthy`, `warning`, `failed`, `stale`, `unavailable`, `unknown` |

Aggregate precedence is `failed`, `unavailable`, `stale`, `warning`, `unknown`,
then `healthy`. Informational classification exclusions do not degrade the
aggregate. Explicit coverage gaps do.

## Freshness and retention model

Freshness is deterministic:

```text
age = audit_timestamp - backup_timestamp
fresh when 0 <= age <= maximum_allowed_age_hours
stale when age > maximum_allowed_age_hours
malformed when backup_timestamp is in the future
```

Retention is met only when all of these hold:

- metadata `expected_days` equals the policy expectation;
- `retained_until >= backup_timestamp + retention_expectation_days`;
- `retained_until >= audit_timestamp`.

Provider lifecycle configuration is not inferred. Unknown provider retention is
missing or unknown, not met.

## Disposable restore drills

Supported local adapters are:

- GitHub artifact manifest parsing;
- Cloudflare KV-shaped JSON export validation;
- incident JSON export validation;
- Chroma/vector-store manifest, collection, JSONL, dimension, checksum, count,
  and size validation;
- bounded ZIP extraction for allowlisted future fixture targets.

Every drill creates a new `tempfile.TemporaryDirectory`, restores only under a
new child path, emits no temporary path in its report, and removes the entire
directory on exit.

Safety restrictions are enforced in code and tests:

- no live application or provider destination;
- no existing destination or file overwrite;
- no provider read, write, or delete API;
- no command, subprocess, hook, or binary execution from policy;
- no absolute path, `..`, backslash path, or fixture-root escape;
- no source, parent, directory-entry, or archive symlink;
- no executable fixture or archive entry;
- no duplicate archive member path;
- no encrypted archive entry;
- maximum file count and uncompressed bytes before and during extraction;
- declared and actual file count and size agreement;
- automatic temporary cleanup.

The archive adapter is exercised with safe, traversal, symlink, and malformed
test archives created in temporary test directories. No binary archive fixture
is committed.

## Findings and runbooks

Findings conform to `contracts/v1/finding.schema.json`, use deterministic
fingerprints, contain no backup payload, and route to focused runbooks.

Rules cover:

- missing target owner;
- missing, stale, or malformed backup evidence;
- missing or violated retention;
- failed or unavailable restore drill;
- unsafe restore path;
- digest mismatch;
- malformed export;
- unknown service ID;
- backup classification conflict;
- production or backup-relevant coverage not declared;
- lifecycle and provenance exclusions.

## CLI and reports

Run the complete fixture audit:

```bash
python3 scripts/backup_audit.py \
  --policy policy/backup-audit.json \
  --fixtures tests/fixtures/backup-audit \
  --report /tmp/backup-audit.json \
  --markdown /tmp/backup-audit.md \
  --now 2026-07-14T12:00:00Z
```

`--now` is required so freshness tests and evidence are reproducible. Targets,
evidence, findings, errors, warnings, and JSON keys are sorted. A second run
with the same inputs produces byte-identical JSON and Markdown.

The committed policy intentionally reports `warning`: the fixture targets are
healthy, but several production or backup-relevant services remain explicitly
`not-declared`. This is an honest coverage result, not a validation failure.

## Workflow integration

The weekly `estate-policy.yml` workflow compiles the auditor, runs the complete
unit-test suite, and runs the fixed-time fixture audit. It has:

- `contents: read` only;
- a bounded job timeout;
- estate-policy concurrency without cancellation;
- immutable GitHub-owned action pins;
- bounded artifact retention;
- no provider or backup credential for fixture validation.

The fixed timestamp validates the fixture scenario and does not claim live
freshness.

## Future provider integration

Provider integration is deliberately separate from fixture assurance. A later
owner-approved phase must add one target-scoped, metadata-only adapter at a
time, with fixtures, redaction, timeouts, rate limits, and no restore, write, or
delete permission.

Potential secret names and minimum scopes, not created by the fixture phase:

- `GH_BACKUP_AUDIT_READ_TOKEN`: selected repositories, GitHub `Metadata: read`,
  `Contents: read`, and `Actions: read` for artifact metadata only;
- `CF_BACKUP_AUDIT_READ_TOKEN`: the narrowest available read scope for the
  explicitly approved Cloudflare backup metadata target;
- a target-specific read credential only when the producer cannot publish
  redacted metadata itself.

Private production data must not be downloaded by default. Prefer
producer-emitted redacted timestamps, counts, retention facts, stable
references, and digests.

Any disposable live-data restore rehearsal requires separate owner approval,
isolated non-production storage, data-handling review, and a new threat model.

## Migration

1. Review the policy, schemas, fixtures, findings, and runbooks.
2. Run contract, registry, deploy-orchestrator, backup-audit, and full unit-test
   validation locally.
3. Merge focused source changes only after review.
4. Let the existing estate-policy workflow validate fixture mode with no new
   backup credential.
5. Resolve each `not-declared` service in separate owner-reviewed changes by
   either adding proven redacted backup evidence or an accurate no-backup
   rationale.
6. Add future provider adapters only after separate permission and safety
   approval. Do not convert fixture targets into live targets implicitly.

No deployment, secret creation, provider migration, or live restoration is part
of the fixture phase.

## Rollback

Before merge, discard the uncommitted feature branch after review. After merge,
revert the focused backup-audit source commit if necessary.

No provider, route, secret, backup object, live data, deployment, or scheduled
frequency needs rollback because fixture mode never mutates them.

## Known limitations

- Fixture success does not prove any live backup exists.
- No provider backup metadata, object, namespace, artifact, Durable Object,
  local vector store, or private incident is accessed in fixture mode.
- Restore drills validate representative shapes, not application startup or
  full recovery time objective.
- RPO and RTO are declared intent; fixture drills do not measure full
  application recovery time.
- `not-declared` services require later owner decisions and remain warnings.
- Provider retention evidence can differ from declared policy; future adapters
  must report unknown when metadata is unavailable.
- ZIP support is fixture-only and deliberately rejects symlinks, executable
  entries, encryption, overwrites, traversal, and oversized extraction.
