# Atlas Systems public interface programme

Status: active at Approval Gate 0.

Started: 28 July 2026.

## Mission

Complete an evidence-backed interface and experience programme across the public Atlas Systems browser estate through focused, validated draft pull requests.

This programme is not a redesign. It preserves the established Atlas Systems identity, route-specific product character, AtlasField hierarchy, operational truth boundaries, publication ownership, and independent deployment contracts.

## Authority order

Use this order when programme evidence conflicts:

1. Current GitHub files, branches, pull requests, commits, Actions runs, and repository settings.
2. Accepted ADRs under `atlas-infra/docs/adrs/`.
3. Authoritative policy inputs under `atlas-infra/policy/`.
4. Generated public repository classifications.
5. `atlas-api-public/data/estate.manifest.json` for topology and presentation only.
6. Live endpoints and generated reports when deployment state matters.
7. `AGENT.md` as the stable operating map.
8. Historical material and memory.

A merged pull request does not prove deployment. A generated article does not prove publication.

## Visual authority

The visual authority remains the Atlas Systems Brand Reference:

- dark backgrounds and nested dark surfaces;
- restrained amber emphasis;
- DM Serif Display for editorial and display headings;
- IBM Plex Mono for interface and operational copy;
- precise spacing;
- a hand-built terminal character;
- route-specific identity instead of one universal template.

## Current rebaseline

The following snapshot was recorded from current GitHub state on 28 July 2026. Every phase must refresh its own repository before editing.

