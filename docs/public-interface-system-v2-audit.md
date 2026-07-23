# Atlas Systems public interface system v2: Phase 0 audit

## Status

This document is a design and information-architecture audit. It does not approve implementation, change a public interface contract, alter provider state, or claim a live rollout.

Audit date: 23 July 2026.

## Purpose

The first public interface programme established a common outer contract across the Atlas Systems public estate: global navigation, estate search, status presentation, browser icons, page metadata, link behaviour, focus treatment, responsive safeguards, and generated-page ownership.

Phase 0 asks a different question:

> Where do the public surfaces still drift in hierarchy, terminology, spacing, components, organisation, and interaction, and which differences are intentional product identity rather than defects?

The goal is not to make every surface look identical. The goal is to make the estate feel designed as one system while preserving the distinct jobs of Work, Writing, Lab, Status, Ramone, API Docs, and CV.

## Evidence inspected

The audit used the current repository state and accepted authority in this order:

1. `AtlasReaper311/atlas-systems` route source, shared shell, sitemap, and current page structures;
2. accepted `ADR-0007` and `policy/public-interface-contract.json` in `AtlasReaper311/atlas-infra`;
3. `AtlasReaper311/atlas-api-public:data/estate.manifest.json` for declared public ownership;
4. current source for Status, Ramone, Public API Docs, and CV;
5. the Atlas Systems Brand Reference;
6. live HTML where it was retrievable during the audit.

The audit does not treat a merged pull request as proof of live deployment. Visual implementation remains blocked until individual preview and rollout evidence exists.

## Current contract versus the proposed v2 scope

The accepted v1 contract already governs:

- the Atlas Systems wordmark and primary routes;
- estate search;
- non-home status indicators;
- same-tab Atlas-owned navigation;
- safe external links;
- repository-local browser icons;
- metadata;
- focus and reduced motion;
- long-form readability;
- product-specific footers;
- generated article ownership.

The proposed v2 scope should extend that contract rather than replace it. It should govern:

- public terminology and state vocabulary;
- page hierarchy and information order;
- design tokens beyond the current colour and typography baseline;
- canonical component roles and permitted variants;
- content organisation and route discoverability;
- maturity labels for tools and experiments;
- responsive verification evidence;
- visual and semantic conformance checks.

## Route and surface audit matrix

Priority meanings:

- `P0`: required before a cohesive-system claim;
- `P1`: high-value improvement after the shared foundation;
- `P2`: useful refinement that can follow the core migration;
- `Preserve`: intentional difference that should remain.

