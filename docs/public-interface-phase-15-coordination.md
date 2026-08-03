# Public interface programme Phase 15 coordination

Status: active; Part 0 inspection complete and programme freeze established.

Started: 3 August 2026.

## Purpose

Phase 15 closes the Atlas Systems public interface programme from current
repository, release, deployment, live-route, generated-output, and residual
finding evidence.

This is a controlled reconciliation and closeout phase. It introduces no new
feature scope, does not revive superseded branches, and does not convert
unrelated maintenance pull requests into programme dependencies.

## Accepted authority

Phase 15 follows:

1. current GitHub repository files, branches, pull requests, commits, checks,
   Actions runs, and release records;
2. accepted ADRs and executable public-interface policy in `atlas-infra`;
3. current phase coordination and deployment receipts;
4. repository-owned source, validation, preview, deployment, and generated-output
   contracts;
5. live endpoints and independent deployment evidence when production state
   matters;
6. `AGENT.md` as the stable operating map.

The programme register defines the Phase 15 outcome as freeze,
dependency-ordered merge, deployment verification, and closeout. Every remaining
production merge, release, publication, workflow dispatch, provider write, or
secret operation requires its own explicit authority. Starting Phase 15 does not
approve unrelated open pull requests.

## Current repository baseline

| Repository | Current main SHA | Phase 15 role |
| --- | --- | --- |
| `atlas-infra` | `d61e0f8fa36df09c8ba10e76dacc59c8bca4a4fa` | Programme authority, phase receipts, policy, and final closeout. |
| `atlas-systems` | `1cc32599ce1ab8630a62b013e939941f0ca4ce1a` | Primary product and accepted browser-budget enforcement. |
| `atlas-interface-kit` | `c38b5b3edd631999dfad838c4fb70e505a9860cf` | Immutable interface release and shared implementation evidence. |
| `status` | `4db1438b1a8859008461903105360a2f09376c02` | Independently deployed operational product. |
| `atlas-doc-viewer` | `2b03d5843588f0415ecc735f6b33ca7527063137` | Independently deployed CV viewer. |
| `ramone-edge` | `3830dd3839847187e0b5ac6c837a5658f5f47341` | Independently deployed browser product and protected edge runtime. |
| `atlas-api-public` | `4a4d575bf673a272447c40ec42a14c8be01101f8` | Public API projection and human documentation. |
| `atlas-api-index` | `96cd81f643429895847a1c2f143084d6e995005c` | JSON-only fail-closed registry verification. |
| `atlas-article-gen` | `57659c5256048c0bef22d99bce608aac7ff38a91` | Canonical article authoring, parser, and generated-draft authority. |
| `atlas-scheduler` | `2432c168e2ed9da252ec5d5973ab45e62e10ca6c` | Publication timing, sequencing, and sole write path into `atlas-systems`. |

GitHub does not expose another operator's local worktree state. This record binds
remote source truth only; any later source branch must still inspect its own
checkout before editing.

## Programme state entering Phase 15

| Phase group | State entering Phase 15 | Evidence authority |
| --- | --- | --- |
| Phases 0 through 5 | complete | Programme authority, System Symphony baseline, browser evidence harness, cross-product evidence, immutable interface-kit release, and main-site adoption records. |
| Phase 6 | complete | Footer authority, kit primitive, generator and scheduler ownership, consumer adoption, deployment, and live verification records. |
| Phase 7 | complete | Metadata, browser identity, supporting-product error behaviour, article refresh, deployment, and live receipts. |
| Phase 8 | complete | Measured accessibility and responsive corrections with browser evidence and production verification. |
| Phase 9 | complete | Reliability, Observability, and Evidence detail surfaces with exact deployment and live smoke. |
| Phase 10 | complete | Article reading, Writing directory, generator, scheduler, publication, and live consumer receipts. |
| Phase 11 | complete | Four Lab slices, exact preview evidence, production runs, and live keyboard smoke. |
| Phase 12 | complete | CV, Status, Ramone, Public API docs, and JSON-only API index receipts. |
| Phase 13 | complete | Accepted AtlasField composition catalogue, fingerprinted policy, validator, and tests. |
| Phase 14 | complete | Accepted browser resource authority, 28-measurement enforcement, exact deployment `30799529583`, custom-domain proof, deploy-watch success, live smoke, and Corpus refresh. |

## Phase 14 transition receipt

Phase 14 closed with:

- authority pull request `atlas-infra#119` merged as
  `d61e0f8fa36df09c8ba10e76dacc59c8bca4a4fa`;
- enforcement pull request `atlas-systems#196` reviewed at
  `376ad78a4b36169cbb37e19f885d1b8c4bade8f5` and merged as
  `1cc32599ce1ab8630a62b013e939941f0ca4ce1a`;
- preview run `30798375945` with 28 expected measurements, 28 observed
  measurements, zero budget violations, and zero blocking interface findings;
- production run `30799529583` proving the exact custom-domain commit and all
  repository-owned production checks;
- independent deploy-watch deployment
  `50929bca-e74d-4491-aacb-13581c5db991` with status `success`;
- guarded Corpus refresh completion.

## Open pull-request and overlap inspection

The following open work was found at Phase 15 start. None is silently adopted by
this programme.