| Repository | Main SHA | Relevant current state | Deployment and preview boundary | Interface kit | Generated or protected paths |
| --- | --- | --- | --- | --- | --- |
| `atlas-infra` | `6c3cb66b1c1c7af0d887811991c6ca8a4d65371e` | ADR-0008 and Public Interface System v2 are accepted and migration state is complete. Draft PR #79 touches only chaos assurance documentation. | No product deployment. `public-interface-contract.yml` validates authority. `estate-policy.yml` is scheduled or manually dispatched and must not be dispatched by this programme without approval. | Governance owner, not a consumer. | Generated public classifications and reports are not hand-edited. |
| `atlas-systems` | `c678ad4767cc195f202553336e587aca31f7d4b1` | PR #158 remains open on `feat/system-symphony-trace-board`. PRs #119 and #125 remain excluded. Main now includes PRs #160, #161, and #162. | `deploy.yml` deploys from `main`, verifies the exact commit, performs production browser smoke, and then refreshes the corpus. `interface-preview.yml` publishes labelled PR previews and captures browser evidence. | `0.2.0`, repository-local and fingerprinted. | Generated sitemap, vendored interface bundle, scheduler-owned article output, AtlasField assets, and System Symphony audio and renderer contracts require separate ownership review. |
| `atlas-interface-kit` | `a23479e5a2ea7ea4f7a5c04bf9c474a7cdbec684` | Version `0.2.0`, contract `2.0.0`, 25 component roles. | CI validates deterministic output. A release is a separate approved action and does not deploy a consumer. | Authority implementation owner. | `dist/` is generated from source and must remain deterministic. Font licences and fingerprints are protected. |
| `atlas-api-public` | `b2f445af65fa727b9753a7f67c35271a3f1f7cef` | Human docs exist at `/v1/docs`; open dependency PRs #46 through #49 and older draft PR #5 are outside interface implementation scope unless they overlap. | Worker deploy remains separate. `interface-preview.yml` creates an isolated `workers.dev` preview with no production routes, service bindings, KV, rate limits, or schedules. | `0.2.0`, repository-local and fingerprinted. | `data/estate.manifest.json` is presentation topology. Generated repository classifications, topology evidence, and embedded docs interface output are not hand-edited. |
| `atlas-api-index` | `074efaf21e84154ef1023984b02d1a29c2e989ca` | JSON-only fail-closed registry. Open dependency PRs #15 and #16 do not change the product decision. | Worker deploy remains repository-owned. No browser application preview is required for the JSON root. | Intentionally not applicable. | Public allowlist and registry output remain contract-owned. No HTML shell is permitted. |
| `status` | `eb759fc899378e2f07b27a1204083e5e1b2b2dd9` | Existing interface evidence already covers Chrome and Firefox from 320 to 1440 pixels. No overlapping interface PR was found. | Pages deploy remains repository-owned. Interface PRs use the existing preview and deterministic evidence workflow. | `0.2.0`, repository-local and fingerprinted. | `slo.json` is generated from reliability policy. Status-owned operational components and canonical API-derived verdicts remain local. |
| `atlas-doc-viewer` | `c109ed403fd12cc20a3309a07de4c9b1ef0fd299` | Explicit initialise, desktop embed, mobile native handoff, focus return, and `noindex, follow` remain protected. No overlapping interface PR was found. | Independent Pages deployment and interface preview remain repository-owned. | `0.2.0`, repository-local and fingerprinted. | Local PDF bytes and viewer behaviour are protected. Vendored bundle files are generated copies. |
| `ramone-edge` | `c0c8028e06e21e71f1fef6f950d46d49f673dba2` | Browser product is in scope. Inference routing, private tunnel, Turnstile, rate limiting, SSE, wake-state decisions, grounding, bindings, secrets, and `/ask` and `/status` contracts are excluded. | Worker deployment remains separate. Existing preview is isolated, binding-free, inference-free, deterministic, and offline by design. | `0.2.0`, repository-local, fingerprinted, and embedded. | Generated interface module is derived. Runtime bindings, secrets, and inference contracts are protected. |
| `atlas-article-gen` | `ec03263172dfb829b92ba2b8525b55f24f5a7adb` | Generator owns article templates, parser, markup, and generated draft folders. | `build-articles.yml` validates on pull requests, builds on `main`, and may sync finished folders to the scheduler. It never writes to the live site. | Article template adoption is a later programme phase. | `drafts/scheduled/` is generated from canonical Markdown. `build_article.py` is parser authority. Generated HTML and metadata are not hand-edited. |
| `atlas-scheduler` | `596967f57d2ca68021f5da41073efdee7b8bd8c0` | Scheduler owns the queue, dates, previous and next links, coming-soon rotation, optional Work insertion, refresh receipts, and the only write path to `atlas-systems`. | `publish.yml` runs at 09:00 UTC and supports bounded manual modes. Production execution requires separate approval. | Article output may consume accepted foundations only through the owned pipeline. | Scheduled queue, sequencing, publication output, refresh requests, and receipts remain scheduler-owned. |

GitHub does not expose another operator's local worktree state. This programme records exact remote main commits and overlapping pull requests. Every implementation phase must still inspect the executing checkout for branch and dirty-state evidence before editing.

## Locked decisions

### System Symphony

- PR #158 is the surviving visual direction.
- PRs #119 and #125 remain outside this programme. Do not close, modify, rebase, merge, or mine them for ideas.
- PR #158 must rebase onto current `main` and preserve all current System Symphony behaviour. Current `main` includes PR #160 transition, health-vector, wording, and audio changes, plus later PR #162 production loudness evidence.
- Resolve cache identity inside PR #158 so old CSS cannot combine with the new renderer.

### API index

- `https://api.atlas-systems.uk/` remains JSON-only.
- No HTML homepage, footer, navigation, browser shell, or visual metadata is permitted.
- Preserve `application/json`, GET-only root behaviour, bounded errors, CORS, caching, and fail-closed publication.

### Ramone

Interface scope includes navigation, metadata, layout, focus, composer presentation, evidence-card presentation, status explanation, reduced motion, and product identity.

The following remain owned by `ramone-edge` runtime contracts and are excluded from interface-foundation work:

- inference routing;
- the private tunnel;
- Turnstile verification;
- rate limiting;
- SSE transport;
- awake, asleep, and offline decisions;
- grounding and source authority;
- `/ask` and `/status` response contracts;
- bindings, secrets, and provider settings.

