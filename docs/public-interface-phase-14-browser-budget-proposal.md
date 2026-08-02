# Public interface programme Phase 14 browser budget proposal

Status: proposed authority; not accepted and not enforced.

Started: 2 August 2026.

## Purpose

Phase 14 promotes reviewed browser-performance measurements into selected
blocking budgets only after evidence supports the metric, value, tolerance, and
exclusion. This document is the authority proposal. It does not add enforcement
code, change product runtime, dispatch workflows, deploy production, or weaken
the existing deterministic static baseline.

## Current baseline

- `atlas-infra/main`: `a3627dde153201068b563c74cd3b229a1d0f8e69`.
- `atlas-systems/main`: `0fd7a98aeaea523f18914c3c7f134fa96607406b`.
- Phase 13 merged through `atlas-infra#117` as
  `a3627dde153201068b563c74cd3b229a1d0f8e69`.
- Current `atlas-systems/data/performance-baseline.json` remains
  `blocking_thresholds: false` and fingerprint
  `f330bfb924ad55927c40b79d21ad74fb18f235866f3a1a328530b59bf2e1a96d`.

## Evidence inspected

### Locked decisions

- Static performance baseline drift is already blocking in `atlas-systems` CI.
- Static size thresholds remain reporting-only.
- Browser performance evidence remains reporting-only until Phase 14 accepts
  specific budgets.
- The 1920-pixel viewport remains reporting-only and is not a blocking budget.

### Reviewed browser evidence cycles

| Pull request | Run | Head SHA | Artifact | Digest | Notes |
| --- | --- | --- | --- | --- | --- |
| `atlas-systems#168` | `30386218935` | `4dafa7d1d4690e94e36e9342e672d41307633d19` | `8699615072` | `sha256:7d3662cdc835c5195bcca30395cc398b5423286b768ae4fdeed6d32bfd38caec` | Original reviewed browser-evidence harness cycle; 36 reporting findings accepted, not performance budgets. |
| `atlas-systems#189` | `30722335070` | `353cb62cd3e25856bd644f3c7505e76dd399eb73` | `8825413605` | `sha256:501eb141cac8474ef7f87e12a82d985c21b57a566c3cf4736fe8e0a6109403f2` | Lab context preview evidence. |
| `atlas-systems#190` | `30724694572` | `44e467899692ce8a8cd6f4544eb351e0861eb5f5` | `8826116404` | `sha256:31a5b8cb379dccf32a4040781cc9046ec25b7a3df8762e7d1d94c1999aac9870` | Lab evidence-tool preview evidence. |
| `atlas-systems#191` | `30742333958` | `2d98d61dbd429ff77e4810d39b1ad26dd6ee7e6b` | `8831862825` | `sha256:0c13b0a912eab612175013af316e3e52839a11a237cf2e43746577a8eddb827f` | Signal Garden preview evidence. |
| `atlas-systems#192` | `30743826242` | `c3cdc62ef9886cfd9569272de6caf4e6fbfec3cc` | `8832353944` | `sha256:465f5fde26078cea91bc6c6c87345c128e43c0a8387b26a98628578fa37f2a28` | Final Phase 11 Lab preview evidence. |

The recent cycles prove that the browser harness captures resource metrics and
that the visual/accessibility gates are repeatable. They do not by themselves
accept resource budgets; this proposal is the approval boundary.

### Fresh local candidate measurement

A local resource cycle was captured from current `atlas-systems/main` served at
`http://127.0.0.1:4175` using Playwright Chromium and Firefox with reduced
motion at 375 and 1440 pixel widths. The raw measurement was written outside
the repository at `/tmp/atlas-phase14-browser-resource-metrics.json`.

The launch required unsandboxed local browser execution because macOS denied
Playwright process registration inside the sandbox. No external route, mutation
endpoint, provider setting, secret, binding, deployment, or workflow dispatch
was used.

## Proposed blocking metrics

These metrics are suitable for the first accepted browser-budget gate because
they are captured by the existing browser evidence harness and are less
environment-sensitive than paint timing:

- `requestCount`;
- `encodedBytes`;
- `decodedBytes`;
- `scriptCount`;
- `styleCount`.

The first enforcement pass should apply only to:

- representative Atlas Systems routes listed below;
- Chromium and Firefox;
- 375 and 1440 pixel viewports;
- deterministic preview evidence with reduced motion and service workers
  blocked;
- first-party resource entries captured through the browser performance API.

## Proposed values

The proposed caps use the maximum observed value from the fresh local cycle,
plus two requests for request count, plus one file for script/style counts, and
plus 12 percent rounded up to the next KiB for byte counts.

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

Do not promote these into blocking budgets in the first pass:

- 1920 pixel viewport measurements;
- paint timing, LCP, CLS, FCP, TTFB, CPU timing, memory, and animation frame
  timing;
- network `transferSize` from live or preview deployments;
- third-party analytics or browser-extension requests;
- fixture-host 503 responses used by deterministic evidence;
- external embeds such as YouTube;
- production live measurements where CDN, cache state, and network path are not
  controlled;
- routes not listed in the proposed value table.

## Rationale

Request count and encoded/decoded byte totals catch common performance
regressions without claiming more precision than the current evidence supports.
They also complement the existing static baseline drift check: static drift
proves source weight changes, while browser resource budgets prove the rendered
page is not accidentally pulling extra first-party resources.

Runtime timing remains excluded because the current evidence set does not prove
stable route-and-device timing across enough controlled cycles. The first
budget gate should be a resource gate, not a synthetic Core Web Vitals claim.

## Approval boundary

This proposal must stop at review. Merging or enforcing browser budgets requires
explicit owner acceptance of:

1. the selected metrics;
2. the route and viewport set;
3. the proposed caps and tolerances;
4. the exclusions;
5. the follow-up repository where enforcement will live.

If accepted, the next implementation should update `atlas-systems` on
`perf/browser-budget-gates` by adding a budget policy consumed by the existing
browser evidence harness. It must not weaken
`data/performance-baseline.json`, skip static drift checks, or silently accept
new reporting findings as blockers.
