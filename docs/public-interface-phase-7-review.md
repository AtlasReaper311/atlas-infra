# Public interface programme Phase 7 review

Status: Phase 7 source preparation complete at exact-head draft pull-request review.

Recorded: 30 July 2026.

Phase 7 implements the accepted metadata and browser-identity authority across the public Atlas Systems browser estate. It does not redesign product interfaces or change machine-facing contracts.

This review stops before every consumer merge, preview provider write, deployment, scheduler execution, article regeneration or sync, publication, provider setting, and secret change.

## Current state

Phase 6 is closed and reconciled. Phase 7 has produced six independent draft pull requests and one measured no-change result:

| Repository | Pull request | Exact head | Outcome |
| --- | ---: | --- | --- |
| `atlas-article-gen` | #39 | `32dcd47a712406b6f82e79f3984546116e9729d2` | Complete generated article browser identity and correct the lifecycle of completed published-refresh export receipts. |
| `atlas-systems` | #178 | `7bac8f67b97b4e1c9d58d1d012bb8f8338111059` | Enforce exact route identity, complete eight Lab icon packages, record two canonical aliases, preserve one Phase 11 console exception, and update the deterministic static baseline. |
| `status` | #32 | `f19bbe3046d3f0a95f6bf813cfebbf855aeb6ea4` | Add an owned noindex Status 404 while preserving live service and reliability ownership. |
| `atlas-doc-viewer` | #31 | `34fead329ae73f9e7f1900cb786822e3438e16e9` | Add an owned noindex CV 404 without loading or exposing the protected document. |
| `ramone-edge` | #30 | `665eb8e4f29af5084a9ac5e5642380d7ba025c8f` | Add negotiated browser HTML errors while preserving JSON API fallbacks and all inference boundaries. |
| `atlas-api-public` | #52 | `2270141b36feb96a50b3858b2f89c6e0e73e56d5` | Add negotiated errors only below the human `/v1/docs` surface while preserving machine API behavior. |
| `atlas-api-index` | no change | `96cd81f643429895847a1c2f143084d6e995005c` | Existing JSON-only contract and evidence already satisfy Phase 7. |

`atlas-interface-kit v0.4.0` remains immutable. No Phase 7 kit source or release is required.

`atlas-scheduler` requires no Phase 7 source change. Generator output may later be synchronized through the existing generator-owned workflow, but publication timing, queue state, sequencing, receipts, and the only production write path into `atlas-systems` remain scheduler-owned.

All six implementation pull requests remain open and draft. None has been merged.

## Evidence inspected

### Authority

- `docs/adrs/ADR-0007-public-interface-contract.md`;
- `docs/adrs/ADR-0008-public-interface-system-v2.md`;
- `docs/adrs/ADR-0009-classic-writing-footer-exception.md`;
- `docs/public-interface-contract.md`;
- `policy/public-interface-contract.json`;
- `policy/public-interface-system-v2.json`;
- `policy/browser-icons-v1.json`;
- current programme and Phase 6 closeout records.

### Repository state

For each affected repository, the inspection covered:

- current `main` commit;
- open pull requests and changed paths;
- repository-native tests;
- preview and deployment workflows;
- generated and protected paths;
- current interface-kit version and local asset contract;
- public and private runtime boundaries;
- exact-head workflow results and review threads.

### Runtime and publication boundaries

No workflow was manually dispatched. No provider-writing preview label was added. No live route, inference endpoint, protected PDF, mutation endpoint, scheduler production path, or private service was called by this programme stage.

The current execution runtime could not independently reach the Atlas custom domains or inspect another operator's local worktree. This review therefore records remote GitHub source and workflow evidence and does not claim new custom-domain verification or local worktree cleanliness.

## Generator outcome

### Measured gaps

The current generator already owned titles, descriptions, canonical URLs, theme colour, local icons, local interface assets, and the accepted classic Writing footer. Phase 7 found that it still emitted:

- the shared `og-default.png` rather than the deterministic route card;
- no `twitter:image:alt`;
- no article publication metadata;
- no Schema.org Article JSON-LD.

