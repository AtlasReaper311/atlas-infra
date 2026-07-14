# Backup audit

## Architecture and ownership

`AtlasReaper311/atlas-infra` owns the Phase 8 backup policy, fixture metadata,
offline validator, disposable restore adapters, BackupEvidence production,
Finding production, documentation, and runbooks.

Backup producers retain their data and provider credentials. Phase 8 does not
modify `atlas-dep-audit`, `atlas-corpus`, `ramone-memory`, `atlas-postmortem`,
`atlas-blackbox`, GitHub, Cloudflare, or any backup store. The only repository
changed by this phase is `atlas-infra`.

The assurance flow is deliberately local:

1. Load the versioned backup policy and Phase 6 registry.
2. Resolve each enabled target to a ServiceContract and repository entry.
3. Load one redacted local metadata fixture.
4. Calculate freshness and validate retention metadata.
5. verify the declared SHA-256 digest.
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
external-derived implementation code. Phase 8 introduces no deployed service,
public route, metadata endpoint, or runtime dependency, so it does not add a
new estate-registry repository/service record.

## Policy and target declaration

`policy/backup-audit.json` conforms to
`policy/backup-audit.schema.json`. Its version is
`atlas-backup-audit/policy/v1` and its mode is fixed to `fixture-only`.

Each target declares:

- stable target and service IDs;
- exact source repository;
- data and storage types;
- accountable owner;
- independent lifecycle, scope, and provenance classifications;
- backup frequency, maximum allowed age, RPO intent, and RTO intent in hours;
- retention expectation in days;
- one allowlisted restore drill type;
- `system-temporary-directory` as the only destination class;
- repository-relative metadata fixture path;
- required metadata fields;
- repository-relative runbook;
- criticality;
- enabled and fixture-only flags;
- notes that distinguish fixture assurance from live backup proof.

The four initial enabled targets are:

| Target | Registry service | Storage shape | Drill |
|---|---|---|---|
| `github-workflow-artifact-fixture` | `atlas-blackbox` | GitHub artifact metadata | artifact metadata validation |
| `cloudflare-kv-export-fixture` | `atlas-vault` | Cloudflare KV-shaped JSON export | JSON export validation |
| `incident-export-fixture` | `atlas-blackbox` | bounded incident JSON export | JSON export validation |
| `chroma-vector-store-export-fixture` | `atlas-corpus` | Chroma-shaped manifest, collections, and JSONL records | vector-store fixture validation |

These are synthetic targets. They prove the auditor's mechanics, not the
existence, freshness, or recoverability of provider data.

## Service coverage and registry rules

The policy contains sorted `service_coverage` records. Every production runtime
service and every ServiceContract already marked backup-relevant has one of:

- `target`: one or more declared fixture/live target IDs;
- `no-backup-rationale`: an owner-reviewable reason the service is
  reconstructable and owns no mutable data under its current contract;
- `not-declared`: no target or no-backup decision is currently proven;
- `excluded`: lifecycle/provenance policy prohibits default active assurance.

`not-declared` emits a warning and cannot make the aggregate healthy. It is
used rather than inventing provider targets where evidence is unknown.

Every enabled target must:

- use a service ID present in `policy/service-contracts/`;
- map to the same repository in `policy/estate-registry.json`;
- match lifecycle, scope, and provenance independently;
- reference an existing runbook;
- avoid archived, deprecated, and external-derived active ownership.

`simple-proxy` is explicitly `excluded`. It remains historically visible but
cannot receive an active default backup drill because it is deprecated,
internal, and external-derived.

## Backup metadata fixtures

`policy/backup-metadata.schema.json` defines the redacted local metadata shape.
Metadata records include target/service/repository identity, backup and
observation timestamps, a redacted HTTPS evidence reference, SHA-256 digest,
retention metadata, restore source, and bounded file/byte expectations.

Metadata absence, parse failure, identity mismatch, unsafe path, future or
misordered timestamp, missing retention, expired retention, digest mismatch,
or restore failure is explicit non-healthy evidence. The auditor never fills
an unknown backup timestamp with the audit time.

## BackupEvidence

Every enabled target produces a record conforming to
`contracts/v1/backup-evidence.schema.json`. Phase 8 requires these additive v1
fields in its producer output:

- target ID, service ID, and repository;
- backup and audit timestamps;
- freshness, retention, and restore-drill states;
- SHA-256 digest and redacted evidence reference when available;
- source type and aggregate result state;
- bounded sorted errors and warnings;
- runbook reference.

The original v1 fields remain present for compatibility. Missing evidence uses
explicit `null` timestamps/references and an `unknown`/`unavailable` result; it
never uses fabricated success data.

