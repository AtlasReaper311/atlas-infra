# Contract registry

## Architecture and ownership

`AtlasReaper311/atlas-infra` owns the canonical estate declaration, the
repository classification model, ServiceContract records, route ownership,
offline validation, dependency graph, local service catalogue, findings, and
runbooks.

The registry has three deliberately different views:

1. `policy/estate-registry.json` declares all 35 approved repositories and
   maps runtime repositories to stable service IDs.
2. `policy/service-contracts/*.json` declares runtime ownership, routes,
   dependencies, metadata, journeys, quota/secret/backup links, and escalation
   policy. Every file validates against
   `contracts/v1/service-contract.schema.json`.
3. `atlas-api-index` remains observed Worker state. It can disagree with the
   declaration without overwriting it. `atlas-api-public` keeps its current
   bounded live registry route; Phase 6 does not publish internal catalogue
   fields or add a new endpoint.

`atlas-dep-audit` is not changed in Phase 6. The existing `atlas-infra`
estate-policy workflow now validates the registry offline before its live
repository conformance scan. This keeps malformed policy fail-closed without
making optional live data part of registry correctness.

## Repository classification

Classification uses independent axes:

- `lifecycle`: `production`, `active`, `experimental`, `deprecated`, or
  `archived`;
- `scope`: `public` or `internal`;
- `provenance`: `original` or `external-derived`.

`scope: public` describes the approved product/repository classification. The
separate `public_surface` flag records whether the repository currently owns
an HTTP, Pages, or other user-facing surface. An internal service can own a
bounded public read only when its ServiceContract contains an exact
origin/path exception approved by the owner.

Each repository entry records its full name, local directory name, owner,
purpose, runtime and contract flags, service IDs, public-surface flag,
deployment/evidence owners, runbook, notes, and exclusions. Null values mean
the field does not currently apply; they are not guessed values.

## ServiceContract format

Phase 6 adds optional v1 properties. Existing v1 instances remain valid, while
canonical registry contracts must provide them:

- HTTPS `origin` on every active route;
- environment list;
- explicit known, unknown, or not-applicable health and metadata endpoints;
- expected metadata shape;
- journey coverage state and references;
- quota policy and secret declaration state/link;
- backup relevance and its evidence link when known;
- release-watch eligibility;
- bounded escalation metadata;
- exact internal/public route exceptions;
- notes that preserve unknowns and exclusions.

Routes are owned by the tuple `(origin, path, method)`. A path without an
origin cannot enter the canonical registry. Route declarations, methods,
dependencies, service IDs, runbooks, and exceptions are sorted so review and
generated output stay deterministic.

## Validation policy

`scripts/validate_contract_registry.py` uses only the Python standard library
and local files. It validates:

- the 35-repository inventory and three classification axes;
- registry and ServiceContract schemas;
- missing or duplicate service IDs and contracts;
- non-runtime contracts without an explicit exception;
- repository/contract owner and classification agreement;
- duplicate route ownership;
- deprecated, archived, or external-derived active ownership;
- public routes on internal services without exact exceptions;
- production runtime runbooks;
- release-watch metadata requirements;
- unknown dependency service IDs;
- sorted inputs, deterministic findings, and idempotent output.

Every policy violation is emitted as a `Finding` v1 record with a stable
fingerprint and focused runbook. The validator checks its own findings against
`contracts/v1/finding.schema.json` before reporting success.

Run the full local report:

```bash
python3 scripts/validate_contract_registry.py \
  --registry policy/estate-registry.json \
  --contracts policy/service-contracts \
  --report /tmp/registry-report.json \
  --markdown /tmp/registry-report.md \
  --graph /tmp/service-dependency-graph.json \
  --catalog /tmp/service-catalog.json
```

The graph contains sorted service nodes and dependency edges. The catalogue is
a local complete view and can contain internal service names. It must not be
served publicly without a separately reviewed projection that includes only
approved public service IDs, routes, declared state, and already-public
metadata endpoints.

## Add a repository

1. Add one sorted entry to `policy/estate-registry.json` with all required
   fields and independent classifications.
2. Increase `approved_repository_count` and update the approved inventory in
   `scripts/contract_registry.py` only after owner approval.
3. If it is not a runtime service, keep `contract_required: false` and
   `service_ids: []`.