| Repository and PR | Classification | Phase 15 treatment |
| --- | --- | --- |
| `atlas-systems#179` | stale, conflicting Phase 8-era draft | Excluded. Do not reuse, merge, or mine as current authority. |
| `atlas-infra#112` | draft RAMONE read-model publisher | Separate programme and provider-write boundary. Excluded from public-interface closeout. |
| `atlas-infra#105` | paused W-09 allocation work | Separate paused work. Excluded. |
| `atlas-doc-viewer#34`, `status#36`, `ramone-edge#33`, `atlas-api-public#55` | current Dependabot maintenance | Normal dependency governance, not a public-interface programme dependency. |
| Older Dependabot pull requests in supporting products | maintenance and possible supersession candidates | Do not merge as part of Phase 15. Resolve under dependency policy separately. |
| `atlas-api-public#53` | automated public repository inventory refresh | Data-refresh ownership, not interface closeout. Excluded. |
| `atlas-api-public#5` | old draft RAMONE public-tools work | Explicit runtime and deployment cutover gate. Excluded. |

No Phase 15 implementation branch exists in a product repository. Current
programme source changes should be limited to closeout evidence unless the audit
proves a missing accepted obligation.

## Programme freeze

From Phase 15 start:

- no new interface feature scope may be introduced;
- no route-specific product identity may be flattened for closeout convenience;
- no generated article HTML or metadata may be hand-edited;
- no new interface-kit release may be created merely to tidy the programme;
- no stale or unrelated pull request may be merged into the closeout path;
- no reporting-only finding may be relabelled as fixed without source and live
  evidence;
- no merged source may be treated as deployed without exact workflow and live
  proof;
- no provider, binding, secret, inference, scheduler, or publication action may
  be inferred from the programme start approval.

## Residual finding register at start

The latest complete `atlas-systems` browser cycle retains 20 reporting-only
findings:

1. Lab directory card-signature coverage reports 21 of 22 at several viewports.
2. The Sonin article retains the known YouTube/CSP console report.
3. Estate Conformance retains its reviewed console `Error` report.
4. Shape Detector retains its reviewed console `Error` report.

Phase 15 must determine whether each family is:

- intentional and accepted with rationale;
- assigned to a named follow-up outside the closed programme;
- obsolete after current live verification;
- or a missing completion obligation requiring a focused correction before
  programme closure.

Resource budgets themselves have no residual violation.

## Part 0 findings

1. Phases 0 through 14 have source and coordination records; Phase 14 now also
   has exact deployment and independent live-state receipts.
2. The programme register and work-allocation entry are stale and still describe
   Phase 5 and Phase 14 as active. They require correction before final closure.
3. Current open pull requests are maintenance, paused, stale, or separately
   gated. There is no dependency-ordered programme merge queue waiting to be
   executed.
4. Supporting-product Phase 12 production receipts are already recorded and do
   not require redeployment merely for Phase 15.
5. Article generator and scheduler ownership remains protected. No article
   refresh or publication is required unless the final audit proves generated
   output drift.
6. The post-programme cross-page conformance audit remains paused in work
   allocation and becomes the principal Phase 15 live audit after this start
   record is accepted.

## Phase 15 execution plan

### 15A: receipt and dependency reconciliation

Inspect accepted phase coordination records and current repository state to
produce one matrix that distinguishes:

- authority accepted;
- source merged;
- release published;
- consumer adopted;
- preview passed;
- production deployed;
- exact production commit verified;
- live browser evidence passed;
- generated content refreshed where required;
- rollback recorded.

Missing evidence must remain `unknown` until proved. Do not infer one state from
another.

### 15B: post-programme cross-page conformance audit

Run a fresh read-only audit across current live browser-facing products,
beginning with:

- `atlas-systems` primary, Systems, Lab, Work, Writing, and representative
  article routes;
- Status;
- CV viewer;
- Ramone;
- Public API documentation;
- the JSON-only API index contract.

Inspect global navigation, active-route treatment, Lab and Systems context
navigation, route labels, breadcrumbs, search and footer behaviour, spacing,
heading hierarchy, canonical card destinations, responsive behaviour, keyboard
focus, serious accessibility findings, page errors, failed requests, and
accidental cross-page drift. Preserve intentional product identities.

The audit is evidence first. Any source correction must be isolated in a fresh
repository-specific branch and pass its own approval, preview, merge, deployment,
and live-verification gates.

### 15C: residual finding disposition

Record each reporting-only family with owner, rationale, next action, and whether
it blocks closure. Do not hide a finding by deleting its baseline signature.

### 15D: final closeout

After 15A through 15C:

- update this coordination record with exact evidence;
- update `docs/public-interface-programme.md` to the final state;
- move Phase 15 and the post-programme audit to completed work;
- record final rollback points and intentional differences;
- confirm no unapproved release, publication, deployment, provider, binding, or
  secret action occurred;
- close the programme only when the completion definition is proved.

## Validation for this start record

The coordination branch must pass the current `atlas-infra` contract registry,
public-interface policy, documentation, unit, CodeQL, and OpenSSF checks. It
changes authority and coordination documents only.

## Security and privacy review

Phase 15 start performs read-only repository inspection and documentation
coordination. It requests no secrets, performs no provider configuration change,
changes no bindings, sends no inference request, runs no scheduler publication,
and alters no product runtime.

## Risks

- The historical programme document contains stale current-state prose from
  Phase 5. Phase 15 must correct it without erasing the dated original rebaseline.
- Open maintenance PRs may move while closeout runs. They remain outside scope
  unless a current programme contract explicitly depends on them.
- The residual browser findings may be harmless or may expose a real final gap.
  Their disposition requires current live evidence, not memory.
- A final live audit can discover a source defect. That would pause closeout at a
  focused correction gate rather than widen Phase 15 into a redesign.

## Current approval boundary

This branch may record the completed Phase 14 receipts, establish the Phase 15
freeze, and begin the read-only Phase 15 reconciliation and live conformance
audit.

No unrelated pull-request merge, interface-kit release, article publication,
scheduler production run, supporting-product redeployment, workflow dispatch,
provider change, binding change, or secret operation is authorised by this
start record.
