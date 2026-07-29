+++
id = "ADR-0009"
date = 2026-07-29
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-article-gen", "AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-scheduler", "AtlasReaper311/atlas-systems"]
services = []
contracts = ["atlas-control-plane/public-interface-footer-extension/v1"]
policies = ["policy/public-interface-footer-extension-v1.json"]
+++

# ADR-0009: Preserve the classic Writing article footer as a bounded exception

## Context

ADR-0008 and the Phase 6 footer extension define normal estate, product, tool, and editorial footers through the `atlas-interface-kit v0.4.0` slot contract.

The completed Writing rollout produced a different owner-approved result. W-01 through W-07 use a compact `<div class="article-footer">` containing scheduler-owned previous and next links, or `Latest article`. Atlas explicitly approved that structure and rejected adding an editorial identity row, Writing-index row, estate-escape row, `.atlas-footer` wrapper, or `.atlas-footer__sequence` wrapper.

The existing footer validator still treated the normal semantic editorial variant as the only accepted Writing shape. That made the accepted policy disagree with the generator, scheduler, published output, and owner decision.

The mismatch must be resolved without weakening the normal footer contract, inventing another interface-kit variant, hand-editing generated article output, or transferring the exception to unrelated surfaces.

## Decision

Atlas Systems accepts one non-transferable intentional difference named `classic_writing_articles`.

It applies only to published Writing article pages owned by the three-repository publication pipeline:

- `AtlasReaper311/atlas-article-gen` owns the article shell and exactly one scheduler placeholder;
- `AtlasReaper311/atlas-scheduler` owns previous and next labels, sequence calculation, publication, and the only write path into `atlas-systems`;
- `AtlasReaper311/atlas-systems` contains the published pages but does not hand-edit their generated footer output.

W-01 through W-07 permanently retain the approved classic structure.

Current generator output also retains the classic structure until the Phase 10 editorial surface review makes a separate, explicit decision. Phase 10 may retain or replace the profile, but it must not silently rewrite historical articles or infer publication from source changes.

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
- `.atlas-footer__estate-escape`.

This exception does not alter the normal estate, product, tool, or editorial variants. It cannot be claimed by a product, tool, Lab route, index page, error page, or other estate surface.

No new `atlas-interface-kit` variant or release is created. `v0.4.0` remains the immutable implementation release for normal Phase 6 footer adoption.

## Validation and rollout

`atlas-infra` validates the exception scope, exact classic structure, ownership, non-transferability, and absence of a new interface-kit variant.

`atlas-article-gen` must validate the single classic placeholder and forbid semantic editorial footer wrappers in generated article shells.

`atlas-scheduler` must explicitly validate both supported publication inputs:

- the normal semantic editorial footer profile where present;
- the accepted classic Writing article profile.

A permissive legacy bypass is not sufficient.

No generated article HTML, metadata, publication date, queue state, provider setting, secret, deployment, or production scheduler execution is authorized by this decision.

Consumer footer adoption remains separate per-repository work with visual review, merge approval, rollout approval, and live verification.

## Consequences

The accepted policy matches the approved Writing output without weakening the shared footer system.

Historical W-01 through W-07 remain visually and structurally unchanged.

The generator and scheduler gain an explicit fail-closed contract instead of relying on an accidental compatibility path.

The normal footer variants remain available through `atlas-interface-kit v0.4.0`, and unrelated consumers cannot use the Writing exception to avoid identity or estate-escape requirements.
