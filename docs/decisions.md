# Atlas Systems — Technical Decisions Log

## Infrastructure

### Hosting

- **Decision:** Cloudflare Pages for static sites, Cloudflare Workers for the API surface
- **Date:** May 2026 (Pages); progressively added Workers through May–June 2026
- **Detail:** Three static sites on Pages — `atlas-systems` (atlas-systems.uk), `status` (status.atlas-systems.uk), `atlas-doc-viewer` (cv.atlas-systems.uk). Worker surface under `api.atlas-systems.uk/*` now spans eleven Workers (see Logic Lego Suite below for the six added 2026-07-02).
- **Why:** Free tier covers everything at this scale (100k Worker requests/day per Worker, unlimited Pages bandwidth). No paid services anywhere on the stack — £0 budget is a hard requirement.

### Cloudflare plan upgrade — Workers Plus *(new 2026-07-02)*

- **Decision:** Upgraded from Workers free tier to Workers Plus.
- **Why:** Several architecture choices earlier in the estate (specular-edge's 60-second Cache API + conditional KV write, atlas-api-index's hourly-not-more-frequent cron, conservative KV write budgeting across the Logic Lego suite) were partly shaped around free-tier KV write/read caps and CPU time limits, not purely by what was technically ideal. This is the first paid line item in the estate — the £0 hard requirement is now relaxed specifically for Cloudflare Workers Plus, not extended to any other service.
- **Practical effect:** KV read/write/storage ceilings raised substantially, per-request CPU time increased, higher-frequency Cron Triggers available. Nothing currently deployed *requires* the upgrade to keep working — everything built so far was designed to survive on free tier — but future design decisions no longer need to treat free-tier limits as a constraint by default.
- **Follow-up (not yet done):** revisit the conservative choices made under the old constraint — `specular-edge`'s cache window, `atlas-api-index`'s cron frequency — and decide deliberately whether to tighten them now that headroom exists, rather than leaving them conservative by inertia.

### CI/CD

- **Decision (June 2026):** GitHub Actions across every repo, with reusable workflows in `atlas-infra`. Cloudflare native Git integration disconnected on all three static sites — Actions is now the only path to production.
- **Detail:** `atlas-infra/.github/workflows/deploy-worker.yml` and `validate-static.yml` are `workflow_call` reusables. Every other repo holds a 12-line caller. Validate (wrangler dry-run + lint, or html-validate + lychee) → deploy → notify Discord. atlas-notify deploys on `workflow_run` of its CI success, not push, so Vitest never runs twice.
- **Why:** Five Worker repos with five hand-maintained deploy.yml files drift in days. One reusable workflow means one PR to change the pipeline shape everywhere. Hard gate over soft gate on static sites: a broken HTML tag literally cannot ship now.
- **Supersedes:** The May 2026 entry that had Cloudflare native integration as the production path and Actions as dormant fallback. That decision was correct for May; superseded once there were enough deployable repos to justify the reusable-workflow investment.
- **Extended 2026-07-02:** New-repo CI convention formalised for the Logic Lego build. Python service repos (ramone-memory, atlas-corpus) ship an inline `ci.yml` — `compileall`, `docker compose build`, direct curl notify to `#ci-cd`. Worker repos (ramone-voice-trigger, atlas-api-index) ship an inline parse-check `ci.yml` and copy the 12-line reusable deploy caller from `github-pulse` rather than guessing `atlas-infra`'s input interface fresh each time. Every new workflow declares `workflow_dispatch:` from day one, because `ramone-trigger` needs to be able to dispatch it without a follow-up patch — see Logic Lego Suite.
- **Gotcha banked:** `npm ci` requires an existing lockfile. Two of the six new repos (`ramone-voice-trigger`, `atlas-api-index`) shipped without `package-lock.json`, so their documented `npm ci` step failed on first run. Fix is a one-time `npm install` to generate the lockfile before CI can use `npm ci`. Worth checking for on every new Worker repo template going forward.

### Release assurance is stateless and journey-owned *(new 2026-07-14)*

- **Decision:** `atlas-journey-watch` owns Phase 3 release verification execution and targeted journeys; `atlas-infra` owns the `ReleaseEvidence` contract, policy, calling example, and runbook. The first version is event-driven and stateless, with no automatic rollback.
- **Why:** Release verification is an extension of the existing public-journey read boundary. Keeping it there avoids a second browser executor or a new repository, while central policy remains independent of one producer.
- **Consequences:** A deploy caller provides explicit repository, full commit, service ID, environment, target, metadata URL, and rollback reference. Missing identity never becomes `live`. No manifest registration is needed because Phase 3 adds no service, public endpoint, storage layer, scheduled job, or deploy credential.

### Secret assurance is declarations plus names-only enforcement *(new 2026-07-14)*

- **Decision:** `atlas-infra` owns the versioned secret declaration and response runbooks; `atlas-dep-audit` owns policy validation, optional GitHub names-only comparison, tracked-file plaintext scanning, and Finding v1 output.
- **Boundary:** No component requests a secret value or writes provider state. GitHub metadata is optional unless a repository declaration explicitly requires it. Missing or under-permissioned metadata is `unavailable`, never healthy. `simple-proxy` remains excluded because it is deprecated and external-derived.
- **Why:** Secret meaning, lifecycle, and classification are estate policy, while detection belongs beside the existing read-only supply-chain assurance path. Keeping those responsibilities separate prevents policy from becoming an API client and prevents the scanner from inventing ownership.

### Token model

- **Decision:** Narrowly-scoped Cloudflare tokens, never one account-wide token. Deploy-time and runtime credential paths never share secrets.
- **Detail:** `CF_WORKERS_DEPLOY_TOKEN` (Workers Scripts:Edit + Workers Routes:Edit) for Worker repos. `CF_PAGES_DEPLOY_TOKEN` (Pages:Edit) for the three static-site repos. Runtime secrets that Workers themselves use (e.g. deploy-watch's Pages:Read token, site-pulse's Zone Analytics:Read token) are set with `wrangler secret put` and are entirely separate from deploy tokens.
- **Why:** A leaked deploy token is bounded by its permission class.
- **Extended 2026-07-02:** `atlas-api-index` introduced a third token class — a **read-only discovery token**. Its runtime `CF_API_TOKEN` is a user API token (not the Global API Key) scoped to `Account → Workers Scripts → Read` and `Zone → Workers Routes → Read` only. It cannot edit anything. This is the same logic as the deploy/runtime split, one level further: a Worker whose entire job is *reading* the estate's shape has no business holding write scope, even accidentally. Treat this as the default pattern for any future estate-introspection Worker.
- **Extended 2026-07-02 (second entry, same day) — least-privilege applies to GitHub tokens too:** `ramone-voice-trigger`'s `GITHUB_TOKEN` is a fine-grained, named-repo-only token scoped to just the repos in its allowlist, not full account access. Broad access is accepted only where GitHub's UI forces it for a required permission — never chosen by default. Same logic as the Cloudflare token split: a leaked or misused trigger token should only be able to affect what it was explicitly scoped to.