4. Run the registry validator and unit tests.
5. Review the dependency graph and catalogue diff before committing.

## Add a runtime service

1. Mark the repository `runtime_service: true`, `contract_required: true`, and
   add one or more stable sorted service IDs.
2. Create `policy/service-contracts/<service-id>.json` from committed source
   evidence. Do not infer a hostname, route, metadata endpoint, dependency, or
   release identity.
3. Use explicit `unknown` or `not-applicable` endpoint states where evidence is
   absent.
4. Add exact route exceptions for any internal service that owns a public read.
5. Add a production runbook reference and the relevant negative tests.
6. Run the full offline validation command twice and compare outputs.

## Deprecate a service

1. Change the registry and contract lifecycle together.
2. Remove active route ownership before marking the service deprecated.
3. Set `registry_visibility: historical` when history should remain visible.
4. Disable new features, default assurance, Gardener remediation, and
   deployment orchestration when retirement policy requires it.
5. Preserve attribution and licence references for external-derived code.
6. Remove or redirect public routes in the owning repository only through a
   separate approved change; Phase 6 does not mutate them.

## simple-proxy

`simple-proxy` is retained as a historical runtime dependency so attribution
and prior dependency edges remain explainable. Its registry and contract are
fixed to deprecated, internal, and external-derived. It owns no routes, public
surface, metadata endpoint, release watch, default assurance, Gardener action,
deployment orchestration, or new features. Its cost and secret policy links
point only to the existing explicit exclusion records.

## Live reconciliation limitations

Phase 6 performs no GitHub, Cloudflare, or public endpoint calls. The canonical
routes come from committed Wrangler/router/README evidence inspected on 14 July
2026. A missing value remains unknown.

A later approved read-only reconciliation needs these names and permissions:

- `GH_CONTRACT_READ_TOKEN`: selected-repository `Metadata: read` and
  `Contents: read` only;
- `CF_CONTRACT_READ_TOKEN`: account `Workers Scripts Read` and zone
  `Workers Routes Read` only;
- `CF_ACCOUNT_ID` and `CF_ZONE_ID`: identifiers, not credentials.

Exact read-only commands for a later approved run are:

```bash
GH_TOKEN="$GH_CONTRACT_READ_TOKEN" gh api --method GET \
  /repos/AtlasReaper311/REPOSITORY/contents/wrangler.toml?ref=main
curl --fail --silent --show-error \
  -H "Authorization: Bearer $CF_CONTRACT_READ_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/scripts"
curl --fail --silent --show-error \
  -H "Authorization: Bearer $CF_CONTRACT_READ_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/workers/routes"
curl --fail --silent --show-error https://SERVICE_HOST/_meta
```

Replace placeholders only after approving the target list. Do not write token
values to reports, shell history, Git, or logs. Live absence must produce
unknown/unavailable drift and must never delete or rewrite canonical data.

## Phase 8 backup-audit integration

`scripts/backup_audit.py` consumes this registry and its ServiceContracts
offline. Every enabled backup target must resolve to the exact registered
repository and service ID, match all three classification axes, and reference
an existing runbook. Production runtime services and records already marked
backup-relevant receive an explicit coverage entry in
`policy/backup-audit.json`; `not-declared` is a warning and never healthy.

`simple-proxy` remains historically visible but excluded from active drills.
No Phase 8 check changes registry ownership, probes a route, or infers a live
backup from `backup_relevance: relevant`.

## Migration

1. Merge the `atlas-infra` registry after review.
2. Let the estate-policy workflow validate the local registry before its live
   conformance scan.
3. Migrate other consumers from the legacy public manifest in separate focused
   changes. Keep adapters dual-readable during that window.
4. Reconcile the existing release-target map with `release_watch_eligible`
   only after each service proves complete release identity metadata.
5. Add a bounded public catalogue projection only after field-level redaction
   and route tests are approved in `atlas-api-public`.

## Rollback

Before merge, discard the uncommitted feature branch after review. After merge,
revert the focused `atlas-infra` commit. That restores the estate-policy
workflow's legacy manifest input and removes the registry gate. ServiceContract
additions are optional within v1, so older readers continue to accept the
previous instances. No provider, route, secret, deployment, or live store needs
rollback because Phase 6 changes repository files only.
