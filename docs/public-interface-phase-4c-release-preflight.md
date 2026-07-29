# Public interface programme Phase 4C release preflight

Status: release candidate technically reproducible, historical deployment receipts attached, and current live routes verified. Documentation review and merge remain required before separately approved tag creation.

Recorded: 29 July 2026.

## Current state

Phase 4A authority is merged in `atlas-infra` at `6b373af7eed8b617e1d121032031d0892e655778`.

Phase 4B implementation is merged in `atlas-interface-kit` at `630c8060ebe61b3f2234cd73ae983b5b41564c3b`. The repository version is `0.3.0`. The proposed immutable release mapping is:

```text
v0.3.0 -> 630c8060ebe61b3f2234cd73ae983b5b41564c3b
```

No `v0.3.0` tag or GitHub Release existed when this preflight was recorded. No consumer repository has adopted `0.3.0`.

## Deterministic release evidence

A canonical Git-tree build from `630c8060ebe61b3f2234cd73ae983b5b41564c3b` reproduced the exact reviewed CI fingerprints:

| File | SHA-256 |
| --- | --- |
| `atlas-interface-kit-0.3.0.tar.gz` | `60dd4a6b4dc308c65aea1b86c01043fe81beab30861058fb3f03f6cdcb393ec4` |
| `atlas-interface-kit-0.3.0.release-manifest.json` | `77886d2236bc65de0f3812c4c086775a8ef9d2ba08fc4daa5e93f40192a8df2f` |

The Windows-backed WSL checkout produced different hashes because `LICENSE` and `docs/BRAND_REFERENCE.md` were materialised with platform line endings. Git's canonical stored tree reproduced the CI bytes exactly. The tag-triggered Ubuntu release workflow remains the publication authority.

## Phase 1 and Phase 3 merge evidence

| Product | Pull request | Reviewed head | Merge commit | Exact-head preview evidence |
| --- | --- | --- | --- | --- |
| Main site and System Symphony | `AtlasReaper311/atlas-systems#158` | `6d34fe4fef526f81b313016d39e14bdcdbe220ef` | `1622b9dcc485282daeec4ed04934dd21a17ce341` | `https://interface-pr-158.atlas-systems-44t.pages.dev` |
| Status | `AtlasReaper311/status#28` | `c31f8b6eff6b1a24b1be329357cf464c602c30db` | `2e9d993193b2823e06ff104eec9f80f9928065aa` | `https://interface-pr-28.status-40s.pages.dev` |
| CV viewer | `AtlasReaper311/atlas-doc-viewer#29` | `cf2288663a61db05ccc62daa23d7094440a05c13` | `dde4faea6d1277bfe4a4a458a3c663a8940edac0` | `https://interface-v2-pr-29.atlas-doc-viewer.pages.dev` |
| Ramone | `AtlasReaper311/ramone-edge#28` | `4d50f1a5e19d689ade1b8e08730f9463d0e5f81b` | `db55cd96408ddf9eebb4d935b19966c64f060597` | `https://ramone-interface-pr-28.anonymous30141592654.workers.dev` |
| API index | `AtlasReaper311/atlas-api-index#17` | `fc62fa768c5dbcc455757c0b49047a2171354aac` | `96cd81f643429895847a1c2f143084d6e995005c` | JSON contract evidence only; no visual preview required |

The preview receipts above prove the reviewed pull-request heads. The production receipts below separately prove that each squash-merge commit entered its repository-owned deployment workflow.

## Production deployment receipts

An owner-run `gh run list --commit` query identified the push-triggered deployment run for each exact merge commit. Connected GitHub job inspection then confirmed successful provider deployment steps against those commits.

