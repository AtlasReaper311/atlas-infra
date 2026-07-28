# Public interface programme Phase 3 closeout

Status: Phase 3 complete at its defined evidence gate. Phase 4 Part 0 inspection may begin. Phase 4 authority merge, interface-kit merge, and release remain separately approval-gated.

Closed: 28 July 2026.

## Current state

Phase 3 added comparable, repeatable evidence for the three supporting browser products and machine-readable contract evidence for the JSON-only API index.

The four repository-local evidence pull requests were reviewed on exact heads, rebased after their prerequisite `actions/checkout` updates, and squash-merged into their current `main` branches:

| Product | Repository pull request | Reviewed head | Merge commit |
| --- | --- | --- | --- |
| Status | `AtlasReaper311/status#28` | `c31f8b6eff6b1a24b1be329357cf464c602c30db` | `2e9d993193b2823e06ff104eec9f80f9928065aa` |
| CV viewer | `AtlasReaper311/atlas-doc-viewer#29` | `cf2288663a61db05ccc62daa23d7094440a05c13` | `dde4faea6d1277bfe4a4a458a3c663a8940edac0` |
| Ramone | `AtlasReaper311/ramone-edge#28` | `4d50f1a5e19d689ade1b8e08730f9463d0e5f81b` | `db55cd96408ddf9eebb4d935b19966c64f060597` |
| API index | `AtlasReaper311/atlas-api-index#17` | `fc62fa768c5dbcc455757c0b49047a2171354aac` | `96cd81f643429895847a1c2f143084d6e995005c` |

The separate SPECULAR-CORE rollout remains owned by `atlas-infra#81` and changes only `docs/work-allocation.md`. It does not overlap this closeout branch.

## Evidence inspected

### Status

Status retains its existing product-specific deterministic browser suite and now emits a separate `atlas-public-interface/evidence/v1` record.

- Product-specific cases: 10.
- Comparable cases: 12.
- Blocking failures: 0.
- P0 findings: 0.
- P1 findings: 0.
- Reporting-only P2 records: 12 repeated browser and viewport measurements around the wordmark, status and search controls, narrow navigation labels, and footer links.
- Evidence artifact: `status-interface-preview-evidence-c31f8b6eff6b1a24b1be329357cf464c602c30db`.
- Artifact digest: `sha256:a953c234f2f0ced95fbda6ffaedd4ddecacac0bae779edd2bbd29921f067f348`.

The existing deterministic unavailable-data fixture remains in use. Deliberate fixture-generated 503 noise is filtered only from the comparable console summary while raw diagnostics remain available.

### CV viewer

The CV viewer retains its protected-document and interaction-specific suite and now emits a separate `atlas-public-interface/evidence/v1` record.

- Product-specific cases: 10.
- Comparable cases: 12.
- Blocking failures: 0.
- P0 findings: 0.
- P1 findings: 0.
- P2 findings: 0.
- Evidence artifact: `document-viewer-evidence-cf2288663a61db05ccc62daa23d7094440a05c13`.
- Artifact digest: `sha256:80fbd669143be78d021bc226e162c84ff0656eb733ba10e7fc077f744a179d76`.

The product-specific evidence separately proves that the protected PDF is not requested before explicit visitor action, and then proves desktop open, Escape close, object identity, and focus return.

### Ramone

Ramone retains its offline, cited-answer, source-card, personality-response, workspace, and composer assertions and now emits a separate `atlas-public-interface/evidence/v1` record.

- Product-specific cases: 10.
- Comparable cases: 12.
- Blocking failures: 0.
- P0 findings: 0.
- P1 findings: 0.
- Reporting-only P2 records: 12 repeated browser and viewport measurements of three inline controls: `atlas reaper`, `read the build log`, and `source`.
- Evidence artifact: `ramone-interface-evidence-4d50f1a5e19d689ade1b8e08730f9463d0e5f81b`.
- Artifact digest: `sha256:e199a57a189f020af37f527da0244e57a1c447dc7b8d073ca79c0c1ccece1d47`.

The evidence preview remained isolated, binding-free, inference-free, deterministic, and offline.

### API index

The API index remains intentionally JSON-only and now emits `atlas-public-interface/registry-evidence/v1` evidence instead of screenshots or visual assertions.

- Contract cases: 4.
- Passed: 4.
- Failed: 0.
- P0 contract findings: 0.
- P1 contract findings: 0.
- Root success: JSON 200 with public CORS and bounded caching.
- Missing path: bounded JSON 404.
- Non-GET root: bounded JSON 405.
- Registry unavailable and rebuild failure: fail-closed JSON 503.
- HTML detected: false in every case.
- Evidence artifact: `registry-contract-evidence-fc62fa768c5dbcc455757c0b49047a2171354aac`.
- Artifact digest: `sha256:0c166b89553f094934645f748a1ba0c269bff9ff739af8abce6175dc01d459fc`.

## Changes

The merged Phase 3 source changes are evidence-only:

- one comparable browser-evidence runner in each of `status`, `atlas-doc-viewer`, and `ramone-edge`;
- repository-local Phase 3 evidence documentation;
- existing preview-workflow wiring extended to run both product-specific and comparable evidence;
- exact-head artifact names and 14-day retention;
- one JSON contract-evidence generator, test, documentation file, and CI step in `atlas-api-index`.

