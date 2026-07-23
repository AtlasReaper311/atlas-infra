# Atlas Systems Public Interface System v2 approved scope

## Status

Approved by Atlas on 23 July 2026.

This document records the decisions that close Phase 0 and authorize Phase 1 source implementation.

It does not authorize:

- merging a pull request;
- creating `atlas-interface-kit`;
- deploying a public surface;
- publishing or refreshing an article;
- changing provider settings;
- performing a production rollout.

Those remain separate actions with separate evidence.

## Global header

Desktop uses three zones:

- left: Atlas Systems wordmark and aggregate status;
- centre: Work, Writing, Lab, Systems, About;
- right: compact `Search` control with keyboard shortcut.

The healthy status label is `Operational`.

Clicking the status opens `https://status.atlas-systems.uk/` in the same tab.

Mobile uses bottom navigation. The top mobile header retains the wordmark, aggregate status, and search icon.

## Systems directory

Create `/systems/`.

The directory groups visitor-facing destinations as:

- Portfolio;
- Products;
- Engineering tools.

Human-facing systems are primary. Machine-facing interfaces remain available as secondary detail.

Private and local components may be described as architecture context but are not shown as public destinations.

Runtime state is selective and appears only where it helps a visitor use a live product or tool.

Systems includes a simplified architecture diagram. The full interactive map moves to `/lab/system-map/`.

A retired-system data model is reserved, but no empty graveyard is rendered.

## Lab

Lab becomes a cleaner directory with a small number of flagships.

Ramone remains the first major experience.

The first migration features:

- System Map as `Tool`;
- Proof Chain as `Tool`;
- Signal Garden as `Experiment`;
- System SYMPHONY as `Preview`.

Approved groups:

### Experience

- Ramone
- System SYMPHONY
- Signal Garden

### Observe

- System Map
- Status
- Activity
- Deployment evidence
- DORA metrics

### Verify

- Proof Chain
- Estate Conformance
- Reliability Trials
- API Docs

### Explore

- Shape Detector

Shape Detector remains an `Experiment`.

Dense activity, event, deployment, API, DORA, health, and map views move behind cards or dedicated routes.

Experiments identify whether their data is live, recorded replay, or simulated.

## Maturity and runtime labels

Approved maturity labels:

- Production
- Tool
- Experiment
- Preview
- Planned
- Retired

Approved runtime states:

- Operational
- Degraded
- Unavailable
- Unknown

Maturity and runtime state remain separate.

Maturity labels appear selectively on Systems, Lab, Work where relevant, and product or tool identity areas. They do not appear on every editorial or personal page.

Retired items remain hidden until at least one exists.

## Work

Work uses selective disclosure.

Each project has:

1. identity;
2. primary evidence;
3. supporting detail.

Supporting technologies and achievements may be collapsed behind `Technical details`.

Project identifiers remain permanent. Display order is independent from identifiers and publication order.

Approved sections:

- Featured work;
- All projects;
- In development;
- Experiments;
- Retired work.

The empty Retired work section remains hidden.

Work shows no more than six first-level technology pills. Full achievement detail belongs in case studies.

Each project requires:

- one explicit result statement;
- an exact repository link where public;
- a stable anchor;
- unique IDs;
- fixed-header scroll offsets;
- automated anchor validation.

Fully private work does not appear.

Work in progress may appear only when public evidence exists and its maturity is explicit.

The future intelligence and data-ownership project is not promoted to completed Featured work until public evidence exists. An existing completed evidence-bearing project occupies the third featured slot in the first migration.

## Writing

Writing is organised into:

- Featured;
- Series;
- All writing.

The scheduler continues to own ordering and upcoming visibility.

Only the next article or next publishing series appears in advance. Scheduled dates use month precision.

When a complete series has published, it receives one larger series card. Individual articles remain visible in All writing.

Primary categories:

- AI Systems;
- Infrastructure;
- Automation;
- Observability;
- Audio Systems;
- Game Development;
- Hardware;
- Engineering Practice.

Secondary tags remain generator-owned.

Series progress uses `Part 1 of 3`.

A separate archive is deferred until approximately 15 to 20 published articles.

Historical visual migration is approved:

- canonical source: regenerate through `atlas-article-gen` and refresh through `atlas-scheduler`;
- no canonical source: bounded scheduler shell refresh only;
- article prose is not rewritten by visual migration.

## About

About is personal and leads with:

1. Systems Engineer;
2. Software and AI Engineer;
3. Audio Systems Specialist;
4. Game Developer.