The isolated preview remains deterministic, offline, inference-free, and binding-free.

### Footer ownership

`atlas-interface-kit` owns footer structure, selectors, tokens, spacing, responsive behaviour, focus behaviour, and accessibility behaviour.

Consumer repositories own product copy, product identity, route escape choices, related routes, operational links, and generated article sequencing.

### CV navigation and viewer

Preserve:

- About active on desktop and mobile;
- `aria-current="page"` on About;
- `noindex, follow`;
- explicit viewer initialisation;
- desktop embed;
- mobile native handoff;
- close and focus return;
- local PDF;
- independent deployment.

### Performance gates

- Static baseline drift remains blocking.
- Browser performance evidence remains reporting-only for one complete evidence cycle.
- Browser budgets become blocking only after route and device measurements are reviewed and accepted.
- Do not invent budgets before evidence exists.

## Existing authority coverage

ADR-0008 and `policy/public-interface-system-v2.json` already govern most proposed shared foundations.

| Proposed primitive | Current authority | Programme treatment |
| --- | --- | --- |
| Global navigation and mobile active route | Covered | Preserve and test. Extend only from measured evidence. |
| Page introduction and hierarchy | Covered | Adopt in source where current pages drift. |
| Shared spacing scale | Covered and non-overridable | Do not redefine locally. |
| Primary, secondary, and text actions | Covered | Implement through the kit and consumer adoption. |
| Focus visibility and touch targets | Covered and non-overridable | Accessibility correction may fix source, not weaken tokens. |
| Base responsive breakpoints | Covered and non-overridable | Use current authority unless measured evidence requires an accepted amendment. |
| Reduced motion | Covered and non-overridable | Preserve meaningful static states. |
| Loading, empty, unavailable, unknown, and error states | Covered | Extend vocabulary only when measured gaps are real. |
| Table wrapper | Covered | Measure whether dense-data continuation, labelled local overflow, and keyboard scrolling need stronger authority. |
| Search dialog | Covered | Correct source semantics and interaction defects without moving product-specific search logic. |
| Footer role | Covered at a high level | Phase 6 may add slot and variant authority if measured evidence proves the existing role is insufficient. |
| Breadcrumbs | Not explicit | Candidate Phase 4 authority extension after measured evidence. |
| Live-region and status announcement strategy | Not explicit enough for the proposed programme | Candidate Phase 4 authority extension after measured evidence. |
| 1920 pixel evidence | Not in the current v2 matrix | Add first as evidence coverage, not as a visual token or budget. |

No new ADR is required at Gate 0. Any lasting architecture change discovered after measured evidence should amend accepted authority or create a focused ADR only when the decision cannot be represented by the current contract.

## Route inventory

The implementation inventory must be regenerated from repository truth at the start of Phase 2. The current minimum scope is:

### Main site

- `/`
- `/systems/`
- `/work/`
- `/writing/`
- `/lab/`
- `/about/`

### Systems

- `/systems/reliability/`
- `/systems/observability/`
- `/systems/evidence/`
- every other public Systems child route found in source or the generated sitemap

### Lab

- `/lab/system-map/`
- `/lab/system-symphony/`
- `/lab/signal/`
- `/lab/anomaly/`
- `/lab/proof-chain/`
- `/lab/conformance/`
- `/lab/reliability/`
- `/lab/almost/`
- `/lab/console/`
- `/lab/speculum/`
- every other current public Lab route

### Editorial and Work

- Writing directory, pagination, filters, and search states;
- representative articles covering prose, code, tables, figures, long headings, and footer chaining;
- Work directory, filters, gallery, lightbox, audio controls, and Work-to-Writing links.

### Supporting products

- `https://status.atlas-systems.uk/`
- `https://cv.atlas-systems.uk/`
- `https://ramone.atlas-systems.uk/`
- `https://api.atlas-systems.uk/`
- `https://api.atlas-systems.uk/v1`
- `https://api.atlas-systems.uk/v1/docs`

