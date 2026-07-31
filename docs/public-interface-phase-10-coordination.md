# Public interface programme Phase 10 closeout

Status: completed.

Recorded: 30 July 2026.
Closed: 31 July 2026.

## Outcome

Phase 10 corrected the Writing directory state model, repaired generated fenced-code rendering, aligned previews with the production publication adapter, refreshed the malformed published W-06 code examples through the controlled generator-to-scheduler path, and established the compact sequence-only classic Writing footer as the sole active footer profile.

The work preserved scheduler ownership of publication, protected published article content, and the distinction between source validation, preview evidence, scheduler execution, site deployment, and live verification.

## Final authority

ADR-0009 now defines the classic sequence footer as the only active Writing footer architecture. It retains scheduler-rendered previous, next, and latest navigation. Retired semantic and Classic Plus shapes remain historical evidence only and are rejected by active generator, scheduler, and consumer validation.

Authority merged through `atlas-infra#104`:

- merge commit: `44e7e15cbc9f9071c1886d0d86260bcafcc97c14`;
- no provider setting, secret, binding, publication timing, or runtime configuration changed.

## Implementation receipts

### Generator parser and immutable refresh preparation

`atlas-article-gen#44` merged as `4b0fa788c78ccc2d8f5747326e460c849974a178`.

It:

- added fail-closed backtick and tilde fenced-code parsing;
- escaped literal code content and preserved newlines;
- validated optional language identities;
- rejected unterminated fences;
- added mixed rendered-block fixtures and deterministic build coverage;
- preserved canonical Markdown, article metadata, publication timing, and live-site state.

The corrected W-06 bundle was exported through `atlas-article-gen#46`, merged as `0eb66140abe0e8d7fd9446a6f285c730c5a35960`, with immutable provenance:

- generator source commit: `fca344e36295d3620e812cbfb4b8c5aa19299816`;
- article blob: `f03cc461cad7880773f8ec21c5e2802d55cb36b3`;
- metadata blob: `dfadb1fa122993a41a026f8d70439a66c2049e91`.

### Scheduler preview parity and W-06 refresh

`atlas-scheduler#51` merged as `50b87ae1114cfda1af765f84450c21f4ff5a4d1f`.

It routed targeted previews through the production editorial adapter and rejected queue shapes that production would reject.

The approved W-06 refresh request landed through `atlas-scheduler#52` as `0e6e2ee2c7a70e32d6942fdde03a94ea3a3709de`.

The scheduler then:

- wrote only `writing/atlas-systems-cicd-pipeline/index.html` to the site;
- produced site commit `b86d3500592d2bd107ad808c6455a92e5a9e863c`;
- changed the existing YAML and TOML examples from flattened paragraph markup to fenced code markup;
- preserved prose, title, W-number, publication date, tags, summary, series state, Writing index, Work index, and classic sequence navigation;
- recorded immutable receipt commit `339959ffb78ba624c950bda6d4d8df7477953ea7` with `exact_deployment_verified: true`.

### Writing directory and browser-owned state

`atlas-systems#184` merged as `ccbb0cbdaa2fadd2d949f8f4765024ea7d3a304e`.

It:

- made case-study, series, upcoming, and all filters mutually coherent;
- added an executable directory state contract;
- required scheduler-owned series attributes rather than repairing missing data in the browser;
- made series observer refresh idempotent;
- preserved article cards, routes, insertion markers, dates, tags, summaries, and source order.

The initial production run exposed a dependency-resolution failure in the shared static deployment path before upload. `atlas-infra#101` pinned Wrangler `4.116.0` as `ba99bab755d5601204ead565a6b308d60a5c53ad`, and `atlas-systems#185` updated the immutable caller pin as `bb18b60e3ef80ae8ad4a3167cf2468ca0489da34`.

A later scheduler preflight found unrelated stale deterministic output at `og/blackbox.png`. Diagnostic PR `atlas-systems#186` was closed without merge. `atlas-systems#187` regenerated only that asset and merged as `2a34f6a56875a3d63a672c08c16bb2b2a41cc8f6`.

### Classic-only footer implementation

`atlas-scheduler#53` merged as `c9fabf6c5f49546bf6175ef1bdeafff8bc2b30ce`.

It:

- removed the retired semantic footer from active validation and dispatch;
- enforced the exact classic container across queue validation, preview, shell refresh, and publication;
- rejected semantic tokens, mixed profiles, bare placeholders, and extra footer classes;
- removed the dormant provider-writing Classic Plus migration workflow;
- preserved historical bundles, requests, receipts, reports, and repository history.

`atlas-article-gen#47` merged as `08288c145df509dcb3ab7385ac148a52918178bb`.

It pinned both scheduler-backed preview workflows to the immutable classic-only scheduler commit and required W-99 output to contain exactly one classic footer with rendered sequence navigation and no retired semantic tokens.

