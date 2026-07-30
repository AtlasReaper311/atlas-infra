# Public interface programme Phase 7 rebaseline

Status: Phase 0 control record for the transition from Phase 6 to Phase 7.

Recorded: 30 July 2026.

This record supersedes the dated current-state, current-risk, and current-approval sections in `docs/public-interface-programme.md`. It does not replace that document's mission, authority order, locked decisions, route inventory, ownership model, phase register, operating rules, exclusions, evidence requirements, or completion definition.

## Current state

Phase 6 is substantially implemented and distributed, but it is not closed.

The shared footer authority is accepted in `atlas-infra`. `atlas-interface-kit v0.4.0` is the immutable implementation release. The main site, Status, CV, Ramone, and Public API documentation have merged consumer adoption. The approved W-01 through W-07 classic Writing footer has been restored through the generator and scheduler-owned publication path.

Two programme-owned Phase 6 draft pull requests remain open:

- `atlas-article-gen` PR #37, `docs/phase-6-classic-writing-footer-authority`, exact head `6f5da05c3a074eec0610b58dca93b2a8d8b645fe`;
- `atlas-scheduler` PR #44, `fix/phase-6-classic-writing-footer-validation`, exact head `4060d5e356ec3ff80fdb90955e0fcdf15e9a1994`.

Both pull requests are mergeable, have successful exact-head validation, and have no unresolved review threads. They remain draft and unmerged. Phase 7 source work is therefore blocked.

### Repository rebaseline

| Repository | Current `main` SHA | Programme state | Relevant open pull requests | Protected boundary |
| --- | --- | --- | --- | --- |
| `atlas-infra` | `3870790c58ee239006535d4597ea6a3c31353037` | ADR-0009 and the bounded classic Writing footer exception are merged. Existing interface authority already covers Phase 7 metadata and icon requirements. | PR #79 is unrelated chaos-assurance documentation. | Policy inputs, schemas, validators, ADRs, generated classifications, and scheduled provider-writing workflows remain separately governed. |
| `atlas-systems` | `8bfb54d1bd7a1abb62bb7aca99a7e997c82788c1` | Phase 6 consumer adoption and footer production-readiness fixes are on `main`. | None. | Generated article output, System Symphony audio and renderer contracts, AtlasField assets, provider settings, and production deployment remain independently owned. |
| `atlas-interface-kit` | `c38b5b3edd631999dfad838c4fb70e505a9860cf` | Immutable source release `v0.4.0`. No Phase 7 kit change is currently justified. | None. | Generated `dist/`, fingerprints, font licences, tags, and release assets remain immutable. |
| `atlas-api-public` | `9218ce9d325e401d5197b3b43cc0c98bddf10cdc` | Human documentation is in browser-identity scope. The JSON API remains contract-owned. | PR #5 is unrelated read-only Ramone control-plane work and must not be combined with Phase 7. | API schemas, registry projection, Worker bindings, schedules, rate limits, and provider settings remain outside browser-identity work. |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | JSON-only registry contract evidence is established. | None. | No HTML shell, visual metadata, footer, navigation, or browser application is permitted. |
| `status` | `73fb6f4ed9114c227b1138e3f39ac22dba8b9aba` | Governed Phase 6 footer and corrected Public API documentation destination are on `main`. | None. | Visitor-side checks, API-derived reliability verdicts, SLO policy projection, stale evidence, and event-feed ownership remain local. |
| `atlas-doc-viewer` | `70697ffea56fff6fdad4eb7108fe2ee76f191a8b` | Governed Phase 6 CV footer is on `main`. | None. | About remains active. `noindex, follow`, explicit initialisation, desktop embed, mobile native handoff, focus return, local PDF, and independent deployment remain protected. |
| `ramone-edge` | `46b90342f7d9316bc4a2f5da1891e823494b8538` | Governed Phase 6 Ramone footer is on `main`. | None. | Inference, private tunnel, Turnstile, rate limiting, SSE, wake-state decisions, grounding, bindings, secrets, and `/ask` and `/status` contracts remain excluded. |
| `atlas-article-gen` | `a492c599cdb7055ca4e8aebd8dd5a4d74ec30d82` | Generator output uses the accepted classic Writing footer. Guidance and tests still need the ADR-0009 alignment in PR #37. | PR #37. | `scripts/build_article.py` remains parser authority. Markdown, generated HTML, metadata, dates, and publication state must not be hand-edited. |
| `atlas-scheduler` | `f1426043ad265d90a809fb3ba62412fda894a9e1` | W-05 through W-07 restore receipts are recorded. Explicit fail-closed classic-profile validation remains in PR #44. | PR #44. | Queue state, publication timing, sequencing, refresh requests, receipts, and the only production write path into `atlas-systems` remain scheduler-owned. |

GitHub proves remote repository and pull-request state. It does not prove another operator's local worktree state. The executing checkout must still be inspected before every implementation branch.

