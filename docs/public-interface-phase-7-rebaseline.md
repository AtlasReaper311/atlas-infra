# Public interface programme Phase 6 closeout and Phase 7 start

Status: Phase 6 closed. Phase 7 active at repository-specific Part 0 inspection.

Recorded: 30 July 2026.

This record supersedes the dated current-state, current-risk, and current-approval sections in `docs/public-interface-programme.md`. It does not replace that document's mission, authority order, locked decisions, route inventory, ownership model, phase register, operating rules, exclusions, evidence requirements, or completion definition.

## Current state

Phases 0 through 6 are closed at their approved source, authority, immutable-release, consumer-adoption, publication-pipeline, and recorded rollout gates.

The Phase 6 footer system now has one coherent authority chain:

- `atlas-infra` owns the normal footer contract and ADR-0009 bounded classic Writing exception;
- immutable `atlas-interface-kit v0.4.0` implements the normal estate, product, tool, and editorial variants;
- `atlas-systems`, Status, CV, Ramone, and Public API documentation contain their approved consumer footers;
- `atlas-article-gen` emits the accepted classic Writing article footer with one scheduler placeholder;
- `atlas-scheduler` validates the normal semantic editorial profile and the bounded classic Writing profile explicitly and fail-closed;
- W-01 through W-07 retain the approved classic published structure.

Phase 7 may begin through fresh repository-specific Part 0 inspections and separate `fix/browser-identity-contract` draft pull requests. Phase 7 source approval does not authorize consumer merges, production deployment, scheduler execution, publication, provider writes, or secret changes.

## Phase 6 final merge receipts

| Repository | Pull request | Reviewed head | Merge commit | Result |
| --- | ---: | --- | --- | --- |
| `atlas-infra` | #91 | `0e9b390e7a346dece0f787e46015918b642d461e` | `3870790c58ee239006535d4597ea6a3c31353037` | Accepted ADR-0009 and the non-transferable classic Writing exception. |
| `atlas-article-gen` | #37 | `6f5da05c3a074eec0610b58dca93b2a8d8b645fe` | `fb4b83bc07a204204383ee321a73a4a4dec6eea8` | Aligned canonical guidance and generator tests with ADR-0009. |
| `atlas-scheduler` | #44 | `4060d5e356ec3ff80fdb90955e0fcdf15e9a1994` | `933dbe9df333342600a2c04f1162d73f1e1c06f6` | Added explicit queued and published validation for both accepted Writing footer profiles. |
| `atlas-infra` | #92 | `357a944367cac984885847ebbfe82001517bd0f5` | `49f44980014028b98aa08637d3efb8ca313fc28f` | Merged the Phase 7 transition rebaseline. |
| `atlas-article-gen` | #38 | `9627b67cf361098e895a33440b8aae5821fe4bb9` | `8b8467a30985372e23bc65f4740363d60d3a2ff9` | Corrected the canonical ADR filename and added a negative regression assertion for the obsolete path. |

PR #38 was required because PR #37 referenced the non-existent filename `ADR-0009-classic-writing-article-footer-exception.md`. The accepted authority file is `docs/adrs/ADR-0009-classic-writing-footer-exception.md`. The correction changes no parser, template, generated article, queue, workflow, or provider path.

## No-publication and no-provider-write evidence

The Phase 6 closeout merges did not publish or refresh an article and did not write a public provider resource.

### `atlas-article-gen`

`Build & Sync Articles` runs on pushes to `main` only when `articles/**.md`, `data/**`, `scripts/**`, or `templates/**` changes. PR #37 changed documentation and a test. PR #38 changed the same documentation and test boundary. Neither merge matched the main-branch generation and scheduler-sync path filter.

The repository's pull-request checks still ran the complete article tests, isolated builds, publication-plan validation, refresh-export validation, and private preview evidence. Those checks are read-only with respect to `atlas-systems`.

### `atlas-scheduler`

The production publication workflow runs only on the daily 09:00 UTC schedule or explicit `workflow_dispatch`. It does not run on a merge to `main`.

PR #44 merged at 10:12 UTC on 30 July 2026, after the day's scheduled 09:00 UTC execution boundary. No workflow was manually dispatched as part of the closeout.

### `atlas-systems`

`atlas-systems/main` remained at `8bfb54d1bd7a1abb62bb7aca99a7e997c82788c1` after the generator, scheduler, rebaseline, and ADR-reference merges. No scheduler-generated site commit followed those merges.

## Footer alignment review

### Authority

ADR-0009 defines:

```html
<div class="article-footer">
  <!-- exactly one scheduler-owned footer placeholder in generated output -->
</div>
```

Published content is limited to scheduler-owned previous and next article links, or `Latest article`. The classic profile forbids the normal `.atlas-footer` wrapper and named slots. The exception applies only to the three-repository Writing pipeline and cannot be reused by other consumers.

### Generator

Current `atlas-article-gen` output contains exactly one `<div class="article-footer">` and exactly one `AUTO-FOOTER` placeholder. Generator tests reject semantic footer wrappers and all governed variant classes inside that classic container.

The canonical guidance now points to the real ADR path and rejects the obsolete filename.

### Scheduler

Current `atlas-scheduler/scripts/publish_editorial.py`:

- accepts exactly one normal semantic editorial footer or one bounded classic Writing footer;
- requires the classic container to use only `class="article-footer"`;
- requires one placeholder in queued output;
- rejects mixed semantic and classic markup;
- rejects forbidden identity, context, sequence, and estate-escape tokens in the classic profile;
- verifies rendered previous and next, or latest, navigation after replacement.

A permissive legacy bypass no longer exists.

### Published site

Current `atlas-systems` source exposes `article-footer` on the seven published Writing articles and contains no `atlas-footer--editorial` occurrence in published Writing HTML. W-05, W-06, and W-07 show the same classic sequence structure as W-01 through W-04.

## Repository rebaseline

| Repository | Current `main` SHA before this closeout branch | Phase 7 role | Relevant open work | Protected boundary |
| --- | --- | --- | --- | --- |
| `atlas-infra` | `49f44980014028b98aa08637d3efb8ca313fc28f` | Authority and programme coordination only. Existing authority already covers metadata and browser identity. | PR #79 is unrelated chaos-assurance documentation. | ADRs, policy, schemas, validators, generated classifications, and provider-writing workflows remain separately governed. |
| `atlas-systems` | `8bfb54d1bd7a1abb62bb7aca99a7e997c82788c1` | Main repository-owned HTML routes, error identity, sitemap, structured data, and browser evidence. | None. | Generated articles, System Symphony audio and renderer contracts, AtlasField assets, provider settings, and production deployment remain independently owned. |
| `atlas-interface-kit` | `c38b5b3edd631999dfad838c4fb70e505a9860cf` | No Phase 7 change currently justified. | None. | `v0.4.0`, generated `dist/`, fingerprints, font licences, tag, and release assets remain immutable. |
| `atlas-api-public` | `9218ce9d325e401d5197b3b43cc0c98bddf10cdc` | Human API documentation only. | PR #5 is unrelated read-only Ramone control-plane work. | API schemas, registry projection, Worker behavior, bindings, schedules, rate limits, and provider settings remain excluded. |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | Contract-only evidence. No visual pull request unless a measured machine-interface regression exists. | None. | JSON-only root, content type, CORS, cache, GET-only behavior, bounded errors, and absence of HTML remain protected. |
| `status` | `73fb6f4ed9114c227b1138e3f39ac22dba8b9aba` | Product metadata, icons, canonical identity, social preview, and error identity. | None. | Visitor-side checks, API-derived verdicts, SLO projection, stale evidence, and event-feed ownership remain local. |
| `atlas-doc-viewer` | `70697ffea56fff6fdad4eb7108fe2ee76f191a8b` | CV metadata, icons, canonical identity, social preview, and error identity. | None. | `noindex, follow`, About active state, explicit initialization, desktop embed, mobile native handoff, focus return, local PDF, and independent deployment remain protected. |
| `ramone-edge` | `46b90342f7d9316bc4a2f5da1891e823494b8538` | Product metadata, icons, canonical identity, social preview, and offline error identity. | None. | Inference, private tunnel, Turnstile, rate limiting, SSE, wake-state decisions, grounding, bindings, secrets, and `/ask` and `/status` remain excluded. |
| `atlas-article-gen` | `8b8467a30985372e23bc65f4740363d60d3a2ff9` | Generator-owned article metadata and generated browser-identity tests. | None. | Markdown prose, publication dates, queue state, generated output ownership, and publication remain separate. |
| `atlas-scheduler` | `933dbe9df333342600a2c04f1162d73f1e1c06f6` | No Phase 7 source change unless metadata sequencing or generated-output validation proves a scheduler-owned defect. | None. | Queue state, timing, sequencing, receipts, and the only production write path into `atlas-systems` remain scheduler-owned. |

