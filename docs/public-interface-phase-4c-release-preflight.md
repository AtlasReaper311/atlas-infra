# Public interface programme Phase 4C release preflight

Status: immutable `atlas-interface-kit` `v0.3.0` release published and independently verified. Phase 4 closeout now waits only for review and merge of this documentation pull request; Phase 5 remains separately approval-gated.

Recorded: 29 July 2026.

## Current state

Phase 4A authority is merged in `atlas-infra` at `6b373af7eed8b617e1d121032031d0892e655778`.

Phase 4B implementation is merged in `atlas-interface-kit` at `630c8060ebe61b3f2234cd73ae983b5b41564c3b`. The repository version is `0.3.0`. The immutable release mapping is:

```text
v0.3.0 -> 630c8060ebe61b3f2234cd73ae983b5b41564c3b
```

The annotated tag and GitHub Release now exist. No consumer repository had adopted `0.3.0` when this closeout was recorded.

## Deterministic release evidence

A canonical Git-tree build from `630c8060ebe61b3f2234cd73ae983b5b41564c3b` reproduced the exact reviewed CI fingerprints:

| File | SHA-256 |
| --- | --- |
| `atlas-interface-kit-0.3.0.tar.gz` | `60dd4a6b4dc308c65aea1b86c01043fe81beab30861058fb3f03f6cdcb393ec4` |
| `atlas-interface-kit-0.3.0.release-manifest.json` | `77886d2236bc65de0f3812c4c086775a8ef9d2ba08fc4daa5e93f40192a8df2f` |

The Windows-backed WSL checkout produced different hashes because `LICENSE` and `docs/BRAND_REFERENCE.md` were materialised with platform line endings. Git's canonical stored tree reproduced the CI bytes exactly. The tag-triggered Ubuntu release workflow is the publication build authority.

## Immutable release publication

The owner created and pushed annotated tag `v0.3.0` only after the Phase 4C evidence record was merged. GitHub Actions release run `30436445914` then validated the tag and version, validated the bundle, built the release files, and uploaded workflow artifact `atlas-interface-kit-v0.3.0` successfully.

| Field | Verified value |
| --- | --- |
| Tag | `v0.3.0` |
| Source commit | `630c8060ebe61b3f2234cd73ae983b5b41564c3b` |
| Release workflow run | `30436445914` |
| Workflow artifact | `atlas-interface-kit-v0.3.0` |
| Workflow artifact ID | `8717601241` |
| Workflow ZIP digest | `sha256:213d293bcee6f133d4c6fbb1599bbcb6bb41a9f51f664e767a6a2c7e0ceb3ad0` |
| GitHub Release | `https://github.com/AtlasReaper311/atlas-interface-kit/releases/tag/v0.3.0` |
| Published at | `2026-07-29T08:44:18Z` |
| Draft | `false` |
| Prerelease | `false` |

The GitHub Release contains exactly the deterministic archive and release manifest. Atlas downloaded both published assets after publication and verified them independently against the reviewed fingerprints:

| Published asset | Asset ID | Size | Verified SHA-256 |
| --- | ---: | ---: | --- |
| `atlas-interface-kit-0.3.0.tar.gz` | `493814640` | 100,378 bytes | `60dd4a6b4dc308c65aea1b86c01043fe81beab30861058fb3f03f6cdcb393ec4` |
| `atlas-interface-kit-0.3.0.release-manifest.json` | `493814642` | 3,101 bytes | `77886d2236bc65de0f3812c4c086775a8ef9d2ba08fc4daa5e93f40192a8df2f` |

GitHub reports `targetCommitish` as `main` in release metadata. The immutable annotated tag remains the release identity and resolves to the exact reviewed source commit above; later movement of `main` does not change the release.

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

Tag creation and GitHub Release publication were performed only under their explicit owner approvals. This closeout branch performs documentation writes only.

No consumer repository was updated. Phase 5 did not begin. No product workflow was dispatched, no interface was deployed, no provider setting or secret changed, no Ramone inference request was sent, and no protected CV document was requested.

## Phase boundary

Phase 4 authority, implementation, immutable release creation, publication, and verification are complete. Closing Phase 4 requires only review and merge of this documentation pull request.

Phase 5 remains a separate programme gate. It must begin with fresh Part 0 inspection of the current `atlas-systems` repository, overlapping branches and pull requests, repository-local bundle state, validation, preview contracts, deployment behaviour, generated paths, and protected product boundaries. No consumer adoption, source change, preview, merge, workflow dispatch, or deployment is authorised by this closeout record.

## Rollback

This file is documentation only. Before merge, close the pull request or delete its branch. After merge, revert the documentation commit. The immutable release is not modified by this closeout and requires no runtime or provider rollback.
