# Public interface programme Phase 12 coordination

Status: active after 12C Ramone product alignment.

Started: 2 August 2026.

## Purpose

Phase 12 aligns the supporting product surfaces after the main Atlas Systems
route work is complete. It covers Status, CV, Ramone, and the human-facing
Public API documentation shell while preserving each repository's runtime
authority and product-specific contract.

The API index remains JSON-only. It receives contract verification only; no
HTML shell, visual home page, global navigation, footer, search, or browser
identity work is in scope.

## Current source baseline

- `atlas-infra/main`: `79062e4ab41c056c4f7fbd15ab66a8313d0495e5`.
- `atlas-systems/main`: `0fd7a98aeaea523f18914c3c7f134fa96607406b`.
- Phase 11 final production deployment run: `30744843987`.
- No Phase 12 implementation, preview, merge, deployment, provider setting,
  binding, secret, publication, or runtime write existed at the start of this
  record.

## Product baselines

| Repository | Main SHA inspected | Local branch state | Open pull requests | Interface surface |
| --- | --- | --- | --- | --- |
| `status` | `1894baf27418dd8a2e073bac4b4a6c0bab7fb7de` | clean on `chore/update-static-workflow-pin` | `#26` Dependabot setup-python | `https://status.atlas-systems.uk/`, `index.html`, interface kit `v0.2.0` |
| `atlas-doc-viewer` | `74438662f7613040824a552a00fd889a63a8a062` | clean on `main` | `#27` Dependabot setup-python, `#28` Dependabot upload-artifact | `https://cv.atlas-systems.uk/`, `index.html`, interface kit `v0.2.0` |
| `ramone-edge` | `ed91c70a21b90c9c81f2d5eb2d98cd71bbe423d9` | clean on `main` | `#26` Dependabot setup-python, `#27` npm minor/patch | `https://ramone.atlas-systems.uk/`, `src/frontend-core.js`, interface kit generated into Worker source |
| `atlas-api-public` | `5b970a9bf3b66b5469ce883aacec4a4b496e72cc` | clean on `feat/codeql-scorecard-pilot` | `#53` public repository inventory, `#46`-`#49` Dependabot, draft `#5` Ramone tools | `https://api.atlas-systems.uk/v1/docs`, `src/routes/docs-shell.js`, generated docs interface |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | clean on `main` | `#16` npm minor/patch | JSON API index only; no `.atlas/public-interface.json` by design |

Local non-main branches in `status` and `atlas-api-public` are preserved. Phase
12 product work must branch from current `origin/main` or use an isolated
worktree before editing those repositories.

## Accepted authority

Phase 12 follows:

1. current repository files, branches, pull requests, commits, checks, and
   Actions runs;
2. accepted ADR-0007, ADR-0008, ADR-0009, and executable public-interface policy
   in `atlas-infra`;
3. each repository's interface manifest, README, deployment workflow, preview
   workflow, validation scripts, and tests;
4. live endpoints and generated evidence only when deployment state matters;
5. `AGENTS.md` as the stable operating map.

## Protected product contracts

### Status

Status retains repository-owned runtime verdicts, operational semantics,
canonical API-derived data sources, `slo.json`, and deploy ownership. Interface
work may correct shell, metadata, focus, responsive layout, footer, search,
status-link treatment, and presentation defects. It must not recompute
canonical reliability mathematics in the browser or replace source-of-truth API
responses.

### CV

CV retains About active state on desktop and mobile, `aria-current="page"` for
About, `noindex, follow`, explicit viewer initialization, desktop embed,
mobile native PDF handoff, close/focus return, local PDF ownership, and
independent deployment. Interface work may polish the surrounding shell,
metadata, route labelling, focus states, responsive spacing, and viewer
presentation without changing indexing or automatic load behaviour.

### Ramone

