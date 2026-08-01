# Public interface programme Phase 11 coordination

Status: active at Part 0 completion and Lab context-wayfinding implementation.

Started: 1 August 2026.

## Purpose

Phase 11 improves Lab wayfinding, evidence tools, and interactive instruments without flattening their individual identity or changing their runtime, evidence, synthesis, simulation, or publication contracts.

This phase begins only after the formally recorded Phase 10 closeout. It treats current GitHub repository state as authority and does not reuse Phase 10 browser artefacts as proof of current Lab behaviour.

## Current source baseline

- `atlas-infra/main`: `59caabc2685ac6b250fdf472329a79252efa4dfc`.
- `atlas-systems/main`: `4896b1c482d89f8b7968ec0baee5763e36843342`.
- Phase 10 production run: `30638766487`.
- Stale `atlas-systems#179` remains excluded and must not be reused or merged.
- No Phase 11 implementation, preview, merge, deployment, provider setting, binding, secret, publication, or runtime write existed at the start of this record.

## Accepted authority

Phase 11 follows:

1. current repository files, branches, pull requests, commits, checks, and Actions runs;
2. accepted ADR-0007, ADR-0008, ADR-0009, and executable public-interface policy in `atlas-infra`;
3. repository-native interface, Lab, Pages, metadata, accessibility, network, and browser-evidence contracts;
4. live endpoints and generated evidence only when deployment state matters;
5. `AGENT.md` as the stable operating map.

The accepted programme register defines Phase 11 as four focused Lab branches. Each branch stops at a reviewed draft pull request and deterministic non-production evidence. System Symphony receives follow-up changes only when current measured evidence proves a defect.

## Part 0 findings

### Lab context navigation

`lab/shared/shell.js` currently builds one flat route strip. It:

- omits The Bearing;
- links Reliability to the retired `/lab/reliability/` location rather than `/systems/reliability/`;
- exposes APU ROMs as a global Lab peer even though System Symphony owns its own nested navigation;
- omits current Observability and Evidence destinations;
- uses exact-path current-state matching, so nested System Symphony routes do not retain useful Lab context.

### Evidence tools

System Map, Proof Chain, Estate Conformance, Blackbox, and Shape Detector remain individually owned tools. Their data, APIs, topology, policy mathematics, provenance, and fail-closed behaviour are protected. Later Phase 11 work may align framing, state language, focus, dense-data access, and interaction feedback only.

### Instruments

Signal Garden and System Symphony have large protected interaction contracts. Synthesis, AudioWorklet behaviour, telemetry mapping, simulation modes, recording, deterministic seeds, topology, loudness, and audio output are excluded unless a current measured defect requires a bounded correction.

### Experiments

Speculum, Almost, Drift, and The Bearing retain distinct visual and simulation identities. Later work may correct keyboard access, focus, reduced-motion states, instructions, escape routes, and generated-state announcements without changing their underlying systems.

### Legacy console

`/lab/console/` remains a no-index compatibility surface. Phase 11 must record panel parity against focused Observability, Evidence, Reliability, Blackbox, and System Map destinations before proposing retirement. A source merge alone cannot prove that parity or production removal.

## Branch programme

### 11A: Lab context wayfinding

Branch: `atlas-systems:refactor/lab-context-wayfinding`.

Scope:

- replace the flat Lab route strip with taxonomy-aware route groups;
- include current canonical destinations and The Bearing;
- keep System Symphony child routes inside its own product navigation;
- preserve active context for nested System Symphony routes;
- retain horizontal access on narrow screens and visible keyboard focus;
- add an executable source contract for route inventory and grouping.

Protected:

- no route content, API, topology, evidence, synthesis, simulation, audio, publication, provider, binding, or secret change;
- no production deployment before a separately reviewed merge gate.

### 11B: Lab evidence tools

Planned branch: `atlas-systems:refactor/lab-evidence-tools`.

Scope includes System Map, Proof Chain, Estate Conformance, Blackbox, Shape Detector, and the legacy-console parity inventory. It begins only after 11A is reviewed so shared-shell paths do not overlap.

### 11C: Lab instruments

Planned branch: `atlas-systems:fix/lab-instrument-interactions`.

Scope includes Signal Garden interaction polish and System Symphony only for measured defects.

### 11D: Lab experiments

Planned branch: `atlas-systems:fix/lab-experiment-interactions`.

Scope includes Speculum, Almost, Drift, and The Bearing.

## Validation and evidence contract

Every implementation branch must run the current repository-native validation, including:

- HTML validation;
- public-interface, main-site, Lab, and System Symphony tests;
- interface-bundle verification;
- sitemap and static-performance checks;
- Pages output and filtered publish-artifact checks;
- social-preview verification;
- committed JSON parsing;
- whitespace and offline-link checks.

Visual or evidence-contract changes require the existing isolated `interface-preview.yml` path. Evidence must cover changed routes in Chromium and Firefox at 320, 375, 768, 1024, and 1440 pixels, with 1920 pixels reporting-only. Serious accessibility failures, unreviewed overflow, page errors, failed requests, or unmatched console errors block review.

Preview publication is non-production. Merge and production deployment remain separate approval gates. A merged commit does not prove deployment.

## Security and privacy boundary

Phase 11 must not:

- request or expose secrets;
- dispatch mutation endpoints;
- send inference questions from acceptance tests;
- expose private routes, provider identifiers, or unbounded graph queries;
- alter Cloudflare settings, bindings, schedules, or deployment configuration;
- alter article generation, scheduling, publication timing, or published output;
- infer live state from merged source.

## Current approval boundary

Atlas approved implementation of 11A and creation of its isolated non-production preview. Stop after the validated draft pull request, preview URL, deterministic browser evidence, exact changed-path record, and remaining findings. Do not merge or deploy production without a new explicit approval.