| Repository | Merge commit | Deployment run | Result | Deployment evidence |
| --- | --- | ---: | --- | --- |
| `atlas-systems` | `1622b9dcc485282daeec4ed04934dd21a17ce341` | `30372973035` | success | Pages validation and deployment succeeded. The production verification job confirmed that `atlas-systems.uk` served the exact merge commit, confirmed the Systems route marker, and passed live homepage AtlasField and System Symphony browser smoke. |
| `status` | `2e9d993193b2823e06ff104eec9f80f9928065aa` | `30405665618` | success | The deployment job checked out the exact merge commit, validated the static site, deployed through Wrangler to Cloudflare Pages, purged the edge cache, and completed reporting successfully. |
| `atlas-doc-viewer` | `dde4faea6d1277bfe4a4a458a3c663a8940edac0` | `30405681772` | success | The deployment job checked out the exact merge commit, validated the static site, deployed through Wrangler to Cloudflare Pages, purged the edge cache, and completed reporting successfully. |
| `ramone-edge` | `db55cd96408ddf9eebb4d935b19966c64f060597` | `30405696420` | success | The Worker deployment job checked out and resolved the exact merge commit, deployed through the pinned Wrangler action, and persisted the deployment event successfully. |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | `30405710114` | success | Validation, pinned metadata contract checks, Wrangler deployment, and deployment reporting succeeded against the exact merge commit. |

These receipts satisfy the historical deployment-provenance requirement. They do not claim that each merge commit remains the current deployed revision because later production deployments may have superseded it.

## Current live-route verification

Atlas ran a bounded read-only route check from SPECULAR-CORE on 29 July 2026. The script requested only each product root. It did not initialise the protected CV document, call Ramone `/ask`, send an inference request, dispatch a workflow, or call any mutation endpoint.

| Product | Route result | Content result | Revision evidence |
| --- | --- | --- | --- |
| Main site | HTTP 200; 22,248 bytes | `text/html; charset=utf-8`; title `Atlas Systems` | Exposed build commit `f82527fcfd4c62cb7cd0983b267cf4b3d639e9b8`. GitHub comparison proves it is five commits ahead of, and descends from, the Phase 1 merge commit `1622b9dcc485282daeec4ed04934dd21a17ce341`. |
| Status | HTTP 200; 25,747 bytes | `text/html; charset=utf-8`; title `Status // Atlas Systems` | The route does not expose a build commit. Historical provenance remains deployment run `30405665618`. |
| CV viewer | HTTP 200; 9,329 bytes | `text/html; charset=utf-8`; title `CV // Atlas Systems` | The root route was checked without initialising or requesting the protected PDF. Historical provenance remains deployment run `30405681772`. |
| Ramone | HTTP 200; 94,648 bytes | `text/html; charset=utf-8`; title `Ramone // Atlas Systems` | The root route was checked without calling `/ask` or sending inference input. Historical provenance remains deployment run `30405696420`. |
| API index | HTTP 200; 19,211 bytes | `application/json; charset=utf-8`; valid object with no HTML shell | Top-level keys observed: `counts`, `discovery_warnings`, `generated_at`, `service`, and `workers`. Historical provenance remains deployment run `30405710114`. |

The five products were reachable and preserved their intended HTML or JSON boundary. A current-route observation proves present reachability only. The deployment run table remains the provenance record for the Phase 1 and Phase 3 commits.

## Security and privacy boundary

This reconciliation performed no workflow dispatch, deployment, provider write, secret access, inference request, protected-document request, release, tag creation, consumer update, or merge.

The route checks were read-only. Ramone verification did not send a question to `/ask`. CV verification preserved explicit visitor initiation before any protected PDF request. API index verification remained JSON-only.

## Release boundary

The evidence prerequisites for Phase 4C tag consideration are now complete. Phase 4C may proceed only after:

1. this documentation pull request is reviewed and merged;
2. the owner separately authorises annotated tag creation against `630c8060ebe61b3f2234cd73ae983b5b41564c3b`.

Tag creation, tag push, release workflow review, and GitHub Release publication remain separate approval gates. Phase 5 consumer adoption remains prohibited until the immutable release is published and verified.

## Rollback

This file is documentation only. Before merge, close the pull request or delete its branch. After merge, revert the documentation commit. No provider, runtime, data, secret, release, or consumer rollback is required.