GitHub proves remote repository and pull-request state. It does not prove another operator's local worktree state. Every Phase 7 implementation branch must inspect the executing checkout before editing.

## Existing Phase 7 authority

No new ADR or interface-kit release is required before Phase 7.

The accepted public interface contract requires indexable HTML pages to provide:

- descriptive page-first titles;
- meta descriptions;
- canonical URLs;
- theme colour;
- complete local browser-icon declarations;
- Open Graph type, title, description, URL, site name, image, image dimensions, and image alt;
- equivalent Twitter metadata.

The contract also:

- requires repository-local copies of the canonical icon package;
- preserves `noindex, follow` for the CV landing page;
- keeps 404 pages `noindex`;
- assigns generated article metadata to `atlas-article-gen`;
- excludes machine-facing JSON surfaces from the visual contract;
- keeps runtime loading of shared assets from another deployment prohibited.

Phase 7 is implementation and evidence against accepted authority, not authority design.

## Phase 7 execution order

1. Inspect `atlas-article-gen` metadata generation, templates, fixtures, and contract tests.
2. Inspect `atlas-systems` route inventory, current metadata generation, static assets, social images, structured data, sitemap generation, 404 behavior, and browser evidence harness.
3. Prepare an `atlas-systems:fix/browser-identity-contract` draft pull request only for measured repository-owned gaps.
4. Prepare an `atlas-article-gen:fix/browser-identity-contract` draft pull request only for measured generator-owned article gaps.
5. Inspect and prepare independent Status, CV, Ramone, and Public API documentation pull requests where current evidence proves changes are required.
6. Confirm the API index machine-interface contract without introducing an HTML shell.
7. Stop with one exact-head draft pull request per affected repository and a measured no-change record for repositories already conforming.

Non-overlapping consumer branches may proceed independently after their own Part 0 inspections. Two branches must not edit overlapping files in the same repository at the same time.

## Phase 7 validation requirements

Each affected repository must use its own inspected commands and existing evidence framework. Required evidence includes, where applicable:

- exact base and head SHAs;
- titles, descriptions, canonicals, icons, manifest, theme colour, Open Graph, and Twitter metadata;
- social-image existence, dimensions, and alt text;
- structured-data validity;
- sitemap and error-route identity;
- Chrome and Firefox evidence at 320, 375, 768, 1024, and 1440 pixels;
- reporting-only 1920-pixel evidence where the existing harness supports it;
- no-JavaScript and 200-percent text-zoom evidence where already contracted;
- serious and critical accessibility findings blocking;
- console, page-error, failed-request, and overflow evidence;
- unchanged CSP, privacy, public/private, operational, inference, and protected-document boundaries;
- repository-local asset verification with no cross-deployment runtime dependency.

Static drift remains blocking. Browser performance remains reporting-only until Phase 14 accepts specific budgets.

## Security and privacy review

This closeout and alignment work changed documentation and one cross-repository ADR reference only.

No secret was requested, read, logged, or changed. No workflow was manually dispatched. No preview-approval label was added. No article was regenerated, refreshed, queued, published, or written to `atlas-systems`. No Worker or Pages deployment, provider setting, binding, variable, environment, repository setting, inference route, protected PDF, or internal service route changed.

## Risks

1. `docs/public-interface-programme.md` retains historical dated sections. This current closeout record explicitly supersedes its current-state, current-risk, and current-approval text.
2. GitHub remote state does not prove local worktree cleanliness.
3. Current custom-domain behavior was not independently reproduced from this runtime during closeout.
4. Merging a Phase 7 consumer pull request may trigger production deployment. Source review and rollout approval remain separate.
5. Generated article metadata crosses generator and scheduler ownership. Published HTML must not be hand-edited.
6. `atlas-api-public` PR #5 and `atlas-infra` PR #79 are unrelated and must not be combined with this programme.

## Approval boundary

Authorized now:

- Phase 7 repository-specific Part 0 inspections;
- source changes on separate `fix/browser-identity-contract` branches where current evidence proves a gap;
- repository-native validation;
- draft pull requests;
- existing pull-request validation and read-only evidence jobs.

Not authorized by this record:

- merging Phase 7 consumer or pipeline pull requests;
- adding preview-approval labels that create provider resources;
- manually dispatching workflows;
- creating releases;
- deploying Workers or Pages;
- running the scheduler in production;
- refreshing or publishing articles;
- changing provider settings, bindings, variables, environments, repository settings, or secrets.

Phase 7 stops at exact-head draft pull requests and evidence review unless Atlas separately approves a later merge and rollout gate.
