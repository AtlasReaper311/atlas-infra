# Public interface programme Phase 10 coordination

Status: active. Part 0 inspection complete. Routine source corrections are authorised; protected article refreshes, production publication, and future-footer architecture remain separately approval-gated.

Recorded: 30 July 2026.

## Outcome

Phase 10 will improve the Writing directory, generated article reading contract, and scheduler-owned editorial navigation without repeating the formatting and rollout failures encountered during the Phase 6 and Phase 7 Writing work.

The work spans four authority layers:

1. `atlas-infra` records the accepted programme boundary and ADR-0009 protection.
2. `atlas-article-gen` owns Markdown parsing, validation, templates, generated HTML, metadata, and queue sync.
3. `atlas-scheduler` owns queue validation, coming-soon state, previous and next links, series navigation, Work insertion, publication planning, and the only production write path into `atlas-systems`.
4. `atlas-systems` owns the Writing directory, published presentation assets, browser evidence, deployment validation, and the live result.

## Current repository state

- `atlas-infra/main`: `0b5f236ca3b46ec48bd90bf67995f02f66e564d9`.
- `atlas-article-gen/main`: `6b5fe2a49b7f8d413fbd19e00b51df78ec5bfd84`.
- `atlas-scheduler/main`: `2f6b7f8e372e25d935eb07c01cd7c5efd443617f`.
- `atlas-systems/main`: `4dd5827b922832efacba4e20146de8dc2e95a1e7`.
- No open pull request overlaps Phase 10 paths in `atlas-article-gen` or `atlas-scheduler`.
- `atlas-systems#179` is stale, excluded, and must not be reused, rebased into Phase 10, or merged.
- No current Phase 10 implementation branch or pull request existed at inspection time.

## Authority inspected

- `AGENT.md`;
- this programme record and Phase 9 closeout;
- ADR-0008 and ADR-0009;
- `atlas-article-gen/docs/CASE_STUDY_INSTRUCTIONS.md`;
- generator starter templates;
- `scripts/build_article.py` and `scripts/build_article_core.py`;
- generator CSS, tests, publication plan, generated drafts, and workflows;
- `atlas-scheduler/docs/PUBLISHING_CONTRACT.md`;
- scheduler publication, series, targeted-preview, shell-refresh, and preview-refresh paths;
- scheduler tests and production workflow;
- `atlas-systems/writing/index.html`, directory, search, and series scripts;
- article and directory presentation CSS;
- representative W-01, W-06, W-07, W-08, standalone, series, table-heavy, and code-heavy output;
- current browser-evidence and contract tests.

## Historical failure pattern

The previous Writing work failed through three interacting classes rather than one isolated styling problem:

1. **Parser defects.** The generator accepted unsupported Markdown shapes and produced malformed HTML while validation inspected metadata and broad structure rather than rendered block fidelity.
2. **Contract churn.** The Writing footer moved through semantic, Classic Plus, sequence-only, and restored classic shapes before ADR-0009, generator output, scheduler validation, and published output agreed.
3. **Rollout sequencing.** Generator merges regenerated drafts and synchronised the scheduler queue; scheduler refreshes then wrote selected published output through separate production paths. Source success, queue sync, refresh generation, scheduler execution, site push, deployment, and live verification were sometimes discussed too loosely.

Phase 10 must prevent all three classes from recurring.

## Confirmed current defects

### P0: fenced code blocks are malformed

`atlas-article-gen` documentation states that fenced code blocks are supported, and multiple canonical articles use them. The current `render_body()` parser has no fenced-code branch. It therefore flattens fences and their contents into ordinary paragraphs, sometimes passing triple backticks through the inline-code substitution.

Confirmed affected state includes:

- unpublished W-08 `specular-core-architectural-recovery` in both generator and scheduler queues;
- unpublished `atlas-control-plane-waves-0-3`;
- unpublished `reliability-one-source-of-truth`;
- unpublished `reliability-release-correlation`;
- published W-06 `atlas-systems-cicd-pipeline`.

This parser defect and its missing regression tests block article-reading changes and future publication.

### P1: cross-repository preview evidence is stale

The generator interface-preview handoff is pinned to scheduler commit `ae04c8bc3a3c9b0e205f387a9d7e64382a68ddfb`, which is 46 commits behind current scheduler main. The delta includes current dual-footer validation, refresh contracts, production receipts, queued shell updates, and workflow validation.

The scheduled-article preview workflow is separately pinned to `929de0e842e469fbd67c9745c50735520c78e0a9`. Both pins are immutable, but neither currently proves compatibility with the scheduler code that would publish the queue.

### P1: targeted preview bypasses the strict footer adapter

`scripts/preview_selected.py` installs the series adapter and calls series publication functions directly. It does not install `publish_editorial.py`, which is the current production entry point and the strict validator for semantic and classic footer profiles. A targeted preview can therefore prove series and Work projection while missing a footer-profile incompatibility that production would reject.

### P1: Writing type filtering is semantically incorrect

`writing/directory.js` classifies published series separately, but the `case-study` filter accepts every non-upcoming card. Published series entries therefore appear under both Case Studies and Series. Current tests verify that filtering tokens exist but do not execute the filter semantics.

### P2: stale series compatibility can conceal source drift

