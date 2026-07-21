# Backup audit

## Architecture and ownership

`AtlasReaper311/atlas-infra` owns the backup policy, fixture metadata, offline validator, disposable restore adapters, BackupEvidence production, Finding production, documentation, and runbooks.

Backup producers retain their data and provider credentials. This public control plane does not enumerate source-owned private repositories, does not modify backup producers, and does not mutate GitHub, Cloudflare, local data stores, or any backup destination.

The current assurance flow is deliberately local and fixture-only:

1. Load the versioned backup policy and public runtime registry.
2. Resolve each enabled target to a public ServiceContract and repository entry.
3. Load one redacted local metadata fixture.
4. Calculate freshness and validate retention metadata.
5. Verify the declared SHA-256 digest.
6. Copy or extract synthetic content into a newly created system temporary directory.
7. Validate the restored fixture shape, count, and byte size.
8. Delete the temporary directory and emit redacted BackupEvidence and Finding records.

No step has a provider client, network fallback, shell-command adapter, live destination, or deletion API.

## Licence and registration

The implementation, policy, tests, and synthetic fixtures are covered by this repository's MIT licence. They contain no copied provider export or external-derived implementation code.

The backup auditor is a control-plane capability, not a deployed service. It therefore does not add a runtime repository or service entry to the public estate registry.

## Policy and target declaration

`policy/backup-audit.json` conforms to `policy/backup-audit.schema.json`. Its schema version is `atlas-backup-audit/policy/v1` and its current mode is `fixture-only`.

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

The six enabled fixture targets are:

| Target | Service | Storage shape | RPO | RTO | Retention | Drill |
|---|---|---|---:|---:|---:|---|
| `atlas-notify-kv-export-fixture` | `atlas-notify` | Cloudflare KV-shaped JSON | 6h | 4h | 30d | JSON export validation |
| `chroma-vector-store-export-fixture` | `atlas-corpus` | Chroma-shaped export | 168h | 8h | 30d | vector-store fixture validation |
| `cloudflare-kv-export-fixture` | `atlas-api-public` | Cloudflare KV-shaped JSON | 24h | 4h | 30d | JSON export validation |
| `github-workflow-artifact-fixture` | `atlas-blackbox` | GitHub artifact metadata | 24h | 4h | 90d | artifact metadata validation |
| `incident-export-fixture` | `atlas-blackbox` | bounded incident JSON export | 24h | 4h | 90d | JSON export validation |
| `ramone-memory-chroma-export-fixture` | `ramone-memory` | Chroma-shaped memory export | 24h | 8h | 30d | vector-store fixture validation |

These targets are synthetic. They prove the auditor's mechanics, not the existence, freshness, or recoverability of live provider data.

## Completed service coverage classification

The policy contains sorted `service_coverage` records for every production public-runtime service plus any ServiceContract explicitly marked backup-relevant.

Each coverage record has one of these states:

- `target`: one or more declared fixture or live target IDs;
- `no-backup-rationale`: an owner-reviewed reason the service is reconstructable and owns no mutable data that needs preservation under its current contract;
- `not-declared`: no target or no-backup decision is currently proven;
- `excluded`: lifecycle or provenance policy prohibits default active assurance.

The reviewed 21 July 2026 policy contains no `not-declared` records.

Owner-approved backup targets are:

- `atlas-api-public`;
- `atlas-blackbox`;
- `atlas-corpus`;
- `atlas-notify`;
- `ramone-memory`.

The remaining covered services have explicit no-backup rationales because their state is static, stateless, derived, cache-like, or bounded and relearnable:

- `atlas-api-index`: `REGISTRY_KV` is rebuilt from approved public Worker metadata;
- `atlas-daily-digest`: each run is regenerated from upstream sources and Git configuration;
- `atlas-doc-viewer`: static Git-backed surface;
- `atlas-dora`: `DORA_CACHE` is derived from bounded public evidence;
- `atlas-quota-watch`: provider-read evidence is recomputed and no mutable store is declared;
- `atlas-systems`: static Git-backed Pages output;
- `deploy-watch`: `DEPLOY_STATE` is rebuilt from Cloudflare deployment state;
- `github-pulse`: `PULSE_CACHE` is rebuilt from GitHub;
- `ramone-edge`: stateless edge gateway;
- `ramone-trigger`: stateless authenticated trigger adapter;
- `site-pulse`: analytics cache rebuilt from Cloudflare;
- `specular-edge`: stateless edge projection;
- `specular-sentinel`: previous delivered WSL2 address is re-derived from current network state;
- `specular-sonify`: stateless read-only telemetry projection;
- `specular-telemetry`: bounded anomaly history and baseline are relearned from fresh telemetry;
- `status`: static Git-backed status surface.

For `specular-telemetry`, the current default detector uses a 24-sample window, requires three windows for warm-up, and samples every 30 seconds. Rebuilding the local anomaly baseline therefore takes about 36 minutes under the default configuration. Losing that bounded state is accepted as a temporary warm-up cost rather than a data-loss event.

Every enabled target must:

- use a service ID present in `policy/service-contracts/`;
- map to the same repository in `policy/estate-registry.json`;
- match lifecycle, scope, and provenance independently;
- reference an existing runbook;
- avoid archived, deprecated, and external-derived active ownership.

Source-owned private repository governance is outside this public policy and is never enumerated here.

## Owner-approved recovery intent

`atlas-notify` is backup-relevant because its rolling event buffer contains bounded but non-reconstructible operational context consumed by incident and delivery evidence. The approved intent is:

- backup frequency: six hours;
- maximum backup age: six hours;
- RPO: six hours;
- RTO intent: four hours;
- retention expectation: 30 days.

`ramone-memory` is backup-relevant because its Chroma store contains persistent long-term conversation memory that cannot be reconstructed from Git. The approved intent is:

- backup frequency: 24 hours;
- maximum backup age: 24 hours;
- RPO: 24 hours;
- RTO intent: eight hours;
- retention expectation: 30 days.

These values are recovery policy intent only. Until a future owner-approved producer or provider adapter supplies redacted live evidence, neither target may be described as having a proven production backup.

## Backup metadata fixtures

`policy/backup-metadata.schema.json` defines the redacted local metadata shape.

Metadata records include target, service, and public repository identity; backup and observation timestamps; a redacted HTTPS evidence reference; SHA-256 digest; retention metadata; restore source; and bounded file and byte expectations.

Metadata absence, parse failure, identity mismatch, unsafe path, future or misordered timestamp, missing retention, expired retention, digest mismatch, or restore failure is explicit non-healthy evidence. The auditor never fills an unknown backup timestamp with the audit time.

## BackupEvidence

Every enabled target produces a record conforming to `contracts/v1/backup-evidence.schema.json`.

The producer output includes:

- target ID, service ID, and public repository;
- backup and audit timestamps;
- freshness, retention, and restore-drill states;
- SHA-256 digest and redacted evidence reference when available;
- source type and aggregate result state;
- bounded sorted errors and warnings;
- runbook reference.

Missing evidence uses explicit `null` timestamps and references plus an `unknown` or `unavailable` result. It never uses fabricated success data.

State meanings are:

| Dimension | States |
|---|---|
| Freshness | `fresh`, `stale`, `unknown`, `unavailable` |
| Retention | `met`, `violated`, `missing`, `unknown` |
| Restore drill | `passed`, `failed`, `unavailable`, `not-run` |
| Result | `healthy`, `warning`, `failed`, `stale`, `unavailable`, `unknown` |

Aggregate precedence is `failed`, `unavailable`, `stale`, `warning`, `unknown`, then `healthy`. Informational classification exclusions do not degrade the aggregate. Explicit coverage gaps do.