### Discord routing

- **Decision:** Three narrow channels, one signal class per channel. CI/deploy notifications post directly via `curl` from inside the reusable workflows, not routed through atlas-notify.
- **Detail:** `#api-deploys` for Worker deploy outcomes, `#deploy-log` for static-site deploy outcomes, `#ci-cd` for test/CI results. Also `#push-log`, `#weekly-digest`, `#vault-backups`.
- **Why:** A single firehose channel buries useful signal. Direct curl over routing through atlas-notify because CI workflows are self-contained and shouldn't depend on the router being up to report their own outcomes.
- **Clarified 2026-07-02 — two separate notification paths now coexist by design, not by accident:**
  - **CI/deploy events** (GitHub Actions outcomes) → direct `curl` to a Discord webhook, as above. Unchanged.
  - **Worker runtime events** (a Worker telling the world something happened while it was live — a trigger fired, telemetry flipped offline, a corpus refresh failed) → a fixed alert envelope, `{source: "alert", level, title, message, fields}`, sent with a Bearer `NOTIFY_TOKEN` over the `ATLAS_NOTIFY` **service binding**, with a URL fallback for local dev, and designed to never throw on failure. `ramone-trigger`, `specular-edge`, and `atlas-corpus` all consume this. `NOTIFY_SIGNAL_CLASS` rides along as a var so channel routing logic can be added inside atlas-notify later without touching any consumer.
  - **Why the split holds:** a GitHub Actions job doesn't need a Worker in the loop to post its own result — direct curl is simpler and has one fewer moving part to be down. A *Worker* telling another Worker something, on the other hand, is already paying the cost of a network hop; routing that hop through a service binding to atlas-notify is strictly better than each Worker maintaining its own webhook logic, and avoids the 522s that public-URL Worker-to-Worker calls produce (see Logic Lego Suite → Problems encountered).

### Docker

- **Decision:** Local pipeline working; ollama-rag-kit was the first production-adjacent use, now joined by three more Docker/systemd-backed local services.
- **Detail:** ollama-rag-kit, ramone-memory, and atlas-corpus all run as docker-compose stacks on SPECULAR-CORE (WSL2 Ubuntu, RTX 5070). specular-telemetry runs as a native WSL systemd unit rather than a container (it needs direct NVML access). The CI gate for Python service repos is `docker compose build`. `atlas-infra/docker/hello-atlas` remains the proven template.
- **Status — milestone reached 2026-07-02:** "Public exposure via Cloudflare Tunnel," previously listed as the next step, is now live for two of the four local services. `specular-telemetry` (port 9000) and `atlas-corpus` (port 8092) are both tunnelled through the existing Cloudflared instance (`C:\ProgramData\cloudflared\config.yml`, ingress rules ordered above the catch-all) and fronted by Cloudflare Workers/routes at `api.atlas-systems.uk/specular` and `corpus.atlas-systems.uk` respectively. `ramone-memory` (port 8091) stays local-only by design — it's consumed by Home Assistant on the same LAN, not the public internet.

### Repo structure

- `atlas-systems` — main site, atlas-systems.uk
- `atlas-doc-viewer` — CV gate + viewer, cv.atlas-systems.uk
- `status` — live status page, status.atlas-systems.uk
- `atlas-notify` — event router Worker, central Discord poster (curl-based for CI, service-binding envelope for Worker runtime alerts)
- `github-pulse` — GitHub stats proxy Worker
- `site-pulse` — Cloudflare Analytics proxy Worker
- `deploy-watch` — Cloudflare Pages deploy poller Worker
- `atlas-vault` — personal streaming-data backup vault Worker
- `atlas-infra` — reusable workflows, Docker templates, decisions docs (this file)
- `atlas-kit-python-rag` — Python RAG kit (FastAPI + ChromaDB + Ollama); currently has uncommitted local changes, left alone
- `ollama-rag-kit` — docker-compose stack for local AI infrastructure
- `atlas-article-gen` (private) — generates case study HTML from Markdown frontmatter, 76 pytest tests, 90% coverage
- `atlas-scheduler` (private) — cron-publishes generated articles to atlas-systems, 50 pytest tests, 83% coverage
- **`ramone-memory`** *(new 2026-07-02)* — local FastAPI + ChromaDB memory-injection proxy (port 8091) sitting in front of raw Ollama (11434), giving Ramone cross-session memory
- **`specular-telemetry`** *(new 2026-07-02)* — local FastAPI hardware/service telemetry (WSL systemd, port 9000) + `specular-edge` Worker exposing it publicly
- **`ramone-voice-trigger`** *(new 2026-07-02)* — Cloudflare Worker (`ramone-trigger`) that authenticates and dispatches allowlisted GitHub Actions workflows, enabling voice-triggered deploys
- **`atlas-corpus`** *(new 2026-07-02)* — local FastAPI + ChromaDB + Ollama RAG search service (port 8092) over estate docs/repos, public at corpus.atlas-systems.uk, embedded in Lab
- **`atlas-bootstrap`** *(new 2026-07-02)* — machine reconstruction/recovery repo: WSL health checks, Windows portproxy refresh, repo cloning, env seeding, service startup
- **`atlas-api-index`** *(new 2026-07-02)* — Cloudflare Worker self-documenting registry at api.atlas-systems.uk/ (and /_meta): discovers and probes every estate Worker, caches in KV, rebuilds hourly

---

## Logic Lego Suite (2026-07-02)

Six repos, installed and corrected in a single day, under the canonical estate root `L:\Atlas-Systems` (`/mnt/l/Atlas-Systems` in WSL2) — the layout is now fixed estate-wide; zip archives stay in Downloads, working trees live under the estate root. All six are live, deployed, and health-checked as of this entry. This section is Pillar 2 (modular library) and Pillar 3 (DevOps core) advancing together: each repo is a self-contained "Logic Lego" brick, but several of them only became load-bearing because of contracts introduced this session — the `/_meta` shape, the alert envelope, and the conditional-KV-write pattern all now apply estate-wide, not just to the repo that introduced them.

### The `/_meta` contract is fixed estate-wide

