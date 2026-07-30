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

### Public interface programme

- **Repo(s):** `atlas-infra`, `atlas-systems`, `atlas-interface-kit`, `atlas-api-public`, `atlas-api-index`, `status`, `atlas-doc-viewer`, `ramone-edge`, `atlas-article-gen`, `atlas-scheduler`
- **Agent:** ChatGPT
- **Status:** blocked
- **Started:** 2026-07-28
- **Last updated:** 2026-07-30
- **Summary:** Phases 0 through 5 are closed. Phase 6 authority, immutable `atlas-interface-kit v0.4.0`, consumer adoption, Writing footer restoration, and W-05 through W-07 deployment receipts are substantially complete. Phase 6 is not formally closed because `atlas-article-gen` draft PR #37 at `6f5da05c3a074eec0610b58dca93b2a8d8b645fe` and `atlas-scheduler` draft PR #44 at `4060d5e356ec3ff80fdb90955e0fcdf15e9a1994` remain open. Both exact heads are mergeable, have successful checks, and have no unresolved review threads. The current Phase 0 rebaseline is recorded in `docs/public-interface-phase-7-rebaseline.md` on `docs/public-interface-programme`.
- **Resume point:** Review and separately approve the exact heads of `atlas-article-gen` PR #37 and `atlas-scheduler` PR #44. After their approved merges, record merge and no-publication evidence, then review and merge the Phase 0 rebaseline pull request. Only then begin fresh repository-specific Part 0 inspections for Phase 7 `fix/browser-identity-contract` branches. Do not create Phase 7 source branches, add preview labels, merge consumer work, deploy, dispatch workflows, publish or refresh articles, run the scheduler in production, modify provider settings, or change secrets before those gates are complete.

### SPECULAR-CORE pending rollout

- **Repo(s):** `atlas-dep-audit`, `atlas-postmortem`, `atlas-blackbox`, `atlas-corpus`, `atlas-eval-harness`, `atlas-api-public`, `atlas-infra`, `ramone-memory`, `atlas-owui-tools`
- **Agent:** ChatGPT with Atlas operating on SPECULAR-CORE
- **Status:** active
- **Started:** 2026-07-28
- **Last updated:** 2026-07-29
- **Summary:** Complete the remaining SPECULAR-CORE rollout threads independently and one state-changing thread at a time. Thread A is complete using scheduled dependency-audit run `30263775549` against `fc565353c83f19d117ed3c3173d667429a672f66`. Thread B source implementation is complete and merged through `atlas-postmortem` PR #8 at `8cf8c0d2bec00dfc415dd76dcbaf3b3a65810491` and `atlas-owui-tools` PR #1 at `e35c9ff6913aecad027e297cb71e34993a5ad141`. The existing separate `ramone-postmortem` Open WebUI preset remains the conversational controller and is not the Ramone Agent. `atlas-postmortem` retains ownership of evidence retrieval, Corpus context, Ollama drafting, linting, local output, and processed-state recording. The controlled live rollout is prepared but has not been executed. The public-interface programme remains separately owned; its branches, pull requests, previews, and evidence are out of scope.
- **Current thread:** Thread B controlled live-rollout preparation and owner-run execution, with no service, secret, Open WebUI database, model assignment, or incident state changed yet.

## Paused work

_(none currently tracked)_

## Recently completed

_(none currently tracked)_

## Standing ownership

| Area | Default owner | Note |
| --- | --- | --- |
| Case study writing and the publishing pipeline | Atlas, agent-assisted | `atlas-article-gen` and `atlas-scheduler` documentation is authoritative. Agents inspect it before changing article generation, sequencing, refresh, or publication behaviour. |
| Repository governance and lifecycle | `atlas-infra` under ADR-0004 | Public repository classification changes begin in the authoritative policy inputs, never in generated projections. |
| Public interface authority | `atlas-infra` under ADR-0008 and ADR-0009 | Shared roles and non-overridable foundations are governed here. The classic Writing article footer is a bounded, non-transferable exception. `atlas-interface-kit` implements the normal accepted authority. |
| Interface-kit implementation and release | `atlas-interface-kit` | Consumers pin immutable repository-local bundles and verify fingerprints. |
| Model promotion evidence | `atlas-eval-harness` | Evidence-sensitive model choices require capability-specific evaluation before rollout. |
