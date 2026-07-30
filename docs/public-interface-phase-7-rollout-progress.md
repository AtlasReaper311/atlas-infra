# Public interface programme Phase 7 closeout

Status: closed.

Recorded: 30 July 2026.

## Outcome

Phase 7 implemented and deployed the accepted browser-identity and metadata contract across the public Atlas Systems browser estate. The rollout completed the main-site identity verifier, product-owned browser error routes, bounded live aggregate-status presentation on error pages, generated Writing metadata, and controlled refreshes of the three already-published generator-owned articles.

The programme did not redesign product interfaces or change machine-facing contracts. Phase 8 may begin only after this closeout pull request is merged.

## Initial implementation receipts

| Repository | Pull request | Reviewed head | Merge commit |
| --- | ---: | --- | --- |
| `atlas-article-gen` | #39 | `32dcd47a712406b6f82e79f3984546116e9729d2` | `9de98a02fc9bdf4430624d2383aafc2528529d61` |
| `atlas-systems` | #178 | `7bac8f67b97b4e1c9d58d1d012bb8f8338111059` | `8154b47e2ba62cbc89d893d06acbf97e73ed3b62` |
| `status` | #32 | `f19bbe3046d3f0a95f6bf813cfebbf855aeb6ea4` | `4ee696150006dd72fe7b0d75eb0b5c5199f36747` |
| `atlas-doc-viewer` | #31 | `34fead329ae73f9e7f1900cb786822e3438e16e9` | `ccf1b036d98cf0b1404089b561dbfe47c2f07432` |
| `ramone-edge` | #30 | `665eb8e4f29af5084a9ac5e5642380d7ba025c8f` | `e0e02775587178670aba09ddf49c37238b3f3e4a` |
| `atlas-api-public` | #52 | `2270141b36feb96a50b3858b2f89c6e0e73e56d5` | `5b970a9bf3b66b5469ce883aacec4a4b496e72cc` |

Every initial implementation merge was bound to its reviewed pull-request head SHA.

## Live-review corrections

Owner review of the deployed error pages identified two bounded presentation gaps: the Status 404 wordmark styling was incomplete, and the Status chips on the Status, CV, and Ramone 404 pages were static rather than using the existing public aggregate-status contract.

| Repository | Pull request | Reviewed head | Merge commit | Result |
| --- | ---: | --- | --- | --- |
| `status` | #33 | `f6593e805c2c69124a8cd031cea5c7d65f53ed82` | `e75580b7e81e7cf69f198766b0deeab298b4f10e` | Restored the canonical wordmark styling and added bounded aggregate status. |
| `atlas-doc-viewer` | #32 | `5d276411a81129d5a46306ede7016d0fac7b56e0` | `74438662f7613040824a552a00fd889a63a8a062` | Added bounded aggregate status without initializing or exposing the CV PDF. |
| `ramone-edge` | #31 | `e15bf68cee1c5d62791302ad060b45127f58bf31` | `ed91c70a21b90c9c81f2d5eb2d98cd71bbe423d9` | Added bounded aggregate status without inference, wake, Turnstile, or private-route calls. |

Each implementation uses the public `/v1/stats` contract, a six-second timeout, stale-evidence handling, and a safe `Unknown` fallback.

## Generator and scheduler evidence

The generator implementation produced regeneration commit `5c32b7109be2e9772a3d7e03142bfabb78032bae`. Its first synchronization commit, `ec901c6a087ce01ad13a1d9dceae15e5c85b8fd4`, changed only unpublished `scheduled/` entries.

Published-article refresh preparation then completed through `atlas-article-gen` PR #40:

- reviewed head: `1b51245e4b0f92333bee4dfd76cf46e9957fb60d`;
- merge commit: `6fc354bf3604f230f4ef31046db9bde97a941ccf`;
- scheduler synchronization commit: `79828ab9045ca82a8ee54df803171af7b6751404`.

That synchronization added exactly three hash-pinned bundles below `rollouts/published-article-refresh/bundles/`, one for each already-published generator-owned article. It did not itself write to `atlas-systems`.

## Published article refresh receipts

The three refreshes were executed independently and in W-number order. Each request pull request added one append-only TOML file. Each production workflow changed one published article HTML file, waited for the exact `atlas-systems` deployment, and then committed an immutable receipt.