It explains the aeronautical-engineering route in detail and mentions the Saltire Scholarship.

It does not name the current employer or discuss heritage.

Approved current priorities:

- production-grade automation and governance;
- local AI and grounded retrieval;
- public observability and evidence systems;
- interactive audio systems;
- portfolio-grade infrastructure engineering.

Engineering principles remain on About for now.

Public contact methods:

- email;
- GitHub;
- LinkedIn.

The current photograph remains. A lightly animated topology visual is added with a reduced-motion fallback.

## Visual direction

The target is more organised, cohesive, spacious, editorial, and visually polished while retaining the existing Atlas Systems identity.

Approved token direction:

- spacing: 4, 8, 12, 16, 24, 32, 48, 64, 96 pixels;
- controls: 32px compact, 40px standard;
- minimum touch target: 44px;
- card padding: 16px compact, 24px standard, 32px editorial;
- radius: 4px to 8px.

Text becomes slightly larger where needed:

- body: 15px minimum, 16px preferred;
- supporting copy: 13px minimum, 14px preferred;
- metadata: 11px minimum;
- 9px to 10px only for nonessential IDs or decorative labels.

One-pixel borders remain part of the visual language but are combined with spacing and nested surface depth.

Standard cards use no or minimal shadow. Floating controls may use subtle shadow. Flagship experiences may use controlled atmospheric glow.

Amber remains the general brand and interaction accent.

Green, red, and blue remain semantic by default.

Flagships and diagrams may use controlled secondary accents.

DM Serif Display remains for brand and editorial headings. Dense operational tools may use IBM Plex Mono or an approved restrained companion. Ramone and System SYMPHONY may retain stronger product typography.

Standard motion remains restrained. Featured experiences may use more expressive motion with complete reduced-motion behaviour.

Diagrams are encouraged. Decorative imagery outside Work is not a general design device.

## Ownership and distribution

`atlas-infra` owns:

- policy;
- schemas;
- validators;
- approved versions;
- adoption and rollback rules.

A future `AtlasReaper311/atlas-interface-kit` repository is approved for creation as a separate provider action.

It will own:

- source CSS;
- component examples;
- build tooling;
- generated bundles.

Runtime assets remain repository-local.

Interface-kit releases open automated update pull requests across adopted repositories.

Visual changes do not auto-merge and require manual approval.

Products may override allowlisted brand-expression tokens only.

The following are not locally overridable:

- focus visibility;
- semantic state colours;
- minimum text contrast;
- minimum touch targets;
- spacing-scale values;
- base breakpoints;
- global header behaviour;
- z-index meanings;
- reduced-motion behaviour.

Product-specific components remain in their owning repository.

Experiments may use unusual layouts and expressive motion, but must retain accessibility, honest data-source labels, maturity language, global navigation, and an estate escape.

## Evidence

Required browsers:

- Firefox;
- Chrome.

Desktop is the primary portfolio experience. Mobile remains required after desktop implementation.

Required viewport matrix:

- 320px;
- 375px;
- 768px;
- 1024px;
- 1440px.

Every route receives semantic and accessibility checks.

Representative route types receive the complete viewport screenshot matrix.

Every changed route receives full screenshots.

Visual changes require manual approval.

Minor nonvisual changes may skip manual screenshot review.

Serious accessibility failures block merge, including:

- keyboard traps;
- missing visible focus;
- invalid heading or landmark structure;
- missing accessible control names;
- contrast failures;
- hidden focused elements;
- fixed navigation obscuring focus.

Screenshot tests use deterministic fixtures. Live-data contract tests remain separate.

## Editorial approval

Substantive portfolio claims, personal narrative, and summary shortening require Atlas's explicit editorial approval before merge.

## Protected identity

Preserve:

- Ramone startup experience;
- homepage primary hero character;
- Work galleries and audio evidence;
- Writing editorial character;
- Lab purpose-specific instruments;
- Status bounded state semantics;
- API Docs OpenAPI authority;
- CV document gate;
- System SYMPHONY audio behaviour.

## Approved implementation order

1. accept authority in `atlas-infra`;
2. create and establish `atlas-interface-kit`;
3. migrate `atlas-systems`, beginning with Lab and the global shell;
4. migrate generated Writing through `atlas-article-gen` and `atlas-scheduler`;
5. migrate Status;
6. migrate Public API Docs;
7. migrate Ramone;
8. migrate CV;
9. complete estate conformance evidence.

Each visual repository change requires a preview before merge.

Production rollout remains separate from source implementation.