State meanings are:

| Dimension | States |
|---|---|
| Freshness | `fresh`, `stale`, `unknown`, `unavailable` |
| Retention | `met`, `violated`, `missing`, `unknown` |
| Restore drill | `passed`, `failed`, `unavailable`, `not-run` |
| Result | `healthy`, `warning`, `failed`, `stale`, `unavailable`, `unknown` |

The aggregate precedence is failed, unavailable, stale, warning, unknown, then
healthy. Informational exclusion findings do not degrade the aggregate, while
explicit coverage gaps do.

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

Provider lifecycle configuration is not inferred. Unknown provider retention
is missing/unknown, not met.

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
- no provider read/write/delete API;
- no command, subprocess, hook, or binary execution from policy;
- no absolute path, `..`, backslash path, or fixture-root escape;
- no source, parent, directory-entry, or archive symlink;
- no executable fixture or archive entry;
- no duplicate archive member path;
- no encrypted archive entry;
- maximum file count and uncompressed bytes before/during extraction;
- declared and actual file count/size agreement;
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
- production/relevant coverage not declared;
- `simple-proxy` exclusion.

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

The committed policy intentionally reports `warning`: all four fixtures are
healthy, but several production or backup-relevant services remain explicitly
`not-declared`. This is an honest coverage result, not a validation failure.

## Workflow integration

The existing weekly `estate-policy.yml` workflow compiles the auditor, runs the
complete unit-test suite, and runs this fixed-time fixture audit. It has:

- `contents: read` only;
- a 25-minute job timeout;
- estate-policy concurrency without cancellation;
- immutable checkout and artifact action SHAs with release comments;
- 90-day artifact retention;
- no provider or backup credential.

The fixed timestamp validates the fixture scenario and does not claim live
freshness. No new third-party action or schedule is introduced.

## Future provider integration

Provider integration is deliberately not implemented. A later phase or
separate approval must add one target-scoped, metadata-only adapter at a time,
with fixtures, redaction, timeouts, rate limits, and no restore/write/delete
permission.

Potential secret names and minimum scopes, not created in Phase 8:

- `GH_BACKUP_AUDIT_READ_TOKEN`: selected repositories, GitHub `Metadata: read`,
  `Contents: read`, and `Actions: read` for artifact metadata only;
- `CF_BACKUP_AUDIT_READ_TOKEN`: named account and named namespace, the narrowest
  available KV metadata/read scope; no Workers, Pages, DNS, token, or account
  write permission;
- a target-specific read credential only when the producer cannot publish
  redacted metadata itself.

Private production data must not be downloaded by default. Prefer producer-
emitted redacted timestamps, counts, retention facts, stable references, and
digests. Any disposable live-data restore rehearsal requires separate owner
approval, isolated non-production storage, data-handling review, and a new
threat model.

## Migration

1. Review the Phase 8 policy, schemas, fixtures, findings, and runbooks.
2. Run the native contract, registry, deploy-orchestrator, backup-audit, and
   full unit-test validation locally.
3. Merge the focused `atlas-infra` change after review.
4. Let the existing estate-policy workflow validate fixture mode with no new
   credential.
5. Resolve each `not-declared` service in separate owner-reviewed changes:
   either add proven redacted backup evidence or an accurate no-backup
   rationale.
6. Add future provider adapters only after separate permission and safety
   approval. Do not convert the fixture targets into live targets implicitly.

No deployment, secret creation, provider migration, or live restoration is
part of Phase 8.

## Rollback

Before merge, discard the uncommitted feature branch after review. After merge,
revert the focused Phase 8 commit. This removes the policy, fixture validator,
workflow validation call, docs, and fixtures. The shared BackupEvidence changes
are additive/relaxed within v1, so older valid instances remain readable.

No provider, route, secret, backup object, live data, deployment, or scheduled
frequency needs rollback because Phase 8 never mutates them.

## Known limitations

- Fixture success does not prove any live backup exists.
- No provider backup metadata, object, namespace, artifact, Durable Object,
  local Chroma store, or private incident was accessed.
- Restore drills validate representative shapes, not application startup or
  full recovery time objective.
- RPO and RTO are declared intent; fixture drills do not measure full
  application recovery time.
- `not-declared` services require later owner decisions and remain warnings.
- GitHub and Cloudflare retention evidence can differ from declared policy;
  future adapters must report unknown when metadata is unavailable.
- ZIP support is fixture-only and deliberately rejects symlinks, executable
  entries, encryption, overwrites, traversal, and oversized extraction.