| Article | Scheduler PR and merge | Site commit | Receipt commit and path | Verified |
| --- | --- | --- | --- | --- |
| W-05 `atlas-pipeline-infrastructure-dashboard` | #45, `891dff723e8f71486abda7e06e000dbd96afd69b` | `f90fe8f767200d452d440e94b02109f1ca367fc4` | `8d185480c0c92f801129615860daa0a2445a0e08`, `rollouts/published-article-refresh/receipts/w05-browser-identity-20260730.json` | `2026-07-30T14:34:51.171150+00:00` |
| W-06 `atlas-systems-cicd-pipeline` | #46, `a4b844edcd4ab615b5f81b73e7c12c42221b4b4c` | `348ad2856d3e939e9fb531e4a99caac29fc2d35a` | `095d83f54972c2198278db4aef93d44943c11ecb`, `rollouts/published-article-refresh/receipts/w06-browser-identity-20260730.json` | `2026-07-30T14:45:19.005084+00:00` |
| W-07 `atlas-lab-observability` | #47, `37cb51beaf1af8fd970d5f3ed71a56a8c26db758` | `d852974cc1bdc62d019c9dac25531ca76c1f66d3` | `a5a2143bf867cc924d164bc9e5108685a152b3c2`, `rollouts/published-article-refresh/receipts/w07-browser-identity-20260730.json` | `2026-07-30T14:55:14.357071+00:00` |

Every receipt records `exact_deployment_verified: true` and binds the site commit to generator commit `5c32b7109be2e9772a3d7e03142bfabb78032bae` and the exact generated blob identities.

The three site commits add the generated Article JSON-LD, `article:published_time`, `article:author`, and correctly placed `twitter:image:alt` declarations. They preserve article prose, titles, publication dates, Writing and Work indexes, work cards, the accepted classic footer profile, and scheduler-owned sequence navigation.

## Deployment and live-route evidence

The owner inspected the relevant repository Deploy runs and reported them green. Live custom-domain review on 30 July 2026 confirmed the new browser error pages and identified the two follow-up issues recorded above. After the follow-up deployments, the owner reported the current surfaces good.

The verified behavior is:

- the main site retains its existing route behavior while exposing complete icons, exact canonical ownership, route-specific social identity, parseable structured data, and the owned noindex 404;
- the Status unknown route exposes the product-owned noindex 404, correctly styled Atlas Systems wordmark, and bounded live aggregate status without starting service-grid or activity behavior;
- the CV unknown route exposes the product-owned noindex 404 and bounded live aggregate status without initializing, embedding, downloading, or naming the protected PDF;
- Ramone browser navigation receives product-owned noindex HTML and bounded aggregate status, while API-style and non-GET unknown requests retain JSON and no inference or private connectivity is invoked;
- unknown browser paths below Public API `/v1/docs/*` receive product-owned noindex HTML, while unknown machine `/v1/*` routes remain JSON;
- `atlas-api-index` remains the intentional JSON-only no-change result at `96cd81f643429895847a1c2f143084d6e995005c`.

The connected GitHub interface used during the rollout cannot enumerate push-triggered workflow runs by commit. This closeout therefore distinguishes owner-observed green consumer Deploy runs from the independently machine-recorded article refresh receipts. No deployment state is inferred from a source merge alone.

## Preserved boundaries

Phase 7 did not change:

- article prose, editorial ordering, publication dates, queue timing, or normal publication scheduling;
- Status service-check cadence, registry discovery, SLO calculations, or activity feed behavior;
- CV initialization, PDF access, desktop embedding, mobile handoff, or document contents;
- Ramone inference, `/ask`, private tunnel, wake behavior, Turnstile, rate limiting, SSE, or bindings;
- Public API schemas, OpenAPI, methods, cache policy, CORS, rate limits, data, search, evidence, topology, or bindings;
- API index JSON-only behavior;
- provider settings or secrets.

No generated article HTML was hand-edited in `atlas-systems`. Every published article refresh used the generator export and scheduler-owned production write path.

## Closeout

Phase 7 is complete. This record supersedes the earlier rollout-progress state while preserving `docs/public-interface-phase-7-review.md` as the dated source-preparation snapshot.

After this closeout pull request is merged, Phase 8 inspection may begin under current repository authority. Phase 8 implementation, provider writes, deployments, workflow dispatches, and secret changes remain separately approval-gated.
