# Public interface programme Phase 11 coordination

Status: complete at source, production deployment, and live-verification gates.

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

## Closeout baseline

- `atlas-infra/main` at closeout inspection: `1d6a09589188cf14a7bc2c5cba5dfd7ed468e966`.
- `atlas-systems/main` after Phase 11: `0fd7a98aeaea523f18914c3c7f134fa96607406b`.
- Final Phase 11 production deployment run: `30744843987`.
- Phase 12 remains a separate supporting-products phase and requires fresh Part 0 inspection of the current programme authority and every product repository before implementation.

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

## Implementation receipts

| Slice | Pull request | Source branch | Reviewed head | Merge commit | Production run |
| --- | --- | --- | --- | --- | --- |
| 11A Lab context wayfinding | `atlas-systems#189` | `refactor/lab-context-wayfinding` | `353cb62cd3e25856bd644f3c7505e76dd399eb73` | `163db2609028dea0d493e56afacbd81cc34e675b` | `30722995814` |
| 11B Lab evidence tools | `atlas-systems#190` | `refactor/lab-evidence-tools` | `44e467899692ce8a8cd6f4544eb351e0861eb5f5` | `519bb402a2f0d4ef1e3fc351efdccfffb0152262` | `30742015214` |
| 11C Lab instruments | `atlas-systems#191` | `fix/lab-instrument-interactions` | `2d98d61dbd429ff77e4810d39b1ad26dd6ee7e6b` | `8e12441b67a1d1eab571022d5d4471701b9ffb89` | `30743228232` |
| 11D Lab experiments | `atlas-systems#192` | `fix/lab-experiment-interactions` | `c3cdc62ef9886cfd9569272de6caf4e6fbfec3cc` | `0fd7a98aeaea523f18914c3c7f134fa96607406b` | `30744843987` |

All four production runs completed successfully. The final run verified the Pages output contract, HTML and offline links, Cloudflare Pages deployment, cache purge, Discord reporting, exact custom-domain commit, v2 Systems route marker, Phase 6 footer assets, live homepage AtlasField renderer, live System Symphony Atlas APU and topology map, and guarded corpus refresh job.

## Final live Lab smoke

After `atlas-systems#192` deployed, a live browser smoke covered the changed Phase 11 Lab experiment routes on `https://atlas-systems.uk` at a 390 pixel mobile viewport with reduced motion enabled:

| Route | Expected shell | Mobile Lab nav | Keyboard focus path | Result |
| --- | --- | --- | --- | --- |
| `/lab/almost/` | yes | active | focus canvas, Space, N | pass |
| `/lab/drift/` | yes | active | focus canvas, ArrowRight, Escape | pass |
| `/lab/speculum/` | yes | active | focus canvas, Space | pass |
| `/lab/bearing/` | no, standalone full-bleed experiment | not applicable | focus lattice, ArrowRight, Space, Escape | pass |

The live smoke produced no page errors, no unmatched console errors, and no non-ignored request failures. Exact deployed commit evidence is provided by deploy run `30744843987`, which confirmed the custom domain served `0fd7a98aeaea523f18914c3c7f134fa96607406b`.

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

## Closeout boundary

Phase 11 is closed from repository, preview, merge, production deployment, and live-route evidence. No provider setting, binding, secret, inference route, article publication path, scheduler path, or Cloudflare configuration was changed as part of this phase.

The next phase is Phase 12: supporting products. Before implementation, inspect the current complete programme definition, accepted ADRs, executable policy, open pull requests, repository baselines, preview workflows, deployment boundaries, and protected product contracts for `status`, `atlas-doc-viewer`, `ramone-edge`, `atlas-api-public`, and `atlas-api-index`.