The complete validation run also exposed a lifecycle defect in `data/published-refresh-exports.toml`: completed W-05 through W-07 refresh receipts still compared their historical output bytes against every future generator build.

### Changes

PR #39:

- emits `https://atlas-systems.uk/og/<slug>.png`;
- emits matching Open Graph and Twitter image alt text;
- emits `article:published_time` and `article:author`;
- emits safe Schema.org Article JSON-LD using effective generated metadata;
- escapes `<`, `>`, and `&` inside JSON-LD script content;
- defines explicit `active` and `retired` refresh-export states;
- preserves historical W-05 through W-07 source commits and blob identities as retired receipts;
- keeps active refresh exports exact-hash blocking;
- prevents retired receipts from writing scheduler bundles or comparing against unrelated future generator bytes.

### Protected boundaries

PR #39 does not change:

- canonical Markdown or article prose;
- publication-plan dates or ordering;
- `meta.toml` schema;
- footer structure or scheduler sequencing;
- generated draft folders on the pull-request branch;
- scheduler queue or publication state;
- `atlas-systems` source;
- workflows, provider settings, or secrets.

### Validation

At exact head `32dcd47a712406b6f82e79f3984546116e9729d2`:

- Build and Sync Articles pull-request validation succeeded;
- Article interface preview evidence succeeded;
- Private Atlas assurance succeeded;
- the complete generator suite passed;
- every canonical article built in isolation;
- publication-plan compilation passed;
- refresh-export validation passed;
- no write-capable build or scheduler-sync job ran on the pull request;
- no review threads remain.

### Later merge consequence

A later approved merge will match the generator workflow's `scripts/**` and `data/**` push filters. It may regenerate `drafts/scheduled/` and synchronize unpublished output to `atlas-scheduler`.

That merge must therefore be treated as generator regeneration and scheduler-sync authorization. It is not article publication. A due scheduler run or explicit production dispatch remains separately required for publication.

## Main-site outcome

### Measured gaps

The existing social verifier required metadata presence and correct image paths but did not prove:

- exact canonical ownership;
- intentional alias targets;
- complete icon declarations across all routes;
- parseable JSON-LD;
- the separate 404 exclusion contract.

Nine Lab routes lacked the complete local icon and manifest package. Eight are current instruments or compatibility routes. `/lab/console/` is the accepted legacy operations route deferred to Phase 11.

### Changes

PR #178:

- validates exact route canonicals and matching `og:url`;
- records `/lab/console/` canonicalizing to `/lab/`;
- records `/lab/reliability/` canonicalizing to `/systems/reliability/`;
- validates title agreement across document, Open Graph, and Twitter metadata;
- requires non-empty product-owned descriptions and theme colours;
- validates exact route social images, dimensions, and image alt text;
- parses present JSON-LD;
- validates link declarations semantically rather than by attribute order;
- verifies the 404 route separately as noindex, non-canonical, and outside the social graph;
- adds real local icon and manifest declarations to System Map, Proof Chain, Signal Garden, Reliability, Conformance, Anomaly, Almost, and Drift;
- records one machine-readable exception for `lab/console/index.html`, limited to complete icon declarations and bound to Phase 11;
- keeps the console canonical target mandatory and leaves its existing indexing behavior unchanged;
- updates the deterministic static-performance baseline from the exact generated candidate.

Only Lab `<head>` declarations changed in public HTML. Instrument bodies and runtime scripts remain unchanged.

### Static performance

Signal Garden and Almost now directly reference the canonical icon package. Their measured first-party request count and bytes therefore changed. The accepted baseline update uses the exact CI-generated candidate and preserves reporting-only thresholds.

No performance threshold was weakened or removed.

### Validation

At exact head `7bac8f67b97b4e1c9d58d1d012bb8f8338111059`:

- Pull request CI succeeded;
- HTML validation succeeded;
- all public-interface, main-site, Lab, and System Symphony tests succeeded;
- title normalization succeeded;
- sitemap validation succeeded;
- static-performance drift validation succeeded;
- complete and filtered Pages-output validation succeeded;
- exact route browser-identity verification succeeded;
- public-interface conformance succeeded;
- CodeQL succeeded;
- OpenSSF Scorecard succeeded;
- no review threads remain.