`writing/series.js` retains a hard-coded W-05 through W-07 fallback even though current scheduler output includes source-owned `data-series` attributes. The fallback can hide missing source data by repairing it in the browser. Repeated `AtlasSeries.refresh()` calls may also attach additional `MutationObserver` instances because existing observers are not retained and disconnected.

### P2: historical and generated article shells are intentionally non-uniform

W-01 through W-04 retain protected historical inline shells and presentation-only overlays. W-05 through W-07 use current generated shells and series markup. Tests and CSS must target shared contracts rather than assuming identical document bytes.

## Protected contracts

Phase 10 must preserve unless Atlas separately approves the exact change:

- W-01 through W-07 classic footer structure under ADR-0009;
- published article prose, dates, W-numbers, tags, summaries, metadata, canonical URLs, social identity, and series history;
- scheduler ownership of sequence calculation and the only production write path;
- one queue entry per slug with matching metadata;
- publication-plan ordering and date semantics;
- no direct edits to generated `index.html` or `meta.toml`;
- no direct article writes into `atlas-systems`;
- no provider settings, secrets, bindings, or workflow dispatch without the relevant gate;
- no claim of publication before scheduler execution, exact site push, deployment verification, and live-route verification.

## Routine authorised work

Atlas has authorised the agent to inspect, implement, validate, mark ready, and merge routine Phase 10 corrections without returning for each normal engineering decision. This includes:

- parser correctness and fail-closed validation;
- deterministic fixture and regression coverage;
- current immutable compatibility pins after measuring the delta;
- preview paths that mirror production validation without production writes;
- directory filtering, search, count, empty-state, and keyboard defects;
- stale browser-only compatibility removal when source contracts are already present;
- documentation and test corrections;
- repository-local source pull requests whose merge does not itself publish to production.

Every pull request must still use an exact current base, repository-native validation, changed-path inspection, current-main rebase, exact-head checks, and a merge head guard.

## Separate approval gates

Return to Atlas with one consolidated evidence bundle before any of the following:

1. choosing whether future articles retain the classic footer or adopt a replacement profile;
2. changing the shared article presentation in a way that materially alters protected W-01 through W-07;
3. refreshing published W-06 or any other published article to repair generated formatting;
4. running a production scheduler publication or published-article refresh;
5. dispatching a provider-writing workflow, changing publication timing, or changing queue semantics;
6. any architecture change not representable by current ADR-0009 and publishing contracts.

## Implementation order

### 10.0 Control and regression baseline

- record this coordination entry and active Work Allocation state;
- add rendered-block fixtures that reproduce current code, table, callout, long-link, and mixed-content failures;
- inventory current queued and published malformed output;
- compare preview pins with current scheduler behavior.

### 10.1 Generator parser correctness

- implement fenced-code parsing with escaped literal content and optional language identity;
- reject unterminated fences;
- add fixtures for short, long, code-heavy, table-heavy, mixed-callout, and long-URL articles;
- prove current canonical articles build deterministically;
- regenerate drafts from Markdown only;
- verify exactly which generator and scheduler queue files change.

### 10.2 Scheduler compatibility and sequencing

- make targeted preview install the production editorial adapter;
- validate both accepted footer profiles through the preview path;
- add first, middle, latest, standalone, series, coming-soon, empty-queue, and malformed-output fixtures;
- update immutable cross-repository pins only to reviewed commits;
- preserve production timing and write boundaries.

### 10.3 Writing directory

- correct mutually exclusive content-type filtering;
- test filter plus search composition, counts, empty states, feature state, and series visibility;
- remove obsolete fallback data only after source attributes are required by tests;
- make series refresh idempotent;
- preserve scheduler insertion markers and source order.

### 10.4 Article reading and navigation review

- capture deterministic browser evidence for representative historical and generated articles;
- measure prose width, heading rhythm, tables, code, long links, figures, callouts, focus, keyboard use, reduced motion, and mobile behavior;
- return once with the exact future-footer and protected-presentation decisions, plus any proposed published W-06 repair bundle.

### 10.5 Controlled rollout

- merge approved source changes in dependency order;
- run a production-shaped scheduler dry run;
- treat any published refresh or scheduler execution as a separate approval;
- prove the exact `atlas-systems` commit, deploy run, live directory, live articles, and rollback path.

## Required evidence matrix

At minimum, Phase 10 evidence must cover:

- no articles, one article, multiple articles, and a continuous future queue;
- W-01 first-article fallback and latest-article fallback;
- standalone and clustered series ordering;
- published, next, scheduled, and no-coming-soon states;
- short prose, long prose, fenced code, inline code, tables, callouts, lists, long URLs, and responsive media;
- search alone, each type filter alone, filter plus search, zero results, reset, and feature behavior;
- keyboard navigation, visible focus, 200 percent text zoom, reduced motion, and narrow widths;
- Chrome and Firefox at the programme evidence widths;
- no serious or critical accessibility findings;
- no console errors, page errors, unintended failed requests, mutation endpoints, secret exposure, or production writes during source review;
- deterministic generated HTML and metadata;
- exact source, queue, scheduler, site, deployment, and live receipts where each stage applies.

## Current approval boundary

This record authorises routine source preparation, validation, ready-for-review transitions, and merges within the boundaries above. It does not authorise future-footer architecture, protected published-article refreshes, production scheduler execution, publication timing changes, provider writes, secret changes, or a live rollout.
