# RAMONE control-plane source reinspection

Date: 2026-08-01

Status: Part 0 source evidence for the Phase 4 reconstruction.

## Current authority

- `atlas-infra/main`: `59caabc2685ac6b250fdf472329a79252efa4dfc`
- `atlas-api-public/main`: `5b970a9bf3b66b5469ce883aacec4a4b496e72cc`
- `ramone-memory/main`: `7b983cd4df1435ea0962ff3179d8570ec8dc0e71`
- `atlas-owui-tools/main`: `cd50e53728557f23a1cb76c4501dd5a5fcbadb3f`

The accepted public and private estate boundary remains ADR-0003 and the
current deterministic classification authority. The read model may include
only public repository identities and services marked as public surfaces.

## Existing implementation

`atlas-infra` already owns the canonical `ControlPlaneSummary` schema, the
offline summary aggregator, fixtures, the nine-operation policy, and the
integration and rollback guidance.

`ramone-memory` already contains the disabled ten-sensor package and dashboard
from PR #2. It has not been proven installed live. The new and legacy packages
both declare `unique_id: atlas_estate_health`, so installation remains blocked
until a source-controlled migration and live entity-registry review exist.

`atlas-owui-tools` now exists as a private source repository. This supersedes
the July repository-only inventory statement that its source owner was
unknown. Current source intent assigns four shared tools to `ramone-text`, only
`postmortem_tool` to `ramone-postmortem`, and leaves `ramone-agent` pipe-managed.
Repository source does not prove the current live Open WebUI database state.

## Stale API pull request

`atlas-api-public` PR #5 remains an open, non-mergeable draft. Its head
`da05d487e9aed3259aea7fe509e2e78e906e9677` is based on
`1d3423afd819ea1120cb5dd7d6c4bea1d7e5e72a`, while current `main` has moved
through 47 later commits.

The original intent remains valid:

- one public bounded summary;
- one dedicated bearer-protected OpenAPI document;
- exactly nine GET-only operations;
- no provider proxy, generic URL, request body, or write method;
- honest `503` when no valid read model exists.

The old route, metadata, OpenAPI, README, and Wrangler patches conflict with
current Trace, reliability, evidence, observability, and public-interface
source. The handwritten fixture is obsolete because it has no reviewed
producer or current source fingerprints. PR #5 must not be rebased or
force-updated.

## Reconstruction decision

The source sequence is:

1. `atlas-infra`: add the bounded read-model contracts, offline producer,
   policy, fixture dry-run artifact, tests, and rollback boundary.
2. A later separate `atlas-infra` change: add a manual exact-digest publisher
   for only `control-plane:read-model:v1`.
3. `atlas-api-public`: reconstruct the current-main reader and nine routes.
4. `ramone-memory`: resolve the entity collision through a focused migration
   PR without altering memory or control behaviour.
5. After the replacement API PR is reviewable, record PR #5 as superseded and
   close it without rewriting the old branch.

Source review is not approval for a KV write, deployment, secret creation,
Home Assistant reload or restart, Open WebUI import, or RAMONE assignment.
