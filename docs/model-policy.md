# Atlas Systems — Model Policy

Which Ollama model to use for which capability, and why. This is a derived
convenience document. When it disagrees with `atlas-eval-harness` promotion
records, a repo's own live configuration (its committed `.env.example`, and
more importantly the actual running container's environment, which have
disagreed with each other before), or current repo code, those win. A model
choice recorded here without a matching `atlas-eval-harness` case is a default,
not a proven promotion.

This document existed only as Claude.ai Project context until 2026-08-18; see
`docs/agent-conventions.md`'s "On this document itself" section for what that
did and did not fix.

## Current model assignments

| Capability | Repo | Model | Why |
|---|---|---|---|
| Corpus grounded Q&A (`/ask`) | `atlas-corpus` | Check `app/config.py` and the live `.env`, not this table | Has disagreed across the committed `.env.example`, the local `.env`, and this document simultaneously. `atlas-infra/policy/model-promotion-coverage.json` tracks this as `corpus-retrieval` and, as of the last check, explicitly flags "decide live/promoted mismatch" as unresolved. `_fallback_answer_from_hits()` returns grounded excerpts if synthesis times out, and, as of `atlas-corpus#33`, the service also degrades to BM25-only search with no synthesis at all if Ollama is unreachable rather than failing the request. |
| Session summarisation | `ramone-memory` | `llama3.1:8b` | Fine for summarisation. Not evaluated or trusted for reasoning tasks — see banned list below. |
| Session summary embedding | `ramone-memory` | `nomic-embed-text` | Shared embedding model across the estate; one pull serves `ramone-memory`, `atlas-corpus`, and `ollama-rag-kit`. |
| Corpus document embedding | `atlas-corpus` | `nomic-embed-text` | Same shared embedding model. |
| Ramone RAG generation | `ollama-rag-kit` | `qwen3:14b` (promoted 2026-08-18) | Evidence-sensitive: this generates Ramone's actual conversational answers. The live container was previously confirmed (via `docker inspect`, not the committed default) running the banned `llama3.1:8b`. `atlas-eval-harness#23` added the capability's first eval cases and scored `qwen3:14b`, `qwen2.5:32b`, and `llama3.1:8b`; the first two both passed 3/3, `llama3.1:8b` scored 2/3 and failed by confidently citing a fabricated answer. `qwen3:14b` was chosen for roughly 7.6x faster generation than `qwen2.5:32b` at equal correctness, on a path where Ramone has to speak the answer back. Confirm the `ollama-rag-kit` config change has actually been applied and rolled out before trusting this row; the eval case and the config change were tracked as separate PRs. |
| Incident postmortem drafting | `atlas-postmortem` | `qwen2.5:32b` | Evidence-sensitive reasoning task. Confirmed via `atlas-eval-harness` regression case after `llama3.1:8b` fabricated a non-existent `AtlasModel` class from a real diff. |
| Daily digest synthesis | `atlas-daily-digest` | `llama3.1:8b` | Not evaluated. `atlas-infra/policy/model-promotion-coverage.json` tracks this as `daily-digest-synthesis` with action "Add eval case." Lower stakes than Ramone RAG generation or postmortem drafting since the digest is a once-a-day summary rather than an interactive or investigative surface, but it is the same banned model and the gap is real. |
| `ollama-rag-kit` generation model | `ollama-rag-kit` | see "Ramone RAG generation" above | Superseded row; kept only so a stale link to this line doesn't resolve to nothing. |

## Banned or restricted models

| Model | Restriction | Evidence |
|---|---|---|
| `llama3.1:8b` | Blocked for evidence-sensitive root-cause writing and any postmortem-adjacent or interactive-answer reasoning task | Fabricated a non-existent `AtlasModel` class and `models/atlas.py` file when given the real diff for `inc-20260713-104620`, despite the causal commit sitting unused in context. This is a permanent regression case in `atlas-eval-harness`, not an anecdote. A second, independent failure was observed on the `ramone-rag-generation` capability during its 2026-08-18 eval: asked which model generates its own answers, given context that stated the embedding model and never stated the generation model, it confidently named the embedding model as the answer, with a citation to a block that did not support the claim. Still acceptable for pure summarisation (see `ramone-memory` above), which does not require causal or factual claims about code or context it hasn't seen. |

## Approved for evidence-sensitive reasoning

`qwen3:14b` and `qwen2.5:32b` are the models currently cleared for factual
postmortem drafting, Ramone RAG generation, and other reasoning tasks where a
wrong answer has real cost. Neither is a blanket endorsement —
`atlas-eval-harness` is what actually proves suitability per capability, not
model size, reputation, or a prior promotion on a different capability.
`qwen3:14b` generates substantially faster than `qwen2.5:32b` in practice
(observed roughly 7.6x on the `ramone-rag-generation` eval run), which matters
more on interactive paths than on batch ones like postmortem drafting.

## How promotion actually works

A model is not "promoted" by informal impression. `atlas-eval-harness` requires:

1. `run` — call every candidate model against every case in `cases/`, deterministic (temperature 0, fixed seed) via `/api/generate`.
2. Human review of the run's pass/fail matrix and specific failure evidence.
3. `promotion-prepare` — build a candidate record from the reviewed run, binding capability, model, prompt fingerprint, and runtime-options fingerprint.
4. `promotion-approve` — explicit human approval with `--confirm-reviewed-evidence`, only after reviewing the underlying run.
5. `promotion-check` — validate the resulting record.

The promotion record is evidence only. It does not pull or delete an Ollama
model, change Open WebUI, change Home Assistant, restart a service, or alter
model routing. Applying a promoted model to a live service is a separate,
explicitly approved rollout step.

## Writing a new eval case

One case per fabrication or capability gap found in practice, dropped into
`atlas-eval-harness/cases/` as a single TOML file: prompt, context, `required`
claims (string or any-of list), `forbidden` strings marking known
fabrications, and named `format_checks`. Forbidden lists are tripwires that
grow every time a new fabrication slips through review, not a guarantee of
completeness. Mirror an existing case file's structure (for example
`cases/corpus-grounding-service-bindings.toml`) rather than inventing a new
shape.

## When adding a new local-AI capability

Before wiring a new capability to a specific model:

1. Check this table first — a capability with similar reasoning-sensitivity to an existing entry should default to the same model, not a fresh guess.
2. If the capability is evidence-sensitive (postmortems, root-cause claims, anything a person could act on if wrong), write an `atlas-eval-harness` case before shipping the default.
3. Update this table once a model choice is either confirmed by an eval case or accepted as an informal default pending evaluation. Mark informal defaults as such rather than implying they were tested.
4. Check `atlas-infra/policy/model-promotion-coverage.json` for the capability's current risk rating and required next action; it is kept closer to live evidence than this table is.
