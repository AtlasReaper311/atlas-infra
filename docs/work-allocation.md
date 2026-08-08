# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This
is not architecture or policy. It records current and queued work so separate
sessions do not silently duplicate or reverse each other.

Update or remove an entry as soon as its status changes.

Last updated: 2026-08-08.

## Active work

### GitHub provider guard Wave 2

- **Repo(s):** `atlas-infra`, `atlas-gardener`, `atlas-interface-kit`, `atlas-journey-watch`
- **Agent:** ChatGPT with Atlas approving any provider write
- **Status:** active, inspection-only source stage
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Continue the default-branch provider-guard programme after the completed canary, Wave 1A, and Wave 1B. Fresh Part 0 identifies `atlas-gardener` and `atlas-interface-kit` as provisional Wave 2A candidates with repository auto-merge disabled and native contexts `test` and `Validate interface kit`. `atlas-journey-watch` is held as Wave 2B because repository auto-merge remains enabled and its selective Dependabot caller depends on the non-secret `DEPENDABOT_AUTOMERGE_ENABLED` variable. The current source stage authorises only an owner-authenticated read-only provider and automation-state inspection.
- **Resume point:** Validate and merge the Wave 2 inspection authority. Then run the owner-authenticated inspection and review existing rulesets/classic protection plus Gardener controller variables and Journey Watch selective auto-merge state. Do not author or execute a provider apply path until that evidence is reviewed. Do not begin Wave 3.

## Queued work

### New public-interface implementation programme

- **Repo(s):** expected initial scope is `atlas-infra`, `atlas-systems`, and
  `atlas-interface-kit`; add generator, scheduler, or supporting products only
  when a current finding requires their ownership
- **Agent:** Claude Design for read-only design refinement and ready-to-apply
  artifacts; ChatGPT or another write-capable agent for GitHub implementation
- **Status:** queued
- **Queued:** 2026-08-05
- **Summary:** Implement the accepted post-programme audit and prototype direction
  through fresh current-main branches. The first Part 0 must revalidate every
  finding against current source. Preserve route-specific product identity,
  protected Ramone and publication boundaries, label-gated previews, and the
  existing automatic `main` production deployment.
- **Start boundary:** Do not create implementation branches until the design
  handoff is internally consistent and a write-capable agent has completed fresh
  repository inspection. Claude Design must not claim GitHub writes that its
  toolset cannot perform.

## Recently completed

### GitHub provider guard Wave 1B

- **Repo(s):** `atlas-infra`, `ollama-rag-kit`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-07
- **Last updated:** 2026-08-08
- **Summary:** Closed the bounded `ollama-rag-kit` Wave 1B rollout. Source authority merged through `atlas-infra#131` as `1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3`. Ruleset `20573090` requires the repository-native `Build and smoke-check` context while blocking deletion and non-fast-forward updates, with no bypass actors and auto-merge unchanged. Owner validation `ollama-rag-kit#18` merged through the new guard as `e2cc5f4dadd3cc1bee5e8f72a6b710c8851c9657`. The final stamped scoreboard recorded 237 required passes, 23 required failures, and zero required unknowns, with `ollama-rag-kit/default_branch_guard` passed.

### atlas-twin Stage 1 change-passport MVP

- **Repo(s):** `atlas-twin`; coordination only in `atlas-infra`
- **Agent:** Cursor agent with Atlas approving exact-head squash merge
- **Status:** done
- **Started:** 2026-08-06
- **Last updated:** 2026-08-06
- **Summary:** Stage 1 offline CLI and library MVP merged through `atlas-twin#1` as squash commit `6ea6444cda72fd2dfb8c702f646010d60b7ac78c` from exact head `bccd49adde178e4ae2a97ebee9b0539f5f46e567`. No deployment or live rollout exists for `atlas-twin`; Stage 1 remains a private offline tool with no hosted runtime. This coordination PR updates work-allocation only and remains separately merge-gated.

### Public interface programme Phase 15

- **Repo(s):** `atlas-infra`, `atlas-systems`; read-only reconciliation included
  `atlas-interface-kit`, `status`, `atlas-doc-viewer`, `ramone-edge`,
  `atlas-api-public`, `atlas-api-index`, `atlas-article-gen`, and
  `atlas-scheduler`
- **Agent:** ChatGPT with Atlas approving preview, exact-head merge, and the
  resulting automatic production rollout
- **Status:** done
- **Started:** 2026-08-03
- **Last updated:** 2026-08-05
- **Summary:** Reconciled Phases 0 through 14, completed the live structural audit,
  corrected the late Blackbox Lab signature through `atlas-systems#198`, proved
  22 of 22 signatures in deterministic browser evidence, merged the reviewed
  head as `3be62f8915c0022e68187d9a66d9a808e87b6caa`, and verified production run
  `30999896059`, exact custom-domain commit identity, production smoke, and Atlas
  Corpus refresh. The original programme is closed. LAB-007a, Mode 04, SONIN,
  and superseded responsive intentions are separate successor-programme inputs.

### GitHub provider guard Wave 1A

- **Repo(s):** `atlas-infra`, `atlas-bootstrap`, `atlas-resource-audit`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated
  provider evidence
- **Status:** done
- **Started:** 2026-08-04
- **Last updated:** 2026-08-05
- **Summary:** Closed the `atlas-badges` canary and Wave 1A. Scoreboard required
  passes increased from 234 to 236, required failures fell from 26 to 24, and
  required unknowns remained zero. `atlas-bootstrap` and `atlas-resource-audit`
  passed `default_branch_guard`. Final closeout merged through
  `atlas-infra#126` as `b82839d0755bdd7e373ff35e59f13d088b2329c4`.

## Standing ownership

| Area | Default owner | Note |
| --- | --- | --- |
| Public-interface authority | `atlas-infra` under accepted ADRs and policy | Current repository truth and executable validators take precedence over historical programme prose. |
| Interface-kit implementation and release | `atlas-interface-kit` | Consumers pin immutable repository-local bundles and verify fingerprints. |
| Main portfolio and Lab implementation | `atlas-systems` | Pull-request previews are label-gated; approved merges deploy automatically from `main`. |
| Case-study authoring and rendering | `atlas-article-gen` | Inspect `docs/CASE_STUDY_INSTRUCTIONS.md`, templates, and `scripts/build_article.py` before work. |
| Publication sequencing and live generated output | `atlas-scheduler` | `docs/PUBLISHING_CONTRACT.md` is canonical and the scheduler remains the only generated-output write path into `atlas-systems`. |
| Repository governance and lifecycle | `atlas-infra` under ADR-0004 | Change authoritative inputs, never generated projections. |
| Model promotion evidence | `atlas-eval-harness` | Evidence-sensitive model choices require capability-specific evaluation before rollout. |