Ramone retains inference routing, private tunnel, Turnstile, rate limiting, SSE,
awake/asleep/offline decisions, grounding/source authority, `/ask`, `/status`,
bindings, secrets, provider settings, and runtime knowledge boundaries.
Interface work may cover navigation, metadata, layout, focus, composer and
evidence-card presentation, reduced motion, product identity, and status
explanation only when tests stay deterministic, offline, inference-free, and
binding-free.

### Public API documentation

The human documentation shell remains derived from repository-owned OpenAPI
authority. Interface work may cover the documentation shell, metadata,
navigation, status link, search, footer, focus, and responsive presentation. It
must not alter JSON API semantics, OpenAPI authority, health, metadata,
topology, trace, badge, reliability, evidence, CORS, cache, or fail-closed
behaviour.

### API index

The API index remains JSON-only and GET-only at the root. Phase 12 may verify
JSON contract, CORS, cache, and bounded error behaviour, but must not introduce
HTML, browser shell, visual metadata, search, footer, or global navigation.

## Branch programme

### 12A: CV document viewer alignment

Planned branch: `atlas-doc-viewer:fix/phase-12-cv-alignment`.

Start here because the repository is clean on `main`, has a small static
surface, and has clear protected behaviour. This branch should produce a
reviewable draft pull request with local validation and preview evidence before
merge.

### 12B: Status product alignment

Planned branch: `status:fix/phase-12-status-alignment`.

Begin after preserving the current non-main local branch. Scope must remain
presentation-only around repository-owned runtime data.

### 12C: Ramone product alignment

Planned branch: `ramone-edge:fix/phase-12-ramone-alignment`.

Begin only after CV and Status product evidence is reviewed so shared shell
expectations are settled before touching the Worker frontend.

### 12D: Public API docs alignment

Planned branch: `atlas-api-public:fix/phase-12-docs-alignment`.

Begin only after preserving the current non-main local branch and checking open
inventory PR overlap. Scope is the human documentation shell only.

### 12E: API index contract check

Planned branch: `atlas-api-index:test/phase-12-json-contract`.

This is verification-only unless current tests prove a JSON contract defect.
Visual work remains excluded.

## Implementation receipts

| Slice | Pull request | Source branch | Reviewed head | Merge commit | Production run | Live smoke |
| --- | --- | --- | --- | --- | --- | --- |
| 12A CV document viewer alignment | `atlas-doc-viewer#33` | `fix/phase-12-cv-alignment` | `bd048d29a80dfdf4d58ca4f5672f0afdc104b94f` | `2b03d5843588f0415ecc735f6b33ca7527063137` | `30746009334` | pass |
| 12B Status product alignment | `status#35` | `fix/phase-12-status-alignment` | `95a8b54ceffb4652536c69b40028418e610c7d89` | `4db1438b1a8859008461903105360a2f09376c02` | `30746440035` | pass |
| 12C Ramone product alignment | `ramone-edge#32` | `fix/phase-12-ramone-alignment` | `81756e4d8d545542dc520cf2a19e6b08ec51acf6` | `3830dd3839847187e0b5ac6c837a5658f5f47341` | `30746842107` | pass |

12A tightened the mobile product strip and footer presentation while preserving
the protected PDF bytes, explicit initialize action, desktop embed, mobile
native handoff, close/focus return, `noindex, follow`, About active state,
metadata, security headers, and independent Pages deployment.

The exact-head pull-request preview run `30745903897` published the isolated
document preview and passed the repository browser evidence capture. Production
run `30746009334` then passed HTML and link validation, Cloudflare Pages deploy,
edge cache purge, and Discord reporting for merge commit
`2b03d5843588f0415ecc735f6b33ca7527063137`.

A live custom-domain smoke on `https://cv.atlas-systems.uk/` at a 390 pixel
mobile viewport confirmed title `CV // Atlas Systems`, H1 `Atlas Reaper.`,
document state `Ready`, no horizontal overflow, mobile bottom navigation
visible, compact footer height, `noindex, follow`, and active About navigation.

12B tightened the Status mobile footer presentation while preserving
repository-owned runtime data, reliability semantics, canonical API sources,
`slo.json`, metadata, security headers, and independent Pages deployment. The
local branch was created from current `origin/main` while preserving the
pre-existing non-main local branch `chore/update-static-workflow-pin`.

