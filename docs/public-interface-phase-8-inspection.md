# Public interface programme Phase 8 inspection

Status: active at repository-specific draft pull-request preparation.

Recorded: 30 July 2026.

## Authority

Phase 8 implements the programme's measured accessibility and responsive corrections. ADR-0008 keeps minimum contrast, the 44-pixel touch target, visible focus, reduced motion, responsive safeguards, and fixed-navigation clearance non-overridable. Production rollout remains separate from source review.

## Evidence inspected

The inspection covered:

- the current programme and Phase 7 closeout;
- ADR-0008 and the accepted foundation extension;
- current default-branch source, open pull requests, tests, preview workflows, and deployment workflows in the affected repositories;
- the exact Phase 2 `atlas-systems` evidence artifact;
- the exact Phase 3 and Phase 6 Status evidence artifacts;
- the exact Phase 3 and Phase 6 Ramone evidence artifacts;
- current generated and protected ownership boundaries.

## Repository outcomes

### `status`

Current Phase 6 evidence retains 12 P2 target-size reports across Chrome and Firefox. The Phase 6 footer corrected its earlier footer-link findings. The remaining measured controls are the global wordmark, aggregate-status chip, narrow global-navigation labels, and estate-search button.

Draft PR #34 applies a repository-local minimum 44 by 44 pixel target correction to the root and owned 404 routes. It does not alter Status data, polling, reliability, recent activity, search behaviour, status parsing, provider configuration, or secrets.

### `atlas-systems`

The carried evidence families requiring current-source correction are:

- Work and Writing mobile-bottom-navigation clipping at 320 pixels;
- narrow Lab context-navigation overflow;
- Signal Garden inactive-layer contrast;
- The Bearing text and code contrast;
- dense table and preformatted regions that still reproduce the accepted overflow-focus findings;
- route-specific horizontal overflow on Signal Garden, Almost, and Drift.

The current shared semantics layer already supplies the accepted dynamic rule for dense regions: add focus and an accessible name only while overflow exists, then remove both when it does not. Phase 8 must preserve that contract and correct the remaining route integration or timing gaps rather than adding unconditional tab stops.

Console, page-error, and failed-request records remain diagnostic evidence. Phase 8 must not suppress or filter them merely to obtain green output. Each must be traced to the owning route and either corrected from current source or carried explicitly to its owning later phase.

### Measured no-change results

- `ramone-edge`: the Phase 3 footer findings are cleared by the later Phase 6 evidence, which records zero comparable findings and zero blocking failures.
- `atlas-doc-viewer`: the accepted comparable evidence carries no accessibility or responsive correction backlog.
- `atlas-api-public`: the current documentation evidence contract already blocks serious and critical findings, horizontal overflow, missing visible focus, undersized search controls, and bottom-navigation obstruction. Unrelated draft PR #5 is outside Phase 8 and must not be modified.
- `atlas-api-index`: remains intentionally JSON-only and receives no visual change.
- `atlas-interface-kit`: current authority already defines the required target, contrast, overflow, focus, and reduced-motion foundations. No new release is justified by the measured consumer defects.

## Sequence

1. Complete `status` PR #34 source validation and provider-gated browser evidence.
2. Review the resulting findings and correct the branch if required.
3. Stop for merge and deployment approval.
4. Only after the Status evidence gate, open the separate `atlas-systems` accessibility and responsive correction branch.
5. Capture route-derived Chrome and Firefox evidence for every changed route.
6. Return the exact remaining merge, deployment, live-verification, and closeout gates.

## Required post-programme conformance follow-up

After the complete public-interface programme is closed and its final production state is verified, run a dedicated estate-wide cross-page conformance audit. This is a required follow-up, not optional polish.

The audit must compare current deployed surfaces and repository source for:

- global navigation order, labels, active-route state, same-tab Atlas-owned destinations, and mobile treatment;
- Lab and Systems context navigation, route discoverability, overflow, and current-page indication;
- route-context labels and breadcrumbs, removing duplication where they do not improve wayfinding;
- shared shell, search, footer, spacing, heading hierarchy, and interaction behaviour;
- card and status-rail destinations, with anchor jumps replaced by canonical product or evidence routes where appropriate;
- intentional product-specific differences, documented explicitly so visual identity is preserved without accidental drift.

Do not treat this follow-up as part of Phase 8 unless a finding is specifically an accessibility or responsive defect owned by Phase 8. Begin it only after all programme phases, merges, deployments, and live verification are complete, using fresh GitHub and browser evidence rather than remembered page behaviour.

## Protected boundaries

Phase 8 does not authorize:

- article generation, scheduler execution, publication, or hand-editing generated article output;
- Status monitoring, reliability, registry, or activity behaviour changes;
- Ramone inference, private connectivity, wake, rate-limit, or binding changes;
- CV document access or initialization changes;
- API schema, method, data, cache, CORS, rate-limit, or binding changes;
- System Symphony audio or telemetry behaviour changes;
- workflow dispatch, provider configuration, deployment, secret changes, merge, or release without a later explicit gate.

## Rollback

Before merge, close each repository-specific pull request and delete its branch. After an approved consumer merge, rollback requires a reviewed revert, the repository's normal deployment, and live verification of the resulting exact commit.
