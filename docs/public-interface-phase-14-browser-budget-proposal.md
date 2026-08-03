# Public interface programme Phase 14 browser budget authority

Status: accepted authority; enforcement pending.

Started: 2 August 2026.
Accepted: 3 August 2026.

## Purpose

Phase 14 promotes reviewed browser-performance measurements into selected
blocking budgets only after evidence supports the metric, value, tolerance, and
exclusion. This document records the accepted authority for the first browser
resource gate. It does not weaken the existing deterministic static baseline or
turn runtime timing into a synthetic Core Web Vitals claim.

## Current baseline

- `atlas-infra/main` before acceptance: `b451737544b5943a2a11ccb279e817742c9228f0`.
- `atlas-systems/main`: `31af5f9b948a9be5dd80fd4a4e685c92137240a0`.
- Phase 13 merged through `atlas-infra#117` as
  `a3627dde153201068b563c74cd3b229a1d0f8e69`.
- Phase 11 follow-up Lab directory polish merged through `atlas-systems#194` as
  `31af5f9b948a9be5dd80fd4a4e685c92137240a0`.
- Current `atlas-systems/data/performance-baseline.json` remains
  `blocking_thresholds: false` and fingerprint
  `19850b063f0817f953c0d853ae3d3d80431c05fc94371bd92f04cb27f0c6a021`.

## Evidence inspected

### Locked decisions

- Static performance baseline drift is already blocking in `atlas-systems` CI.
- Static size thresholds remain reporting-only.
- Browser resource budgets may block only for the exact accepted route,
  browser, viewport, metric, tolerance, and exclusion set below.
- The 1920-pixel viewport remains reporting-only and is not a blocking budget.

### Reviewed browser evidence cycles

| Pull request | Run | Head SHA | Artifact | Digest | Notes |
| --- | --- | --- | --- | --- | --- |
| `atlas-systems#168` | `30386218935` | `4dafa7d1d4690e94e36e9342e672d41307633d19` | `8699615072` | `sha256:7d3662cdc835c5195bcca30395cc398b5423286b768ae4fdeed6d32bfd38caec` | Original reviewed browser-evidence harness cycle; 36 reporting findings accepted, not performance budgets. |
| `atlas-systems#189` | `30722335070` | `353cb62cd3e25856bd644f3c7505e76dd399eb73` | `8825413605` | `sha256:501eb141cac8474ef7f87e12a82d985c21b57a566c3cf4736fe8e0a6109403f2` | Lab context preview evidence. |
| `atlas-systems#190` | `30724694572` | `44e467899692ce8a8cd6f4544eb351e0861eb5f5` | `8826116404` | `sha256:31a5b8cb379dccf32a4040781cc9046ec25b7a3df8762e7d1d94c1999aac9870` | Lab evidence-tool preview evidence. |
| `atlas-systems#191` | `30742333958` | `2d98d61dbd429ff77e4810d39b1ad26dd6ee7e6b` | `8831862825` | `sha256:0c13b0a912eab612175013af316e3e52839a11a237cf2e43746577a8eddb827f` | Signal Garden preview evidence. |
| `atlas-systems#192` | `30743826242` | `c3cdc62ef9886cfd9569272de6caf4e6fbfec3cc` | `8832353944` | `sha256:465f5fde26078cea91bc6c6c87345c128e43c0a8387b26a98628578fa37f2a28` | Final Phase 11 Lab preview evidence. |
| `atlas-systems#194` | `30762531071` | `bb32c18765e8d99fb3fb08439b6d56b2259e1c21` | `8838070224` | `sha256:5bc2aed19685525f99f54982c6b247c5a1cf3291ea1c4999ac1cc0e5f1318e61` | Current Lab directory follow-up and refreshed Phase 14 evidence baseline. |

The reviewed cycles prove that the browser harness captures resource metrics and
that the visual and accessibility gates are repeatable. The `#194` cycle is the
current acceptance baseline because it contains the latest source and static
performance fingerprint.

### Current observed maxima

The `#194` exact-head evidence remained within every proposed cap. The maximum
observed aggregate resource values across Chromium and Firefox at 375 and 1440
pixels were:

