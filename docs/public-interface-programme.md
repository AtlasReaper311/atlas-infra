# Atlas Systems public interface programme

Status: complete.

Started: 28 July 2026.

Closed: 5 August 2026.

## Final programme state

Phases 0 through 15 are complete at their required authority, source, immutable
release where applicable, consumer adoption, deterministic preview, production
deployment, exact live commit, browser evidence, generated refresh, security,
and rollback boundaries.

The detailed historical evidence remains in the phase-specific records under
`docs/public-interface-phase-*.md` and in repository history. The final Phase 15
receipt is `docs/public-interface-phase-15-reconciliation.md`.

## Final production baseline

The final programme product commit is:

```text
AtlasReaper311/atlas-systems
3be62f8915c0022e68187d9a66d9a808e87b6caa
```

It was produced by `atlas-systems#198` from reviewed head:

```text
52e1dfda7bd26e20bb824ce61da721a231887734
```

Deterministic preview run `30996286181` proved 22 of 22 governed Lab card
signatures in Chrome and Firefox at 320, 375, 768, 1024, 1440, and
reporting-only 1920 pixels, with zero blockers and zero browser-budget
violations.

Production run `30999896059` proved the exact merge commit on
`https://atlas-systems.uk`, passed Pages, HTML, routing, footer, homepage
AtlasField, and System SYMPHONY production checks, and completed the guarded
Atlas Corpus refresh.

## Phase summary

| Phase | Outcome | State |
| --- | --- | --- |
| 0 | Programme control and current-state rebaseline | complete |
| 1 | Verified System SYMPHONY baseline | complete |
| 2 | Main-site browser evidence harness and deterministic static baseline | complete |
| 3 | Comparable supporting-product evidence | complete |
| 4 | Accepted foundation authority and immutable interface-kit release | complete |
| 5 | Main-site shared-foundation adoption | complete |
| 6 | Footer authority, kit primitive, generator, scheduler, and consumers | complete |
| 7 | Metadata, identity, canonical URLs, and supporting-product error behaviour | complete |
| 8 | Measured accessibility and responsive corrections | complete |
| 9 | Reliability, Observability, and Evidence analytical surfaces | complete |
| 10 | Writing directory and article reading pipeline | complete |
| 11 | Lab interaction and wayfinding slices | complete |
| 12 | Status, CV, Ramone, Public API docs, and JSON-only API index alignment | complete |
| 13 | Normative AtlasField composition catalogue | complete |
| 14 | Accepted blocking browser resource budgets | complete |
| 15 | Receipt reconciliation, live audit, final correction, deployment, and closeout | complete |

## Enduring authority

The programme leaves these decisions active:

- `atlas-infra` owns public-interface governance, policy, schemas, validators,
  adoption rules, and rollback rules.
- `atlas-interface-kit` owns shared implementation and immutable releases.
- Consumers keep repository-local pinned assets and do not load another Atlas
  repository at runtime.
- `atlas-systems` owns the primary portfolio, Systems, Work, Writing directory,
  Lab, AtlasField consumers, and System SYMPHONY browser experience.
- `atlas-article-gen` owns canonical Markdown, templates, parsing, rendering, and
  generated drafts.
- `atlas-scheduler` owns publication order, timing, refresh receipts, and the only
  production write path for generated article output in `atlas-systems`.
- `atlas-api-index` remains JSON-only.
- Ramone interface changes must preserve inference, tunnel, Turnstile, rate
  limit, SSE, grounding, binding, secret, and runtime-decision boundaries.
- Serious accessibility failures and accepted browser budgets remain blocking.
- Reporting-only evidence must remain visible and honestly classified.

## Deployment and preview model

The accepted `atlas-systems` model remains:

1. pull-request checks;
2. optional `interface-preview-approved` label;
3. isolated non-production Cloudflare preview and deterministic browser evidence;
4. explicit owner approval to merge an exact reviewed head;
5. automatic production deployment from `main`;
6. exact custom-domain commit verification, production smoke, and guarded Corpus
   refresh.

Merge approval is production rollout approval for this repository. No second
manual deployment dispatch is required. Cloudflare Pages native Git integration
is not used for this path.

## Intentional differences and follow-ups

The programme closes with these separate follow-ups:

- **LAB-007a:** missing Conformance evidence currently renders four literal zero
  counts. A new programme must render unavailable, unknown, or unscored state
  instead of a false clean result.
- **Mode 04:** Shape Detector retains its deterministic demonstration, but all
  related labels must identify it as `Simulated`, never live or replay.
- **SONIN:** preserve strict CSP and recover any canonical article source through
  `atlas-article-gen` and `atlas-scheduler`. Do not hand-edit published HTML.
- **Superseded responsive work:** `atlas-systems#179` is closed. Reimplement any
  still-valid 44-pixel or tablet-header corrections from current `main` only.

These are inputs to future controlled work. They do not invalidate the completed
Phase 15 source and deployment receipts.

## Security and privacy closeout

The programme exposed no secret, changed no provider binding or environment,
weakened no CSP, altered no Ramone inference contract, and hand-edited no
generated article output. Production writes occurred only through approved
repository and scheduler contracts.

## Rollback

The final product rollback point is a reviewed revert of
`3be62f8915c0022e68187d9a66d9a808e87b6caa`, followed by the normal automatic
production deployment and exact live verification.

Each supporting product retains its repository-owned rollback contract. Article
rollback remains generator and scheduler owned.

## New programme boundary

No new interface implementation is authorised by this closeout.

A successor programme must perform a fresh Part 0 inspection against current
GitHub state, accepted ADRs, executable policy, current interface-kit assets,
preview and deployment workflows, generated-output ownership, and live evidence.
The completed design audit and prototypes are inputs, not current-state proof.
