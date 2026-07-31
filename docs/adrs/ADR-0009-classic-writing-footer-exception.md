+++
id = "ADR-0009"
date = 2026-07-29
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-systems"]
services = []
contracts = ["atlas-control-plane/public-interface-footer-extension/v1"]
policies = ["policy/public-interface-footer-extension-v1.json"]
+++

# ADR-0009: Preserve the classic Writing article footer as a bounded exception

Amended 31 July 2026 after the Phase 10 editorial-surface review.

## Context

ADR-0008 and the Phase 6 footer extension define normal estate, product, tool, and editorial footers through the `atlas-interface-kit v0.4.0` slot contract.

The completed Writing rollout produced a different owner-approved result. W-01 through W-07 use a compact `<div class="article-footer">` containing scheduler-owned previous and next links, or `Latest article`. Atlas explicitly approved that structure and rejected adding an editorial identity row, Writing-index row, estate-escape row, `.atlas-footer` wrapper, or `.atlas-footer__sequence` wrapper.

The earlier compatibility layer accepted both that classic shape and a semantic editorial profile. Phase 10 confirmed that no current published or queued article consumes the semantic profile, while retaining two active profiles increases the chance of future generator, preview, or scheduler drift.

The contract must therefore match the accepted Writing output without weakening the normal footer system, inventing another interface-kit variant, hand-editing generated article output, or transferring the exception to unrelated surfaces.

## Decision

Atlas Systems accepts one non-transferable intentional difference named `classic_writing_articles`.

It applies only to Writing article pages owned by the three-repository publication pipeline:

- `AtlasReaper311/atlas-article-gen` owns the article shell and exactly one scheduler placeholder;
- `AtlasReaper311/atlas-scheduler` owns previous and next labels, sequence calculation, preview simulation, publication, and the only write path into `atlas-systems`;
- `AtlasReaper311/atlas-systems` contains the published pages but does not hand-edit their generated footer output.

The classic structure is the sole active footer profile for current and future Atlas Systems Writing articles. W-01 through W-07 permanently retain it, and future generated articles use the same profile unless a later accepted ADR explicitly replaces this decision.

The accepted classic structure is:

```html
<div class="article-footer">
  <!-- exactly one scheduler-owned footer placeholder in generated output -->
</div>
```

Published content is limited to scheduler-owned previous and next article links, or `Latest article`.

The classic profile must not contain:

- `.atlas-footer`;
- `.atlas-footer--editorial`;
- `.atlas-footer__identity`;
- `.atlas-footer__context`;
- `.atlas-footer__sequence`;
- `.atlas-footer__estate-escape`;
- `.atlas-footer__escape`.

The previous semantic Writing footer remains only in historical bundles, receipts, and repository history where it records completed experiments or rollback evidence. Those artifacts must not be rewritten, but they are not accepted active generator input, preview input, refresh output, or publication input. No active workflow may generate or apply that profile.

This exception does not alter the normal estate, product, tool, or editorial variants. It cannot be claimed by a product, tool, Lab route, index page, error page, or other estate surface.

No new `atlas-interface-kit` variant or release is created. `v0.4.0` remains the immutable implementation release for normal Phase 6 footer adoption and for the non-footer shared interface assets referenced by generated Writing pages.

## Validation and rollout

`atlas-infra` validates the exception scope, exact classic structure, ownership, non-transferability, and absence of a new interface-kit variant.

`atlas-article-gen` must:

- emit exactly one classic `article-footer` container;
- place exactly one scheduler placeholder inside it;
- forbid semantic Writing footer wrappers and named slots;
- retain the classic profile in generated preview fixtures and authoring guidance.

`atlas-scheduler` must:

- accept only the classic Writing profile for active queue, preview, shell-refresh, and publication paths;
- replace only the scheduler placeholder or preserve only the scheduler-owned rendered sequence;
- reject semantic, mixed, bare-placeholder, duplicate, or otherwise malformed footer input;
- preserve historical semantic bundles and receipts as immutable evidence without exposing an active migration workflow that can recreate them.

A permissive legacy bypass is not sufficient.

No generated article HTML, metadata, publication date, queue state, provider setting, secret, deployment, or production scheduler execution is authorized by this decision alone. Source changes require repository-native validation. Browser-facing preview evidence is required before the final generator and consumer-facing contract is merged.

## Consequences

The accepted policy matches all current Writing output and removes an unused active compatibility branch.

Historical W-01 through W-07 remain visually and structurally unchanged.

Future Writing articles retain the same compact sequence-only footer, so generator output, targeted preview, scheduler publication, and live articles share one fail-closed contract.

Historical semantic experiments remain available as evidence, but cannot be reintroduced through an active workflow by accident.

The normal footer variants remain available through `atlas-interface-kit v0.4.0`, and unrelated consumers cannot use the Writing exception to avoid identity or estate-escape requirements.