- **Decision:** `GET <route-prefix>/_meta` returns `{name, description, version, endpoints[], status, source}` on every Worker.
- **Detail:** The module is a vendored ~40-line file, canonical copy at `atlas-api-index/shared/_meta.js`, copied into each Worker's `src/` rather than npm-published — one import line per Worker, no publish step, no registry dependency, £0. Suffix matching means the same file works behind any route prefix or a bare `workers.dev` host.
- **Why:** `atlas-api-index` can only document what adopts the contract. A vendored file with no publish step keeps the £0 constraint intact while still giving every Worker a canonical, reusable implementation instead of eleven bespoke ones.
- **Current adoption:** 3 of 11 discovered Workers are documented (`atlas-api-index`, `ramone-trigger`, `specular-edge`). 8 are not yet (`atlas-backend`, `atlas-notify`, `atlas-vault`, `deploy-watch`, `github-pulse`, `ramone-edge`, `simple-proxy`, `site-pulse`) — this is the single biggest open item from today's build (see Gaps).

### KV conditional-write rule now covers caching, not just polling

- **Decision:** Cache API for hot data, KV only for a last-known-good snapshot written on state change or staleness, never as a naive per-request cache.
- **Detail:** `specular-edge` uses the Cache API as its 60-second hot cache (free, unlimited) and `TELEMETRY_KV` only for a last-known-good snapshot, written on an online/offline flip or when the stored copy is over ten minutes old — roughly 150 writes/day where a naive "cache in KV for 60s" design would cost up to 1,440 against the 1,000/day free-tier cap.
- **Why:** Same shape as the `deploy-watch` fix banked earlier this year. Treat conditional-write-on-state-change as the default pattern for any edge cache going forward, not just for polling loops.
- **Note 2026-07-02 (Workers Plus upgrade):** this pattern was partly cost-driven under the free tier. Worth a deliberate pass to decide whether to relax it now that KV headroom is larger — see Cloudflare plan upgrade above.

### Worker naming and route layering

- **Decision:** New Workers — `specular-edge` (mirrors `ramone-edge`'s naming), `ramone-trigger` (the deployed name of the `ramone-voice-trigger` repo), `atlas-api-index` (atlas-noun pattern). Route claims are ordered most-specific-first.
- **Detail:** All three claim `api.atlas-systems.uk` paths more specific than `atlas-notify`'s `/*` wildcard. `atlas-api-index` claims exactly `/` and `/_meta`, which retires the hand-maintained root JSON list with no unwiring required elsewhere.
- **Why:** Cloudflare route matching is most-specific-wins; keeping new routes deliberately narrower than the wildcard means new Workers can be added without ever touching `atlas-notify`'s catch-all.
- **Note:** this is the first time a repo name (`ramone-voice-trigger`) and its deployed Worker name (`ramone-trigger`) have diverged for brevity. `specular-telemetry` → `specular-edge` is the same pattern. Worth formalising as a documented convention rather than an implicit one — see Decisions Pending.

### `ramone-memory` is an Ollama-compatible proxy, not a custom integration

- **Decision:** `ramone-memory` speaks the exact Ollama API shape (`/api/chat`, streaming included) rather than inventing a new protocol.
- **Detail:** Memory is injected into the system prompt server-side, so pointing Home Assistant at it is a URL swap (`:11434` → `:8091`) with zero HA-side protocol changes. Ollama has no end-of-conversation event, so sessions finalise by explicit `/sessions/{id}/end` call or a 300-second idle reaper with bounded retry. Sessions are fingerprinted from the first user message; an `X-Session-Id` header opts out of fingerprinting. Long-term memory lives in its own `ramone_memory` ChromaDB collection; `ollama-rag-kit`'s `ramone_sessions` collection stays the separate short-term rolling layer — the two never share data.
- **Why:** An Ollama-compatible proxy is a drop-in for any existing Ollama client, not just Home Assistant, and costs nothing extra to build since the proxy has to parse the request anyway.
- **Operational gotcha banked:** Home Assistant can have two valid-looking Ollama integrations configured (`Ollama (raw, no memory)` on `:11434` and `Ollama (Ramone memory)` on `:8091`) and still bypass memory entirely, because the thing that actually matters is which conversation entity the *Assist pipeline* has selected as `conversation_engine` — not which integrations exist in the list. This produced a real incident (Ramone was talking but not remembering) and is banked as a general principle below.
- **Recurrence flagged 2026-07-02 (later same day):** the same class of symptom (memory not working, voice-deploy not firing) reappeared after the TRIGGER_SECRET rotation session below. Not yet root-caused — see Decisions Pending / open item.

### `atlas-notify` consumers standardise on the alert envelope over service bindings

- Covered above under Discord routing; recorded here too because it's a Logic Lego-introduced contract, not a pre-existing one.

### Voice deployment is a client of the pipeline, not a new capability

- **Decision:** `ramone-trigger`'s `REPO_ALLOWLIST` var (a JSON map of `repo → workflow file`) is the single source of truth for what voice can touch. All allowlisted callers now declare `workflow_dispatch:` in their own workflow files.
- **Detail:** Home Assistant resolves a spoken phrase to a repo slug, sends it with `x-trigger-secret` to the Worker, the Worker checks the secret and the allowlist, then calls GitHub's `workflow_dispatch` API for the mapped workflow, then notifies via the `ATLAS_NOTIFY` envelope. `atlas-notify` itself is a special case in the allowlist because its deploy chains through `workflow_run` rather than a direct push-triggered workflow. HA's `rest_command` integration does not expose the HTTP response body back to the automation, so the spoken confirmation ("Deploy request sent...") only proves the request left Home Assistant — it cannot prove GitHub accepted or finished it. A 120-second completion watch runs in `waitUntil` as additive comfort; the pipeline's own Discord notify remains the guaranteed completion signal, not the spoken response.
- **Why:** Voice is not a parallel deployment system with its own trust model — it's the exact same GitHub Actions pipeline everything else uses, gated by one more authenticated client. That keeps the attack surface and the mental model both small.
- **Confirmed working end-to-end** via a live voice command ("Deploy GitHub Pulse") → Worker dispatch → GitHub Actions run → Discord notification, same day.
- **Confirmed a second time 2026-07-02 (manual API test, post-build):** direct `Invoke-RestMethod` POST to `/trigger` with a rotated `TRIGGER_SECRET` returned `triggered: true` with a real `run_url`, independent of the HA voice path — see PowerShell secrets handling below for how this test was nearly derailed by an unrelated shell-quoting issue.

### Public search endpoints carry edge protections in-app

- **Decision:** `atlas-corpus`'s `/search` is browser-facing through the tunnel, so it holds its own per-IP sliding hourly rate limit (`CF-Connecting-IP`), a 500-character query cap, and a CORS allowlist — all inside the FastAPI service itself, not delegated to a Worker in front of it. `/refresh` is gated by `CORPUS_SECRET` and fail-closed at startup, the same precedent `ATLAS_SECRET` set earlier.
- **Why:** `/search` is intentionally unauthenticated (it powers the public Lab widget), so the protections that would normally live at the edge have to live in-app instead, since there's no Worker sitting in front of this particular tunnel route doing that job.

### Corpus re-ingest converges rather than accretes

- **Decision:** Chunk IDs are deterministic — `sha1(repo:path:index)` — so a `/refresh` is an upsert-plus-prune of stale indexes, not an ever-growing pile of duplicate vectors.
- **Detail:** Chunking is a word-window of 512 words with 64-word overlap, approximating a token-based spec without adding a tokenizer dependency. The brand and context docs ingest from a gitignored, read-only `./docs` mount populated from `atlas-brand.md` and `Atlas_Systems_-context.md`.
- **Why:** Deterministic IDs make re-ingestion idempotent by construction — running `/refresh` twice in a row produces the same corpus state, not two overlapping ones.

### `atlas-bootstrap` owns the machine contracts

- **Decision:** Portproxy rules are delete-then-add and re-derived by a SYSTEM scheduled task at startup and logon — this supersedes the old `ATLAS_BOOTSTRAP.bat` script and **closes its long-standing documented portproxy-drift gap for good.**
- **Detail:** Ollama's `0.0.0.0` binding is written as a systemd drop-in by bootstrap (drop-ins survive package upgrades; direct unit edits don't). Docker Desktop is skipped when native Docker Engine is already detected inside WSL2. Repos, services, health endpoints, and models are all `lib/*.json` configuration, not hardcoded into the script — so fixing a stale repo reference is a JSON edit, not a script edit.
- **Why:** The previous state of this problem (WSL2 IP drifting on every reboot, portproxy silently going stale) was a recurring, self-inflicted outage. Making the refresh a boot/logon task rather than something remembered-and-run-manually removes the human from the failure path entirely.
- **Health check hardening banked:** the `nomic-embed-text` vs `nomic-embed-text:latest` string-match bug (a present model reading as "missing") and the `HTTP 000` vs a real failure code bug (a dead connection reading as "up") were both fixed as part of this repo. Small, boring bugs, but exactly the kind that make a health check lie to you at 2am.