The API index root receives contract evidence, not visual assertions.

## Repository ownership

| Capability | Owner |
| --- | --- |
| Shared interface policy, schemas, validators, accepted versions, adoption rules, and rollback rules | `atlas-infra` |
| Shared token and component implementation, generated bundle, manifest, documentation, tests, and release artefact | `atlas-interface-kit` |
| Main portfolio, Systems, Work, Writing directory, Lab, AtlasField consumers, and System Symphony browser experience | `atlas-systems` |
| Human API documentation and public API projection | `atlas-api-public` |
| JSON-only public Worker registry | `atlas-api-index` |
| Operational status product and visitor-side checks | `status` |
| CV document gate and viewer | `atlas-doc-viewer` |
| Ramone browser product and edge runtime | `ramone-edge` |
| Article source templates, parser, and generated article markup | `atlas-article-gen` |
| Publication timing, sequencing, Work insertion, and only live-site write path | `atlas-scheduler` |

## Programme dependency graph

```text
Phase 0  programme control and rebaseline
  -> Phase 1  System Symphony PR #158
  -> Phase 2  atlas-systems browser evidence harness
  -> Phase 3  cross-product baseline evidence
  -> Phase 4  authority extension and interface-kit release
  -> Phase 5  atlas-systems shared foundation adoption
  -> Phase 6  footer authority, primitive, and consumers
  -> Phase 7  metadata and browser identity
  -> Phase 8  accessibility and responsive correction
  -> Phase 9  Systems detail surfaces
  -> Phase 10 Writing and article reading pipeline
  -> Phase 11 Lab interaction polish
  -> Phase 12 supporting products
  -> Phase 13 AtlasField composition catalogue
  -> Phase 14 accepted browser performance gates
  -> Phase 15 controlled rollout and closeout
```

Phases 6 through 12 may use independent consumer pull requests only after their shared dependency is merged and released. Two branches must not edit overlapping files in the same repository at the same time.

## Phase register and approval gates

| Phase | Primary outcome | Main branch or branches | Approval boundary |
| --- | --- | --- | --- |
| 0 | Durable programme record and current-state rebaseline | `atlas-infra:docs/public-interface-programme` | Documentation-only draft PR. No source implementation. |
| 1 | Rebase, validate, and evidence System Symphony PR #158 | Existing `atlas-systems:feat/system-symphony-trace-board` | Gate 1A before merge, Gate 1B after separately approved live verification. |
| 2 | Complete atlas-systems browser evidence harness and corrected static baseline | `test/browser-evidence-harness`, optional `perf/static-baseline-v2` | No production UI change. Stop after evidence artefact review. |
| 3 | Comparable baseline evidence for Status, CV, Ramone, and API index contracts | Repository-local `test/interface-evidence-contract` and `test/browser-registry-contract` | Stop with measured P0 and P1 backlog. |
| 4 | Measured authority extension, kit implementation, then immutable release | `policy/interface-foundation-extension`, `feat/interface-foundation-extension` | Separate authority, implementation, merge, and release approvals. |
| 5 | Main-site adoption of accepted foundations | `refactor/shared-interface-foundations` | Stop at exact-head draft PR and preview, then separate rollout gate. |
| 6 | Footer authority, primitive, generator and scheduler ownership, and independent consumers | Repository-specific branches under `policy/`, `feat/`, or adoption scope | One draft PR per repository. Release before consumers. |
| 7 | Metadata, browser icons, canonical URLs, previews, and error identity | `fix/browser-identity-contract` in each repository | One draft PR per repository. |
| 8 | Measured accessibility and responsive corrections | Repository-specific `fix/accessibility-*` branches | Stop after each repository draft PR and browser evidence. |
| 9 | Reliability, Observability, and Evidence analytical surfaces | `refactor/systems-detail-surfaces` or two focused branches | One or two draft PRs depending on reviewability. |
| 10 | Article reading contract, scheduler sequencing, and Writing directory | `feat/article-reading-contract`, `feat/editorial-navigation-sequencing`, `refactor/writing-directory` | Separate generator, scheduler, directory, and production publication approvals. |
| 11 | Lab wayfinding, evidence tools, and instruments | Four focused `refactor/` or `fix/` branches | Stop after each draft PR. Symphony follow-up only for measured defects. |
| 12 | Product-specific Status, CV, and Ramone alignment | One product branch per repository | One draft PR per product. API index visual work remains excluded. |
| 13 | Normative AtlasField composition catalogue and validation | `docs/atlasfield-composition-catalogue` | Documentation and validation only. No new public route. |
| 14 | Promote reviewed browser measurements into selected blocking budgets | `perf/browser-budget-gates` | Stop with proposed metrics, values, tolerances, and exclusions. |
| 15 | Freeze, dependency-ordered merge, deployment verification, and closeout | Existing reviewed heads plus final documentation branch | Explicit approval before every production merge or publication action. |

