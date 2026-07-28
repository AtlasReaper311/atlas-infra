# Public interface programme Phase 4 authority extension

Status: accepted source authority on the Phase 4 Gate 4A branch. Merge remains separately approval-gated.

## Purpose

This record converts measured Phase 2 and Phase 3 evidence into a bounded additive authority extension for Public Interface System v2.

It does not redesign the interface system, weaken existing tokens, update a consumer, publish an interface-kit release, or authorize production rollout.

## Evidence basis

The extension is grounded in:

- `AtlasReaper311/atlas-systems#168`, which established route-derived evidence across the main browser estate;
- `docs/public-interface-phase-3-closeout.md`, which recorded 70 cross-product cases with no P0 findings, no P1 findings, and no blocking failures;
- reporting-only findings covering horizontal overflow, focusability of local scroll regions, route context, announcement coverage, and 1920-pixel observation.

The Status and Ramone touch-target findings do not create a new token decision. The existing 44-pixel minimum remains authoritative and those findings belong to later consumer correction.

## Authority model

The base authority remains:

- `docs/adrs/ADR-0008-public-interface-system-v2.md`;
- `policy/public-interface-system-v2.json`;
- `policy/public-interface-contract.json`.

The additive measured extension is:

- `policy/public-interface-foundation-extension-v1.json`;
- `contracts/v1/public-interface/public-interface-foundation-extension.schema.json`.

The extension has its own `1.0.0` version so the accepted `2.0.0` base policy is not silently rewritten. `atlas-interface-kit` must implement both contracts in its proposed `0.3.0` release.

## Breadcrumb navigation

Breadcrumbs are an optional shared role for hierarchical human-facing routes.

Required semantics when used:

- a labelled `nav` landmark;
- an ordered list;
- meaningful link text;
- the current page represented as text or marked with `aria-current="page"`.

Breadcrumbs are forbidden on the homepage and are not required for JSON APIs, health endpoints, registry responses, or purpose-specific experiences where they duplicate primary navigation.

Consumers retain route selection, labels, and product-specific presentation.

## Transition-driven announcements

A separate optional status-announcement role is accepted.

Default semantics:

- `role="status"`;
- `aria-live="polite"`;
- `aria-atomic="true"`.

Announcements occur only after meaningful user-visible state transitions. Initial polling, unchanged polling, and routine refreshes remain silent.

`role="alert"` is reserved for immediate blocking failures.

The global header status remains `aria-live="off"`. Consumer repositories own wording and trigger logic. Shared runtime JavaScript is prohibited.

## Dense-data overflow

The existing table-wrapper role is extended to cover tables, code, preformatted output, and dense data regions.

When a region actually overflows it requires:

- an accessible name;
- keyboard focus;
- the standard visible-focus treatment;
- local horizontal scrolling.

When no overflow exists, an unnecessary tab stop is forbidden.

Consumers retain content, rendering, and dynamic overflow detection.

## 1920-pixel evidence

The blocking viewport matrix remains:

- 320;
- 375;
- 768;
- 1024;
- 1440 pixels.

`1920` is accepted as reporting-only evidence coverage.

It is not:

- a breakpoint;
- a layout token;
- a blocking performance budget;
- permission to widen standard content;
- a reason to redesign a passing route.

## Distribution boundary

The intended implementation target is `atlas-interface-kit` `0.3.0`.

Merging this authority does not:

- change interface-kit source;
- create a tag;
- publish a GitHub Release;
- update a consumer;
- deploy a public surface;
- change provider settings or secrets.

Each later action remains separately approval-gated.

## Excluded work

Phase 4 Gate 4A excludes:

- footer slots and variants;
- consumer touch-target remediation;
- colour, spacing, typography, or breakpoint token changes;
- consumer source changes;
- provider settings and secrets;
- runtime routing;
- model or inference behaviour.

## Rollback

Revert the authority pull request.

No provider rollback, consumer rollback, deployment rollback, data migration, secret rotation, or publication rollback is required because this gate changes source authority only.