### Port allocations

- `8091` — `ramone-memory`
- `8092` — `atlas-corpus`
- `9000` — `specular-telemetry` (moved Portainer to `9001` to free this)
- Joining the existing portproxy set: `8000`, `8080`, `8081`, `11434`

### Registry discovery is read-only by construction

- **Decision:** `atlas-api-index`'s runtime `CF_API_TOKEN` carries `Workers Scripts:Read` and `Workers Routes:Read` only, minted separately from any deploy token (see Token model).
- **Detail:** Registry KV carries a 75-minute TTL against the hourly cron (`7 * * * *`), with on-demand rebuild on a cold read — so one missed cron degrades nothing and a genuinely dead cron surfaces within the hour rather than silently. New-worker notifications diff against the previous snapshot, so the first pass and any flapping worker stay silent instead of spamming Discord.
- **Why:** A registry that can only read the estate is safe to run unattended on a cron with no write blast radius if it's ever compromised. The TTL-plus-cold-rebuild pattern means correctness never depends on the cron firing on schedule.

### New-repo CI convention

- Covered above under CI/CD; recorded here too as the Logic Lego-specific instance of the estate-wide rule.

### Problems encountered and fixed (lessons banked)

- **A healthy API can still fail in the browser.** `atlas-corpus`'s service and CLI checks were all green while the live Lab search failed with a `NetworkError`. Root cause was the site's Content-Security-Policy `connect-src` not allowlisting `https://corpus.atlas-systems.uk` — nothing to do with the API itself. Always test from the actual browser context, not just curl, before declaring a public-facing feature done. **Standing rule:** any repo that adds a new `*.atlas-systems.uk` API surface must include a CSP `connect-src` reminder in its own README, referencing `atlas-systems/_headers` explicitly.
- **Worker-to-Worker calls through the public hostname return 522.** `atlas-api-index` probing other Workers' `/_meta` via `https://api.atlas-systems.uk/...` — the exact same URLs that work fine from outside — got `522`s internally. Fix is Cloudflare **service bindings** for known Workers; this is now the estate default for any Worker-to-Worker call, not just this one (`ramone-edge`'s notify calls hit the identical issue earlier this year).
- **Route-metadata generation can double-append a suffix.** The registry was generating `.../ _meta/_meta` by blindly appending `/_meta` to every discovered route, including routes that already ended in `/_meta`. Fix: detect already-terminal routes before appending anything.
- **Wrangler refuses an empty KV namespace ID in config.** `id = ""` in `wrangler.toml` blocks Wrangler from processing the file at all — including the command that would create the namespace. Workaround: `npx wrangler kv namespace create <NAME> --config /dev/null`, then patch the returned ID into `wrangler.toml` by hand.
- **`wsl sudo <cmd>` can hang indefinitely from PowerShell** waiting for an interactive password prompt that never appears. `wsl -u root <cmd>` runs as root directly and doesn't hang.
- **GitHub token *display* names are cosmetic.** A token labelled `RAMONE_TOKEN` in GitHub's UI is fine as long as its *value* is stored under the secret name the code actually reads (e.g. `GITHUB_TOKEN`). This caused real confusion twice in one day across two different repos.
- **The Windows→WSL NVIDIA bridge can drop independently of both the Windows driver and the telemetry code.** Windows-side `nvidia-smi` working while `wsl nvidia-smi` fails with "GPU access blocked by the operating system" means neither the app nor the driver is broken — the WSL2/NVIDIA bridge is. Recovery order: `wsl nvidia-smi` → `wsl --shutdown` and retry → reboot Windows if still failing. **Do not** install a Linux-native NVIDIA driver inside WSL; GPU support there comes from the Windows driver being projected in via `/usr/lib/wsl/lib/libnvidia-ml.so.1`.
- **PowerShell double-quoted strings silently corrupt secrets containing `$` or backticks.** *(new 2026-07-02)* Testing `ramone-trigger`'s `/trigger` endpoint from native PowerShell with `curl.exe -H "x-trigger-secret: $realSecret"` produced `{"error":"unauthorised"}` against a secret that had just been set correctly via `wrangler secret put` and copy-pasted identically. Root cause: PowerShell interpolates `$` and processes backtick escapes inside double-quoted strings *before* curl ever sees the value — a secret containing either character can differ between what was typed and what was actually sent, even on an exact copy-paste. Separately, once past auth, `curl.exe -d '{"repo":"..."}'`  also mangled the JSON body, because `curl.exe` is a native binary and Windows' argument parser only understands double quotes, forcing PowerShell to re-escape the embedded quotes when handing the argument over — a second, unrelated Windows-quoting failure mode stacked on the first. **Fix and standing rule:** all manual API testing involving secrets or JSON bodies from native PowerShell uses `Invoke-RestMethod` with a hashtable `-Headers` argument and `ConvertTo-Json` for the body, never `curl.exe` with inline double-quoted values. WSL bash does not have either issue — this is a native-PowerShell-only failure class.
- **Secrets must only ever be entered at an interactive prompt.** *(new 2026-07-02)* During the above debugging, a real `TRIGGER_SECRET` value was pasted into a chat context while trying to isolate the fault. Treated as compromised on sight and rotated immediately, not reused. **Standing rule:** secret values are only ever entered at `wrangler secret put`'s interactive prompt — never inline in a command, never in a chat client, never in a script file, never in shell history. If a secret is ever exposed outside that one place, rotate immediately regardless of whether it's "probably fine."

