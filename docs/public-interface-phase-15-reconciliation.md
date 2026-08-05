# Public interface programme Phase 15 reconciliation

Status: complete.

Recorded: 5 August 2026.

## Purpose

This record closes the original Atlas Systems public-interface programme after
reconciling authority, source, preview, production, live verification, generated
refresh, rollback, and residual follow-up state.

No state is inferred from another. Source merge, production deployment, live
commit identity, browser evidence, and Corpus refresh are recorded separately.

## Final source baseline

| Repository | Verified state | Programme role |
| --- | --- | --- |
| `atlas-infra` | closeout branch based on `b82839d0755bdd7e373ff35e59f13d088b2329c4` | Programme authority and final closeout. |
| `atlas-systems` | `3be62f8915c0022e68187d9a66d9a808e87b6caa` on `main` | Primary public product and Phase 15 correction. |
| `atlas-interface-kit` | `c38b5b3edd631999dfad838c4fb70e505a9860cf` | Immutable shared interface implementation. |
| `status` | `4db1438b1a8859008461903105360a2f09376c02` | Independent operational product. |
| `atlas-doc-viewer` | `2b03d5843588f0415ecc735f6b33ca7527063137` | Independent CV viewer. |
| `ramone-edge` | `3830dd3839847187e0b5ac6c837a5658f5f47341` | Protected browser product and edge runtime. |
| `atlas-api-public` | `4a4d575bf673a272447c40ec42a14c8be01101f8` | Public API projection and human documentation. |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | JSON-only fail-closed registry. |
| `atlas-article-gen` | `538fb2801ebe772906b6e16560ee2480c14103b1` | Canonical article authoring and rendering authority. |
| `atlas-scheduler` | `d4c88e32958790c9a1f45d69ee8b45197309d03f` | Publication sequencing and sole production write path into generated article output. |

The earlier Phase 15 start record contained invalid article-generator and
scheduler SHAs. The verified heads above remain the corrected source record.

## Phase 15 correction receipt

The sole blocking Phase 15 product defect was late Lab card-signature
enhancement for the dynamically inserted Blackbox card.

`atlas-systems#198` was reviewed at:

```text
52e1dfda7bd26e20bb824ce61da721a231887734
```

The pull request changed only:

- `static/js/card-signatures.js`;
- `js/tests/card-signatures.test.mjs`;
- `data/performance-baseline.json`.

It squash-merged as:

```text
3be62f8915c0022e68187d9a66d9a808e87b6caa
```

## Deterministic preview evidence

Preview run `30996286181` completed successfully for the exact reviewed head.

Artifacts:

| Artifact | ID | Digest |
| --- | --- | --- |
| Route-derived interface evidence | `8926870557` | `sha256:8051031bb10efa7edd31a721fb893afb6dfa9d9b954f581660d3886f17842827` |
| Batch H evidence | `8926871851` | `sha256:a12940dc978b0a1af8b1b9b3a955d8e81874de3f413227f619e2992e9650aec4` |
| Validation plan | `8926287238` | `sha256:19c3781a122f1ba7037f88a171bdf6e1e32ff5cd91764d351c30ad1b2f565afd` |

Verified results:

- 360 route, browser, and viewport results;
- zero blocking failures;
- 28 of 28 required browser-budget measurements observed;
- zero browser-budget violations;
- 24 findings, all matched the accepted reporting baseline;
- zero unmatched or unresolved findings;
- 56 Batch H results with zero findings and zero blockers;
- 22 governed Lab cards and 22 enhanced signatures in Chrome and Firefox at
  320, 375, 768, 1024, 1440, and reporting-only 1920 pixels;
- zero Lab card overlaps, route overflows, or blockers in every matrix cell.

## Production deployment receipt

The owner explicitly approved merging `atlas-systems#198` at the reviewed head.
Under the confirmed repository model, that merge approval was also production
rollout approval because `main` deploys automatically through the existing
repository-owned workflow.

Production run `30999896059` completed successfully for exact merge commit:

```text
3be62f8915c0022e68187d9a66d9a808e87b6caa
```

The run proved:

