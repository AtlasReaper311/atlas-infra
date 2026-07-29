# Public interface programme Phase 6 footer authority

Status: Phase 6A authority implementation prepared for review. Phase 6B has not begun.

Opened: 29 July 2026.

## Purpose

Phase 6 defines the shared structural contract for purpose-specific Atlas Systems footers without making every product, tool, or article footer identical.

ADR-0008 already requires a purpose-specific footer and an estate escape. The base policies preserve local product identity, repository-local assets, independent deployment, shared focus behaviour, and same-tab navigation across Atlas-owned HTML surfaces. This phase converts that accepted direction into an executable slot and variant contract.

## Evidence inspected

Part 0 inspected current authority and current footer implementations in:

- `AtlasReaper311/atlas-systems`;
- `AtlasReaper311/status`;
- `AtlasReaper311/atlas-api-public`;
- `AtlasReaper311/ramone-edge`;
- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-article-gen`;
- `AtlasReaper311/atlas-scheduler`;
- `AtlasReaper311/atlas-interface-kit`.

The inspection found four real footer families:

1. estate footers on the primary portfolio surface;
2. product footers on Status, Public API Docs, Ramone, and CV;
3. tool footers on Lab tools and experiments;
4. editorial footers whose previous and next links are computed by the publishing pipeline.

The current interface kit provides the `.atlas-footer` role and outer spacing only. It does not yet define internal slots or variants.

## Accepted contract

The footer role remains `.atlas-footer` and uses a semantic `footer` element.

A normal page has one primary footer. When a page has more than one footer landmark, each requires an accessible name. Empty footers and empty rendered slots are forbidden.

### Slots

| Slot | Requirement | Ownership |
| --- | --- | --- |
| Identity | Required | Consumer-owned name for the estate, product, tool, section, or editorial surface |
| Context | Optional except on tool footers | Consumer-owned local destinations that do not duplicate the complete global navigation |
| Evidence | Optional | Consumer-owned links to relevant source, status, documentation, or operational evidence |
| Sequence | Required only on editorial footers | Consumer- or publisher-owned ordered navigation; article chaining remains scheduler-owned |
| Estate escape | Required | Consumer-owned route from the local surface into the wider Atlas Systems estate |

### Variants

| Variant | Required slots | Optional slots | Forbidden slots |
| --- | --- | --- | --- |
| Estate | identity, estate escape | context, evidence | sequence |
| Product | identity, estate escape | context, evidence | sequence |
| Tool | identity, context, estate escape | evidence | sequence |
| Editorial | identity, sequence, estate escape | context, evidence | none |

Variant selection describes information architecture. It does not permit local consumers to override focus visibility, minimum touch targets, base breakpoints, reduced-motion behaviour, semantic state colours, or link policy.

## Shared behaviour

Footer implementations must:

- use purpose-specific labels;
- avoid reproducing the complete global navigation;
- keep Atlas-owned HTML destinations in the same tab;
- open external destinations in a new tab with `rel="noopener noreferrer"`;
- preserve visible focus;
- provide 44-pixel minimum interactive targets;
- wrap without horizontal clipping;
- retain clearance above fixed mobile bottom navigation;
- preserve reduced-motion behaviour;
- keep runtime assets repository-local;
- introduce no shared runtime JavaScript or remote presentation dependency.

## Ownership

### `atlas-infra`

Owns policy, schema, validation, release approval, and accepted architecture traceability.

### `atlas-interface-kit`

May implement selectors, layout foundations, responsive behaviour, and focus foundations after a separate Phase 6B approval.

It must not own consumer wording, consumer destinations, publication sequencing, or runtime data.

### `atlas-article-gen`

Owns the article shell, the single scheduler footer placeholder, and generator tests.

It does not own due-date selection, published previous and next chaining, or production writes.

### `atlas-scheduler`

Owns published article footer chaining, previous and next labels, series sequencing, and the only write path into `atlas-systems`.

A dry run and any production execution remain separately approval-gated.

### Consumers

Each consumer owns its footer content, variant selection, local links, rendering integration, tests, preview, and rollback.

Every adoption requires a separate pull request, visual review, merge approval, and rollout approval.

## Distribution

The intended implementation release is `atlas-interface-kit v0.4.0`.

This document does not create that release. Phase 6B must update the kit source, deterministic output, tests, version declarations, release evidence, and immutable distribution under a separate approval.

Consumers may adopt only after the immutable release is published and independently verified.

## Exclusions

Phase 6A does not authorise:

- interface-kit source changes or release publication;
- consumer source changes;
- generated article output edits;
- scheduler or publication execution;
- workflow dispatch;
- deployment;
- provider-setting or secret changes;
- runtime routing changes;
- content rewriting;
- global-navigation redesign;
- Phase 6B.

## Validation

Repository-native validation for this authority change is:

```bash
python3 -m py_compile \
  scripts/validate_public_interface.py \
  scripts/validate_public_interface_foundation_extension.py \
  scripts/validate_public_interface_footer_extension.py
python3 scripts/validate_public_interface.py --root .
python3 scripts/validate_public_interface_foundation_extension.py --root .
python3 scripts/validate_public_interface_footer_extension.py --root .
python3 -m unittest \
  scripts.tests.test_validate_public_interface \
  scripts.tests.test_validate_public_interface_foundation_extension \
  scripts.tests.test_validate_public_interface_footer_extension \
  -v
python3 scripts/adr_trace.py check --root .
git diff --check
```

Pull-request checks remain authoritative for the exact branch bytes.

## Next gate

After this authority pull request is reviewed and merged, Phase 6B requires separate approval to update `atlas-interface-kit`, prepare `v0.4.0`, validate deterministic output, and open a draft pull request.

No consumer, generator, scheduler, release, preview, deployment, or production action is authorised by this record.