No shared production interface component, visual token, route, runtime binding, secret, provider setting, inference path, protected document, reliability calculation, or public API behaviour was changed.

## Validation

All reviewed heads passed their repository-native pull-request checks before merge.

Status passed:

- Pull request CI;
- Public interface conformance;
- isolated Pages preview publication;
- product-specific and comparable browser evidence;
- CodeQL;
- OpenSSF Scorecard;
- Gardener remediation gate.

CV viewer passed:

- Pull request CI;
- Public interface conformance;
- isolated Pages preview publication;
- protected-PDF and product-specific viewer evidence;
- comparable browser evidence;
- CodeQL;
- OpenSSF Scorecard;
- Gardener remediation gate.

Ramone passed:

- Pull request CI;
- Public interface conformance;
- isolated Workers preview publication;
- product-specific and comparable browser evidence;
- CodeQL;
- OpenSSF Scorecard.

API index passed:

- lint;
- tests;
- registry evidence generation;
- evidence artifact upload;
- Wrangler dry run;
- pinned Worker metadata validation;
- CodeQL;
- OpenSSF Scorecard.

Across Phase 3, 70 evidence cases completed with no P0 findings, no P1 findings, and no blocking failures.

## Browser evidence

The three browser products were measured in Chrome and Firefox at:

- 320 pixels;
- 375 pixels;
- 768 pixels;
- 1024 pixels;
- 1440 pixels;
- 1920 pixels as reporting-only coverage.

The comparable records include:

- semantic structure;
- keyboard focus;
- WCAG 2.2 findings;
- console and page errors;
- failed requests and HTTP errors;
- request totals and transfer sizes;
- CSS and JavaScript resource counts.

Browser performance remains reporting-only. Phase 3 does not establish or authorise blocking browser budgets.

## Security and privacy review

Phase 3 preserved the following boundaries:

- Status did not call mutation endpoints, require browser secrets, change `slo.json`, or recompute canonical service verdicts.
- The CV viewer did not change `noindex, follow`, automatic-load policy, protected PDF bytes, desktop embed, mobile handoff, close behaviour, or focus return.
- Ramone evidence did not call production `/ask`, use runtime bindings, access inference, expose secrets, or alter tunnel, Turnstile, rate-limit, SSE, wake-state, grounding, or response contracts.
- API index evidence did not write KV, dispatch schedules, change the public allowlist, alter bindings or secrets, deploy a Worker directly, add HTML, or create a browser shell.
- No secret values were requested, recorded, or committed.

## Deployment evidence boundary

Each merge advanced the repository's `main` branch and invoked its repository-owned push deployment contract.

This closeout records the exact merge commits and the previously reviewed exact-head preview evidence. The connected GitHub Actions reader available to this session does not enumerate push-triggered workflow runs, and the execution runtime cannot resolve the public Atlas domains. Therefore this document does not invent deployment run IDs or claim an independently observed live revision.

That tooling limitation does not change the Phase 3 evidence result. Phase 3's defined gate is the measured P0 and P1 backlog, which is empty. Post-merge deployment receipts remain a programme evidence item and must be attached before any Phase 4 interface-kit release or consumer adoption is approved.

## Risks and carried findings

1. Status and Ramone have reporting-only touch-target candidates. They are not P0 or P1 blockers and should be reviewed during the measured accessibility and product-alignment phases rather than silently changing shared tokens in Phase 4.
2. The 1920-pixel viewport is evidence coverage only. It is not yet an accepted breakpoint or blocking budget.
3. The current authority does not explicitly cover breadcrumbs or a complete live-region and status-announcement strategy. Phase 4 may propose bounded authority additions only when the measured evidence supports them.
4. Footer slot and variant authority remains a later Phase 6 concern. Phase 4 must not absorb that work without a new approval decision.
5. Push-triggered deployment run IDs and live-route receipts are not independently observable from this session and remain required before Phase 4 release or consumer rollout.

## Rollback

Each evidence merge can be reverted independently in its owning repository. Reverting removes only the additional evidence runner, test, documentation, and workflow wiring.

No data migration, secret rotation, provider rollback, content rollback, model rollback, or runtime-state rollback is required.

## Phase 4 entry boundary

Phase 3 is complete at its defined evidence gate.

Phase 4 may begin with read-only Part 0 inspection of:

- accepted interface authority in `atlas-infra`;
- measured Phase 2 and Phase 3 evidence;
- current `atlas-interface-kit` source, generated output, manifest, versioning, tests, and release workflow;
- open pull requests and overlapping paths in both repositories.

Phase 4 is not yet authorised to:

- amend policy or an ADR;
- change `atlas-interface-kit` source;
- merge an authority pull request;
- merge an interface-kit pull request;
- publish an immutable kit release;
- update a consumer repository;
- deploy a consumer;
- change provider settings or secrets.

The next approval decision must follow Phase 4 Part 0 and identify the exact measured authority additions, implementation scope, branch sequence, validation, release boundary, and rollback plan.
