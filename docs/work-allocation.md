# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This is not architecture or policy. It records who is doing what now so separate sessions do not silently duplicate or reverse each other.

This file only has value while it remains current. Update or remove an entry as soon as its status changes.

Last updated: 2026-08-02.

## How to use this file

Before starting non-trivial multi-session work, check for an existing entry on the same repository or capability. When starting such work, add an active entry. When work finishes, pauses, blocks, or is abandoned, update the entry immediately.

Entry format:

```text
### <short title>

- Repo(s): repositories in scope
- Agent: agent or tool doing the work
- Status: active | paused | blocked | done
- Started: date
- Last updated: date
- Summary: what is being done and why
- Resume point: required only when paused or blocked
```

## Active work

### Public interface programme Phase 14

- **Repo(s):** `atlas-infra`; read-only evidence inspection of `atlas-systems`
- **Status:** active
- **Started:** 2026-08-02
- **Last updated:** 2026-08-02
- **Summary:** Drafting the Phase 14 browser-budget authority proposal from reviewed browser evidence cycles and a fresh local current-main resource measurement. Scope is authority proposal only: no enforcement, public route, product runtime, static-baseline weakening, provider setting, binding, secret, workflow dispatch, release, or production deployment change.
- **Resume point:** Validate and open the Phase 14 authority pull request, then stop at the explicit approval boundary before merging or enforcing any browser budget.

### GitHub provider guard audit

- **Repo(s):** `atlas-infra` plus the 33 repositories in the authoritative public projection
- **Agent:** ChatGPT with Atlas providing owner-authenticated read-only evidence and approving any later provider write
- **Status:** active
- **Started:** 2026-07-31
- **Last updated:** 2026-07-31
- **Summary:** The owner-authenticated audit resolved all 27 Phase II branch-guard unknowns. Six repositories have a qualifying active ruleset, five have classic protection without pull-request review protection, and 22 have no qualifying default-branch guard. The evidence digests, exact repository classifications, and a one-repository `atlas-badges` canary plan are recorded in `docs/github-provider-guard-audit.md`. No ruleset, branch-protection, token, repository, release, tag, workflow, deployment, or secret change has been performed.
- **Resume point:** Obtain separate approval before opening the bounded `atlas-badges` validation pull request or creating the canary ruleset.

## Paused work

### Post-programme cross-page conformance audit

- **Repo(s):** all public browser-facing Atlas Systems surfaces, beginning with `atlas-systems`, `status`, `atlas-doc-viewer`, `ramone-edge`, and human-facing `atlas-api-public` documentation
- **Agent:** unassigned until the public-interface programme is fully closed
- **Status:** paused
- **Started:** 2026-07-30
- **Last updated:** 2026-07-31
- **Summary:** Required estate-wide follow-up after the complete public-interface programme. Audit and correct global navigation, active-route treatment, Lab and Systems context navigation, route labels and breadcrumbs, shared shell/search/footer behaviour, spacing and heading hierarchy, canonical card destinations, and accidental page-to-page drift while preserving intentional product identities.
- **Resume point:** Begin only after every public-interface programme phase, consumer merge, production deployment, and live-verification gate is complete. Reinspect current GitHub source and deployed surfaces rather than relying on programme-era screenshots or memory.

## Recently completed

### Public interface programme Phase 13

- **Repo(s):** `atlas-infra`; read-only inspection of `atlas-systems` and `atlas-interface-kit`
- **Agent:** ChatGPT with Atlas approving autonomous merge when evidence is clean
- **Status:** done
- **Started:** 2026-08-02
- **Last updated:** 2026-08-02
- **Summary:** Added the normative AtlasField composition catalogue and validation gate through `atlas-infra#117` as `a3627dde153201068b563c74cd3b229a1d0f8e69`. The catalogue fingerprint is `sha256:9a739d2588a851b7e5918ea9545c831c8676e8eebee717bd223abfc1d86e1fdb`. Local validators and 429 tests passed; pull-request checks and post-merge main Contract registry CI, CodeQL, OpenSSF Scorecard, and Refresh Corpus passed. No public route, product runtime, renderer source, interface-kit release, provider setting, binding, secret, workflow dispatch, or production deployment changed.

### Public interface programme Phase 12

