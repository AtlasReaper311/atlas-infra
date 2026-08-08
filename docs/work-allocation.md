# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This
is not architecture or policy. It records current and queued work so separate
sessions do not silently duplicate or reverse each other.

Update or remove an entry as soon as its status changes.

Last updated: 2026-08-08.

## Active work

### GitHub provider guard Wave 2B

- **Repo(s):** `atlas-infra`, `atlas-journey-watch`
- **Agent:** ChatGPT with Atlas approving any provider write
- **Status:** active, apply authority pending provider approval
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Wave 2A is closed. Owner-authenticated Wave 2B inspection authority merged through `atlas-infra#137` as `6c828ea1e98d4a731ffed3ee3def448212eb15df`. The reviewed archive SHA-256 is `abf7f135257a5b842188ea8ffae6cc9e2be28b0a0e60bbcba06d46c83bef0141`; all 18 manifest entries match. Existing ruleset `19154613` is active but only enforces `Offline journey validation` with strict status policy enabled. It does not require pull requests or block deletion/non-fast-forward updates, so `default_branch_guard` still fails. Repository auto-merge remains enabled, `DEPENDABOT_AUTOMERGE_ENABLED=true`, and genuine Dependabot PR `#12` is intentionally ineligible with `autoMergeRequest=null` because it is a GitHub Actions update rather than the narrow npm direct-development patch shape allowed by the pinned policy.
- **Resume point:** Validate and merge the fail-closed Wave 2B in-place reconciliation authority. Then obtain separate provider-write approval before updating existing ruleset `19154613`. The proposed provider mutation preserves the ruleset identity and name, adds the Atlas PR/deletion/non-fast-forward controls, preserves the native status context, leaves repository auto-merge and `DEPENDABOT_AUTOMERGE_ENABLED` unchanged, does not merge PR `#12`, and does not begin Wave 3.

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

### GitHub provider guard Wave 2A

- **Repo(s):** `atlas-infra`, `atlas-gardener`, `atlas-interface-kit`; read-only held-state evidence for `atlas-journey-watch`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Closed the bounded Wave 2A rollout. Source authority merged through `atlas-infra#134` as `487c7ba6ea6ffaf5e5a3e9bcc756435d075ba0f3`. A local post-write verifier-path defect stopped the first apply after Gardener ruleset `20576711` had been created successfully and before Interface Kit was touched. Recovery inspection proved the exact partial state; recovery authority merged through `atlas-infra#135` as `57cba128ea6f8e09ff293f84aec803e59ac8ecfe`; Interface Kit ruleset `20583644` then completed the approved provider scope. Owner validation `atlas-gardener#25` merged as `7e2b719c106f6da40c270a5aa2cf5b050ef05658` and `atlas-interface-kit#15` merged as `cd3f7223960a75e9344116e3960e613cdf267d90`. The final stamped scoreboard recorded 239 required passes, 21 required failures, and zero required unknowns, with both Wave 2A repositories passing `default_branch_guard`. Journey Watch ruleset `19154613` remains held for separate reconciliation with auto-merge enabled and `DEPENDABOT_AUTOMERGE_ENABLED=true`; Wave 3 remains unstarted.

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
