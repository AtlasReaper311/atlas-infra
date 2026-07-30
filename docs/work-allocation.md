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
- **Status:** active
- **Started:** 2026-07-28
- **Last updated:** 2026-07-30
- **Summary:** Phases 0 through 6 are closed. Phase 7 implementation is merged through `atlas-article-gen` PR #39 at `9de98a02fc9bdf4430624d2383aafc2528529d61`, generator regeneration commit `5c32b7109be2e9772a3d7e03142bfabb78032bae`, scheduler sync commit `ec901c6a087ce01ad13a1d9dceae15e5c85b8fd4`, `atlas-systems` PR #178 at `8154b47e2ba62cbc89d893d06acbf97e73ed3b62`, `status` PR #32 at `4ee696150006dd72fe7b0d75eb0b5c5199f36747`, `atlas-doc-viewer` PR #31 at `ccf1b036d98cf0b1404089b561dbfe47c2f07432`, `ramone-edge` PR #30 at `e0e02775587178670aba09ddf49c37238b3f3e4a`, and `atlas-api-public` PR #52 at `5b970a9bf3b66b5469ce883aacec4a4b496e72cc`. The API index remains an intentional no-change result. Generator output synchronized only unpublished queue entries; the scheduler publication workflow was not dispatched and `atlas-systems` received no scheduler publication commit before its separate Phase 7 merge.
- **Current thread:** Obtain and record push-run and live custom-domain evidence for the main site, Status, CV, Ramone, and Public API documentation. Do not declare Phase 7 closed or begin Phase 8 until exact production deployment and representative live-route checks are recorded. Do not run the scheduler in production, publish or refresh articles, modify provider settings, or change secrets.

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