- **Repo(s):** `atlas-infra`, `status`, `atlas-doc-viewer`, `ramone-edge`, `atlas-api-public`, `atlas-api-index`
- **Agent:** ChatGPT with Atlas approving autonomous merge and rollout gates where evidence is clean
- **Status:** done
- **Started:** 2026-08-02
- **Last updated:** 2026-08-02
- **Summary:** Completed supporting-product alignment after the Phase 11 Lab closeout. 12A CV document viewer alignment merged through `atlas-doc-viewer#33` as `2b03d5843588f0415ecc735f6b33ca7527063137` with production run `30746009334` and live CV smoke passing. 12B Status product alignment merged through `status#35` as `4db1438b1a8859008461903105360a2f09376c02` with production run `30746440035` and live Status smoke passing. 12C Ramone product alignment merged through `ramone-edge#32` as `3830dd3839847187e0b5ac6c837a5658f5f47341` with production deploy run `30746842107` and live Ramone smoke passing. 12D Public API docs alignment merged through `atlas-api-public#54` as `4a4d575bf673a272447c40ec42a14c8be01101f8` with production deploy run `30747322035` and live docs smoke passing. 12E verified `atlas-api-index` as JSON-only on `96cd81f643429895847a1c2f143084d6e995005c` without a source change. Formal receipts are recorded in `docs/public-interface-phase-12-coordination.md`. No product runtime, provider, binding, secret, deployment configuration, PDF, indexing, inference, or API behaviour changed.

### Public interface programme Phase 11

- **Repo(s):** `atlas-infra`, `atlas-systems`
- **Agent:** ChatGPT with Atlas approving preview, merge, and rollout gates
- **Status:** done
- **Started:** 2026-08-01
- **Last updated:** 2026-08-02
- **Summary:** Completed Lab interaction polish through four focused `atlas-systems` pull requests: context wayfinding `#189` as `163db2609028dea0d493e56afacbd81cc34e675b`, evidence-tool wayfinding and console parity `#190` as `519bb402a2f0d4ef1e3fc351efdccfffb0152262`, Signal Garden keyboard controls `#191` as `8e12441b67a1d1eab571022d5d4471701b9ffb89`, and experiment keyboard access `#192` as `0fd7a98aeaea523f18914c3c7f134fa96607406b`. The final production run `30744843987` verified the custom domain served the exact merge commit, passed Pages, HTML, route, footer, homepage AtlasField, and System Symphony production checks, and a live Lab browser smoke passed Almost, Drift, Speculum, and standalone Bearing focus paths. Formal receipts are recorded in `docs/public-interface-phase-11-coordination.md`.

### Public interface programme Phase 10

- **Repo(s):** `atlas-infra`, `atlas-article-gen`, `atlas-scheduler`, `atlas-systems`
- **Agent:** ChatGPT with Atlas approving protected architecture, preview, published refresh, merge, and production gates
- **Status:** done
- **Started:** 2026-07-30
- **Last updated:** 2026-07-31
- **Summary:** Completed the generated article reading contract, Writing directory state correction, scheduler preview parity, fenced-code parser repair, controlled W-06 refresh, and final classic-only Writing footer architecture. The authority merged through `atlas-infra#104`; scheduler enforcement through `atlas-scheduler#53`; generator preview authority through `atlas-article-gen#47`; and final consumer proof through `atlas-systems#188` as `4896b1c482d89f8b7968ec0baee5763e36843342`. Preview run `30637397463` passed route-derived Chrome and Firefox evidence for the Writing directory and all seven published articles. Production run `30638766487` deployed the exact consumer merge, verified it on `atlas-systems.uk`, passed homepage AtlasField and System Symphony smoke, and completed the guarded corpus refresh with HTTP `202`. Formal receipts are recorded in `docs/public-interface-phase-10-coordination.md`.

### GitHub conformance Phase II closeout

- **Repo(s):** `atlas-infra`
- **Agent:** ChatGPT with Atlas approving the closeout merge
- **Status:** done
- **Started:** 2026-07-31
- **Last updated:** 2026-07-31
- **Summary:** Closed the read-only public-repository source-conformance phase through `atlas-infra#102`. The verified 30 July scheduled scoreboard checked 33 public repositories, recorded 233 required passes and zero required failures, and preserved 27 unreadable branch-guard outcomes plus one deferred `worker-meta-kit` release as separate provider and release work. The formal evidence, contract-continuity check, and closure boundary are recorded in `docs/github-conformance-phase-ii-closeout.md`.

