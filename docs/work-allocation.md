# Atlas Systems - Work Allocation

Living coordination document for agents currently working on Atlas Systems. This
is not architecture or policy. It records current and queued work so separate
sessions do not silently duplicate or reverse each other.

Update or remove an entry as soon as its status changes.

Last updated: 2026-08-19.

## Active work

### Runtime-aware model self-improvement inventory

- **Repo(s):** `atlas-infra` first; follow-up work may involve
  `atlas-eval-harness`, `ramone-memory`, `ollama-rag-kit`,
  `atlas-corpus`, `atlas-postmortem`, `atlas-daily-digest`, and
  `specular-telemetry` only after a reviewed source plan proves ownership
- **Agent:** ChatGPT/Codex on SPECULAR-CORE with owner-approved batching
- **Status:** active
- **Started:** 2026-08-19
- **Summary:** Add source-owned runtime model-call inventory and mismatch checks
  so live-interactive, async, draft, embedding, telemetry, Open WebUI, and Home
  Assistant warmup model usage are compared against promotion and eval evidence
  rather than stale policy labels. The first slice is source-only in
  `atlas-infra`; SPECULAR-CORE runtime repair and any eval-harness expansion
  remain separately bounded follow-ups.
- **Boundary:** No Home Assistant model routing changes, no Ollama model pulls or
  deletes, no workflow dispatch, no deployment, no merge, and no secret-value
  inspection. Model-promotion evidence must continue through
  `atlas-eval-harness` and the `promotion-prepare` -> `promotion-approve`
  process.

### Ramone RAG generation model promotion

- **Repo(s):** `atlas-eval-harness`, `ollama-rag-kit`
- **Agent:** Claude Code on SPECULAR-CORE; Atlas approving model choice and rollout
- **Status:** active
- **Started:** 2026-08-18
- **Last updated:** 2026-08-19
- **Summary:** `ramone-rag-generation` was Critical risk with no eval coverage; the live `ollama-rag-kit` container was confirmed, via `docker inspect` on the actual running container rather than the committed default, to be running the banned `llama3.1:8b`. Eval cases and a scored three-model comparison merged through `atlas-eval-harness#23`. Atlas selected `qwen3:14b`: equal correctness to `qwen2.5:32b` (3/3 each; `llama3.1:8b` scored 2/3 and failed by confidently citing a fabricated answer), roughly 7.6x faster generation on this interactive path.
- **Resume point:** Review and merge the pending `atlas-eval-harness` promotion
  evidence for `qwen3:14b`, then draft the `ollama-rag-kit` config change
  (`LLM_MODEL` to `qwen3:14b`) as its own PR. Live rollout to the running
  service is a separate approved step after that.

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

### Corpus degraded search and digest event-window fix

