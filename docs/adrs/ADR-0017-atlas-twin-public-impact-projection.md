+++
id = "ADR-0017"
date = 2026-09-12
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-systems"]
services = []
contracts = ["atlas-control-plane/twin-impact-projection/v1"]
policies = ["policy/public-repository-classifications.json"]
+++

# ADR-0017: Publish a bounded public Twin impact projection

## Context

Atlas Twin can calculate change-impact relationships from a change passport,
but the Twin product remains a private, offline-first analysis tool. Atlas
Systems Phase 2.4 needs bounded impact context beside the public Evidence
Console. It must not turn an impact analysis into evidence that a change was
merged, deployed, running, failing, published, or live.

The public plane already has a deterministic static-data projection pattern in
`AtlasReaper311/atlas-api-public`. Adding a separate bounded document to that
path is smaller and safer than creating a Twin Worker, hosted Twin API,
database, or public Twin service. The existing public evidence routes remain
the authority for their own lifecycle and observation contracts; this decision
does not add Twin records to those evidence documents.

## Decision

The accepted public contract is
`atlas-control-plane/twin-impact-projection/v1`, defined and governed by
`AtlasReaper311/atlas-infra` at
`contracts/v1/twin-impact-projection.schema.json`.

`AtlasReaper311/atlas-twin` remains the producer of the projection. Its future
exporter must be an explicit opt-in operation over a validated Twin passport;
it must not publish directly, gain runtime authority, or change the existing
offline and read-only provider boundaries. The private repository identity is
not emitted in the public document. The public `producer_id` value
`atlas-twin` identifies the product capability, not a public repository,
source URL, provider object, or deployment.

`AtlasReaper311/atlas-infra` owns the projection schema, compatibility rules,
deterministic fingerprint rules, public classification authority, ADR
authority, and fail-closed validators. It does not produce Twin analysis and
does not claim that a projection is runtime or live evidence.

`AtlasReaper311/atlas-api-public` remains the serving owner. A dependent
implementation must add the document as the static asset
`data/twin-impact-projection.json` and expose it through the bounded
`GET /v1/evidence/twin-impact` route in the existing public API. This is an
extension of the current static/public serving path, not a new service. The
actual asset must be added to `policy/public-boundary-projections.json` in the
dependent API implementation once it exists; this ADR does not register a
missing projection target.

`AtlasReaper311/atlas-systems` may consume the route for Phase 2.4 only after
the exporter and serving implementation are separately accepted. It must
render Twin impact as a separate context layer from the Evidence Console's
delivery and observation lifecycle.

## Public contract

The projection may contain only:

- the public subject repository and its public base/head object ids, when the
  current public classification authority proves the subject is public;
- bounded public repository, component, and service identifiers that the
  exporter can prove are public through the current classification/topology
  authorities;
- relationship kinds limited to `changed`, `direct-consumer`,
  `indirect-consumer`, and `declared-service`;
- the fixed conclusion `could-be-affected` and public-scope coverage;
- the Twin producer version, passport schema version, passport request
  fingerprint, and generation timestamps;
- provenance for the infra authority commit, classification projection
  fingerprint, public topology source commit, contract policy, static serving
  repository/path, and route; and
- explicit unknown and limitation codes.

The projection must not contain changed-file paths, private repository or
service identities, private topology, PR or review content, comments, tokens,
credentials, provider object ids, free-form private labels, or fields that
describe merge, release, deployment, runtime, failure, publication, or live
state. It must not expose the private Twin source identity as a public
repository relationship.

## Identity, redaction, and unknowns

The exporter must apply the current
`policy/public-repository-classifications.json` before writing any public
identity. The projection binds that file's fingerprint and the public
topology source commit in `provenance`. The source subject uses a public
repository plus base/head object ids only after public classification is
available. A private or unclassified subject uses `visibility =
private-or-unknown` and null repository/object ids.

Private or unclassified affected entities are dropped, not renamed,
generalised into a guessed public entity, or represented by a private
identifier. If dropping them means the public view is incomplete, the
projection uses `partial-public-scope` and an explicit unknown code. If the
subject or source cannot be established, it uses `unknown` coverage and no
relationships. Missing classification, topology, passport, or private
evidence remains unknown; no later lifecycle state may be inferred from its
absence.

`generated_at` and the passport generation timestamp describe analysis/export
creation. They are not freshness guarantees and are not observation times for
deployment, runtime, or live behaviour. A static API copy does not become
live evidence merely because it is reachable over HTTPS.

## Phase 2.4 claim boundary

Phase 2.4 may claim only that a named public repository/component/service
could be affected within the projection's stated public coverage, and may
show the projection's provenance, generation time, and unknown limitations.

Phase 2.4 may not claim that the subject was merged, approved, released,
published, deployed, running, healthy, failing, live, or causally responsible
for an observed result. It may not treat an empty relationship list as proof
that nothing private or unclassified could be affected, or treat known public
coverage as complete estate coverage. Lifecycle stages and observation
results remain governed by ADR-0013 and ADR-0014 and must be displayed and
validated independently.

## Consequences

The public contract gives Phase 2.4 a small, stable impact context without
making the private Twin repository or analysis graph a public service. The
separate schema and route prevent impact context from being mistaken for the
existing public evidence lifecycle.

The contract is intentionally conservative: public consumers may see less
than Twin knows. That loss is explicit through coverage and unknown codes.
The contract does not grant any repository permission, provider access,
publication authority, deployment authority, runtime authority, or live
verification authority.

## Dependent implementation issues

The smallest first dependency is an `atlas-twin` issue titled **Add explicit
public-safe Twin impact projection exporter**. It must consume this exact v1
schema, use current public classification/topology inputs, and fail closed as
described above.

That is followed by an `atlas-api-public` issue titled **Serve the versioned
Twin impact projection through the existing public API static projection path**
and an `atlas-systems` issue titled **Consume Twin impact context in Evidence
Console Phase 2.4**. Those issues are separate repository changes and are not
implemented by this ADR.