| Surface | Owner | Current purpose | Intentional identity to preserve | Confirmed drift or risk | Recommended change | Priority |
|---|---|---|---|---|---|---|
| `/` | `atlas-systems` | Estate introduction and primary routing | Operational homepage treatment and existing hero identity | The homepage is the natural place to explain the estate, but the wider set of products and engineering interfaces is not exposed as a coherent directory | Add a concise route-by-intent section and link to a new `/systems/` directory; do not duplicate the status controller | P1 |
| `/work/` | `atlas-systems` | Portfolio evidence and completed projects | Galleries, audio evidence, project-specific metrics, case-study links | Each project card presents identity, role, long summary, metrics, full stack, achievements, gallery, audio, and links at the same visual level; taxonomy and action labels vary | Rebuild the project hierarchy into identity, evidence, and supporting detail; standardise taxonomy and action labels; add stable project anchors and a compact project index | P0 |
| `/writing/` | `atlas-systems`, generated and refreshed through the publishing pipeline | Published case studies, series, and scheduled writing | Editorial card treatment, W-number identity, scheduler-owned ordering and states | Published, next, and scheduled material share similar card weight; date and state labels vary; series structure must be inferred from card metadata | Separate Featured, Series, and All writing views; standardise scheduled and published labels; keep scheduler as the only production writer | P0 |
| Published article routes | `atlas-article-gen` -> `atlas-scheduler` -> `atlas-systems` | Long-form technical evidence | Editorial typography, article-specific diagrams and media, scheduler footer and series navigation | Future article shells can be updated centrally, but historical content lacks canonical Markdown and requires bounded scheduler refresh paths | Define v2 article components in the generator; migrate historical shells only through scheduler-owned refresh evidence | P1 |
| `/lab/` | `atlas-systems` | Live estate interfaces, experiments, and operational evidence | Ramone as the first major experience, dense technical instruments, System SYMPHONY identity | The page combines Ramone, signal and reliability cards, system map, activity, event log, pipeline grid, API surface, DORA, and other tools without a single public taxonomy; labels mix technical type, state, and marketing-like descriptions | Organise the landing page into Observe, Verify, Experience, and Explore; add maturity badges with defined meanings; preserve Ramone first | P0 |
| `/lab/proof-chain/` | `atlas-systems` | Bounded source-to-service and ADR proof | Evidence-first graph and fail-closed behaviour | Needs consistent product strip, data-card, empty/error, and action language with other verification tools | Adopt shared verification-tool components without changing graph contracts | P1 |
| `/lab/signal/` | `atlas-systems` | Interactive browser audio and DSP experiment | Purpose-specific audio controls and visualisation | Control labels and state presentation are unique; this is acceptable, but framing and maturity language should align with Lab | Keep the instrument UI; standardise outer shell, maturity badge, instructions, focus, and error states | Preserve / P1 |
| `/lab/anomaly/` | `atlas-systems` | Telemetry-shape replay and analysis | Specialist telemetry controls and evidence display | Product name, route label, and Lab-card label do not consistently communicate the same purpose | Select one public name and use it in the Lab card, product strip, title, and contextual navigation | P0 |
| `/lab/conformance/` | `atlas-systems` | Estate policy and coverage evidence | Dense audit evidence and weighted rules | State and finding labels should align with the public copy contract rather than local terms | Standardise evidence, pass, warning, unavailable, and freshness language | P1 |
| `/lab/reliability/` | `atlas-systems` | Chaos and recovery evidence | Trial-specific detail and reliability evidence | “Reliability”, “trials”, “chaos evidence”, and “passed” describe different concepts but currently appear near each other without a clear hierarchy | Use one product name, one maturity label, and separate current evidence state from tool type | P0 |
| `status.atlas-systems.uk` | `status` | Immediate estate condition and detailed reliability evidence | Operational density, bounded state semantics, activity evidence | The current interface risks presenting detailed evidence before the simple visitor question, “Is the estate working?”; service grouping and action hierarchy need a clearer public structure | Create overview-first hierarchy, then grouped service evidence, freshness, objectives, and recent events | P0 |
| `ramone.atlas-systems.uk` | `ramone-edge` | Grounded public conversational interface | Conversation-first product layout, model and grounding behaviour | Controls, loading, errors, citations, and grounding explanation are locally defined; terminology can diverge from the estate | Preserve conversation layout; align control, state, citation, search, and footer components; add a clear public grounding-boundary explanation | P1 |
| `api.atlas-systems.uk/v1/docs` | `atlas-api-public` | Human documentation rendered from OpenAPI authority | Contract-derived endpoint catalogue and technical density | The page is readable but acts primarily as a long catalogue; endpoint grouping, navigation, copy actions, and public/authenticated distinctions can be clearer | Add group navigation, consistent method badges, copy-path controls, parameter and response components, and a raw OpenAPI link | P1 |
| `cv.atlas-systems.uk` | `atlas-doc-viewer` | Formal CV document gate and viewer | Deliberate PDF initialisation, download path, minimal document framing | Expansion would create duplication with About; only concise document metadata and action clarity are needed | Keep the surface minimal; standardise summary, update date, file metadata, Open CV, Download PDF, and About escape | Preserve / P2 |
| `/404.html` and error routes | route owner | Honest route failure and recovery | Minimal fail-closed presentation | Error, unavailable, empty, and unknown states are implemented independently across products | Define canonical state components and action wording while preserving route-specific detail | P0 |
| Proposed `/systems/` | `atlas-systems` | Human-readable directory of public products, tools, and interfaces | New route, no existing visual identity to preserve | The estate has more public surfaces than the four primary header links can expose without crowding navigation | Add a directory grouped into Portfolio, Products, and Engineering interfaces, with purpose, type, maturity, valid live state, and source links | P1 |

## Cross-estate findings

### 1. The outer shell is coherent, but the inner component vocabulary is not

The accepted contract intentionally allows repository-specific markup and CSS. That decision remains correct because a remote runtime stylesheet would create cross-repository failure coupling.

However, the estate currently repeats local implementations of:

- product strips;
- page introductions;
- section labels;
- buttons and action links;
- cards and metric grids;
- tags and badges;
- filters;
- dialogs and search panels;
- loading, empty, unavailable, and error states;
- data tables;
- footers.

Recommendation: define common component roles and generate repository-local pinned copies. Do not introduce a shared live CSS dependency.

### 2. Public terms are not controlled tightly enough

The estate uses overlapping labels such as project, product, service, system, tool, experiment, interface, component, repository, live, operational, active, healthy, published, deployed, and merged.

These labels represent different facts. Treating them as stylistic synonyms weakens the estate's evidence discipline.

Recommended public vocabulary:

| Term | Public meaning |
|---|---|
| Project | A portfolio body of work |
| Product | A user-facing application or experience |
| Service | A deployed runtime component |
| Tool | A focused operational or engineering utility |
| Experiment | Exploratory work without a stable product contract |
| Interface | A human-facing view over a product, service, or evidence source |
| Case study | Long-form technical explanation tied to a body of work |
| Article | Editorial writing that need not map to one project |
| Repository | A source-control location |
| Merged | Source reached the default branch |
| Deployed | A production deployment completed successfully |
| Published | Writing passed through scheduler execution and is live |
| Operational | Fresh runtime evidence says the public function is available |
| Degraded | The function remains available but current evidence shows impairment |
| Unavailable | The public function cannot currently be performed |
| Unknown | Evidence is absent, stale, invalid, or failed |

Recommendation: add this vocabulary to the v2 policy and test visible state labels where practical.

### 3. Page hierarchy varies by surface

The estate needs one default reading order:

1. global header;
2. product or section identity;
3. eyebrow or identifier;
4. page title;
5. concise purpose;
6. primary state or action;
7. main content;
8. evidence and metadata;
9. purpose-specific footer.

Purpose-specific products may vary inside the main content area. They should not vary in the meaning or order of identity, purpose, state, and escape routes without a documented reason.

### 4. Work requires hierarchy reduction, not content removal

Work is the highest-priority main-site change. Current entries contain strong evidence but ask the visitor to process too much at once.

Recommended card anatomy:

- Identity: `P-NN`, title, role, one-sentence result, two or three categories.
- Evidence: four metrics, gallery or audio evidence, one prominent outcome.
- Detail: selected technologies, supporting achievements, source, and case study.

The full stack and deeper lessons belong in the case study. Work should help a visitor choose which evidence to inspect.

### 5. Writing requires explicit architecture for featured, series, and archive content

The scheduler already owns published ordering, upcoming rotation, series metadata, and publication state. The public page should expose that structure directly.

Recommended sections:

- Featured;
- Series;
- All writing.

Recommended card state labels:

- `Published 23 July 2026`;
- `Scheduled 26 July 2026`;
- `Part 1 of 3`;
- `12 min read`.

Avoid decorative status text such as `NEXT CHAPTER` where a precise scheduler state is available. Editorial flavour can remain in titles and summaries.

### 6. Lab needs a public taxonomy

Recommended Lab groups:

- Observe: System Map, Status, Reliability views, Anomaly, Signal.
- Verify: Proof Chain, Conformance, Public API evidence.
- Experience: Ramone, System SYMPHONY, interactive demonstrations.
- Explore: prototypes and explicitly non-production experiments.

Recommended maturity labels:

- `Production product`;
- `Operational tool`;
- `Experiment`;
- `Preview`;
- `Planned`.

Maturity is not current runtime state. A production product can be unavailable; an experiment can be operational. These must remain separate fields.

### 7. A Systems directory is justified

The current primary navigation is appropriately compact. Adding every product to it would create crowding and make the main routes less clear.

A new `/systems/` route should expose the wider public estate without becoming a second system map.

The directory should show only public human-facing destinations and should group them as:

- Portfolio: Work, Writing, About, CV.
- Products: Ramone, Status, System SYMPHONY where directly accessible.
- Engineering interfaces: Lab, API Docs, Proof Chain, Reliability, Conformance, Signal, Anomaly.

Each item should include a name, one-sentence purpose, public type, maturity, valid live state where evidence exists, source repository where public, and primary action.

The page must not expose private components from the estate manifest.

### 8. Tokens need to expand beyond the brand essentials

The Brand Reference provides the colour palette, fonts, content widths, base size, navigation height, and grid.

The v2 token contract should add:

- spacing scale;
- type roles and line heights;
- control sizes;
- touch-target requirements;
- card padding;
- surface roles;
- border and radius roles;
- z-index layers;
- motion duration and easing;
- standard content widths;
- responsive breakpoints.

Recommended spacing scale: `4`, `8`, `12`, `16`, `24`, `32`, `48`, `64`, and `96` pixels.

Recommended control sizes:

- compact: 32px;
- standard: 40px;
- minimum touch target: 44px.

These values are proposed, not accepted, until ADR-0008 is approved.

### 9. Canonical components should be role-based

Recommended first component set:

1. global header;
2. product strip;
3. page introduction;
4. section heading;
5. primary button;
6. secondary button;
7. text action;
8. status chip;
9. type badge;
10. maturity badge;
11. metric grid;
12. standard card;
13. editorial card;
14. data card;
15. interactive card frame;
16. tag list;
17. filter bar;
18. table wrapper;
19. search dialog;
20. loading state;
21. empty state;
22. unavailable state;
23. error state;
24. footer.

The contract should allow a small number of variants. It should reject a new one-off card class when an existing role already fits.

### 10. Responsive and visual evidence is incomplete

The first programme added responsive safeguards but did not establish a standard evidence matrix for every public route.

The v2 programme should require evidence at:

- 320px;
- 375px;
- 768px;
- 1024px;
- 1440px.

Evidence should cover:

- navigation density;
- heading scale;
- card rhythm;
- table and code overflow;
- dialogs;
- touch targets;
- keyboard focus;
- reduced motion;
- loading, empty, and error states.

## New pages considered

### Recommended: `/systems/`

Reason: the estate now has enough public surfaces that discoverability cannot be solved by the four primary links alone.

### Deferred: `/principles/`

Engineering principles should first appear as an evidence-linked section on About. A separate route should be added only if each principle can link to real ADRs, case studies, or operational examples.

### Rejected for now

- separate Contact page;
- generic Blog page;
- separate Projects page;
- Skills page;
- technology-logo catalogue;
- duplicate system-map route;
- timeline page.

These would duplicate existing information or pull the site towards a conventional CV structure.

## Intentional differences that must remain

The programme must preserve:

- Work galleries and audio evidence;
- Writing editorial typography and scheduler-owned structure;
- Lab visualisations and instrument-specific controls;
- Status evidence density and bounded state semantics;
- Ramone conversation layout and inference behaviour;
- API Docs OpenAPI-derived content;
- CV document gate;
- System SYMPHONY audio behaviour and identity.

Cohesion applies to framing, hierarchy, labels, spacing, controls, states, accessibility, and navigation. It does not remove product-specific interaction models.

## Proposed implementation sequence after approval

### Phase 1: accept authority

- review and accept ADR-0008;
- version the v2 policy and schemas;
- define token, terminology, component, and evidence ownership.

### Phase 2: executable foundation

- create versioned token and component source in `atlas-infra`;
- generate repository-local pinned copies;
- add validators and fixtures;
- prohibit remote runtime dependency on shared presentation assets.

### Phase 3: primary site

- homepage route-by-intent improvements;
- Work hierarchy and taxonomy;
- Writing architecture;
- Lab grouping and maturity labels;
- About structure and principles section;
- new `/systems/` directory;
- error-state components.

### Phase 4: generated writing

- update `atlas-article-gen` source shell;
- update `atlas-scheduler` preview and migration paths;
- prove publication ownership and historical body preservation.

### Phase 5: specialist surfaces

Migrate and verify separately:

1. Status;
2. Public API Docs;
3. Ramone;
4. CV.

### Phase 6: conformance evidence

- standard viewport evidence;
- accessibility checks;
- token and component checks;
- terminology checks;
- visual comparison artifacts;
- final public-interface conformance report.

## Approval questions

Before Phase 1 implementation, Atlas should approve or amend:

1. the proposed public vocabulary;
2. the Lab groups and maturity labels;
3. the `/systems/` route;
4. Work card hierarchy;
5. Writing sections;
6. proposed spacing and control scales;
7. the repository-local generated component distribution model;
8. the migration order.

## Phase 0 conclusion

The estate should not be described as visually unfinished. The first programme established a credible and consistent public shell.

The remaining work is deeper: information architecture, controlled terminology, component roles, hierarchy, and conformance evidence. Those changes are justified because they improve comprehension and maintenance, not because the pages need a generic redesign.