### Public interface programme Phase 9

- **Repo(s):** `atlas-infra`, `atlas-systems`
- **Agent:** ChatGPT with Atlas approving preview, merge, and rollout gates
- **Status:** done
- **Started:** 2026-07-30
- **Last updated:** 2026-07-30
- **Summary:** Completed the Reliability, Observability, and Evidence detail-surface refactor. Coordination PR `atlas-infra#96` merged as `c43148d8fc7bbaecf79753f612ea44593459dbe8`. Source PR `atlas-systems#183` merged as `4dd5827b922832efacba4e20146de8dc2e95a1e7` after exact-head preview run `30580400479` passed candidate validation, isolated publication, deterministic route-and-viewport evidence, accessibility checks, and Batch H assertions. Production run `30582815398` deployed the exact merge commit, verified it on the custom domain, confirmed the Systems route and footer assets, passed homepage AtlasField and System Symphony live smoke, and completed the guarded corpus refresh. The formal receipts are recorded in `docs/public-interface-phase-9-coordination.md`.

### Public interface programme Phase 8

- **Repo(s):** `atlas-infra`, `atlas-systems`, `status`; measured no-change review also covered `atlas-interface-kit`, `atlas-api-public`, `atlas-api-index`, `atlas-doc-viewer`, and `ramone-edge`
- **Agent:** ChatGPT with Atlas approving preview and rollout gates
- **Status:** done
- **Started:** 2026-07-30
- **Last updated:** 2026-07-30
- **Summary:** Completed the accepted measured accessibility and responsive correction phase. `status#34` corrected global-header touch targets and merged as `1894baf27418dd8a2e073bac4b4a6c0bab7fb7de`. `atlas-systems#180` corrected the carried target, contrast, dense-overflow, and narrow-layout findings and merged as `54cb0bd892d0eb4b90d926393b5a9968a92f84df`. Follow-up `atlas-systems#182` removed duplicated route labels and corrected homepage destinations, with 348 Chrome and Firefox cases, zero blocking failures, 56 Batch H cases, and zero Batch H findings; it merged as `b559641cc663512de9775ea7e355e32b4b6346a9`. Atlas confirmed production deployment and live verification. The formal receipts are recorded in `docs/public-interface-phase-8-inspection.md`.

### Public interface programme Phase 7

- **Repo(s):** `atlas-infra`, `atlas-systems`, `atlas-interface-kit`, `atlas-api-public`, `atlas-api-index`, `status`, `atlas-doc-viewer`, `ramone-edge`, `atlas-article-gen`, `atlas-scheduler`
- **Agent:** ChatGPT with Atlas performing live review
- **Status:** done
- **Started:** 2026-07-28
- **Last updated:** 2026-07-30
- **Summary:** Phases 0 through 7 are closed through `atlas-infra` PR #94. Phase 7 merged the exact browser-identity implementation, deployed the bounded Status, CV, Ramone, and Public API documentation error behavior, corrected the live Status wordmark and aggregate-status presentation, and refreshed published W-05 through W-07 through the generator-to-scheduler production contract. The three article receipts record `exact_deployment_verified: true`; article prose, publication dates, indexes, classic footer state, machine API behavior, CV loading boundaries, Ramone inference boundaries, provider settings, and secrets were preserved.

## Standing ownership

| Area | Default owner | Note |
| --- | --- | --- |
| Case study writing and the publishing pipeline | Atlas, agent-assisted | `atlas-article-gen` and `atlas-scheduler` documentation is authoritative. Agents inspect it before changing article generation, sequencing, refresh, or publication behaviour. |
| Repository governance and lifecycle | `atlas-infra` under ADR-0004 | Public repository classification changes begin in the authoritative policy inputs, never in generated projections. |
| Public interface authority | `atlas-infra` under ADR-0008 and ADR-0009 | Shared roles and non-overridable foundations are governed here. The classic sequence-only Writing article footer is a bounded, non-transferable exception. `atlas-interface-kit` implements the normal accepted authority. |
| Interface-kit implementation and release | `atlas-interface-kit` | Consumers pin immutable repository-local bundles and verify fingerprints. |
| Model promotion evidence | `atlas-eval-harness` | Evidence-sensitive model choices require capability-specific evaluation before rollout. |