The exact-head pull-request preview run `30746329149` passed Status preview
candidate validation, non-production preview publication, and deterministic
Status browser evidence. Pull-request CI, public-interface conformance, CodeQL,
OpenSSF Scorecard, and the Gardener barrier also passed for reviewed head
`95a8b54ceffb4652536c69b40028418e610c7d89`. Production run `30746440035` then
passed HTML and link validation, Cloudflare Pages deploy, edge cache purge, and
Discord reporting for merge commit
`4db1438b1a8859008461903105360a2f09376c02`.

A live custom-domain smoke on `https://status.atlas-systems.uk/` at a 390 pixel
mobile viewport confirmed title `Status // Atlas Systems`, no horizontal
overflow, mobile bottom navigation visible, compact footer height, canonical
`https://status.atlas-systems.uk/`, and the deployed CSS rule
`flex: 0 0 auto`. The live aggregate status label was `degraded`; that was
runtime evidence, not a changed verdict.

12C tightened the Ramone product footer on mobile and mirrored the same compact
behaviour on the browser-route 404 footer while preserving inference routing,
private tunnel boundaries, Turnstile, rate limiting, SSE, `/ask`, `/status`,
bindings, secrets, provider settings, grounding authority, and runtime knowledge
boundaries. No acceptance check sent an inference question.

The exact-head pull-request preview run `30746718047` passed Ramone interface
candidate validation, isolated preview publication, product-specific Chrome and
Firefox evidence, comparable cross-product evidence, and artifact upload. The
earlier preview run `30746713668` was cancelled after the preview-approval label
started the replacement run, and is not treated as a code failure. Pull-request
CI, public-interface conformance, CodeQL, and OpenSSF Scorecard passed for
reviewed head `81756e4d8d545542dc520cf2a19e6b08ec51acf6`. Production deploy run
`30746842107` deployed merge commit
`3830dd3839847187e0b5ac6c837a5658f5f47341` and persisted the deploy event to
Lab.

A live custom-domain smoke on `https://ramone.atlas-systems.uk/` confirmed
`GET /` returned `200`, title `Ramone // Atlas Systems`, no horizontal overflow
at 390 and 1440 pixel browser widths, compact 390 pixel mobile footer, compact
desktop footer, mobile bottom navigation visible, and live CSS containing the
mobile `flex: 0 0 auto` footer rules. A browser-route smoke with
`Accept: text/html` confirmed the live 404 page title
`404 // Ramone // Atlas Systems`, the public-boundary heading, and the compact
404 footer rule. Live browser console noise was limited to the intentional 404
request and Cloudflare analytics beacon being blocked by the existing CSP.

## Validation and evidence contract

Every product branch must run repository-native validation after inspecting the
current scripts and workflows. Where available, this includes:

- HTML validation or repository-specific shell validation;
- interface-bundle or generated-interface verification;
- public-interface conformance checks;
- route, metadata, browser identity, footer, security text, and protected
  runtime-contract tests;
- deterministic browser evidence in Chromium and Firefox across repository-owned
  preview widths;
- `git diff --check`.

Preview publication is non-production. Merge and production deployment remain
separate evidence gates. A merged commit does not prove deployment.

## Security and privacy boundary

Phase 12 must not:

- request, expose, persist, or print secrets;
- alter Cloudflare bindings, provider settings, routes, schedules, or deployment
  configuration;
- dispatch mutation endpoints;
- send Ramone inference questions from acceptance tests;
- expose internal routes or provider data;
- change article generation, scheduling, publication timing, or published
  output;
- change API index from JSON-only behaviour;
- infer live state from merged source.

## Approval boundary

This coordination branch may merge after documentation validation. Product work
then proceeds one repository at a time. Each product branch must report current
state, inspected evidence, changed paths, validation, browser evidence, security
review, risk, rollback, and the next approval gate before merge or production
verification.