---

## Site Design

### Aesthetic

- **Decision:** Dark/terminal aesthetic
- **Why:** Matches the technical identity of Atlas Systems, signals intentionality to senior engineers.

### Brand specifics

- **Background:** `#0a0a0f` / `#111118`
- **Accent:** amber `#f5a623`
- **Text:** off-white `#e8e8e0`
- **Typefaces:** IBM Plex Mono (body) + DM Serif Display (display)
- **Logo:** node-network mark, sideways A-shape
- **Contact:** atlas@atlas-systems.uk

### Stack

- **Decision:** Static HTML/CSS/JS, hand-crafted
- **Why:** Plugs directly into Cloudflare Pages pipeline; hand-crafted signals fundamentals over framework dependency. React components can be added selectively later — none added so far, none needed.

### Case study voice rules

- **Decision:** Direct, senior-engineer prose. No em dashes, no "leveraged / utilised / robust / seamless." Outcomes section closes with a transferable insight, not an achievements list.
- **Detail:** Frontmatter is TOML with `+++` delimiters. `summary`, `w_number`, `slug` are never pre-filled (only Atlas knows them). `title`, `subtitle`, `tags` and most of `[work_card]` are decided by Claude during generation. `date_written`, `read_time`, `section_pills`, `project_number` are computed by the generator.

### Published case studies

- W-01: SONIN
- W-02: SlamPunk
- W-03: Ramone
- W-04: Overclocking (published)
- W-05: Pipeline Infrastructure (later this month)
- W-06: CI-CD
- **Correction from this audit, confirmed by Atlas 2026-07-02:** the previous version of this file had both "Overclocking" and "Pipeline Infrastructure" labelled `W-05`. Overclocking is actually `W-04` (already published); `W-05` belongs to Pipeline Infrastructure, scheduled later this month. Fixed here rather than left as a flag.

### Lab page

- **Decision:** The Lab page shows _historical_ signal the home page status dot cannot. Failure log panel reads from `atlas-notify`'s ring buffer (`KV NOTIFY_LOG`, key `notify:recent:v1`, last 200 events) via `GET /notify/recent`. Heatmap above it reads from a `/pulse/heatmap` endpoint.
- **Why:** The previous "System log" duplicated home-page liveness signal and the status page.
- **Extended 2026-07-02:** Lab gained two new panels this session. A **corpus search widget** calls `atlas-corpus`'s public `/search` endpoint (with a local-first fallback to `http://localhost:8092` when Lab is being previewed from `localhost`/`127.0.0.1`, falling through to the public tunnel, then a real error — never a silent failure). An **API registry panel** replaces the old hand-maintained endpoint list and now renders `atlas-api-index`'s live registry document. This required a follow-up fix (`atlas-systems` commit, same day): the API root's response shape changed from a flat `data.endpoints` array to a richer `data.workers[*].meta.endpoints` structure once `atlas-api-index` went live, and Lab's panel needed to normalise both shapes — otherwise a perfectly healthy backend rendered as "No endpoints reported." Banked as a general lesson: **when an API's response shape changes, check every consumer, even ones that look unrelated to the change you made.**
- **Open question, still deferred (see Pending):** whether pipeline events should flow _through_ atlas-notify into the Failure log, or stay direct. New Worker runtime alerts (trigger, telemetry, corpus) already flow through atlas-notify via service binding as of this session — see Discord routing — which is a step in that direction, but doesn't resolve the original CI/deploy-event question.

---

## Operating principles

### Full-file rewrites over partial edits

- **Decision:** When touching JSON, TOML, or YAML config files, replace the entire file rather than editing lines in place. Use heredocs (`cat > file <<'EOF' ... EOF`) so shell metacharacters in content don't get interpreted.
- **Why:** Partial edits race other partial edits. Full-file rewrites eliminate the merge conflict surface for config files.

### Verify locally before pushing

- **Decision:** Every commit that touches a gated file gets validated locally first. `node --check` for JS, `npm ci` for lockfile integrity, `npx html-validate` for HTML, `npx eslint .` for Worker source.
- **Why:** GitHub Actions is the _enforcement_ of the gate; local validation is the _fast feedback loop_.

### `git pull --rebase` before every push

- **Decision:** Standard practice across all repos. `git config --global pull.rebase true` sets it as default.
- **Why:** GitHub web UI edits race with local edits constantly.

### One command per state-changing step

- **Decision:** In complex git sequences, paste commands one at a time, not chained with `&&`. Read the output before running the next.
- **Why:** Chained blocks have repeatedly run the second command before the first finished registering, producing false-positive failures.

### Direct acknowledgement of mistakes

- **Decision:** When something breaks — including a script Claude wrote — name what broke and why, no deflecting. Banked lessons go into this file.
- **Why:** Pattern-matching against expected file contents is the failure mode; pulling and reading the real file is the working pattern.

### Ask "who is making the request?" *(new 2026-07-02)*

- **Decision:** Before writing any hostname into config, identify the caller's execution context explicitly, because the correct hostname is different for each one: a **browser on Windows** wants `localhost` or a public URL; a **container** wants `host.docker.internal` for host services; a **WSL-native service** wants `localhost` from inside WSL; a **Cloudflare Worker** wants a public URL or a service binding.
- **Why:** Today's build repeatedly produced confusion from `host.docker.internal` being correct in one context and wrong in an adjacent one. Naming the caller before naming the host resolves it in one step instead of trial-and-error.

### Trace the active path, not the visible option list *(new 2026-07-02)*

