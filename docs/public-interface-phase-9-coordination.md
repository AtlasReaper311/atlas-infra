# Public interface programme Phase 9 coordination

Status: active. Part 0 inspection complete. Source and isolated preview approved for merge; production rollout remains separate.

Recorded: 30 July 2026.

## Outcome

Phase 9 will make the three focused Systems detail routes analytically stronger and easier to scan without changing their evidence sources, public API boundaries, runtime decisions, or accessibility foundations.

The intended relationship is explicit:

1. Observability answers what is happening now.
2. Reliability answers whether the measured behaviour supports the reliability claims.
3. Evidence answers what records prove the public claims.

## Current repository state

- `atlas-systems/main`: `ede5b95874ace4154d6a6f8f8370892d6476e172`.
- Current main includes the completed Phase 8 correction, the route cleanup, and the restored dedicated Blackbox route.
- Phase 9 implementation branch: `refactor/systems-detail-surfaces`, to be created from the exact current main commit.
- No current Phase 9 implementation commit, preview, or pull request existed at inspection time.
- Draft pull request `atlas-systems#179` is stale, diverged, and not mergeable. It must not be reused, rebased into Phase 9, or merged.
- No open pull request was found that overlaps the Reliability, Observability, Evidence, or proposed Phase 9 stylesheet paths.

## Evidence inspected

- current `atlas-systems` default branch and recent commits;
- `systems/reliability/index.html`;
- `systems/observability/index.html`;
- `systems/evidence/index.html`;
- `static/css/systems-focus.css`;
- `static/js/focused-systems-shell.js`;
- `static/js/secondary-surface-fields.js`;
- `static/js/atlas-field-composition-registry.js`;
- current page scripts and their fixed public endpoint boundaries;
- pull request and preview workflows;
- repository-native validation commands;
- ADR-0008 and the accepted public-interface foundation extension;
- Phase 8 closeout receipts and current Work Allocation state.

## Measured problem

The three pages already preserve sound public data boundaries, honest stale and unknown states, fixed allowlists, semantic dense-data wrappers, and exact-route AtlasField compositions.

The remaining problem is presentation. Each page uses a long sequence of nearly identical hero, summary, section heading, table, list, and source rail blocks. The repetition weakens analytical hierarchy and obscures the relationship between observation, reliability evaluation, and proof.

## Accepted implementation boundary

Phase 9 may change:

- semantic breadcrumb presentation on the three hierarchical routes;
- page purpose and evidence-boundary presentation;
- a shared three-question Systems detail sequence;
- section order and visual hierarchy;
- source and freshness explanation;
- responsive ordering;
- table and provenance placement;
- related Status and Lab route placement;
- a repository-local Phase 9 stylesheet;
- route-specific hierarchy tests and implementation documentation.

Phase 9 must preserve:

- all existing endpoint URLs and request methods;
- fixed field allowlists and `textContent` rendering;
- stale, malformed, unavailable, unmeasured, and insufficient-evidence semantics;
- current dynamic element identifiers used by route scripts;
- no broad provider-response rendering;
- no internal route, credential, or private repository disclosure;
- current table semantics and dense-data overflow behaviour;
- current footer installation and tool variant;
- exact-route AtlasField composition names, seeds, host selector, pointer transparency, and reduced-motion behaviour;
- System Symphony, Writing, publication, provider, binding, secret, and deployment contracts.

## Branch and pull request plan

1. Create `refactor/systems-detail-surfaces` from exact `atlas-systems/main`.
2. Refactor all three HTML entrypoints while preserving script-owned IDs and public source boundaries.
3. Add one Phase 9 stylesheet layered after the existing Systems foundation stylesheet.
4. Add focused contract tests for hierarchy, breadcrumbs, route sequence, preserved IDs, and AtlasField host continuity.
5. Add a concise repository implementation record.
6. Run repository-native validation.
7. Fetch current main, rebase if required, rerun validation, and inspect every changed path.
8. Open one draft pull request unless the final measured diff becomes too difficult to review.
9. Stop before adding `interface-preview-approved`, publishing a preview, merging, deploying, or changing any provider state.

## Approval boundary

This coordination record authorises source preparation on a fresh branch only. It does not authorise preview publication, pull request merge, production deployment, provider writes, workflow dispatch, article publication, secret changes, or any modification of stale pull request #179.
