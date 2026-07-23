+++
id = "ADR-0008"
date = 2026-07-23
status = "proposed"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-doc-viewer", "AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-systems", "AtlasReaper311/ramone-edge", "AtlasReaper311/status"]
services = []
contracts = ["atlas-control-plane/public-interface-surface/v1"]
policies = ["policy/atlas-owned-domains.json", "policy/browser-icons-v1.json", "policy/public-interface-contract.json"]
+++

# ADR-0008: Extend the public interface into a governed design system

## Context

ADR-0007 established the first Atlas Systems public interface contract. It standardised global navigation, estate search, aggregate status presentation, browser icons, metadata, link behaviour, focus treatment, responsive safeguards, generated-page ownership, and repository-local assets across independently deployed public surfaces.

That contract solved the most visible estate-wide drift without forcing every product into one template or introducing a remote runtime stylesheet. The independent deployment and product-identity decisions remain sound.

The completed implementation also exposed a second class of drift. Work, Writing, Lab, Status, Ramone, Public API Docs, CV, generated articles, and specialist Lab tools still define many of the same inner interface concerns independently:

- page introductions and product strips;
- spacing and type scales;
- cards, metrics, tags, badges, and filters;
- buttons and action labels;
- loading, empty, unavailable, unknown, and error states;
- tables, dialogs, and footers;
- maturity, publication, deployment, and runtime vocabulary;
- responsive evidence and visual conformance.

The current Brand Reference provides a strong visual foundation but is not yet a complete executable token and component contract. The current public-interface policy governs outer behaviour but does not yet govern information hierarchy, public terminology, component roles, or route organisation.

A universal template remains inappropriate. Status is an operational evidence surface, Ramone is a conversational product, Writing is editorial, API Docs is contract-derived documentation, CV is a protected document viewer, and the Lab contains purpose-specific instruments. Cohesion must not erase those interaction models.

A remote shared presentation asset also remains inappropriate. It would couple independent deployments at runtime, complicate Content Security Policy, and create an estate-wide presentation failure mode.

## Decision

Atlas Systems extends ADR-0007 with a versioned Public Interface System v2 owned by `atlas-infra`.

The v2 system governs shared interface grammar rather than one universal layout. It will define:

- an expanded executable design-token contract;
- controlled public terminology and state vocabulary;
- a default page-information hierarchy;
- canonical component roles and a bounded set of variants;
- route-type and maturity labels;
- responsive and accessibility evidence requirements;
- conformance validators for adopted repositories.

### Distribution

Canonical token and component sources are owned by `atlas-infra` and distributed as deterministic, versioned, repository-local copies.

Public surfaces must not load shared presentation CSS or JavaScript from another Atlas Systems deployment at runtime. Every surface remains independently deployable and usable when another presentation surface is unavailable.

Generated copies must carry a version or fingerprint that repository-native tests can verify. Product repositories retain ownership of their semantic markup, purpose-specific CSS, JavaScript, and interaction logic.

### Public vocabulary

The v2 policy will distinguish at least:

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

These terms are evidence-bearing labels and must not be used as decorative synonyms.

Maturity and runtime state remain separate concepts. For example, a production product may be unavailable, while an experiment may currently be operational.

### Page hierarchy

Unless a route-specific contract states otherwise, public pages follow this order:

1. global Atlas Systems header;
2. product or section identity;
3. eyebrow, identifier, or route type;
4. page title;
5. concise purpose;
6. primary state or action;
7. main content;
8. supporting evidence and metadata;
9. purpose-specific footer and estate escape.

Purpose-specific interfaces may vary inside the main content region. Deviations from identity, purpose, state, and escape-route order require documented evidence.

### Component roles

The initial v2 component contract will cover:

- global header;
- product strip;
- page introduction;
- section heading;
- primary and secondary actions;
- text actions;
- status chips;
- type and maturity badges;
- metric grids;
- standard, editorial, data, and interactive card roles;
- tag lists and filter bars;
- table wrappers;
- search dialogs;
- loading, empty, unavailable, unknown, and error states;
- purpose-specific footers.

The contract limits variants to those needed by real route types. It does not require identical markup or forbid product-specific visualisations, media controls, conversational controls, or technical evidence layouts.

### Route organisation

The primary header remains Work, Writing, Lab, and About.

The estate adds a human-readable `/systems/` directory rather than placing every public destination in the global header. The directory lists only intentionally public human-facing routes and groups them as Portfolio, Products, and Engineering interfaces.

The directory must not expose private components from the public estate manifest or infer live state without bounded evidence.

The Lab landing page adopts a public taxonomy that distinguishes observation, verification, experiences, and exploratory work. Maturity labels remain separate from runtime evidence.

### Publishing boundary

Generated article component changes originate in `atlas-article-gen`, pass through `atlas-scheduler`, and reach `atlas-systems` only through the established publication or bounded refresh path.

The v2 design system does not permit hand-editing generated article HTML, bypassing scheduler ownership, changing publication timing, or treating a generator build as proof of publication.

### Evidence

Adopted routes must produce repository-native conformance evidence for:

- token and component versions;
- approved terminology where machine-checkable;
- keyboard and focus behaviour;
- reduced motion;
- heading and landmark structure;
- loading, empty, unavailable, unknown, and error states;
- representative viewport widths of 320, 375, 768, 1024, and 1440 pixels;
- route-specific preserved behaviour.

Visual comparison evidence supports review but does not replace semantic, accessibility, or repository-native tests.

### Protected product identity

The v2 contract preserves:

- Work galleries and audio evidence;
- Writing editorial typography and scheduler-owned structure;
- Lab instruments and visualisations;
- Status evidence density and bounded state semantics;
- Ramone conversation and inference behaviour;
- Public API Docs OpenAPI authority;
- CV document gate;
- System SYMPHONY audio behaviour.

## Consequences

The estate gains a common inner interface grammar in addition to the accepted outer shell. Visitors should encounter consistent hierarchy, terminology, controls, states, spacing, and escape routes while each product retains a recognisable purpose.

The new `/systems/` directory improves discoverability without crowding the primary header or duplicating the system map.

Repository-local distribution preserves independent deployment, CSP boundaries, rollback, and offline validation. It also creates maintenance work: each adopted repository must receive and verify versioned generated assets when the contract changes.

A change to public terminology, tokens, or canonical component roles becomes an interface-contract revision rather than an informal local styling choice.

The policy and validators will become more opinionated. They must remain bounded to shared roles and must not reject justified product-specific behaviour merely because markup differs.

Implementation requires staged previews and one-surface-at-a-time rollout. An accepted ADR, merged asset package, or green preview does not prove production deployment.

The proposed route and component changes remain unapproved until this ADR is reviewed and moved from `proposed` to `accepted`.