The legacy Cloudflare Pages preview workflow skipped. The governed preview validated the exact candidate, then stopped at the required approval gate. Preview publication and deterministic browser-capture jobs skipped. No provider resource was created.

### Writing boundary

Published Writing HTML remains generator and scheduler-owned. PR #178 validates committed Writing metadata but does not edit it. PR #39 is the upstream source dependency for future generated article metadata.

## Status outcome

### Finding and change

The Status root already satisfies the metadata, canonical, social-image, icon, and manifest contract. PR #32 adds an owned `404.html` so unknown paths no longer depend on provider fallback behavior.

The error route is:

- `noindex, follow`;
- non-canonical;
- outside the social-card graph;
- built from repository-local assets;
- product-specific;
- free of service checks and API calls.

### Protected boundaries

No service-check cadence, reliability verdict, SLO projection, activity feed, root page, deployment workflow, provider setting, or secret changes.

### Validation and preview

At exact head `f19bbe3046d3f0a95f6bf813cfebbf855aeb6ea4`, repository CI, interface conformance, Gardener gate, CodeQL, Scorecard, and preview candidate validation succeeded. The preview publication and browser-capture jobs skipped because provider approval was absent. No review threads remain.

## CV outcome

### Finding and change

The CV root already satisfies `noindex, follow`, profile metadata, canonical identity, icons, manifest, and About-active behavior. PR #31 adds an owned noindex 404.

The error route contains:

- no canonical URL;
- no social card;
- no PDF URL;
- no initialization control;
- no JavaScript;
- no embed or download behavior;
- About active on desktop and mobile.

### Protected boundaries

Explicit initialization, desktop embed, mobile native handoff, close and focus return, local PDF, independent deployment, provider settings, and secrets remain unchanged.

### Validation and preview

At exact head `34fead329ae73f9e7f1900cb786822e3438e16e9`, repository CI, interface conformance, Gardener gate, CodeQL, Scorecard, and preview candidate validation succeeded. Preview publication and browser-capture jobs skipped. No review threads remain.

## Ramone outcome

### Finding and change

The Ramone root already satisfies its product metadata and local asset contract. Unknown browser navigation previously received the same JSON error as API clients.

PR #30 adds content negotiation:

- unknown browser `GET` navigation receives noindex HTML;
- API-style unknown `GET` requests retain JSON;
- unknown non-GET requests retain JSON;
- existing root, status, ask, metadata, icon, asset, and security routes retain their current behavior.

The HTML error document is script-free and performs no inference, wake, Turnstile, tunnel, or private-route request.

### Protected boundaries

Inference, private tunnel, Turnstile, rate limiting, SSE, wake-state decisions, grounding, `/ask`, `/status`, bindings, provider settings, and secrets remain unchanged.

### Validation and preview

At exact head `665eb8e4f29af5084a9ac5e5642380d7ba025c8f`, repository CI, interface conformance, Gardener gate, CodeQL, Scorecard, and deterministic offline preview validation succeeded. Isolated Worker publication and browser evidence skipped. No review threads remain.

## Public API documentation outcome

### Finding and change

The human `/v1/docs` root already satisfies the metadata and local asset contract. Unknown documentation browser paths previously received the machine JSON error.

PR #52 adds bounded content negotiation only below `/v1/docs/*`:

- browser navigation receives noindex HTML;
- API-style requests to the same unknown path retain JSON;
- unknown `/v1/*` machine endpoints remain JSON regardless of an HTML `Accept` header;
- docs assets resolve before the error boundary.

### Protected boundaries

OpenAPI, response schemas, cache policy, CORS, methods, rate limits, evidence, reliability, topology, registry, search, stats, SLO, infrastructure, RAG, cron, bindings, provider settings, and secrets remain unchanged.

### Validation and preview

At exact head `2270141b36feb96a50b3858b2f89c6e0e73e56d5`, repository CI, interface conformance, Gardener gate, CodeQL, Scorecard, exact production-shaped Wrangler bundling, and preview candidate validation succeeded. Isolated Worker publication and browser evidence skipped. No review threads remain.