## Evidence inspected

### Programme and authority

- `docs/public-interface-programme.md`;
- `docs/work-allocation.md`;
- `docs/public-interface-contract.md`;
- `policy/public-interface-system-v2.json`;
- ADR-0008 and ADR-0009 authority referenced by current policy and merged pull requests;
- `.github/workflows/public-interface-contract.yml`.

### Phase 6 implementation and distribution

- current `main` commits for all ten programme repositories;
- merged `atlas-infra` PR #91;
- merged `atlas-interface-kit` PR #13 and repository `VERSION` value `0.4.0`;
- merged `atlas-systems` PRs #174 and #176;
- merged Status PRs #30 and #31;
- merged CV PR #30;
- merged Ramone PR #29;
- merged Public API documentation PR #50;
- generator and scheduler publication receipts for W-05 through W-07;
- open generator PR #37 and scheduler PR #44;
- exact-head workflow results and review-thread state for PRs #37 and #44.

### Preview and deployment boundaries

The existing repository preview and deployment workflows were inspected from current repository evidence. No workflow was dispatched. No preview or production deployment was created by this rebaseline.

The current runtime could not independently reach the Atlas custom domains or create a local Git checkout. This record therefore does not claim new live-route verification, local worktree cleanliness, or local repository-native test execution.

## Phase 6 closeout finding

Phase 6 may be declared closed only after both remaining pull requests are reviewed and separately approved for merge:

1. `atlas-article-gen` PR #37 aligns the canonical case-study guidance and executable tests with ADR-0009 without changing parser source or generated output.
2. `atlas-scheduler` PR #44 adds explicit fail-closed validation for the bounded classic Writing profile without changing queue entries, publication dates, receipts, production state, or provider configuration.

Required closeout evidence for each pull request:

- exact reviewed head SHA;
- successful repository-native checks;
- no unresolved review threads;
- changed-path review;
- merge commit after explicit approval;
- confirmation that the merge did not trigger an unauthorised publication or provider write;
- updated Work Allocation and programme handoff.

No article refresh or scheduler production execution is required to close these documentation and validation changes.

## Existing Phase 7 authority

No new ADR is required before Phase 7.

The accepted public interface contract already requires, for indexable HTML pages:

- descriptive titles;
- meta descriptions;
- canonical URLs;
- theme colour;
- complete local icon declarations;
- Open Graph type, title, description, URL, site name, image, image dimensions, and image alt;
- equivalent Twitter metadata.

It also requires local copies of the canonical icon package, preserves `noindex, follow` for the CV, keeps the 404 route `noindex`, assigns generated article metadata to `atlas-article-gen`, and excludes machine-facing JSON surfaces from the visual contract.

Phase 7 is therefore an implementation and evidence phase against accepted authority, not an authority-design phase.

## Phase 7 execution map

After Phase 6 closeout and approval of this rebaseline, each repository receives a fresh Part 0 inspection and a separate `fix/browser-identity-contract` branch.

### `atlas-systems`

Audit and correct repository-owned HTML routes for:

- page-first title grammar;
- descriptions;
- canonical URLs;
- Open Graph and Twitter metadata;
- social images, dimensions, and alt text;
- favicons, Apple touch icon, manifest, and theme colour;
- structured data;
- sitemap coverage;
- 404 and other noindex routes;
- recently promoted routes, including Speculum;
- browser-tab evidence without runtime JavaScript dependency.

Generated article metadata must not be edited in published HTML. Any article metadata defect routes upstream to `atlas-article-gen`.

### `atlas-article-gen`

Inspect `docs/CASE_STUDY_INSTRUCTIONS.md`, relevant templates, `scripts/build_article.py`, metadata fixtures, and generated contract tests before deciding whether a Phase 7 generator PR is required.

Only generator-owned article metadata may change. Article prose, dates, publication order, scheduler queue state, and live output remain unchanged.

### `status`

Preserve Status-specific social identity while applying the shared icon package, manifest contract, canonical URL, title grammar, local asset verification, and error-page identity.

### `atlas-doc-viewer`

Preserve `og:type=profile`, `noindex, follow`, CV-specific social card, canonical URL, About relationship, protected PDF behaviour, and independent deployment.

### `ramone-edge`

Verify product title, description, canonical URL, social image, theme colour, icons, offline-error metadata, and local asset declarations without disclosing private inference details or modifying runtime decisions.

### `atlas-api-public`

Apply Phase 7 only to the human documentation surface. Preserve API response contracts, schemas, cache policy, CORS, method behaviour, and provider boundaries.

### `atlas-api-index`

No visual pull request. Confirm JSON content type, cache headers, CORS, method behaviour, bounded errors, and absence of an HTML shell or visual metadata.

## Proposed Phase 7 dependency order