## Operating rules

### One phase at a time

At the end of each phase, report current repository state, exact changed paths, validation, preview or browser evidence, security and privacy review, risks, rollback, dependencies, and the exact approval boundary. Stop before the next phase.

### Repository inspection

Before changing a repository:

1. fetch current `origin/main`;
2. inspect branch and worktree status;
3. inspect open pull requests touching the same paths;
4. inspect repository-native validation;
5. inspect deployment workflows;
6. inspect preview workflows;
7. inspect generated and protected files;
8. inspect the current interface-kit version and manifest;
9. inspect governing ADRs and policy.

Do not reuse test commands from another repository without inspection.

### Branch discipline

Before opening a pull request:

1. validate locally;
2. fetch current `origin/main`;
3. rebase onto current `origin/main`;
4. rerun validation;
5. run `git diff --check`;
6. inspect every changed path;
7. push the actual branch;
8. open a draft pull request;
9. observe checks.

### Change boundaries

Do not:

- request or expose secrets;
- alter Cloudflare bindings or provider settings;
- dispatch workflows without explicit approval;
- create production previews manually;
- merge a pull request;
- publish an interface-kit release;
- deploy a Worker or Pages site;
- change article publication timing;
- run the scheduler against production;
- change Ramone inference behaviour;
- hand-edit generated article HTML or metadata.

Existing pull-request-triggered previews may run under their reviewed repository contract. A new provider-writing workflow requires approval before activation.

### Merge and deployment boundary

Treat merge approval as production authorisation whenever `main` deploys. After merge, prove the exact merge commit, deployment run, deployed commit identity when available, live route, metadata, browser evidence, and rollback path.

### Interface-kit distribution

Consumers copy one pinned immutable release into their own repository and verify every fingerprint. No consumer loads shared CSS, JavaScript, or fonts from another Atlas Systems repository at runtime.

### Evidence rules

- Use deterministic fixtures for pull-request acceptance.
- Label fixture, replay, stale, and simulated data.
- Do not call mutation endpoints.
- Do not send inference questions from interface acceptance tests.
- Do not use secrets in browser evidence.
- Do not expose internal routes or provider data.
- Static drift remains blocking.
- Browser measurements remain reporting-only until reviewed and accepted.

## Expected evidence artefacts

The programme will produce, as applicable:

- exact main, branch, head, merge, and deployed commit identities;
- pull-request dependency and changed-path records;
- deterministic Chromium and Firefox screenshots at required widths;
- 1920 pixel evidence where added by this programme;
- titles, canonical URLs, metadata, landmarks, headings, active route, tab-order, focus, keyboard, overflow, console, page-error, failed-request, request-count, byte, CSS, JavaScript, and reduced-motion evidence;
- accessibility reports with serious and critical findings blocking;
- static performance baselines and later accepted browser budgets;
- interface-kit release identifier, manifest, and fingerprints;
- production deployment run identifiers and live smoke reports;
- generator fixture output, scheduler dry-run output, publication run, and live article verification;
- AtlasField catalogue fingerprint;
- final merged pull request, rollback, and intentional-difference register.