The exact-head W-99 run `30637492984` passed:

- 183 generator tests;
- the complete pinned scheduler suite;
- production-adapter W-99 construction;
- classic footer and sequence validation;
- HTML and filtered Pages validation;
- unchanged Writing and Work indexes;
- private artifact `8795959298`, digest `sha256:6a65a4eff3f0777bbd5b7abe90b488a42ac6e8da530e787b0d1b0af429c37c24`.

## Final consumer proof

`atlas-systems#188` merged as `4896b1c482d89f8b7968ec0baee5763e36843342`.

It added:

- explicit `overflow-wrap: anywhere` for visible prose links;
- an executable inventory test over every published Writing article;
- exact-one classic footer enforcement;
- rejection of retired semantic tokens, placeholders, and extra footer classes;
- sequence evidence requiring previous and next navigation or `Latest article`.

No generated article HTML, prose, metadata, publication date, Writing index, Work index, scheduler state, workflow, provider setting, binding, or secret changed in that pull request.

## Preview evidence

Atlas approved the isolated non-production preview for exact source head `3da0b1b9f76272fb5ce2bcf065148e3447abb5c3`.

Preview run `30637397463` passed:

- candidate and approval gates;
- isolated Pages publication at `https://interface-pr-188.atlas-systems-44t.pages.dev`;
- route-derived Chrome and Firefox evidence for the Writing directory and all seven published articles;
- keyboard, responsive, accessibility, page-error, request-error, and console-error gates;
- Batch H assertions;
- System Map and directory-header pixel smokes;
- no new blocking findings, with 12 reviewed reporting-baseline findings preserved.

Artifacts:

- interface validation `8795915019`, digest `sha256:bcdc04cdcd8182f3b24f41d8fa0fe611178fe3a6233f758a899ac788781a2bf4`;
- public interface evidence `8796413189`, digest `sha256:90ae70bcceadb6e4c8b69fb8ee260c7f074f01c1441af1472b100e99baa83673`;
- Batch H evidence `8796414553`, digest `sha256:c52d46e20fe10b55535d7d222a312b7231d86377f4765ced46550f79a0a5a2af`.

## Production verification

Production run `30638766487` deployed exact merge commit `4896b1c482d89f8b7968ec0baee5763e36843342`.

Observed evidence:

- Pages output contract: success;
- HTML and offline link validation: success;
- immutable shared workflow pin: `atlas-infra@ba99bab755d5601204ead565a6b308d60a5c53ad`;
- Wrangler: `4.116.0`;
- Cloudflare Pages upload: 472 files inspected, one file uploaded, 471 reused;
- atomic Pages deployment: `https://ffd93356.atlas-systems-44t.pages.dev`;
- custom domain exposed the exact merge commit on the second readiness attempt;
- Systems v2 route marker: success;
- Phase 6 footer asset readiness: success;
- homepage AtlasField production smoke: success;
- System Symphony live topology and 32-bar loudness smoke: success;
- corpus refresh: HTTP `202`.

Production artifacts:

- homepage AtlasField smoke `8796533559`, digest `sha256:54c09b90299028b9d33475cba04d59757fe5ffa14c491416a7a27682330b7724`;
- System Symphony smoke `8796675029`, digest `sha256:becd326962434a44b15d80977153e6dc8465e3e5be30a57a300f6ba711b967b3`.

## Closure state

Phase 10 is complete.

The active publication contract is now:

1. `atlas-article-gen` creates and validates deterministic generated article output.
2. `atlas-scheduler` validates the classic footer, computes sequence and series state, owns publication timing, and remains the only write path into published Writing output.
3. `atlas-systems` validates the committed consumer inventory, serves the published output, and records browser and production evidence.
4. Publication or refresh remains proven only by scheduler execution, exact site commit, deployment success, custom-domain verification, and live-route evidence.

Current repository heads at closure include later unrelated W-08 image work and its queue sync:

- `atlas-infra/main`: `44e7e15cbc9f9071c1886d0d86260bcafcc97c14` before this closeout change;
- `atlas-article-gen/main`: `6f2d432bc1fbd3510679601524df405de25222d4`;
- `atlas-scheduler/main`: `d9abcf0843c1663181dd6d74bcf06b89255ff2cd`;
- `atlas-systems/main`: `4896b1c482d89f8b7968ec0baee5763e36843342`.

The W-08 image update and resulting queue sync are not publication evidence and are not part of the Phase 10 architecture decision.

## Next programme stage

Phase 11 begins with a fresh Part 0 inspection. It owns Lab interaction polish and the remaining declared legacy-console exception. It must inspect current repository and deployed state rather than reuse Phase 10 assumptions or preview artifacts.
