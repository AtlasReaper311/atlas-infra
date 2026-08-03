# Public interface programme Phase 14 browser budget authority

Status: complete at authority, enforcement, production deployment, and live-verification gates.

Started: 2 August 2026.
Accepted: 3 August 2026.
Completed: 3 August 2026.

## Purpose

Phase 14 promotes reviewed browser-performance measurements into selected
blocking budgets only after evidence supports the metric, value, tolerance, and
exclusion. The accepted gate protects rendered first-party resource weight
without weakening the deterministic static baseline or making unsupported
runtime-timing or Core Web Vitals claims.

## Authority baseline

- Phase 13 authority: `atlas-infra#117`, merged as
  `a3627dde153201068b563c74cd3b229a1d0f8e69`.
- Current acceptance source baseline: `atlas-systems/main` at
  `31af5f9b948a9be5dd80fd4a4e685c92137240a0` after `atlas-systems#194`.
- Static performance fingerprint at acceptance:
  `19850b063f0817f953c0d853ae3d3d80431c05fc94371bd92f04cb27f0c6a021`.
- Authority acceptance pull request: `atlas-infra#119`.
- Authority reviewed head: `c2b726ea8355a1013d58fc284f47e90919ba8921`.
- Authority merge commit: `d61e0f8fa36df09c8ba10e76dacc59c8bca4a4fa`.

The authority pull request passed Contract registry CI, CodeQL, OpenSSF
Scorecard, pull-request impact validation, and the expected Dependabot policy
skip. It changed documentation authority only.

## Evidence inspected

| Pull request | Run | Head SHA | Artifact | Digest | Notes |
| --- | --- | --- | --- | --- | --- |
| `atlas-systems#168` | `30386218935` | `4dafa7d1d4690e94e36e9342e672d41307633d19` | `8699615072` | `sha256:7d3662cdc835c5195bcca30395cc398b5423286b768ae4fdeed6d32bfd38caec` | Original complete route-derived browser-evidence cycle. |
| `atlas-systems#189` | `30722335070` | `353cb62cd3e25856bd644f3c7505e76dd399eb73` | `8825413605` | `sha256:501eb141cac8474ef7f87e12a82d985c21b57a566c3cf4736fe8e0a6109403f2` | Lab context preview evidence. |
| `atlas-systems#190` | `30724694572` | `44e467899692ce8a8cd6f4544eb351e0861eb5f5` | `8826116404` | `sha256:31a5b8cb379dccf32a4040781cc9046ec25b7a3df8762e7d1d94c1999aac9870` | Lab evidence-tool preview evidence. |
| `atlas-systems#191` | `30742333958` | `2d98d61dbd429ff77e4810d39b1ad26dd6ee7e6b` | `8831862825` | `sha256:0c13b0a912eab612175013af316e3e52839a11a237cf2e43746577a8eddb827f` | Signal Garden preview evidence. |
| `atlas-systems#192` | `30743826242` | `c3cdc62ef9886cfd9569272de6caf4e6fbfec3cc` | `8832353944` | `sha256:465f5fde26078cea91bc6c6c87345c128e43c0a8387b26a98628578fa37f2a28` | Final Phase 11 Lab preview evidence. |
| `atlas-systems#194` | `30762531071` | `bb32c18765e8d99fb3fb08439b6d56b2259e1c21` | `8838070224` | `sha256:5bc2aed19685525f99f54982c6b247c5a1cf3291ea1c4999ac1cc0e5f1318e61` | Latest pre-enforcement source and static-baseline evidence. |

## Accepted gate

The blocking gate covers only:

- `requestCount`;
- `encodedBytes`;
- `decodedBytes`;
- `scriptCount`;
- `styleCount`;
- Chromium and Firefox;
- 375 and 1440 pixel viewports;
- deterministic preview evidence with reduced motion and service workers
  blocked;
- first-party resources served by the isolated preview origin or canonical
  `https://atlas-systems.uk` origin.

| Route | Request cap | Encoded byte cap | Decoded byte cap | Script cap | Style cap |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/` | 44 | 322560 | 391168 | 16 | 15 |
| `/systems/` | 30 | 301056 | 305152 | 12 | 14 |
| `/lab/` | 47 | 450560 | 458752 | 22 | 19 |
| `/lab/signal/` | 28 | 289792 | 297984 | 12 | 12 |
| `/lab/almost/` | 29 | 290816 | 299008 | 12 | 13 |
| `/lab/bearing/` | 9 | 56320 | 56320 | 2 | 5 |
| `/writing/` | 38 | 320512 | 324608 | 18 | 17 |

The gate excludes 320, 768, 1024, and 1920 pixel resource measurements,
runtime and paint timing, LCP, CLS, FCP, TTFB, CPU and memory measurements,
network `transferSize`, API and fixture hosts, third-party analytics, external
embeds, live production network measurements, and routes outside the table.
The 1920-pixel viewport remains reporting-only.

## Enforcement implementation

Repository: `AtlasReaper311/atlas-systems`.

- Branch: `perf/browser-budget-gates`.
- Pull request: `atlas-systems#196`.
- Base: `31af5f9b948a9be5dd80fd4a4e685c92137240a0`.
- Reviewed head: `376ad78a4b36169cbb37e19f885d1b8c4bade8f5`.
- Merge commit: `1cc32599ce1ab8630a62b013e939941f0ca4ce1a`.
- Changed paths:
  - `scripts/interface-evidence/browser-performance-budgets.json`;
  - `scripts/interface-evidence/performance-budget.mjs`;
  - `scripts/interface-evidence/browser-core.mjs`;
  - `js/tests/browser-performance-budget.test.mjs`.