With the reviewed 21 July 2026 fixture policy, all six fixture targets pass and all required services have either a target or an approved no-backup rationale, so the deterministic fixture report is healthy.

That result means the policy and synthetic recovery mechanics are complete. It does not mean live production backups have been observed.

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

Provider lifecycle configuration is not inferred. Unknown provider retention is missing or unknown, not met.

## Disposable restore drills

Supported local adapters are:

- GitHub artifact manifest parsing;
- Cloudflare KV-shaped JSON export validation;
- incident JSON export validation;
- Chroma/vector-store manifest, collection, JSONL, dimension, checksum, count, and size validation;
- bounded ZIP extraction for allowlisted future fixture targets.

Every drill creates a new `tempfile.TemporaryDirectory`, restores only under a new child path, emits no temporary path in its report, and removes the entire directory on exit.

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

## Findings and runbooks

Findings conform to `contracts/v1/finding.schema.json`, use deterministic fingerprints, contain no backup payload, and route to focused runbooks.

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

`--now` is required so freshness tests and evidence are reproducible. Targets, evidence, findings, errors, warnings, and JSON keys are sorted. A second run with the same inputs produces byte-identical JSON and Markdown.

## Workflow integration

The weekly `estate-policy.yml` workflow compiles the auditor, runs the complete unit-test suite, and runs the fixed-time fixture audit. It has:

- `contents: read` only;
- a bounded job timeout;
- estate-policy concurrency without cancellation;
- immutable GitHub-owned action pins;
- bounded artifact retention;
- no provider or backup credential for fixture validation.

The fixed timestamp validates the fixture scenario and does not claim live freshness.

## Future provider integration

Provider integration is deliberately separate from fixture assurance. A later owner-approved phase must add one target-scoped, metadata-only adapter at a time, with fixtures, redaction, timeouts, rate limits, and no restore, write, or delete permission.

Potential secret names and minimum scopes, not created by the fixture phase:

- `GH_BACKUP_AUDIT_READ_TOKEN`: selected repositories, GitHub `Metadata: read`, `Contents: read`, and `Actions: read` for artifact metadata only;
- `CF_BACKUP_AUDIT_READ_TOKEN`: the narrowest available read scope for an explicitly approved Cloudflare backup metadata target;
- a target-specific read credential only when the producer cannot publish redacted metadata itself.

Private production data must not be downloaded by default. Prefer producer-emitted redacted timestamps, counts, retention facts, stable references, and digests.

Any disposable live-data restore rehearsal requires separate owner approval, isolated non-production storage, data-handling review, and a new threat model.

## Migration state

The fixture-phase recovery classification is complete:

1. Public runtime and backup-relevant services have a reviewed coverage decision.
2. `atlas-notify` and `ramone-memory` have owner-approved recovery intent and separate synthetic fixtures.
3. Reconstructable or derived services carry explicit no-backup rationales.
4. The canonical fixture audit no longer depends on `not-declared` warning states.
5. Live provider backup evidence remains a separate future phase.

No deployment, secret creation, provider migration, or live restoration is part of this classification change.

## Rollback

Before merge, discard the feature branch after review. After merge, revert the focused backup-classification commit set if necessary.

No provider, route, secret, backup object, live data, deployment, or scheduled frequency needs rollback because fixture mode never mutates them.

## Known limitations

- Fixture success does not prove any live backup exists.
- No provider backup metadata, object, namespace, artifact, Durable Object, local vector store, or private incident is accessed in fixture mode.
- Restore drills validate representative shapes, not application startup or measured full recovery time.
- RPO and RTO are declared intent; fixture drills do not measure actual production recovery time.
- Provider retention evidence can differ from declared policy; future adapters must report unknown when metadata is unavailable.
- ZIP support is fixture-only and deliberately rejects symlinks, executable entries, encryption, overwrites, traversal, and oversized extraction.
