+++
id = "ADR-0008"
date = 2026-07-23
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-doc-viewer", "AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-systems", "AtlasReaper311/ramone-edge", "AtlasReaper311/status"]
services = []
contracts = ["atlas-control-plane/public-interface-surface/v1", "atlas-control-plane/public-interface-system/v1"]
policies = ["policy/atlas-owned-domains.json", "policy/browser-icons-v1.json", "policy/public-interface-contract.json", "policy/public-interface-system-v2.json"]
+++

# ADR-0008: Extend the public interface into a governed design system

## Context

ADR-0007 established the first Atlas Systems public interface contract. It standardised global navigation, estate search, aggregate status presentation, browser icons, metadata, link behaviour, focus treatment, responsive safeguards, generated-page ownership, and repository-local assets across independently deployed public surfaces.

That contract solved the outer-shell drift without forcing every product into one template or introducing a remote runtime stylesheet. The independent deployment and product-identity decisions remain sound.

The completed implementation exposed a second class of drift. Work, Writing, Lab, Status, Ramone, Public API Docs, CV, generated articles, and specialist Lab tools still define many of the same inner interface concerns independently:

- page introductions and product strips;
- spacing and type scales;
- cards, metrics, tags, badges, and filters;
- buttons and action labels;
- loading, empty, unavailable, unknown, and error states;
- tables, dialogs, and footers;
- maturity, publication, deployment, and runtime vocabulary;
- route organisation, responsive evidence, and visual conformance.

The Brand Reference provides a strong visual foundation but is not a complete executable token and component contract. The existing public-interface policy governs outer behaviour but not information hierarchy, terminology, component roles, or page organisation.

A universal template remains inappropriate. Status is operational evidence, Ramone is a conversational product, Writing is editorial, API Docs is contract-derived documentation, CV is a protected document viewer, and Lab contains purpose-specific instruments. Cohesion must not erase those interaction models.

A remote shared presentation asset also remains inappropriate. It would couple independent deployments at runtime, complicate Content Security Policy, and create an estate-wide presentation failure mode.

## Decision

Atlas Systems adopts Public Interface System v2 as an extension of ADR-0007.

`atlas-infra` owns governance, schemas, validators, release approval, and the accepted policy in `policy/public-interface-system-v2.json`.

The current ADR-0007 shell contract remains active during migration. Accepting this decision does not claim that current repositories already implement v2, does not merge any product change, and does not authorize a production rollout.

### Public vocabulary

The v2 policy distinguishes:

- project;
- product;
- service;
- tool;
- experiment;
- interface;
- case study;
- article;
- repository;
- merged;
- deployed;
- published;
- operational;
- degraded;
- unavailable;
- unknown.

`Operational` is the healthy public runtime state. `Degraded` means the public function remains available but is impaired. These terms carry evidence and are not decorative synonyms.

Maturity and runtime state remain separate. A production product may be unavailable, while an experiment may be operational.

Public identifiers such as `P-01`, `W-05`, service identifiers, and repository names remain visible where they aid classification, navigation, and traceability.

### Global navigation

The v2 desktop header uses three zones:

- left: Atlas Systems wordmark and aggregate status;
- centre: Work, Writing, Lab, Systems, About;
- right: compact estate search with the keyboard shortcut.

The aggregate status uses a state-only label such as `Operational`, links directly to Status in the same tab, and does not open a local dashboard.

Mobile uses a bottom navigation for Work, Writing, Lab, Systems, and About. The top header keeps the wordmark, aggregate status, and search icon. Fixed navigation must not obscure content or focused controls.

### Systems directory

Atlas Systems adds `/systems/` as a human-readable directory.

It groups visitor-facing destinations as:

- Portfolio;
- Products;
- Engineering tools.

Human-facing destinations are primary. Machine-facing interfaces are available as secondary detail. Private and local components may be described as architecture context but are not presented as public destinations.

Runtime state appears only where it helps a visitor decide whether a live product or tool can be used. The page includes a simplified architecture diagram. The full interactive System Map moves to `/lab/system-map/`.

