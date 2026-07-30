# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This is not architecture or policy. It records who is doing what now so separate sessions do not silently duplicate or reverse each other.

This file only has value while it remains current. Update or remove an entry as soon as its status changes.

Last updated: 2026-07-30.

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

### Public interface programme Phase 8

- **Repo(s):** `atlas-infra`, `atlas-systems`, `status`; measured no-change review also covers `atlas-interface-kit`, `atlas-api-public`, `atlas-api-index`, `atlas-doc-viewer`, and `ramone-edge`
- **Agent:** ChatGPT with Atlas approving preview and rollout gates
- **Status:** active
- **Started:** 2026-07-30
- **Last updated:** 2026-07-30
- **Summary:** Execute the accepted measured accessibility and responsive correction phase one repository at a time. Current evidence narrows source changes to Status global-header touch targets and the carried `atlas-systems` accessibility, contrast, dense-overflow, and narrow-layout findings. Ramone's Phase 6 evidence clears its earlier footer targets; CV and Public API documentation have no carried blocking accessibility findings; API index remains JSON-only; no interface-kit release is currently justified.
- **Current thread:** `atlas-systems` Phase 8 source correction is merged. Follow-up PR #182 corrects homepage routes and removes duplicated route labels; it must complete exact-head browser evidence, merge approval, production deployment verification, and live-route verification before Phase 8 closeout is recorded in `atlas-infra` PR #95.

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