The implementation:

- stores one versioned accepted policy;
- evaluates all 28 required browser, viewport, and route combinations whether or
  not a route is otherwise classified as changed;
- fails closed when a required measurement is absent;
- recomputes first-party metrics from captured resource entries;
- records measured values, caps, completeness, and violations in
  `evidence.json`;
- applies the budget before reviewed reporting-baseline reconciliation;
- preserves unrelated blocking findings and reporting-only evidence;
- leaves `data/performance-baseline.json` and static drift enforcement unchanged.

## Exact-head validation and browser evidence

All exact-head checks passed for reviewed head
`376ad78a4b36169cbb37e19f885d1b8c4bade8f5`:

| Check | Run | Conclusion |
| --- | ---: | --- |
| Pull request CI | `30798376093` | pass |
| Public interface conformance | `30798376335` | pass |
| CodeQL | `30798375954` | pass |
| OpenSSF Scorecard | `30798376044` | pass |
| Dependabot review policy | `30798376267` | skipped as expected |
| Public interface preview | `30798375945` | pass |

Preview:
`https://interface-pr-196.atlas-systems-44t.pages.dev`.

The deterministic preview recorded 28 expected measurements, 28 observed
measurements, zero browser-budget violations, zero blocking interface findings,
and successful Batch H assertions.

| Artifact | ID | Digest |
| --- | ---: | --- |
| `public-interface-preview-evidence-376ad78a4b36169cbb37e19f885d1b8c4bade8f5` | `8850156321` | `sha256:b74c2c50f6f0bd1d40e1f0026b52bab566f4525465490eb600735b5ca97be9fe` |
| `batch-h-preview-evidence-376ad78a4b36169cbb37e19f885d1b8c4bade8f5` | `8850157512` | `sha256:3949f7c6a895f7b49fd1b4070a3a226029bf8048b1941f9d086695ab6ae57e66` |
| `interface-validation-376ad78a4b36169cbb37e19f885d1b8c4bade8f5` | `8849815584` | `sha256:bc066c898aaa34a0039394c8ebea4aea23dfba1d1be0bcd4bf82476236080d22` |

## Reporting-only findings retained

The enforcement did not erase or silently promote the 20 existing reporting
findings. They remain visible for later ownership decisions:

- the Lab directory reported 21 of 22 card signatures at several viewports;
- the Sonin article retained the known YouTube/CSP console report;
- Estate Conformance retained its reviewed console `Error` report;
- Shape Detector retained its reviewed console `Error` report.

These findings did not exceed an accepted browser resource budget and were not
new Phase 14 blockers.

## Production deployment and live verification

The normal `main` deployment for merge commit
`1cc32599ce1ab8630a62b013e939941f0ca4ce1a` completed successfully:

- Deploy workflow run: `30799529583`;
- workflow run number: `323`;
- event: `push`;
- branch: `main`;
- created: `2026-08-03T08:59:31Z`;
- completed: `2026-08-03T09:10:02Z`;
- conclusion: success.

The run passed Pages-output validation, deployment, cache purge, exact custom
-domain commit verification, the Systems route marker, Phase 6 footer assets,
homepage AtlasField smoke, System Symphony APU and topology smoke, Discord and
Lab reporting, and guarded Corpus refresh.

An independent custom-domain check confirmed that `https://atlas-systems.uk`
served the full build marker
`1cc32599ce1ab8630a62b013e939941f0ca4ce1a`.

`deploy-watch` independently reported:

- deployment ID `50929bca-e74d-4491-aacb-13581c5db991`;
- branch `main`;
- commit prefix `1cc3259`;
- status `success`;
- checked at `2026-08-03T09:05:50.933Z`.

A temporary read-only diagnostic PR, `atlas-systems#197`, captured the Actions,
live-marker, and deploy-watch receipts. It was closed without merge. Diagnostic
run `30800377996` passed and uploaded artifact `8850540234`,
`phase-14-closeout-receipt`, with digest
`sha256:b6c27b97e7655c1894cae8c0da3b2badfc6a1dcf123876c01385dafda92532e7`.

## Security and privacy review

Phase 14 did not request or expose secrets, change provider settings, alter
bindings, call mutation endpoints from browser evidence, send inference
questions, weaken static drift, add production runtime features, or change
article generation or publication ownership.

## Rollback

- Authority rollback: revert `d61e0f8fa36df09c8ba10e76dacc59c8bca4a4fa`.
- Enforcement rollback: revert
  `1cc32599ce1ab8630a62b013e939941f0ca4ce1a` and verify the resulting normal
  deployment.
- Do not edit individual caps or suppress violations without a reviewed authority
  revision.

## Closeout

Phase 14 is complete from accepted authority, exact-head source validation,
deterministic browser evidence, guarded merge, successful production deployment,
exact custom-domain commit proof, independent deployment monitoring, live route
smoke, and Corpus refresh evidence.

The next programme phase is Phase 15: freeze, dependency-ordered closeout,
deployment-state reconciliation, residual-finding ownership, and final programme
closure. Phase 15 introduces no new feature scope.