A retired-item model is reserved, but an empty retired section is not rendered.

### Lab organisation

Lab becomes a directory with flagships instead of one continuous operational console.

Ramone remains the first major experience.

The first migration features:

- System Map as a Tool;
- Proof Chain as a Tool;
- Signal Garden as an Experiment;
- System SYMPHONY as a Preview.

Lab groups are:

- Experience: Ramone, System SYMPHONY, Signal Garden;
- Observe: System Map, Status, Activity, Deployment evidence, DORA metrics;
- Verify: Proof Chain, Estate Conformance, Reliability Trials, API Docs;
- Explore: Shape Detector.

Shape Detector remains an Experiment.

Dense activity, event, deployment, API, DORA, health, and map views move behind cards or dedicated routes. Experiments identify whether their data is live, recorded replay, or simulated.

### Page hierarchy and components

Unless a route-specific contract states otherwise, public pages follow this order:

1. global header;
2. product or section identity;
3. eyebrow, identifier, or route type;
4. page title;
5. concise purpose;
6. primary state or action;
7. main content;
8. supporting evidence and metadata;
9. purpose-specific footer and estate escape.

The initial component contract covers:

- global header;
- product strip;
- page introduction;
- section heading;
- primary, secondary, and text actions;
- status, type, and maturity badges;
- metric grids;
- standard, editorial, data, and interactive card roles;
- tag lists and filter bars;
- table wrappers;
- search dialogs;
- loading, empty, unavailable, unknown, and error states;
- purpose-specific footers.

Product-specific components remain in their owning repository. Experiments may use unusual layouts and expressive motion, but they still require the global header, visible focus, keyboard access, contrast, reduced motion, honest maturity and data-source language, and an estate escape route.

### Work

Work uses selective disclosure.

Each project presents:

- identity;
- primary evidence;
- supporting detail.

Project identifiers remain permanent. Display order is independent from identifier order and article publication order. The planned sections are Featured work, All projects, In development, Experiments, and Retired work, with empty retired sections hidden.

Work limits the first-level technology list to six items, moves full achievement detail into case studies, requires an explicit result statement, links exact public repositories, and uses stable anchors with unique IDs, fixed-header offsets, and anchor tests.

Fully private work is not shown. Work in progress appears only when public evidence exists and the maturity is explicit.

### Writing and publishing

Writing presents Featured, Series, and All writing.

The scheduler remains authoritative for ordering and upcoming visibility. Only the next article or next series is shown in advance. Scheduled cards use month precision. Completed series receive one larger group card while individual articles remain in All writing.

Primary categories are:

- AI Systems;
- Infrastructure;
- Automation;
- Observability;
- Audio Systems;
- Game Development;
- Hardware;
- Engineering Practice.

Secondary tags remain generator-owned. Series position uses `Part 1 of 3`. A separate archive is deferred until approximately 15 to 20 published articles.

Historical visual migration follows the publishing boundary:

- where canonical source exists, regenerate through `atlas-article-gen` and refresh through `atlas-scheduler`;
- where canonical source is absent, use the bounded scheduler shell-refresh path;
- do not rewrite article prose as part of visual migration.

### About

About leads with Systems Engineer, followed by Software and AI Engineer, Audio Systems Specialist, and Game Developer.

It may describe the route from aeronautical engineering in detail, mention the Saltire Scholarship, and remain personal. It does not name the current employer or discuss heritage.

Current public priorities are:

- production-grade automation and governance;
- local AI and grounded retrieval;
- public observability and evidence systems;
- interactive audio systems;
- portfolio-grade infrastructure engineering.

Engineering principles remain on About for now. Public contact methods are email, GitHub, and LinkedIn.

The existing photograph remains and is paired with a lightly animated topology visual with a reduced-motion fallback.

### Visual direction

The shared direction is spacious and editorial while retaining the Atlas Systems dark technical identity.

The token authority defines:

- spacing values of 4, 8, 12, 16, 24, 32, 48, 64, and 96 pixels;
- compact and standard control heights of 32 and 40 pixels;
- a minimum touch target of 44 pixels;
- compact, standard, and editorial card padding of 16, 24, and 32 pixels;
- subtle radii between 4 and 8 pixels.

