# Atlas Systems public interface contract

## Purpose

This contract defines the shared browser-facing foundations for approved public Atlas Systems HTML surfaces. It standardises navigation, status presentation, search, metadata, browser icons, link behaviour, focus treatment, mobile wayfinding, and generated-page ownership without forcing every product into one visual template.

The contract applies only to intentionally public, human-facing HTML surfaces. Machine-facing JSON, health, metadata, topology, reliability, badge, OpenAPI, and telemetry responses remain outside the visual contract.

## Ownership model

`atlas-infra` owns this contract and its validators. Each product repository owns its local semantic markup, CSS, JavaScript, and product identity. Browser assets are copied into each deployed surface from the canonical package in `AtlasReaper311/atlas-systems: favicon_io/` and verified against the checksum manifest.

Runtime loading of a shared stylesheet or script from another Atlas Systems deployment is prohibited. Every public surface must remain independently deployable and usable when another surface is unavailable.

## Required global header

Every public HTML interface must expose:

- the Atlas Systems wordmark linked to `https://atlas-systems.uk/`;
- Work, Writing, Lab, and About links;
- estate search;
- a compact status indicator on every non-homepage surface.

The homepage keeps its existing live-state treatment and must not receive a duplicate status indicator.

The current route must use `aria-current="page"` where applicable.

## Status indicator

The status indicator links to `https://status.atlas-systems.uk/` in the same tab.

It consumes only the bounded aggregate fields from `https://api.atlas-systems.uk/v1/stats`:

- `estate.operational`;
- `estate.total_components`;
- `estate.checked_at`.

Labels:

- `checking`: the first request is pending;
- `nominal`: all components are operational and the snapshot is fresh;
- `degraded`: more than half, but not all, components are operational;
- `unavailable`: half or fewer components are operational;
- `unknown`: the response is missing, invalid, failed, or older than 1,200 seconds.

The indicator is not a live region. It must not reproduce the homepage live-state controller or announce every refresh.

## Estate search

Search uses a versioned repository-local implementation. It must remain keyboard-operable, restore focus after closing, trap focus while open, expose loading and unavailable states honestly, and avoid unsafe cross-origin script or stylesheet dependencies.

Production consumers use `https://api.atlas-systems.uk/v1/search` as the primary search endpoint. Local development may use the local corpus service.

## Link targets

Links to approved Atlas-owned domains open in the same tab. External destinations open in a new tab and include `rel="noopener noreferrer"`.

Atlas-owned domains are declared in `policy/atlas-owned-domains.json`. A subdomain is not external merely because another repository deploys it.

## Browser icons

Every independently deployed HTML surface must expose local copies of:

- `favicon.ico`;
- `favicon-16x16.png`;
- `favicon-32x32.png`;
- `apple-touch-icon.png`;
- `android-chrome-192x192.png`;
- `android-chrome-512x512.png`;
- `site.webmanifest`.

The canonical package is `AtlasReaper311/atlas-systems:favicon_io/`. Deployed manifests must use the Atlas background and theme colour `#0a0a0f`.

## Metadata

Indexable pages require:

- a descriptive title;
- meta description;
- canonical URL;
- theme colour;
- complete local icon declarations;
- Open Graph type, title, description, URL, site name, image, image dimensions, and image alt;
- equivalent Twitter card metadata.

The CV landing page must use `noindex, follow`. The 404 page must remain `noindex`.

Generated article metadata must be changed in `atlas-article-gen`, not in published generated HTML.

## Typography and contrast

The shared palette and typography follow the Atlas Systems Brand Reference. `--text-faint` is restricted to decorative or redundant information. Required labels, controls, states, and explanatory metadata use a colour that meets WCAG 2.2 AA for their size and weight.

Long-form article prose uses a 720px maximum measure, 15px base size, and 1.8 line height unless route-specific evidence supports a different value.

## Focus, motion, and touch

Keyboard focus must be visible. The default focus treatment is a 2px amber outline with a 3px offset.

Primary touch targets should be at least 44 by 44 CSS pixels. No required target may be smaller than 24 by 24 CSS pixels.

`prefers-reduced-motion: reduce` disables decorative animation and smooth scrolling without removing textual state or changing audio-system behaviour.

## Contextual navigation

Contextual navigation augments the global header and never replaces it.

On the Lab home page, Ramone remains the first major content experience after the global header. Lab contextual navigation appears beneath the Ramone flagship section.

## Product identity and footers

Independent products may render a compact product identity strip beneath the global header. Footers remain purpose-specific while following shared typography, spacing, focus, ownership, and link-target rules.

## Generated content

`atlas-article-gen` owns generated article HTML and metadata. `atlas-scheduler` owns publication timing, queue state, footer chaining, series navigation, Work-card insertion, and the only production write path into `atlas-systems`.

The interface contract must be applied through those authorities. Generated HTML and scheduler-managed markers must not be hand-edited.

## Validation and rollout

Every affected repository must validate:

- global header presence;
- status indicator presence on non-home surfaces and absence of a duplicate homepage indicator;
- search presence;
- icon declarations and local asset existence;
- metadata completeness;
- Atlas-owned same-tab links;
- safe external new-tab links;
- CV indexing policy;
- reduced-motion and focus treatment;
- generator and scheduler markers;
- unchanged CSP and browser hardening;
- unchanged public/private boundary and operational contracts.

A green pull request proves source validation only. It does not prove production deployment. Preview deployment, merge, and production rollout remain separate evidence states.
