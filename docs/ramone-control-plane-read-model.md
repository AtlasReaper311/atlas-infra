# RAMONE control-plane read model

Status: source implementation only, offline, dry-run only, not deployed.

## Purpose

`atlas-api-public` cannot serve meaningful RAMONE control-plane results until a
bounded producer creates `control-plane:read-model:v1`. This source stage adds
the deterministic producer and its contracts without adding a Cloudflare API
client, KV writer, workflow dispatch, credential, schedule, or deployment.

## Ownership

`AtlasReaper311/atlas-infra` owns:

- the canonical `ControlPlaneSummary` contract;
- the RAMONE read-model and collection-source schemas;
- `policy/control-plane-read-model.json`;
- `scripts/control_plane_read_model.py`;
- fixture sources, expected output, tests, and rollback guidance.

`atlas-api-public` will remain a bounded reader. A later publisher may write one
exact key only after a separate source PR and owner approval. RAMONE never
receives Cloudflare or other provider credentials.

## Input boundary

The producer accepts three roots:

1. the existing eleven `ControlPlaneSummary` source documents;
2. exactly eight collection-source documents declared by policy;
3. the current public repository classification and estate registry authority.

Unexpected JSON files, missing files, malformed documents, unsafe relative
paths, private identities, machine-local values, unapproved reference origins,
and secret-bearing fields all fail closed. No output is written after a failed
validation.

The collection order is fixed:

- `services`;
- `releases`;
- `findings`;
- `quota`;
- `backups`;
- `gardener_proposals`;
- `runbooks`;
- `evidence`.

Only services marked `public_surface: true` and repositories present in the
public classification projection may enter the read model. This preserves the
accepted public and private estate boundary.

## Deterministic identity

Every source receipt records:

- source ID and policy-relative path;
- source schema version;
- generated and stale-after timestamps when present;
- effective state;
- required status;
- canonical SHA-256 fingerprint.

The producer sorts receipts by source ID, hashes the complete receipt list into
`source_fingerprint`, then hashes the complete model excluding only
`read_model_fingerprint`. Identical inputs, source revision, and `--now` value
produce byte-identical output and receipts.

Expired collection sources are reclassified as stale, and their item states are
raised to at least stale. Missing or malformed required sources abort the run.
The complete model is limited to 65,536 bytes.

## Local dry run

```bash
python3 scripts/control_plane_read_model.py \
  --summary-sources tests/fixtures/control-plane-summary/sources \
  --collection-sources tests/fixtures/control-plane-read-model/collections \
  --authority-root tests/fixtures/control-plane-read-model/authorities \
  --source-revision aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --now 2026-07-14T10:30:00Z \
  --output /tmp/control-plane-read-model.json \
  --receipt /tmp/control-plane-read-model-receipt.json
```

The fixture run is retained at:

- `tests/fixtures/control-plane-read-model/expected/read-model.json`;
- `tests/fixtures/control-plane-read-model/expected/dry-run-receipt.json`.

The receipt must always state:

```json
{
  "mode": "dry-run",
  "bounded_kv_key": "control-plane:read-model:v1",
  "provider_write_performed": false
}
```

## Validation

```bash
python3 -m py_compile scripts/control_plane_read_model.py
python3 -m unittest discover -s scripts/tests -v
python3 scripts/validate_control_plane_contracts.py
```

The focused tests cover deterministic output, exact fixture bytes, canonical
fingerprints, schema validation, source inventory rejection, secret and local
value rejection, public identity enforcement, stale propagation, source
revision validation, output bounds, and local-only CLI artifacts.

## Future publisher boundary

This change deliberately does not implement publication. The later publisher
must be a separate focused change and must:

- accept only a reviewed read-model artifact and exact expected digest;
- revalidate schema, freshness, source and model fingerprints;
- allow only `control-plane:read-model:v1` in the approved namespace;
- expose no arbitrary key, namespace, delete, list, or payload input;
- run manually behind an approval environment;
- retain a redacted write and read-back receipt;
- remain separate from the public API Worker and from RAMONE.

Source approval is not approval for the first KV write.

## Rollback

Before any publisher exists, rollback is a normal revert of the producer source
PR. No provider state exists to remove.

After a future publisher rollout, disable that publisher first. Preserve the
source evidence and previous read-model receipt. Do not add a fallback provider
call to `atlas-api-public`, and do not give RAMONE a provider credential to
compensate for unavailable data.