## API index no-change result

The API index remains intentionally JSON-only and needs no Phase 7 source branch.

Current tests and deterministic evidence already prove:

- `application/json` responses;
- public CORS;
- bounded cache policy;
- GET-only root behavior;
- JSON 404, 405, and 503 responses;
- fail-closed KV behavior;
- no HTML shell or visual metadata;
- no screenshots;
- no KV writes during evidence capture.

Introducing HTML metadata, icons, navigation, footer, or browser errors would violate the accepted product boundary.

## Browser evidence

No new browser preview was published in Phase 7 source preparation.

For Status, CV, Ramone, and Public API documentation:

- exact-head preview validation succeeded;
- provider publication jobs skipped;
- browser evidence jobs skipped.

For `atlas-systems`:

- exact-head candidate validation succeeded;
- the approval gate failed as designed because `interface-preview-approved` was absent;
- preview publication and deterministic browser evidence skipped.

For `atlas-article-gen`:

- private artifact-based article preview evidence succeeded;
- no public provider resource or live-site write occurred.

Visual and live-route evidence therefore remain later approval gates. Source CI is not represented as deployment proof.

## Security and privacy review

Phase 7 source preparation did not:

- request, read, log, or change a secret;
- modify Cloudflare bindings, routes, environments, variables, schedules, or provider settings;
- manually dispatch a workflow;
- add a provider-writing preview label;
- create a public preview;
- deploy a Worker or Pages site;
- regenerate or synchronize article output on `main`;
- change scheduler queue state or publication timing;
- publish or refresh an article;
- call Ramone inference or private tunnel paths;
- request the protected CV PDF;
- mutate an API endpoint or KV namespace.

## Risks

1. Merging PR #39 will regenerate committed drafts and may synchronize unpublished output to `atlas-scheduler`. Review it as a generator and queue-sync action, not as a documentation-only merge.
2. Merging PR #178, #32, #31, #30, or #52 will trigger a repository-owned production deployment. Source approval and rollout approval remain separate.
3. Browser previews and live-route verification are not complete because provider-writing approval was deliberately withheld.
4. The legacy console retains one icon-declaration exception until Phase 11. The exception is machine-readable, path-specific, canonical-bound, and cannot spread to another route.
5. Published Writing metadata remains generator and scheduler-owned. Do not hand-edit article HTML in `atlas-systems`.
6. GitHub remote state does not prove local worktree cleanliness.
7. Unrelated `atlas-infra` PR #79 and `atlas-api-public` PR #5 remain outside this programme.

## Dependency and rollout order

A later approved rollout should use this order:

1. Review PR #39 as the upstream Writing metadata source and regeneration boundary.
2. If approved, merge PR #39 and verify the generator build, regenerated drafts, any scheduler sync commit, and absence of publication.
3. Rebase or revalidate PR #178 against current `atlas-systems/main` if generator output changes overlap published or queued article metadata.
4. Review PR #178 and, if approved, merge and verify exact production deployment and live route identities.
5. Review and roll out Status PR #32, CV PR #31, Ramone PR #30, and Public API PR #52 independently. Their order is not technically coupled.
6. Confirm the API index no-change contract remains green.
7. Record exact merge, deployment, live-route, rollback, and intentional-exception receipts before declaring Phase 7 production-closeable.

No pull request should be merged from this review record alone. Every merge remains separately approval-gated.

## Approval boundary

Ready for owner review:

- `atlas-article-gen` PR #39;
- `atlas-systems` PR #178;
- `status` PR #32;
- `atlas-doc-viewer` PR #31;
- `ramone-edge` PR #30;
- `atlas-api-public` PR #52;
- the API-index no-change result;
- this documentation-only review branch.

Not authorized:

- merging any Phase 7 implementation pull request;
- adding `interface-preview-approved` or another provider-writing label;
- creating public previews;
- deploying Workers or Pages;
- running the scheduler in production;
- regenerating or synchronizing generator output through a merge;
- publishing or refreshing articles;
- modifying provider settings, bindings, variables, environments, schedules, repository settings, or secrets;
- beginning Phase 8.