- Pages output contract validation passed;
- HTML and offline-link validation passed;
- Cloudflare Pages deployment passed;
- edge-cache purge passed;
- Discord and Lab deployment reporting passed;
- `https://atlas-systems.uk` exposed the exact build commit;
- the Systems route marker passed;
- the Phase 6 footer assets remained live;
- the production homepage AtlasField browser smoke passed;
- the production System SYMPHONY live and 32-bar loudness smoke passed;
- guarded Atlas Corpus refresh passed.

Production artifacts:

| Artifact | ID | Digest |
| --- | --- | --- |
| Homepage AtlasField production smoke | `8927818375` | `sha256:76fd9352c152af3093a762db470a985152ba2f69984dd1c6cb278f987835839a` |
| System SYMPHONY production smoke | `8927952703` | `sha256:7b903bc3cc5d4035d709b4dae4dbdca5d5780002d2515a15b9d356ec42e8999e` |

The live custom-domain verification reported:

```text
Custom domain is serving 3be62f8915c0022e68187d9a66d9a808e87b6caa
```

## Deployment approval model

The accepted owner model is retained:

1. pull-request source and deterministic preview evidence are reviewed;
2. the owner explicitly approves the exact pull-request head for merge;
3. that merge approval authorises the existing automatic `main` deployment;
4. the workflow must prove the exact deployed commit, live checks, and guarded
   Corpus refresh.

A second manual deployment dispatch is not required. Cloudflare Pages native Git
integration is not part of this deployment path. Pull-request previews remain
label-gated and separate from production.

## Residual follow-up register

These items do not reopen Phase 15. They are inputs to a new, separately
controlled interface implementation programme.

### LAB-007a: Conformance missing-evidence counts

Status: confirmed follow-up.

`lab/conformance/conformance-core.js` correctly renders `estate_score: null` as
`unscored`, but its fallback report supplies literal zeroes for repositories,
errors, warnings, and unknowns. The page therefore presents four clean-looking
counts when no report was published.

Required outcome: unavailable evidence must render as unavailable, unknown, or
unscored. It must not render as a clean zero.

### Mode 04: Shape Detector evidence mode

Status: accepted owner decision and implementation follow-up.

The deterministic demonstration remains available, but every relevant chip,
score, table, chart, and source label must identify it as `Simulated`. It must
not be described as live evidence or replay evidence.

### SONIN YouTube and CSP

Status: accepted strict-security outcome with a separate publication-pipeline
follow-up.

Do not weaken the global CSP and do not hand-edit published article HTML.
Canonical-source recovery must begin in `atlas-article-gen`, pass through its
parser, and use `atlas-scheduler` as the only production write path.

### Superseded responsive work

`atlas-systems#179` was closed as superseded. Its valid 44-pixel touch-target and
tablet-header intentions may be reimplemented from current `main` only after a
fresh inspection. The stale branch is not an implementation base.

### Retired P0-DG proposal

`atlas-systems#199` was closed without merge. Its manual-dispatch deployment
model was rejected because it did not match the owner's established automatic
`main` deployment and label-gated preview workflow.

## Security and privacy review

The Phase 15 closeout:

- requested no secret;
- changed no provider setting, binding, environment, repository visibility, or
  runtime permission;
- sent no inference request;
- changed no Ramone runtime behaviour;
- weakened no CSP or browser-security header;
- hand-edited no generated article HTML or metadata;
- performed no scheduler publication;
- preserved strict separation between preview and production evidence.

## Rollback

Product rollback is a reviewed revert of
`3be62f8915c0022e68187d9a66d9a808e87b6caa` on `atlas-systems/main`, followed by
verification of the normal automatic production deployment.

Documentation rollback is a revert of the final `atlas-infra` closeout merge.
No provider rollback is required because Phase 15 changed no provider setting.

## Completion statement

Phases 0 through 15 are complete at their required authority, source, preview,
production, live-verification, generated-refresh, and rollback boundaries.

The original public-interface programme is closed. Any further interface work
must begin as a new programme with a fresh Part 0 inspection of current
repositories and must not assume that this closeout package proves future source
or deployment state.