Body and supporting text increase where needed for readability. One-pixel borders remain important but are combined with spacing and surface depth. Heavy glass effects are prohibited.

Standard cards use no or minimal shadow. Floating UI may use subtle shadow. Flagship experiences may use controlled atmospheric glow.

Amber remains the general brand and interaction accent. Green, red, and blue are semantic by default. Flagships and diagrams may use controlled secondary accents.

DM Serif Display remains for brand and editorial headings. Dense operational tools may use IBM Plex Mono or an approved restrained companion. Ramone and System SYMPHONY may retain stronger product typography while using the shared scale and spacing rhythm.

Standard motion remains restrained. Featured experiences may use more expressive motion with complete reduced-motion behaviour.

Diagrams are encouraged. Decorative imagery outside Work is not a general design device.

### Distribution and ownership

A dedicated `AtlasReaper311/atlas-interface-kit` repository is approved for creation in a later provider action.

`atlas-infra` remains the governance authority. `atlas-interface-kit` will own source CSS, component examples, build tooling, and generated bundles.

Runtime assets remain repository-local. Remote presentation dependencies are prohibited. Bundles carry a version and fingerprint.

Approved interface-kit releases open automated update pull requests across adopted repositories. Visual changes do not auto-merge. Each repository runs its own tests and previews, and receives manual visual approval.

Products may override only allowlisted brand-expression tokens. Focus visibility, semantic state colours, minimum contrast, minimum touch targets, spacing values, base breakpoints, global header behaviour, z-index meanings, and reduced-motion behaviour are not locally overridable.

### Evidence and review

Firefox and Chrome are the required browsers.

Desktop is the primary portfolio experience. Mobile remains required and follows after desktop implementation rather than being omitted.

The standard viewport matrix is 320, 375, 768, 1024, and 1440 pixels.

Every route receives semantic and accessibility checks. Representative route types receive the full standard screenshot matrix. Every changed route receives full screenshots.

Visual changes require manual approval. Minor nonvisual changes may skip manual screenshot review.

Serious accessibility failures block merge, including keyboard traps, missing focus, invalid heading or landmark structure, missing control names, contrast failures, hidden focused elements, and fixed navigation obscuring focus.

Screenshot tests use deterministic fixtures. Live endpoint tests separately verify data contracts.

Substantive portfolio claims, personal narrative, and summary shortening require owner editorial approval before merge.

### Protected identity and rollout

The v2 system preserves:

- Ramone's startup experience;
- the homepage primary hero character;
- Work galleries and audio evidence;
- Writing editorial character and scheduler ownership;
- Lab purpose-specific instruments;
- Status bounded state semantics;
- Public API Docs OpenAPI authority;
- CV document gate;
- System SYMPHONY audio behaviour.

Implementation follows staged previews and repository-level draft pull requests. An accepted ADR, generated bundle, green preview, merged pull request, or successful source sync does not by itself prove a production deployment.

Production rollout remains a separate approved action.

## Consequences

The estate gains a common inner interface grammar in addition to the accepted outer shell. Visitors encounter consistent hierarchy, terminology, controls, states, spacing, navigation, and escape routes while each product retains its own purpose.

The new Systems route improves discoverability without turning the header into a complete service inventory. Lab becomes easier to understand because flagship experiences and deeper tools no longer compete in one continuous page.

Repository-local distribution preserves independent deployment, CSP boundaries, rollback, and offline validation. It also adds maintenance work: each adopted repository must receive and verify versioned generated assets when the contract changes.

Creating `atlas-interface-kit` adds a dedicated implementation repository. This keeps UI build concerns out of `atlas-infra`, but requires release, pinning, update, and rollback rules.

The policy and validators become more opinionated. They must remain bounded to shared roles and must not reject justified product-specific behaviour merely because markup differs.

No current product is declared v2-conformant until its repository-native implementation, preview evidence, merge, deployment, and live verification are complete.
