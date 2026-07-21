+++
id = "ADR-0004"
date = 2026-07-21
status = "accepted"
slug = "public-repository-classification-authority"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-infra"]
services = ["atlas-api-public"]
contracts = ["atlas-control-plane/service-contract/v1"]
policies = ["policy/estate-registry.json", "policy/public-assurance-repositories.json", "policy/public-repository-classifications.json"]
+++

# ADR-0004: Public repository classification authority

## Context

Public repository lifecycle, scope, and provenance have been represented in more than one repository. The public runtime registry in `atlas-infra` carries those classification axes, while the public topology manifest in `atlas-api-public` has also carried manually maintained lifecycle values. Public source-only repositories were additionally treated as `production` by topology code even though they are not runtime services.

That creates avoidable drift. A topology or presentation document must not become a second authority for repository governance.

The accepted public/private boundary remains unchanged. Private repository classification is source-owned in the authenticated private repository and is not projected into public policy.

## Decision

`AtlasReaper311/atlas-infra` is the sole public authority for repository lifecycle, scope, and provenance.

Public runtime repositories are classified in `policy/estate-registry.json`.

Public non-runtime repositories that participate in default public assurance are classified in `policy/public-assurance-repositories.json`. These two source sets must not overlap.

`policy/public-repository-classifications.json` is a deterministic generated projection of those two authoritative inputs. It is not an independent authoring surface. The projection records a SHA-256 fingerprint of the canonical classification material and must be regenerated whenever either authority input changes.

Downstream public repositories may consume a verified copy of that projection when runtime packaging prevents direct cross-repository imports. Their CI must prove that the copy matches the current `atlas-infra` projection before it can be treated as current classification evidence.

`atlas-api-public/data/estate.manifest.json` remains the topology and presentation declaration. A repository-backed manifest component must not independently author lifecycle, scope, or provenance. Those values are projected from the Atlas Infra classification authority. Repository-less documented components may retain presentation state needed by topology output, but that state is not repository governance.

Unknown repository classification fails closed. No downstream consumer may infer `production`, `active`, scope, or provenance from repository visibility, manifest membership, account membership, or the existence of a deployed runtime.

## Consequences

A lifecycle change is made once in the applicable Atlas Infra authority input and then propagated through the generated projection.

Public non-runtime repositories receive explicit lifecycle classification without being inserted into the runtime contract registry or falsely represented as runtime services.

The public topology API can continue to expose lifecycle for compatibility, but repository-backed values are derived from the verified classification projection rather than from manually maintained manifest values.

Projection fingerprints make stale copied classifications detectable without adding volatile timestamps that create meaningless diffs.

Private repository identities remain absent from public classification policy and projections.
