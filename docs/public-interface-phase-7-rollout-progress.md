# Public interface programme Phase 7 rollout progress

Status: implementation merged; production verification pending.

Recorded: 30 July 2026.

## Confirmed merge receipts

| Repository | Pull request | Reviewed head | Merge commit |
| --- | ---: | --- | --- |
| `atlas-article-gen` | #39 | `32dcd47a712406b6f82e79f3984546116e9729d2` | `9de98a02fc9bdf4430624d2383aafc2528529d61` |
| `atlas-systems` | #178 | `7bac8f67b97b4e1c9d58d1d012bb8f8338111059` | `8154b47e2ba62cbc89d893d06acbf97e73ed3b62` |
| `status` | #32 | `f19bbe3046d3f0a95f6bf813cfebbf855aeb6ea4` | `4ee696150006dd72fe7b0d75eb0b5c5199f36747` |
| `atlas-doc-viewer` | #31 | `34fead329ae73f9e7f1900cb786822e3438e16e9` | `ccf1b036d98cf0b1404089b561dbfe47c2f07432` |
| `ramone-edge` | #30 | `665eb8e4f29af5084a9ac5e5642380d7ba025c8f` | `e0e02775587178670aba09ddf49c37238b3f3e4a` |
| `atlas-api-public` | #52 | `2270141b36feb96a50b3858b2f89c6e0e73e56d5` | `5b970a9bf3b66b5469ce883aacec4a4b496e72cc` |

Every merge was bound to the reviewed pull-request head SHA.

## Generator and scheduler outcome

Merging `atlas-article-gen` PR #39 triggered the expected generator pipeline.

Confirmed follow-up commits:

- generator regeneration: `5c32b7109be2e9772a3d7e03142bfabb78032bae`;
- scheduler synchronization: `ec901c6a087ce01ad13a1d9dceae15e5c85b8fd4`.

The scheduler synchronization changed only unpublished files below `scheduled/`. It did not add a published-refresh bundle.

The production publishing workflow remains schedule- or dispatch-owned. It is not triggered by a scheduler repository push. No production scheduler dispatch was performed during this rollout.

Before the separate `atlas-systems` Phase 7 merge, the site repository remained at `6994d522492d999b6e9b0527d668b82b2f705417`. Therefore the generator and scheduler stage did not publish or refresh an article.

## Consumer deployment contracts

The merged consumer repositories each declare production deployment on a push to `main`:

- `atlas-systems` uses the governed Pages deployment and custom-domain verification pipeline;
- `status` uses the governed static Pages pipeline for `status.atlas-systems.uk`;
- `atlas-doc-viewer` uses the governed static Pages pipeline for `cv.atlas-systems.uk`;
- `ramone-edge` uses the pinned Wrangler action for its production Worker;
- `atlas-api-public` uses the governed Worker deployment contract with lint, metadata, and OpenAPI requirements.

Source merge therefore authorized and triggered each repository-owned deployment path. A source merge is not recorded here as proof that the deployment completed.

## Current evidence boundary

The connected GitHub interface available to this run exposes pull-request workflow evidence but not push-triggered workflow-run listings. The current execution runtime also cannot resolve the Atlas custom domains.

Consequently, this record does not claim:

- successful completion of any post-merge deployment run;
- that the custom domains are serving the merge commits;
- live HTML or JSON behavior on the new error routes;
- completed production browser evidence.

No rollback or intervening source commit appeared after the six implementation merges at the time this record was written.

## Required production verification

Phase 7 remains open until the following evidence is recorded:

1. `atlas-systems` deployment run succeeded for `8154b47e2ba62cbc89d893d06acbf97e73ed3b62` and the custom domain exposes that build commit.
2. Representative main-site routes expose the expected icons, canonical identity, and 404 behavior.
3. Status deployment succeeded for `4ee696150006dd72fe7b0d75eb0b5c5199f36747` and an unknown route serves the noindex Status 404.
4. CV deployment succeeded for `ccf1b036d98cf0b1404089b561dbfe47c2f07432` and an unknown route serves the noindex script-free CV 404 without requesting the PDF.
5. Ramone deployment succeeded for `e0e02775587178670aba09ddf49c37238b3f3e4a`; browser navigation receives HTML while API-style unknown requests remain JSON.
6. Public API deployment succeeded for `5b970a9bf3b66b5469ce883aacec4a4b496e72cc`; only unknown browser paths below `/v1/docs/*` receive HTML and machine API paths remain JSON.
7. The API index JSON-only evidence remains green at `96cd81f643429895847a1c2f143084d6e995005c`.

## Boundary

Phase 8 must not begin until production verification is complete and the Phase 7 closeout is merged.

Do not run the scheduler in production, publish or refresh articles, change provider configuration, or modify secrets as part of this remaining verification step.