- **Decision:** When a system offers multiple valid-looking configured options (e.g. two Ollama integrations in Home Assistant), don't assume the intended one is active. Find the specific field that actually selects runtime behaviour (here, the Assist pipeline's `conversation_engine`) and verify that, not the presence of the option in a list.
- **Why:** Ramone had both the raw-Ollama and memory-proxy integrations configured correctly the whole time; the pipeline was simply still pointed at the old one. The bug wasn't a missing feature, it was an unverified assumption about which of several correct-looking things was actually wired in. This generalises well beyond Home Assistant — check route bindings, active feature flags, and selected entities the same way.

### Secrets live only at the interactive prompt *(new 2026-07-02)*

- **Decision:** Secret values are entered only via `wrangler secret put`'s interactive prompt (or the equivalent for other tools) — never inline in a command, never in a double-quoted PowerShell string, never pasted into a chat client, script file, or shell history.
- **Why:** A real `TRIGGER_SECRET` was pasted into a debugging conversation while trying to isolate a PowerShell quoting bug. It was rotated on sight rather than reused. The rule removes the judgment call of "is this probably fine" from the failure path entirely — any exposure outside the one sanctioned entry point triggers rotation, no exceptions considered.

---

## What Doesn't Exist Yet (known gaps)

- **`/_meta` contract adoption for 8 legacy Workers** *(new gap, 2026-07-02)* — `atlas-backend`, `atlas-notify`, `atlas-vault`, `deploy-watch`, `github-pulse`, `ramone-edge`, `simple-proxy`, `site-pulse` are all discovered live by `atlas-api-index` but don't yet return a valid `/_meta`. The helper and adoption guide already exist (`atlas-api-index/shared/_meta.js`, `examples/adding-meta-to-existing-worker.md`) — this is now pure retrofit work, not design work. Known specific causes so far: some 404 at `/_meta` outright, `atlas-notify` 405s because that path currently expects POST, `site-pulse` responds but not in the expected contract shape, `github-pulse` 502s through its service binding during probing.
- **Conversational "ask my infrastructure" interface** — partially delivered 2026-07-02: `specular-telemetry` (live hardware stats) and `atlas-corpus` (semantic search over estate docs) are both public via Cloudflare Tunnel and embedded in Lab. What's still open is a true chat-style interface over the corpus, rather than keyword/semantic search alone.
- Environment promotion (dev / staging branches) per Worker — pattern is built into the reusable workflow, not yet adopted per-repo
- Claude Code plugin `atlas-systems` with four skills: `atlas-ci-debug`, `atlas-worker-scaffold`, `atlas-case-study-writer`, `atlas-decisions-logger`
- Homelab secondary build (SPECULAR-NODE) using a Ryzen 9 9900X + RTX 3060 — always-on Ollama inference node + Jellyfin media server, a separate physical machine from SPECULAR-CORE, not yet assembled
- Ingesting real documents into `atlas-kit-python-rag` — note: `atlas-corpus` now performs a related role (ingestion + embedding + search) specifically over estate docs/repos, but `atlas-kit-python-rag` itself is untouched and currently carries uncommitted local changes that blocked bootstrap's fast-forward
- AWS integration — still not done, still not blocking anything
- Windows-native Node.js LTS install — `winget` install currently fails with exit code `1603`; non-blocking, WSL Node covers every current need
- Ollama model directory ownership is mixed across `ollama` / `atlas` / `root` — not blocking today, but the next failed `ollama pull` should prompt a deliberate ownership fix rather than another workaround
- **Ramone memory + voice-deploy regression, second occurrence, untriaged** *(new gap, 2026-07-02)* — after the TRIGGER_SECRET rotation and manual API test above, Ramone was reported "back to being weird with no memory and no deploy" in normal (voice/HA) use, despite the direct API test succeeding minutes earlier. A diagnostic pass was dispatched (checking Assist pipeline agent selection, ramone-memory container health, the known WSL-sleep container-restart failure mode, and whether HA's stored copy of TRIGGER_SECRET was updated to match the rotation) but the root cause and resolution are not yet confirmed as of this entry. Update this section once triaged — don't assume it's the same root cause as the first occurrence (Assist pipeline pointed at the wrong agent) without checking.

---

## Decisions Pending

- **Lab + atlas-notify pipeline events** — should CI/deploy events flow _through_ atlas-notify (populating the Lab Failure log organically, single event bus) or stay as direct `curl` posts from inside the reusable workflows? Still undecided. Note: new Worker *runtime* alerts (trigger, telemetry, corpus) already flow through atlas-notify via service binding as of 2026-07-02 — a partial, organic move in that direction — but that's a different event source (Worker runtime, not CI/deploy) and doesn't resolve the original question.
- **Knowledge Base framework** — Hugo / Docusaurus / hand-crafted? No movement since May; not blocking.
- **Logic Lego naming convention** — the repo count crossed 19 with today's build, past the "15+ repos" threshold set as the original revisit trigger. The pattern that's actually emerged: `<subsystem>-<noun>`, where subsystem is `ramone` / `specular` / `atlas` (`ramone-memory`, `ramone-voice-trigger`, `specular-telemetry`, `atlas-corpus`, `atlas-bootstrap`, `atlas-api-index`). New this session: repo name and deployed Worker name have started deliberately diverging for brevity (`ramone-voice-trigger` deploys as `ramone-trigger`; `specular-telemetry`'s Worker is `specular-edge`). Formalising "repo name" and "deployed service name" as two intentionally-different, documented fields is now due.
- **dev environments per Worker** — every Worker has its `[env.dev]` block sketched in `wrangler.toml`. Adoption is per-Worker, when staging is actually wanted for that one. Not a single estate-wide decision.
- **Free-tier-driven design choices, now revisitable** *(new 2026-07-02)* — with the Workers Plus upgrade, `specular-edge`'s 60-second cache window and `atlas-api-index`'s hourly-only cron frequency were both chosen partly for free-tier conservatism. Worth a deliberate pass to decide whether to tighten either now that headroom exists, rather than leaving them as-is by inertia.

---

## Update Log

## 2026-07 — atlas-cli reads the estate from the terminal, argparse over click

**Decision.** A pip/pipx-installable Python CLI, `atlas`, wraps the estate's
public read endpoints: `ask` (corpus search), `recent` (notify ring buffer),
`incidents` (blackbox), `status` (cross-service health with exit code 1 on
any DOWN). Built on argparse plus httpx plus rich, src layout, tests over
httpx's MockTransport with fixtures trimmed from live responses captured
2026-07-13.

**Why.** The estate's read surface existed but only through curl and the Lab
page. A CLI makes it ambient: `atlas status` in any terminal on any box, and
an exit code scripts can gate on. argparse over click or typer because four
subcommands is stdlib territory and a dependency-light tool reads end to
end; the parser is one file, so outgrowing that line costs a cheap swap. The
`ask` command reuses the estate's fallback convention verbatim: local corpus
first with a 1.5s budget, public second, both failures reported in one
error, never a silent empty result.

**Consequences.**
- The two originally open upstream shapes were confirmed during integration
  on 2026-07-13: blackbox detail returns `frames: [{ts, telemetry, events}]`,
  and corpus POST `/search` accepts `query` plus `top_k` and returns `hits`.
  Tests now pin both contracts.
- All field access goes through a `pick()` helper carrying plausible
  spellings, so an upstream rename costs a visible gap in output, not a
  traceback in four tools.
- The live notify endpoint reported total=200, returned=1 on 2026-07-13:
  the server appears to cap the default page. The CLI sends `?limit=` as a
  hint and slices client side; if the cap is hard, the fix belongs in
  atlas-notify, and the comment in `fetch_recent` is the breadcrumb.

## 2026-07 — atlas-postmortem drafts incidents with local Ollama, never publishes

**Decision.** A local tool on SPECULAR-CORE polls `/blackbox/incidents`
every 10 minutes, and for each newly sealed incident queries atlas-corpus
for history and prompts local Ollama (qwen2.5:32b via `/api/chat`) to draft
a five-section postmortem into `~/atlas-postmortems/<id>.md`, frontmatter
stamped `DRAFT - NEEDS HUMAN REVIEW`. State in
`~/.atlas-postmortem/processed.json`, written atomically, marked only after
the draft is safely on disk. Scheduled as `once` under a systemd --user
timer on WSL2 and a launchd agent on macOS. It has no publish path: no
commits, no pushes, no notifications.

**Why.** The blackbox seals a 14-frame flight-recorder window per incident,
and assembling a timeline from that is mechanical work a local model does
well; deciding what the incident meant is not, so the human/machine
boundary is physical, not procedural. Oneshot under a timer over a daemon
because a process that exits every run cannot leak for a week and its
failure state is a red unit with the reason in the journal. The prompt
sends telemetry as per-frame deltas (changed numeric keys only, capped)
because raw frames drown the trigger in unchanged numbers; the full window
stays in the blackbox. The Likely cause section is forced to open by
declaring itself a draft inference, and Relevant history may cite only the
numbered excerpts the tool actually retrieved, checked after generation by
a lint that fixes dashes mechanically and reports banned words in a
reviewer-notes block rather than rewriting meaning.

**Consequences.**
- Corpus down degrades to a draft with an explicit "history unavailable"
  note; Ollama down fails that incident loudly and retries next run;
  unsealed incidents wait; a corrupt state file is quarantined with a
  warning, and because drafts are never overwritten, the worst outcome of
  lost state is suffixed duplicate drafts, not lost edits.
- Requires user systemd on WSL2; the installer detects its absence and
  prints the `/etc/wsl.conf` fix instead of half-installing.
- The Mac agent needs its own pulled model; `ATLAS_PM_MODEL` exists for
  exactly that.

## 2026-07 — atlas-dora computes DORA metrics from the estate's own endpoints

**Decision.** A Worker, atlas-dora, computes deployment frequency, change
failure rate, and MTTR from `/notify/recent`, `/blackbox/incidents`, and
`/deploy-watch/latest`, cached in KV for 5 minutes with an `x-dora-cache:
HIT|MISS` header, serving `/dora/metrics`, `/dora/health` (self only), and
the estate `/_meta` contract. Pure downstream consumer: no secrets, no
writes beyond its own cache. A vanilla-JS panel with trend arrows drops
into the Lab page from a marked copy region.

**Why.** The estate already emits every event needed to measure its own
delivery performance; wiring a consumer over them turns the portfolio claim
"observable pipeline" into numbers on the Lab page. The honesty constraint
shaped every heuristic, because the data has no explicit deploy->incident
or incident->recovery links: CFR attributes a non-drill incident triggering
within 30 minutes after a successful deploy (correlation, stated in the
response), MTTR matches recovery by token overlap between trigger and later
success events and reports "n of m measured" with reasons for the rest, the
window is the ring buffer's real span rather than a round 30 days that
would undercount, drill incidents are excluded and counted, and zero
deploys yields a null rate, never a fake 0%. Upstreams are fetched with
individual 5s budgets under `Promise.allSettled`: partial estate, partial
metrics plus a `degraded` list; only a fully dark estate returns 503, and
errors are never cached.

**Consequences.**
- Deploy frequency depends on the notify title convention
  (`Deployed: <repo>`); renaming that convention silently changes the
  metric, so the detector and its test fixture are the canonical statement
  of it.
- CI is inline (ESLint, Vitest, wrangler dry run) with a marked swap point
  for the reusable `deploy-worker.yml` once the repo has proven itself.
- Writing a `dora_summary` event back into atlas-notify was considered and
  dropped: posting needs a secret, and this Worker's value is holding none.
  If wanted later, it belongs in a separate minimal producer.
- KV id and zone_id are deliberate placeholders filled at deploy time;
  route uses zone_id, never zone_name, per the banked lesson.

---

- 2026-05-28: Document created, Pillars 1 and 3 complete
- 2026-06-21: Major update reflecting six weeks of build-out — full CI/CD rollout, reusable workflows in atlas-infra as canonical source, hard-gate cutover on all three static sites, Discord routing across three channels, atlas-notify ring buffer + Lab Failure log, brand spec captured, case study voice rules captured, operating principles section added.
- 2026-07-02: **Logic Lego six-repo build shipped.** `ramone-memory` (cross-session memory proxy for Ramone), `specular-telemetry` (public live hardware telemetry), `ramone-voice-trigger` (voice-triggered GitHub Actions dispatch), `atlas-corpus` (public RAG search over estate docs, embedded in Lab), `atlas-bootstrap` (machine reconstruction/recovery, closes the long-standing portproxy-drift gap for good), `atlas-api-index` (self-documenting Worker registry at api.atlas-systems.uk/). New estate-wide contracts introduced: fixed `/_meta` shape, alert envelope over service bindings for Worker runtime notifications, conditional-KV-write-on-state-change generalised to caching. Fixed: Worker-to-Worker 522s (service bindings), corpus CSP block, doubled `/_meta` route bug, Lab API panel registry-shape mismatch, two health-check false-negatives in atlas-bootstrap. Voice deploy and memory routing both confirmed working end-to-end (Discord notification + Home Assistant, respectively) same day. Repo count crossed 19 — Logic Lego naming convention formalisation now due. Two new operating principles banked. Cloudflare account_id confirmed as `49e221b7e55a9e5c45b88d08efca5771` (corrects the value previously on record — see Key infrastructure constants). W-04/W-05 case study numbering corrected (Overclocking is W-04, published; Pipeline Infrastructure is W-05).
- 2026-07-02 (later same day): **Upgraded Cloudflare to Workers Plus** — first paid line item in the estate, KV/CPU/cron limits raised; several earlier free-tier-driven design choices flagged for a deliberate revisit rather than changed on the spot. **TRIGGER_SECRET rotated and reconfirmed working end-to-end** via direct API test after an initial "unauthorised" turned out to be a PowerShell double-quote string-interpolation bug corrupting the secret value in transit, not an actual credential mismatch — banked as a new problem class alongside a second, related Windows curl.exe JSON-body-quoting bug. A real secret value was briefly exposed in a debugging conversation and rotated immediately as a precaution; banked as a standing operating principle (secrets only at the interactive prompt, always rotate on any exposure, no exceptions). **New unresolved item:** Ramone reported losing memory and voice-deploy again shortly after the rotation, in normal use — a diagnostic pass has been dispatched but root cause is not yet confirmed; logged as an open gap rather than assumed-fixed.


# decisions.md entries, 2026-07-13

Four entries in the log's own format, ready to paste under the relevant
sections (first two probably under CI/CD or a new Tooling heading, the
last two under Website).

---

### atlas-badges: concept badges are evidence-first _(new 2026-07-13)_

- **Decision:** Built `atlas-badges`, a packaged Python CLI (`scan` / `apply`) that greps a local clone for signals of specific engineering concepts (HMAC verification, KV caching with TTL, service bindings, scoped tokens, and seven more) and writes a shields.io badge block into that repo's README between `ATLAS_CONCEPT_BADGES` markers, styled in the brand palette. Detection is evidence-first: `scan` prints file and line for every hit, and a per-repo `.atlas-concepts.yml` can force-include or force-exclude concepts.
- **Why:** Language pills tell a reviewer what a repo is written in, not what it proves. A senior engineer skimming the estate for ninety seconds should see claims that are checkable, which is why every detection carries its evidence and why the override file exists: static scanning has limits, and a tool that admits them is more trustworthy than one that asserts confidently and wrong. Exclude beats include on conflict for the same reason; when the record disagrees with itself, claim less.
- **Consequences:** READMEs now carry a generated block that has to stay honest. Re-running `apply` is byte-idempotent, so it can join CI later without noise commits. New concepts cost a detector plus tests against synthetic snippets, which is deliberate friction: no badge without a grounded signal. Two self-reference guards were needed in practice: the generated block and the override file itself are both excluded as evidence sources, or the tool bootstraps its own detections on the second run.

### Profile README regenerates itself _(new 2026-07-13)_

- **Decision:** `AtlasReaper311/AtlasReaper311` now carries `update-readme.yml` (cron every 6 hours at :17, plus `workflow_dispatch`) running a stdlib-only Python script that fetches `/pulse`, `/deploy-watch/latest`, and `writing/manifest.json`, then rewrites only the content between `ATLAS:LIVE` markers: a terminal block in the `atlas@SPECULAR-CORE:~$ status` dialect plus three shields badges. The job commits only when the rendered bytes change, using the default `GITHUB_TOKEN` with `contents: write`.
- **Why:** Everything else on the estate refreshes itself; the front door on GitHub was the one static page. Six hours because `/pulse` is KV-cached hourly upstream and profile stats move slowly, so anything faster buys commit noise, not information. Diff-before-commit is the deploy-watch rule applied to a README: only signal genuine change. No fetch timestamp is embedded anywhere, precisely so identical data renders to identical bytes and the diff check can work. Data failures degrade to honest "couldn't confirm" lines; missing markers fail the run loudly, because that is a config error a human must fix.
- **Consequences:** The profile repo spends a few free Actions minutes a day and its own commits keep the 60-day schedule-disable rule at bay. `GITHUB_TOKEN` pushes cannot trigger other workflows, so no loop is possible. The case-study line depends on `writing/manifest.json` existing in `atlas-systems` (shipped alongside, four published entries); until committed, the block degrades to a plain `/writing` pointer.

### 404 page with an idle clicker _(new 2026-07-13)_

- **Decision:** Added `404.html` at the `atlas-systems` repo root. Cloudflare Pages serves a root-level `404.html` as the custom not-found page (verified against current docs; without one, Pages assumes SPA mode). The page is the full site shell, self-contained CSS on purpose, with a shell-line echo of the actual missing path (set via `textContent` only) and an idle clicker: a glowing `$ deploy_worker` button, eight milestone lines in the Ramone voice, `localStorage` persistence, a reset control, `aria-live="polite"` announcements, and `prefers-reduced-motion` support.
- **Why:** A dead route was the one place on the estate showing default chrome, and a 404 is the cheapest possible page for tone: someone who lands there by accident should leave knowing a person built this. Self-contained styles because a 404 page that 404s its own stylesheet is the one failure mode the file must never have. `localStorage` is correct here, not a compromise: production static site, no backend by design, and the fleet should survive a return visit.
- **Consequences:** One static file, zero cost, no build step. The milestone copy shares a voice with the Lab Ramone easter eggs, so a future tone shift means editing two places. The page calls `AtlasSound` behind guards, so it works identically before and after the sound module ships.

### UI sound pass: synthesised, muted by default _(new 2026-07-13)_

- **Decision:** One shared module, `js/atlas-sound.js`, synthesising four cues with the Web Audio API at play time: a 12ms bandpassed noise tick for nav hover, a downward sine glide for clicks, a rising perfect fifth for status-good against a lowpassed tritone for status-bad, and a major-triad arpeggio with a noise-shimmer tail for easter-egg moments. No audio files. Default muted, with a persisted `[ sound: off ]` toggle mounted in the nav. `AtlasSound.status(state)` plays only on genuine state change, tracked in `sessionStorage`.
- **Why:** The estate is built by someone whose specialisation is audio systems and the interface was silent. Synthesis over assets means zero weight, zero licensing, and a demonstration of the actual skill rather than a shopping trip. Muted by default because unsolicited sound on a portfolio reads as a mistake; opt-in makes it a detail a visitor discovers. The toggle click is also the browser gesture that unlocks the `AudioContext`, so enabling sound and permitting it are the same act: designed with the autoplay policy, not against it. The status cue applies the deploy-watch rule to a speaker: polling is free, only transitions make sound.
- **Consequences:** One small script on any page that wants it, inert until wired (`mountToggle`, optional `autowire`, one `AtlasSound.status()` line wherever the nav dot is set). If `AudioContext` is unavailable the whole module degrades to silent no-ops, never a visitor-visible error. Cross-page navigation does not re-chime, because the last status lives in `sessionStorage`, not module memory.
