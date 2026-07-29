# Public interface programme Phase 4C release preflight

Status: release candidate technically reproducible; immutable release remains blocked until production deployment receipts and live-route verification are attached.

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

The preview receipts above prove the reviewed pull-request heads only. They do not prove production deployment of the squash-merge commits.

## Production deployment receipt inspection

The connected GitHub Actions reader available during this reconciliation returned no push-triggered runs for the merge commits. It is documented to enumerate pull-request-triggered runs only. The execution environment also could not resolve the Atlas public domains, so no production route response, deployed revision, or live browser state was invented.

The following evidence therefore remains required before release approval:

| Repository | Required production evidence |
| --- | --- |
| `atlas-systems` | successful push deployment run for `1622b9dcc485282daeec4ed04934dd21a17ce341`, exact deployed commit verification, and live `https://atlas-systems.uk/` smoke |
| `status` | successful push deployment run for `2e9d993193b2823e06ff104eec9f80f9928065aa` and live `https://status.atlas-systems.uk/` smoke |
| `atlas-doc-viewer` | successful push deployment run for `dde4faea6d1277bfe4a4a458a3c663a8940edac0` and live `https://cv.atlas-systems.uk/` smoke preserving protected-document behaviour |
| `ramone-edge` | successful push deployment run for `db55cd96408ddf9eebb4d935b19966c64f060597` and live `https://ramone.atlas-systems.uk/` smoke without inference mutation |
| `atlas-api-index` | successful push deployment run for `96cd81f643429895847a1c2f143084d6e995005c` and live JSON contract check at `https://api.atlas-systems.uk/` |

A later deployment may have superseded these commits. In that case, the receipt must show that the relevant merge commit entered the deployment chain and that the current live revision contains it. Current health alone is not a substitute for deployment provenance.

## Security and privacy boundary

This reconciliation performed no workflow dispatch, deployment, provider write, secret access, inference request, protected-document request, release, tag creation, consumer update, or merge.

The production checks remain read-only. Ramone verification must not send a question to `/ask`. CV verification must preserve explicit visitor initiation before the protected PDF is requested. API index verification remains JSON-only.

## Release boundary

Phase 4C may proceed to tag creation only after:

1. the five production deployment receipts are attached or an evidence-backed superseding deployment chain is recorded;
2. the five current live routes are verified read-only;
3. this documentation pull request is reviewed and merged;
4. the owner separately authorises annotated tag creation.

Tag creation, tag push, release workflow review, and GitHub Release publication remain separate approval gates. Phase 5 consumer adoption remains prohibited until the immutable release is published and verified.

## Rollback

This file is documentation only. Before merge, close the pull request or delete its branch. After merge, revert the documentation commit. No provider, runtime, data, secret, release, or consumer rollback is required.