## Current risks

1. PR #158 is behind current `atlas-systems/main`. Its stated validation count and cache question are stale until the branch is deliberately rebased and revalidated.
2. Current `atlas-systems/main` contains Symphony production evidence added after the plan snapshot. Phase 1 must preserve it.
3. The current shared evidence authority stops at 1440 pixels. Adding 1920 pixel evidence is coverage expansion, not permission to change visual tokens.
4. The existing kit has a general footer role but not the proposed complete slot and variant contract. Phase 6 depends on measured evidence and accepted authority.
5. Breadcrumb and live-region rules are not explicit enough for the proposed programme. Phase 4 may need a bounded authority amendment.
6. Work Allocation existed in supplied project context but not in current `atlas-infra` GitHub source. Phase 0 materialises a repository-local coordination copy without granting it policy authority.
7. The user-supplied route list can become stale. Phase 2 must derive the actual matrix from repository truth and sitemap output.
8. A merge into several consumer repositories can deploy production. Source approval and rollout approval must remain separate.
9. Article appearance changes cross generator, scheduler, and live-site ownership. Hand-editing generated output would violate the publication contract.
10. Browser evidence frameworks already exist in several repositories. The programme must extend them rather than create competing stacks.

## Excluded work

- PRs #119 and #125;
- API index visualisation or HTML shell;
- new AtlasField compositions before the catalogue and a real product need;
- Ramone inference, grounding, tunnel, rate-limit, Turnstile, SSE, bindings, secrets, and runtime-decision changes;
- Status-side recomputation of canonical reliability mathematics;
- CV indexing, automatic PDF load, or replacement of the native mobile handoff;
- article prose rewrites during interface migration;
- direct edits to generated article HTML or metadata;
- scheduler production execution without explicit publication approval;
- provider writes, releases, deployments, merges, and workflow dispatches not explicitly approved at the relevant gate;
- unrelated repositories.

## Phase report contract

Every phase report uses these sections:

1. Current state.
2. Evidence inspected.
3. Changes.
4. Validation.
5. Browser evidence.
6. Security and privacy review.
7. Risks.
8. Approval boundary.

The report names exact repositories, SHAs, branches, open pull requests, worktree state, changed paths, commands, test counts, warnings, failures, preview URLs, browsers, widths, accessibility results, overflow results, console and page errors, performance evidence, endpoints called, mutation proof, secret handling, rollback, unresolved decisions, and dependencies.

## Completion definition

The programme is complete only after:

- PR #158 is the verified live System Symphony baseline;
- every in-scope browser surface has repeatable evidence;
- shared foundations are authority-backed and distributed through an immutable kit release;
- every consumer pins and verifies a local bundle;
- navigation and active-route treatment are consistent;
- footer structure is shared while product content remains local;
- metadata and browser identity are complete;
- accepted P0 and P1 accessibility defects are resolved;
- required widths and dense-data access pass;
- Work lightbox and search interactions pass keyboard review;
- Writing changes originate in generator and scheduler ownership;
- Lab tools retain individual identity;
- Status retains operational authority;
- CV retains About active and protected PDF behaviour;
- Ramone retains runtime and knowledge boundaries;
- API index remains JSON-only;
- AtlasField placements are catalogued and bounded;
- static drift blocks and accepted browser budgets block;
- every production deployment is verified from Actions and live routes;
- remaining differences are documented as intentional.

## Approval Gate 0

Phase 0 authorises only this documentation record and the active Work Allocation entry.

Not authorised:

- Phase 1 source changes;
- rebasing or modifying PR #158;
- modifying PRs #119 or #125;
- workflow dispatch;
- preview creation outside existing pull-request automation;
- merge;
- release;
- deployment;
- provider settings or secret changes;
- scheduler production execution;
- article publication.
