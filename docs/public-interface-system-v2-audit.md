# Atlas Systems public interface system v2: Phase 0 audit

## Status

Phase 0 is complete. The audit findings were approved by Atlas on 23 July 2026 and are implemented as source authority by accepted `ADR-0008` and `policy/public-interface-system-v2.json`.

This audit does not claim that any public surface already implements v2. Product migration, merge, deployment, and live verification remain separate evidence stages.

## Purpose

The first public interface programme established a common outer contract across the Atlas Systems public estate: global navigation, estate search, status presentation, browser icons, page metadata, link behaviour, focus treatment, responsive safeguards, and generated-page ownership.

Phase 0 asked:

> Where do the public surfaces still drift in hierarchy, terminology, spacing, components, organisation, and interaction, and which differences are intentional product identity rather than defects?

The goal is not to make every surface identical. The goal is to make the estate feel designed as one system while preserving the distinct jobs of Work, Writing, Lab, Status, Ramone, API Docs, and CV.

## Evidence inspected

The audit used the current repository state and accepted authority in this order:

1. `AtlasReaper311/atlas-systems` route source, shared shell, sitemap, and current page structures;
2. accepted `ADR-0007` and `policy/public-interface-contract.json` in `AtlasReaper311/atlas-infra`;
3. `AtlasReaper311/atlas-api-public:data/estate.manifest.json` for declared public ownership;
4. current source for Status, Ramone, Public API Docs, and CV;
5. the Atlas Systems Brand Reference;
6. live HTML where it was retrievable during the audit.

The audit does not treat a merged pull request as proof of live deployment.

## Approved outcome

The accepted implementation target is recorded in:

- `docs/adrs/ADR-0008-public-interface-system-v2.md`;
- `docs/public-interface-system-v2-approved-scope.md`;
- `policy/public-interface-system-v2.json`;
- `contracts/v1/public-interface/public-interface-system.schema.json`.

The current v1 shell contract remains active until repository migrations are reviewed, previewed, merged, deployed, and verified.

## Route and surface audit matrix

Priority meanings:

- `P0`: required before a cohesive-system claim;
- `P1`: high-value improvement after the shared foundation;
- `P2`: useful refinement that can follow the core migration;
- `Preserve`: intentional difference that should remain.