| Route | Requests | Encoded bytes | Decoded bytes | Scripts | Styles |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/` | 42 | 144426 | 275677 | 15 | 15 |
| `/systems/` | 28 | 118180 | 267290 | 11 | 13 |
| `/lab/` | 46 | 177445 | 400122 | 21 | 19 |
| `/lab/signal/` | 26 | 119004 | 255694 | 11 | 11 |
| `/lab/almost/` | 27 | 138261 | 256571 | 11 | 12 |
| `/lab/bearing/` | 7 | 41446 | 50201 | 1 | 4 |
| `/writing/` | 37 | 128743 | 285293 | 17 | 16 |

`/lab/` has no style-count headroom beyond its accepted cap. Any additional
first-party stylesheet on that route must therefore be justified and accompanied
by an authority revision rather than silently grandfathered.

## Accepted blocking metrics

The first browser budget gate uses only metrics already captured by the browser
evidence harness and less environment-sensitive than paint timing:

- `requestCount`;
- `encodedBytes`;
- `decodedBytes`;
- `scriptCount`;
- `styleCount`.

The enforcement applies only to:

- the representative Atlas Systems routes listed below;
- Chromium and Firefox;
- 375 and 1440 pixel viewports;
- deterministic preview evidence with reduced motion and service workers
  blocked;
- first-party resource entries captured through the browser performance API.

## Accepted values

The accepted caps retain the proposal method: maximum reviewed value plus two
requests, plus one script or stylesheet, and plus 12 percent rounded up to the
next KiB for byte counts.

| Route | Request cap | Encoded byte cap | Decoded byte cap | Script cap | Style cap |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/` | 44 | 322560 | 391168 | 16 | 15 |
| `/systems/` | 30 | 301056 | 305152 | 12 | 14 |
| `/lab/` | 47 | 450560 | 458752 | 22 | 19 |
| `/lab/signal/` | 28 | 289792 | 297984 | 12 | 12 |
| `/lab/almost/` | 29 | 290816 | 299008 | 12 | 13 |
| `/lab/bearing/` | 9 | 56320 | 56320 | 2 | 5 |
| `/writing/` | 38 | 320512 | 324608 | 18 | 17 |

## Exclusions

The first blocking pass excludes:

- 1920 pixel viewport measurements;
- 320, 768, and 1024 pixel resource measurements;
- paint timing, LCP, CLS, FCP, TTFB, CPU timing, memory, and animation frame
  timing;
- network `transferSize` from live or preview deployments;
- third-party analytics or browser-extension requests;
- deterministic fixture-host responses;
- external embeds such as YouTube;
- production live measurements where CDN, cache state, and network path are not
  controlled;
- routes not listed in the accepted value table.

## Rationale

Request count and encoded and decoded byte totals catch common performance
regressions without claiming more precision than the evidence supports. They
complement the existing static baseline drift check: static drift proves source
weight changes, while browser resource budgets prove the rendered page is not
accidentally pulling extra first-party resources.

Runtime timing remains excluded because the evidence set does not prove stable
route-and-device timing across enough controlled cycles. The first budget gate
is a resource gate, not a synthetic performance-score claim.

## Accepted decision

The owner accepted on 3 August 2026:

1. the five selected resource metrics;
2. the seven-route set;
3. Chromium and Firefox at 375 and 1440 pixels;
4. the caps and tolerance method above;
5. the exclusions above;
6. `AtlasReaper311/atlas-systems` as the enforcement repository.

## Enforcement boundary

The implementation must use branch `perf/browser-budget-gates` in
`atlas-systems` and add a versioned policy consumed by the existing deterministic
browser evidence harness. It must:

- block selected route, browser, and viewport combinations even when the route
  is not otherwise classified as changed;
- fail closed when an expected measurement is missing;
- report measured values, caps, and violations in `evidence.json`;
- preserve reviewed reporting-baseline reconciliation;
- preserve 1920 as reporting-only;
- exclude non-first-party resources;
- leave `data/performance-baseline.json` and static drift checks unchanged.

Phase 14 closes only after the enforcement pull request is exact-head green,
merged with the reviewed head guard, deployed through the normal `main` path,
and the exact production commit and live route contract are verified and
recorded in this document and `docs/work-allocation.md`.
