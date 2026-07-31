# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This is not architecture or policy. It records who is doing what now so separate sessions do not silently duplicate or reverse each other.

This file only has value while it remains current. Update or remove an entry as soon as its status changes.

Last updated: 2026-07-31.

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

### GitHub provider guard audit

- **Repo(s):** `atlas-infra` plus the 27 public repositories with unreadable `default_branch_guard` evidence in scoreboard run `30535544793`
- **Agent:** ChatGPT with Atlas providing owner-authenticated read-only evidence and approving any later provider write
- **Status:** active
- **Started:** 2026-07-31
- **Last updated:** 2026-07-31
- **Summary:** Resolve the Phase II branch-guard unknowns without assuming protection is present or absent. Part 0 confirmed that Atlas Infra already queries repository rulesets and classic branch protection correctly, while the scheduled token and connected GitHub tool cannot read the required provider surfaces. The current phase records the exact scope and owner-authenticated local evidence procedure in `docs/github-provider-guard-audit.md`. No ruleset, branch-protection, token, repository, release, tag, workflow, deployment, or secret change is authorised.
- **Resume point:** Run the existing policy-aware scoreboard locally with an owner-authenticated `gh` session, provide the generated JSON and Markdown evidence, classify all 27 repositories, and return any proposed canary for separate approval.

### Public interface programme Phase 10

- **Repo(s):** `atlas-infra`, `atlas-article-gen`, `atlas-scheduler`, `atlas-systems`
- **Agent:** ChatGPT with Atlas approving protected article, publication, and architecture gates
- **Status:** active
- **Started:** 2026-07-30
- **Last updated:** 2026-07-30
- **Summary:** Phase 10 owns the generated article reading contract, scheduler sequencing and preview parity, and the Writing directory. Part 0 found a current fenced-code parser defect affecting queued articles and published W-06, stale cross-repository scheduler pins, targeted preview drift from the production editorial adapter, incorrect type-filter semantics, and stale browser-only series compatibility. Routine source corrections, validation, ready-for-review transitions, and merges are authorised. Future-footer architecture, material changes to protected W-01 through W-07 presentation, published-article refreshes, production scheduler execution, publication timing, provider writes, and secrets remain separately approval-gated. The detailed inspection and implementation order are recorded in `docs/public-interface-phase-10-coordination.md`.

## Paused work

### Post-programme cross-page conformance audit

- **Repo(s):** all public browser-facing Atlas Systems surfaces, beginning with `atlas-systems`, `status`, `atlas-doc-viewer`, `ramone-edge`, and human-facing `atlas-api-public` documentation
- **Agent:** unassigned until the public-interface programme is fully closed
- **Status:** paused
- **Started:** 2026-07-30
- **Last updated:** 2026-07-30
- **Summary:** Required estate-wide follow-up after the complete public-interface programme. Audit and correct global navigation, active-route treatment, Lab and Systems context navigation, route labels and breadcrumbs, shared shell/search/footer behaviour, spacing and heading hierarchy, canonical card destinations, and accidental page-to-page drift while preserving intentional product identities.
- **Resume point:** Begin only after every public-interface programme phase, consumer merge, production deployment, and live-verification gate is complete. Reinspect current GitHub source and deployed surfaces rather than relying on programme-era screenshots or memory.

## Recently completed

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
| Public interface authority | `atlas-infra` under ADR-0008 and ADR-0009 | Shared roles and non-overridable foundations are governed here. The classic Writing article footer is a bounded, non-transferable exception. `atlas-interface-kit` implements the normal accepted authority. |
| Interface-kit implementation and release | `atlas-interface-kit` | Consumers pin immutable repository-local bundles and verify fingerprints. |
| Model promotion evidence | `atlas-eval-harness` | Evidence-sensitive model choices require capability-specific evaluation before rollout. |