| Surface | Owner | Current purpose | Intentional identity to preserve | Confirmed drift or risk | Approved change | Priority |
|---|---|---|---|---|---|---|
| `/` | `atlas-systems` | Estate introduction and primary routing | Operational homepage treatment and existing hero identity | The wider set of products and engineering tools is not exposed as a coherent directory | Add route-by-intent improvements, preserve the main hero, and link to `/systems/` | P1 |
| `/work/` | `atlas-systems` | Portfolio evidence and completed projects | Galleries, audio evidence, project metrics, case-study links | Each project presents identity, role, long summary, metrics, full stack, achievements, media, and links at the same level | Use selective disclosure, stable identifiers and anchors, explicit result statements, exact repository links, and Featured, All projects, In development, Experiments, and hidden-until-needed Retired sections | P0 |
| `/writing/` | `atlas-systems`, generated and refreshed through the publishing pipeline | Published case studies, series, and scheduled writing | Editorial treatment, W-number identity, scheduler-owned ordering and states | Published, next, and scheduled material share similar card weight; state labels vary | Present Featured, Series, and All writing; show only the next article or series; use month precision for scheduled material; preserve scheduler ownership | P0 |
| Published article routes | `atlas-article-gen` -> `atlas-scheduler` -> `atlas-systems` | Long-form technical evidence | Editorial typography, article diagrams and media, scheduler footer and series navigation | Historical content has mixed source availability | Update canonical-source articles through generator and scheduler; use bounded scheduler shell refresh where source is absent; never rewrite prose as visual migration | P1 |
| `/lab/` | `atlas-systems` | Public products, engineering tools, experiments, and evidence | Ramone first, purpose-specific instruments, System SYMPHONY identity | The page combines too many dense views without a public taxonomy | Convert to a directory with flagships and Experience, Observe, Verify, and Explore groups; move dense views behind cards or dedicated routes | P0 |
| `/lab/system-map/` | `atlas-systems` | Full interactive estate map | Current graph and evidence semantics | The map is useful but too dense inside the Lab landing page | Create a dedicated route and show only a compact preview on Lab and Systems | P0 |
| `/lab/proof-chain/` | `atlas-systems` | Bounded source-to-service and ADR proof | Evidence-first graph and fail-closed behaviour | Needs consistent framing and state components | Adopt shared verification-tool components without changing proof contracts | P1 |
| `/lab/signal/` | `atlas-systems` | Interactive browser audio and DSP experiment | Audio controls and visualisation | Outer framing and maturity language drift | Preserve the instrument; classify it as Experiment; standardise framing, data mode, focus, and error states | Preserve / P1 |
| `/lab/anomaly/` | `atlas-systems` | Telemetry-shape replay and analysis | Specialist telemetry controls | Product naming and maturity are inconsistent | Use one public name and classify Shape Detector as Experiment | P0 |
| `/lab/conformance/` | `atlas-systems` | Estate policy and coverage evidence | Dense audit evidence and weighted rules | State and finding labels drift from shared vocabulary | Standardise evidence, state, warning, unavailable, and freshness language | P1 |
| `/lab/reliability/` | `atlas-systems` | Chaos and recovery evidence | Trial detail and reliability evidence | Product type, maturity, and current result are mixed | Use Reliability Trials as a Tool and separate current evidence state from maturity | P0 |
| `status.atlas-systems.uk` | `status` | Immediate estate condition and detailed reliability evidence | Operational density and bounded state semantics | Detailed evidence can precede the visitor's primary question | Create overview-first hierarchy, then grouped service evidence, freshness, objectives, and recent events | P0 |
| `ramone.atlas-systems.uk` | `ramone-edge` | Grounded public conversational interface | Startup sequence, conversation layout, model and grounding behaviour | Controls, loading, errors, citations, and grounding explanation are locally defined | Preserve the product experience; align shared controls and states; explain the public grounding boundary | P1 |
| `api.atlas-systems.uk/v1/docs` | `atlas-api-public` | Human documentation rendered from OpenAPI authority | Contract-derived endpoint catalogue | Navigation and endpoint actions can be clearer | Add group navigation, method badges, copy-path controls, parameter and response components, and raw OpenAPI access | P1 |
| `cv.atlas-systems.uk` | `atlas-doc-viewer` | Formal CV document gate and viewer | PDF initialisation, download path, minimal framing | Expansion would duplicate About | Keep it minimal; standardise summary, update date, file metadata, actions, and About escape | Preserve / P2 |
| `/404.html` and error routes | route owner | Honest failure and recovery | Minimal fail-closed presentation | State components are implemented independently | Adopt canonical loading, empty, unavailable, unknown, and error roles | P0 |
| `/systems/` | `atlas-systems` | Directory of visitor-facing products and engineering tools | New route | The estate has more public destinations than the old four-link header exposed | Add Portfolio, Products, and Engineering tools groups, selective runtime state, and a simplified architecture diagram | P0 |

## Cross-estate findings

### Shared interface grammar

The accepted v1 contract intentionally allows repository-specific markup and CSS. That remains correct because a remote runtime stylesheet would create cross-repository failure coupling.

The estate repeats local implementations of product strips, page introductions, section labels, actions, cards, metrics, tags, badges, filters, dialogs, state panels, tables, and footers.

Public Interface System v2 defines shared roles and distributes deterministic repository-local bundles. It does not introduce a shared live CSS or JavaScript dependency.

### Public terminology

Approved evidence-bearing meanings:

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

Maturity labels are Production, Tool, Experiment, Preview, Planned, and Retired. Maturity and runtime state remain separate.

### Default page hierarchy

1. global header;
2. product or section identity;
3. eyebrow, identifier, or route type;
4. page title;
5. concise purpose;
6. primary state or action;
7. main content;
8. evidence and metadata;
9. purpose-specific footer and estate escape.

Purpose-specific products may vary inside the main content area.

### Global navigation

