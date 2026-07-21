# Worker contract enforcement

Wave 3 moves public Worker contracts from documentation convention into deploy-time validation.

## Authority

`atlas-infra/.github/workflows/deploy-worker.yml` remains the canonical reusable Cloudflare Worker pipeline. Callers opt into contract gates explicitly; the workflow does not infer public requirements from account membership or repository visibility.

The public estate declaration in `atlas-api-public/data/estate.manifest.json` remains the authority for which components are intentionally published and which public contract URLs exist.

## Deployment rule

Contract validation runs after `wrangler deploy --dry-run --outdir dist` and before any Cloudflare deployment step.

The validator reads only the generated deploy bundle. It does not call a live endpoint, require provider credentials, read secrets, or mutate Cloudflare state.

A failed required contract blocks the deploy job because `deploy` depends on the complete `validate` job.

## `require_meta`

A caller that sets:

```yaml
with:
  require_meta: true
```

asserts that its deploy candidate must preserve the Atlas `/_meta` contract.

The bundle must contain the `/_meta` route marker and the fixed fleet-wide metadata shape markers:

- `name`;
- `description`;
- `version`;
- `endpoints`;
- `status`;
- `source`.

This is a deploy-artifact check. It catches accidental removal of the route or fixed contract fields before Wrangler is allowed to publish the Worker.

## `require_openapi`

A caller that sets:

```yaml
with:
  require_openapi: true
```

asserts that its deploy candidate must preserve the versioned public OpenAPI surface.

The bundle must contain:

- `/v1/openapi.json`;
- the `openapi` document marker;
- the `paths` document marker;
- an OpenAPI 3.0 or 3.1 version marker.

`atlas-api-public` is the current public API authority and is the intended caller for this gate.

## Rollout order

Wave 3 uses a staged source rollout while keeping production deployment separately owner-gated.

1. Merge and pin the reusable Atlas Infra contract gates.
2. Enable `require_meta` and `require_openapi` on `atlas-api-public`.
3. Enable `require_meta` on `atlas-api-index`.
4. Verify the caller PR checks against the exact merged Atlas Infra revision.
5. Extend `require_meta` to the remaining intentionally public Worker callers whose manifest records declare `meta_url`.
6. Merge caller changes only with explicit awareness that Worker repositories may deploy on `main` push.
7. Observe the real deployment run and then verify the declared live contract surface before marking rollout live-verified.

## Public/private boundary

This enforcement applies to intentionally public Worker contracts. A private Worker is not required to expose `/_meta` merely because it exists in the same Cloudflare account.

Account discovery is not publication authority. The public estate manifest and source-owned governance remain the boundary.

## Failure semantics

A contract gate failure means the release candidate is blocked before deployment. It does not mean the currently deployed Worker is unhealthy.

A successful source merge does not prove that a new Worker version is live. Deployment and live verification remain separate states.
