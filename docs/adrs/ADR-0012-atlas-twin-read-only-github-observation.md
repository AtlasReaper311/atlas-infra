+++
id = "ADR-0012"
date = 2026-08-17
status = "accepted"
visibility = "internal"
repositories = ["AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-api-public"]
services = []
contracts = []
policies = []
supersedes = "ADR-0010"
+++

# ADR-0012: Permit explicit read-only GitHub observation without changing Atlas Twin authority

## Context

ADR-0010 established Atlas Twin as the owner of change-impact passports and
related comparison/export contracts while keeping Twin offline-first, free of
provider writes, and outside merge, rollout, deployment, publication, and live
state authority.

Atlas Twin 1.0.0 now closes the local product boundary with stable documented
CLI and versioned passport, graph, compare, archive, and semantic contracts.
Those contracts deliberately encode offline operation and must not be weakened
by later additive stages.

Stage 5 introduces an optional operator workflow that needs current GitHub
pull-request evidence: pull-request identity, base/head refs and object ids,
changed-file metadata, check state, and review state. Reading current provider
state is live observation, so the blanket no-live-observation rule in ADR-0010
cannot remain the complete authority for Stage 5.

The architecture therefore needs a narrow exception that makes the provider
read explicit and auditable without turning Twin into a GitHub controller or
changing the meaning of its existing offline contracts.

## Decision

This ADR supersedes ADR-0010 and carries forward its ownership and authority
boundaries except for the explicit read-only observation exception defined
below.

Atlas Twin continues to own change-impact passports and derived comparison and
export contracts.

`AtlasReaper311/atlas-infra` continues to own policy, classification, ADR
authority, and the change-impact algorithm consumed by Twin through a pinned
local adapter.

`AtlasReaper311/atlas-api-public` continues to supply topology presentation
data only. It is not classification authority.

`AtlasReaper311/atlas-motion` continues to own deterministic cinematic
rendering and must not infer missing Twin truth. Motion output does not prove
deployment, publication, or live state.

`AtlasReaper311/atlas-agent-workflows` continues to own how Twin evidence is
attached to inspection, review, merge, rollout, and handoff gates. Twin does
not approve merges or rollouts.

Twin remains offline-first. Existing Atlas Twin 1.0 request and passport
contracts keep their current offline semantics, including their existing
`network = offline` boundary. Normal `passport`, `inspect`, archive, compare,
doctor, and workbench paths must not gain implicit provider access.

Stage 5 may perform GitHub observation only through a dedicated operator-
requested provider-read path with an explicit network opt-in. That path is
read-only and may obtain only the minimum pull-request evidence required for
inspection: repository and pull-request identity, base/head refs and object
ids, changed-file metadata, check state, and review state. It must not ingest
comment bodies, review bodies, secret values, credentials, or unrelated private
overlays by default.

GitHub observation uses an already-authenticated operator session or equivalent
approved read-only provider route. Twin must never request, print, persist,
validate, or expose token values. Missing authentication, unavailable provider
state, insufficient access, or incomplete evidence fails closed as
`unavailable`; Twin must not guess the missing state.

Stage 5 GitHub evidence is additive evidence, not a rewrite of the stable
offline passport contract. It must use a separately versioned Twin-owned
provider-evidence contract. Provider observations may inform an operator what
GitHub currently reports, but they must not alter Atlas Infra policy or
classification truth, manufacture deployment/live state, or convert check or
review status into merge, deployment, publication, or rollout approval.

Twin performs no provider writes. The Stage 5 provider-read path must not
comment, label, submit reviews, merge, push branches, dispatch workflows,
create releases, deploy, publish, or mutate GitHub or any other provider.
Default privacy remains `public_plane_only`.

CI success, source merge, GitHub check state, review state, Motion output, and
Twin provider evidence do not prove deployment or live behaviour.

## Consequences

Operators gain an explicit way to attach current GitHub pull-request evidence
to Twin inspection without changing the deterministic offline behaviour that
Atlas Twin 1.0 established.

Stage 5 implementation must keep the network-capable adapter isolated from
existing offline paths, add deterministic tests that reject provider mutation
operations, minimise retained provider metadata, and preserve clear provenance
between local/source authority and observed GitHub evidence.

The provider-read path depends on network availability, provider availability,
and an already-authenticated operator context. Those dependencies are reported
as evidence availability, not hidden or inferred.

The separate provider-evidence contract may evolve additively within its own
versioning rules. Breaking the stable Atlas Twin 1.0 offline contracts still
requires the compatibility process defined by Twin; this ADR does not grant an
exception.

Costs: Stage 5 introduces a deliberately bounded network surface that requires
additional security, privacy, provenance, and regression testing. Later agent,
Motion, rollout, or publication stages remain separately owned and separately
approval-gated.