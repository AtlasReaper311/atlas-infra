# RAMONE control-plane read model

Status: producer and manual publisher source implemented; no production artifact,
GitHub environment, credential, workflow dispatch, KV write, API deployment, Home
Assistant installation, or Open WebUI assignment is proven by source state.

## Purpose

`atlas-api-public` cannot serve meaningful RAMONE control-plane results until a
bounded producer creates `control-plane:read-model:v1` and an independently
approved publisher writes that exact artifact to the existing public API KV
namespace. The producer and publisher remain separate programs and separate
approval surfaces.

## Ownership

`AtlasReaper311/atlas-infra` owns:

- the canonical `ControlPlaneSummary` contract;
- the RAMONE read-model, collection-source, and publication-receipt schemas;
- `policy/control-plane-read-model.json`;
- `policy/control-plane-read-model-publisher.json`;
- `scripts/control_plane_read_model.py`;
- `scripts/control_plane_read_model_publisher.py`;
- fixture sources, expected output, tests, receipts, and rollback guidance.

`atlas-api-public` remains a bounded reader. RAMONE never receives Cloudflare or
other provider credentials.

## Producer input boundary

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
public classification projection may enter the read model.

## Deterministic identity

Every source receipt records the source ID, policy-relative path, schema version,
generated and stale-after timestamps, effective state, required status, and
canonical SHA-256 fingerprint.

The producer sorts receipts by source ID, hashes the complete receipt list into
`source_fingerprint`, then hashes the complete model excluding only
`read_model_fingerprint`. Identical inputs, source revision, and `--now` value
produce byte-identical output and receipts.

Expired collection sources are reclassified as stale, and their item states are
raised to at least stale. Missing or malformed required sources abort the run.
The complete model is limited to 65,536 bytes and a maximum freshness window of
600 seconds.

## Local dry run

```bash
python3 scripts/control_plane_read_model.py \
  --summary-sources tests/fixtures/control-plane-summary/sources \
  --collection-sources tests/fixtures/control-plane-read-model/collections \
  --authority-root tests/fixtures/control-plane-read-model/authorities \
  --source-revision aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --now 2026-07-14T10:30:00Z \
  --output /tmp/control-plane-read-model.json \
  --receipt /tmp/dry-run-receipt.json
```

A publisher-eligible workflow artifact has the fixed name
`ramone-control-plane-read-model` and contains exactly:

- `control-plane-read-model.json`;
- `dry-run-receipt.json`.

The producer receipt must always state `mode: dry-run`, name only
`control-plane:read-model:v1`, and state `provider_write_performed: false`.

## Manual exact-digest publisher

`.github/workflows/publish-control-plane-read-model.yml` has only a
`workflow_dispatch` trigger. It has no push, pull-request, schedule, automatic
follow-up, delete, list, bulk, generic URL, generic key, generic namespace, or
request-body input.

The operator supplies only:

- the numeric ID of a successful `atlas-infra` workflow run on `main`;
- the exact SHA-256 digest of `control-plane-read-model.json`;
- the exact `read_model_fingerprint` reviewed in that artifact;
- the fixed confirmation phrase `publish-control-plane-read-model-v1`.

The preflight job has no provider credential. It downloads only the fixed
artifact name from the same repository and rejects any bundle with extra or
missing files. It revalidates:

- file digest and canonical model fingerprint;
- source fingerprint and producer receipt agreement;
- canonical JSON Schema;
- public-only leak controls;
- full source revisions;
- byte limit;
- generated and stale-after timestamps;
- the 600-second maximum freshness window.

The write job is protected by the GitHub environment
`ramone-control-plane-publish`. After approval it downloads the artifact again
and repeats the entire validation, so an artifact that becomes stale while
waiting for approval fails before provider access.

The publisher then performs exactly three provider operations against one fixed
URL derived from policy:

1. `GET` the current value for rollback evidence;
2. `PUT` the reviewed bytes to `control-plane:read-model:v1`;
3. `GET` the same key and require byte-for-byte equality.

The fixed authority is:

- Cloudflare account `49e221b7e55a9e5c45b88d08efca5771`;
- KV namespace `33fa7cbf66fc495ea0304a5f95ffc9a8`;
- API route family `/accounts/{account}/storage/kv/namespaces/{namespace}/values/{key}`;
- token secret name `CF_RAMONE_CONTROL_PLANE_KV_WRITE_TOKEN`;
- required permission `Workers KV Storage Write` for the one Atlas account.

The token value is never accepted as an argument, printed, written to a receipt,
or exposed to RAMONE. It must be created through an approved interactive GitHub
secret prompt after separate approval.

## Evidence

Preflight and successful publication produce receipts conforming to
`control-plane-read-model-publication-receipt.schema.json`. Receipts include:

- source workflow run ID and head SHA;
- exact artifact, source, and read-model fingerprints;
- source revision and freshness timestamps;
- fixed key and redacted account and namespace suffixes;
- whether a previous value existed and its digest;
- whether a provider write occurred;
- whether exact read-back verification succeeded.

Receipts never contain the token, authorization headers, raw previous values, or
arbitrary provider response bodies.

## Validation

```bash
python3 -m py_compile \
  scripts/control_plane_read_model.py \
  scripts/control_plane_read_model_publisher.py
python3 -m unittest discover -s scripts/tests -v
python3 scripts/validate_control_plane_contracts.py
```

The publisher tests cover exact digest and fingerprint approval, strict bundle
inventory, freshness, leak rejection, producer-receipt agreement, fixed provider
URL construction, GET-PUT-GET sequencing, exact read-back, confirmation and token
refusal, receipt schema validation, and static workflow boundaries.

## Approval and rollout boundary

Merging publisher source does not create the protected environment or secret,
does not create a production source artifact, and does not dispatch the workflow.
The first qualifying dry-run artifact, environment configuration, token creation,
and first KV write are separate Phase 5B approval gates.

## Rollback

Before any publisher dispatch, rollback is a normal source revert and no provider
state exists.

After a successful write, retain the redacted receipt and the separately reviewed
previous artifact. Rollback is another exact-digest publication of that previous
artifact through the same protected workflow. The publisher exposes no delete or
arbitrary overwrite path. Disable the workflow or set
`RAMONE_CONTROL_PLANE_PUBLISH_FREEZE=true` before investigating an incident.