- **Repo(s):** `atlas-corpus`, `atlas-notify`, `atlas-daily-digest`
- **Agent:** Claude Code on SPECULAR-CORE; Atlas approving each merge
- **Status:** done
- **Started:** 2026-08-18
- **Last updated:** 2026-08-18
- **Summary:** `atlas-corpus` previously failed to start, and returned 500s on `/search`, whenever Ollama was unreachable, because embedding ran unconditionally before retrieval and startup blocked on Ollama being reachable. `atlas-corpus#33` (merged) adds a BM25-only degraded path with a `degraded` response flag, observed working against a real stopped-then-restarted Ollama, with the pre-change image's crash captured as before/after evidence. Separately, the daily digest's thin output on busy days traced to two defects, not buffer size as first assumed: `/notify/recent` capped every read at 50 events regardless of buffer depth, and a non-atomic KV read-modify-write let dependency-PR bursts erase earlier history. `atlas-notify#26` (merged) splits the ring buffer into per-day keys and raises the page cap; `atlas-daily-digest#16` (merged, depended on #26) excludes routine dependency-bump events from the digest's window using the same `signal_class` filtering `atlas-infra`'s rollout board already applies.

### GitHub provider guard Wave 4

- **Repo(s):** `atlas-infra`; provider scope covered the reviewed 13-repository Wave 4A create-first batch, `atlas-dora` Wave 4B, the separately owner-operated final profile guard, and day-zero reconciler activation
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-08
- **Last updated:** 2026-08-09
- **Summary:** Closed GitHub Provider Guard Wave 4. Wave 4A created the 13 reviewed default-branch guards. Wave 4B reconciled `atlas-dora` ruleset `19581236` in place to the four-rule shape while preserving `check` and `Gardener native auto-merge barrier`. The profile writer redesign landed through `AtlasReaper311/AtlasReaper311#8`, pre-guard automation succeeded through `#9`, and final profile ruleset `20595678` was installed by a separate owner-operated provider action. The day-zero create-only reconciler is enabled, scheduled, and healthy with observed no-op apply evidence of 33 compliant / 0 create / 0 blocked. One-shot Wave 4A and Wave 4B operators are retained unchanged as historical fail-closed evidence and are not current maintenance authority. Final owner-authenticated scoreboard: 260 required passes, 0 required failures, 0 required unknowns; fingerprint `sha256:34265f801dfcd5ca1d24d93b0041aa707a8746d01879f3da8bab30df053ed5fe`. Permanent closeout: `docs/github-provider-guard-wave-4-closeout.md` and `reports/github-provider-guard-wave-4-final-receipt.json`.

### GitHub provider guard Wave 3

- **Repo(s):** `atlas-infra`, `atlas-doc-viewer`, `atlas-quota-watch`, `site-pulse`, `specular-sonify`, `status`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Closed the five-repository classic-protection migration. Inspection authority merged through `atlas-infra#140` as `1cd123cafcaab0bb2736c1659e6f389922190c60`; batch migration authority merged through `atlas-infra#141` as `2edd65f4cc1b1e62c50630881ba7df42b8a2c0b7`. The approved fail-closed provider batch created and verified rulesets `20586980` through `20586984` before removing the five superseded classic protections. Repository auto-merge, `ATLAS_GARDENER_AUTOMERGE_ENABLED=true`, absent `DEPENDABOT_AUTOMERGE_ENABLED`, the Gardener controller, secrets, runtime state, and existing Dependabot PRs were preserved. Owner validation PRs `atlas-doc-viewer#35`, `atlas-quota-watch#15`, `site-pulse#17`, `specular-sonify#20`, and `status#37` all passed their repository-native required context plus `Gardener native auto-merge barrier` and were squash-merged from the exact reviewed heads. The final owner-authenticated scoreboard recorded 245 required passes, 15 required failures, and zero required unknowns, with all five Wave 3 `default_branch_guard` outcomes passed. Final scoreboard fingerprint: `sha256:3a105c77e74827fd5a46e8cf89f59c0981422c4e7b071f1bf4a1dc314fab8e5b`. Final evidence archive SHA-256: `b11c0f23f52dc26bcee5cf7436511ad97966aa1a8f1662207a4803c58fcda28b`, with all 66 manifest payloads present and matching. Wave 4 later completed under a separate programme; see `docs/github-provider-guard-wave-4-closeout.md`.

### GitHub provider guard Wave 2B

- **Repo(s):** `atlas-infra`, `atlas-journey-watch`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Closed the Journey Watch reconciliation without creating a second ruleset. Inspection authority merged through `atlas-infra#137` as `6c828ea1e98d4a731ffed3ee3def448212eb15df`; apply authority merged through `atlas-infra#138` as `4b91cdb43734ddf507193022aa0ce847aadcee11`. Existing ruleset `19154613` was updated in place to the four-rule Atlas default-branch guard while preserving `Offline journey validation`, repository auto-merge, and `DEPENDABOT_AUTOMERGE_ENABLED=true`. Owner validation `atlas-journey-watch#13` merged through the reconciled guard as `40c77bd6926833fccc09fe0db098a38b1ea507f8`. Genuine Dependabot PR `#12` remains open and unmerged. The final stamped scoreboard recorded 240 required passes, 20 required failures, and zero required unknowns, with `atlas-journey-watch/default_branch_guard` passed. The final ZIP had a packaging-scope omission of two pre-existing Atlas Infra reports only; all packaged payload hashes matched and the canonical scoreboard fingerprint recomputed exactly.

### GitHub provider guard Wave 2A

- **Repo(s):** `atlas-infra`, `atlas-gardener`, `atlas-interface-kit`; read-only held-state evidence for `atlas-journey-watch`
- **Agent:** ChatGPT with Atlas supplying and approving owner-authenticated provider evidence
- **Status:** done
- **Started:** 2026-08-08
- **Last updated:** 2026-08-08
- **Summary:** Closed the bounded Wave 2A rollout. Source authority merged through `atlas-infra#134` as `487c7ba6ea6ffaf5e5a3e9bcc756435d075ba0f3`. A local post-write verifier-path defect stopped the first apply after Gardener ruleset `20576711` had been created successfully and before Interface Kit was touched. Recovery inspection proved the exact partial state; recovery authority merged through `atlas-infra#135` as `57cba128ea6f8e09ff293f84aec803e59ac8ecfe`; Interface Kit ruleset `20583644` then completed the approved provider scope. Owner validation `atlas-gardener#25` merged as `7e2b719c106f6da40c270a5aa2cf5b050ef05658` and `atlas-interface-kit#15` merged as `cd3f7223960a75e9344116e3960e613cdf267d90`. The final stamped scoreboard recorded 239 required passes, 21 required failures, and zero required unknowns, with both Wave 2A repositories passing `default_branch_guard`. Journey Watch subsequently completed separate Wave 2B reconciliation.

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
| Cross-agent estate conventions | `atlas-infra` (`docs/agent-conventions.md`, `docs/model-policy.md`) | These previously existed only as Claude.ai Project context, not committed source; agents working from a fresh checkout had no way to discover them. Committed 2026-08-18. Individual repos' own `AGENTS.md`/`CLAUDE.md` do not yet point here — that is separate follow-up work, not solved by this commit. |