1. Close `atlas-article-gen` PR #37.
2. Close `atlas-scheduler` PR #44.
3. Review and merge this Phase 0 rebaseline after explicit approval.
4. Inspect `atlas-article-gen` metadata authority and tests.
5. Inspect and prepare the `atlas-systems` browser-identity draft PR.
6. Prepare independent Status, CV, Ramone, and Public API documentation draft PRs where current evidence proves changes are needed.
7. Prepare API index contract-only evidence if the current contract suite has a measured gap.
8. Stop with one exact-head draft PR per affected repository. Do not merge or deploy under Phase 7 implementation approval.

Non-overlapping consumer branches may proceed in parallel after steps 1 through 3, but each repository still requires its own Part 0 inspection and approval report.

## Changes

This Phase 0 branch changes documentation only:

- `docs/public-interface-phase-7-rebaseline.md` records the current ten-repository state, remaining Phase 6 blockers, existing Phase 7 authority, execution map, risks, and approval boundary;
- `docs/work-allocation.md` records the current programme owner and exact resume point.

Deliberately untouched:

- ADRs;
- policy and schemas;
- validators and workflows;
- `atlas-interface-kit` source, generated bundle, tag, and release;
- consumer source and generated assets;
- article Markdown, generated HTML, metadata, dates, queue state, and publication state;
- Cloudflare configuration, provider settings, secrets, runtime bindings, and live routes.

## Validation

### Observed before branch creation

- all ten repository `main` SHAs were read from GitHub;
- open pull requests were inspected in every programme repository;
- PR #37 exact-head workflows succeeded: Build and Sync Articles, Private Atlas assurance, and Article interface preview evidence;
- PR #44 exact-head workflows succeeded: Validate and Private Atlas assurance;
- both remaining Phase 6 pull requests are mergeable and have no unresolved review threads;
- the interface contract and current `v0.4.0` release identity were inspected.

### Branch validation boundary

Local validation was unavailable because the execution runtime could not resolve GitHub for a checkout. Pull-request checks are authoritative for the committed branch bytes.

Expected repository checks include Markdown and text policy, pull-request impact, CodeQL, OpenSSF Scorecard, estate conformity where configured, and `git diff --check`. No test result is claimed until GitHub reports it against the exact branch head.

## Browser evidence

No new browser preview was created because this is documentation-only Phase 0 work.

No new live verification is claimed. Previously recorded Phase 6 preview and deployment evidence remains historical evidence only and must not be treated as a new 30 July live check.

## Security and privacy review

Actions performed:

- read repository files, commits, pull requests, review threads, and workflow results through the connected GitHub application;
- reset the closed historical Phase 0 documentation branch to current `atlas-infra/main`;
- write only the two documentation paths listed above;
- open a draft documentation pull request.

Actions not performed:

- no secret was requested, read, logged, or changed;
- no mutation endpoint, inference endpoint, protected PDF, or internal service route was called;
- no workflow was manually dispatched;
- no preview, deployment, release, scheduler run, article refresh, or publication was triggered;
- no provider setting, binding, variable, environment, or repository setting was changed;
- no Phase 6 or Phase 7 product pull request was modified or merged.

## Risks

1. Phase 6 is not closed while generator PR #37 and scheduler PR #44 remain open.
2. The historical master programme document still contains dated status sections. This rebaseline explicitly supersedes those sections and should be linked or folded into the master record during the next documentation closeout.
3. GitHub remote state does not prove local worktree cleanliness.
4. Current custom-domain behaviour was not independently reproduced from this runtime.
5. Merging consumer Phase 7 pull requests may trigger production deployment. Source approval and rollout approval remain separate.
6. Generated article metadata crosses generator and scheduler ownership. Published HTML must not be hand-edited.
7. `atlas-api-public` PR #5 and `atlas-infra` PR #79 are unrelated open work and must not be rebased, modified, or combined with this programme.

## Rollback

Before merge, close the draft pull request and reset or delete `docs/public-interface-programme`.

After merge, revert the documentation commit. No runtime, provider, data, release, publication, or secret rollback is required.

## Approval boundary

Ready:

- current Phase 0 repository rebaseline;
- evidence-backed identification of the two remaining Phase 6 obligations;
- confirmation that existing authority covers Phase 7;
- repository and dependency map for Phase 7.

Not authorised:

- merging PR #37 or PR #44;
- merging this Phase 0 pull request;
- creating a Phase 7 branch in any consumer or pipeline repository;
- changing metadata, icons, manifests, social images, structured data, sitemap output, or error pages;
- adding preview-approval labels;
- dispatching workflows;
- creating releases;
- deploying Workers or Pages;
- running the scheduler;
- refreshing or publishing articles;
- changing provider settings, bindings, variables, repository settings, or secrets.

Phase 7 begins only after Phase 6 is formally closed and this rebaseline is reviewed and approved.