Desktop target:

- left: wordmark and aggregate status;
- centre: Work, Writing, Lab, Systems, About;
- right: compact Search control.

The healthy label is `Operational`, and the status links directly to Status.

Mobile uses bottom navigation with the wordmark, status, and search icon retained above.

### Lab taxonomy

Experience:

- Ramone;
- System SYMPHONY;
- Signal Garden.

Observe:

- System Map;
- Status;
- Activity;
- Deployment evidence;
- DORA metrics.

Verify:

- Proof Chain;
- Estate Conformance;
- Reliability Trials;
- API Docs.

Explore:

- Shape Detector.

Ramone remains first. System SYMPHONY is Preview. Shape Detector and Signal Garden are Experiments in the first migration.

### Systems directory

Systems lists only meaningful visitor-facing destinations in its main body. Machine-facing systems are secondary detail. Private and local components are architecture context, not destinations.

The page includes a simplified architecture diagram. The full interactive System Map remains a Lab tool.

### Tokens and components

Approved spacing scale: `4`, `8`, `12`, `16`, `24`, `32`, `48`, `64`, and `96` pixels.

Approved control sizes:

- compact: 32px;
- standard: 40px;
- minimum touch target: 44px.

Approved card padding:

- compact: 16px;
- standard: 24px;
- editorial: 32px.

Approved radius range: 4px to 8px.

The visual direction is spacious and editorial, with slightly larger text, restrained standard motion, controlled flagship motion, one-pixel borders combined with surface depth, minimal standard shadows, and diagram-led information design.

The first shared component roles cover the global header, product strip, page introduction, headings, actions, badges, metrics, card roles, tags, filters, tables, search, state components, and footers.

### Distribution

`atlas-infra` owns governance.

A future `AtlasReaper311/atlas-interface-kit` repository is approved for source CSS, examples, build tooling, and generated bundles. Repository creation remains a separate provider action.

Bundles remain repository-local, versioned, and fingerprinted. Approved releases open automated repository update pull requests. Visual changes require manual preview approval and do not auto-merge.

### Evidence

Required browsers:

- Firefox;
- Chrome.

Required viewport matrix:

- 320px;
- 375px;
- 768px;
- 1024px;
- 1440px.

Desktop is primary. Mobile remains required.

Every route receives semantic and accessibility checks. Representative route types receive the full viewport matrix. Every changed route receives full screenshots.

Serious accessibility failures block merge. Screenshot tests use deterministic fixtures; live-data contract tests remain separate.

## Intentional differences that remain protected

- Ramone startup and conversation experience;
- homepage main hero character;
- Work galleries and audio evidence;
- Writing editorial character and scheduler ownership;
- Lab instruments and visualisations;
- Status bounded state semantics;
- API Docs OpenAPI authority;
- CV document gate;
- System SYMPHONY audio behaviour.

## Implementation sequence

### Phase 1: authority

- accept ADR-0008;
- commit the v2 policy and schema;
- validate approved terminology, hierarchy, ownership, distribution, and evidence rules.

### Phase 2: interface kit

- create `atlas-interface-kit` through a separately approved provider action;
- implement tokens, shared roles, examples, bundle generation, fingerprints, and update-PR automation.

### Phase 3: primary site

- implement the v2 global shell;
- restructure Lab first;
- add Systems and the dedicated System Map route;
- then migrate homepage, Work, Writing, About, and error states.

### Phase 4: generated writing

- update `atlas-article-gen`;
- update `atlas-scheduler` previews and migration paths;
- prove body preservation and publication ownership.

### Phase 5: specialist surfaces

1. Status;
2. Public API Docs;
3. Ramone;
4. CV.

### Phase 6: conformance

- complete viewport and accessibility evidence;
- add token, terminology, component, and fingerprint checks;
- publish the final conformance report after verified production rollouts.

## Conclusion

The first programme established a credible shared shell. Public Interface System v2 governs the deeper work: information architecture, terminology, component roles, organisation, visual rhythm, and evidence.

No production surface is declared v2-conformant until its own implementation, preview, merge, deployment, and live verification are complete.
