+++
id = "ADR-0010"
date = 2026-08-17
status = "superseded"
visibility = "internal"
repositories = ["AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-api-public"]
services = []
contracts = []
policies = []
+++

# ADR-0010: Atlas Twin owns change-impact passports within offline authority boundaries

## Context

Atlas Systems needed a local, evidence-backed answer to what a proposed change
affects, why that conclusion is trusted, what evidence is missing, and what
validation remains separately approval-gated. Stage 1 delivered an offline
change-passport simulator in the private repository `AtlasReaper311/atlas-twin`.

Atlas Twin Stage 2 is now merged on `AtlasReaper311/atlas-twin` main as squash
commit `7c333fa0d39e3281ef82decdc59ae3b3fb1ac1c6`. Version `0.2.0` provides
contract hardening and deterministic passport comparison. No deployment, live
rollout, release, publication, or hosted runtime exists for Twin.

Without an accepted ownership record, later work risks conflating:

- change-impact truth with cinematic rendering;
- Twin analysis with agent-workflow merge or rollout authority;
- topology presentation data with classification authority;
- CI success or source merge with deployment or live behaviour.

Private repositories such as `atlas-twin`, `atlas-motion`, and
`atlas-agent-workflows` remain source-owned and are intentionally absent from
public classification frontmatter. This ADR records the ownership boundary for
public Atlas authorities while naming those private collaborators in the
decision text only.

## Decision

Atlas Twin owns change-impact passports and derived comparison and export
contracts.

`AtlasReaper311/atlas-infra` owns policy, classification, ADR authority, and the
change-impact algorithm consumed by Twin through a pinned local adapter.

`AtlasReaper311/atlas-api-public` supplies topology presentation data only. It
is not classification authority.

`AtlasReaper311/atlas-motion` owns deterministic cinematic rendering and must
not infer missing Twin truth. Motion render output does not prove deployment,
publication, or live state.

`AtlasReaper311/atlas-agent-workflows` owns how passports are attached to
inspection, review, merge, rollout, and handoff gates. Agent workflows do not
rewrite Twin conclusions. Twin does not approve merges or rollouts.

Twin remains offline-first. It performs no provider writes, deployment,
publication, or live observation. Private overlays are opt-in, local-only, and
deferred. Default privacy remains `public_plane_only`.

Motion rendering, CI success, and source merge do not prove deployment or live
behaviour.

## Consequences

Operators and later stages can extend Twin contracts, workbench surfaces, and
optional consumers without relocating impact truth into Motion or agent gates.

Infra retains algorithm and classification ownership. Api-public remains a
topology presentation source. Future Twin ADRs may refine contracts, but they
must preserve the offline-first and non-authority boundaries recorded here.

Costs: Twin must keep adapter compatibility with Infra callables; Motion and
agent-workflow consumers must validate Twin export and attachment contracts in
their owning stages before adoption; private Twin identity remains outside
public registry membership.