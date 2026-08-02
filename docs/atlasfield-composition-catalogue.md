# AtlasField composition catalogue

Status: accepted for Public Interface System Phase 13.

Catalogue fingerprint: `sha256:9a739d2588a851b7e5918ea9545c831c8676e8eebee717bd223abfc1d86e1fdb`.

## Purpose

This catalogue is the normative control-plane record for the AtlasField
compositions that existed after Phase 12 and before browser-performance gates.
It records what may be mounted, where it may be mounted, and which evidence is
required before a future route can add, remove, rename, or remap a composition.

Phase 13 is documentation and validation only. It does not create a public
route, alter renderer source, change product runtime behaviour, write provider
settings, change bindings, touch secrets, or publish a new interface-kit
release.

## Source authority

- Source repository: `AtlasReaper311/atlas-systems`.
- Source main SHA: `0fd7a98aeaea523f18914c3c7f134fa96607406b`.
- Consumer contract: `docs/ATLAS_FIELD.md`.
- Runtime registry: `static/js/atlas-field-composition-registry.js`.
- Machine-readable catalogue: `policy/atlasfield-composition-catalogue.json`.
- Validator: `scripts/validate_atlasfield_composition_catalogue.py`.

## Shared renderer boundary

AtlasField is a decorative canvas primitive. The renderer owns simulation,
adaptive particle budgets, pointer response, reduced-motion behaviour,
visibility pausing, and one-instance-per-host lifecycle. Consumers own the
composition: selector, seed, local colour treatment, masks, gradients, contrast,
and readability.

The allowed renderer presets remain `hero`, `ambient`, and `card`. Current
catalogued compositions all use `ambient` with pointer interaction disabled.
The preset is a behaviour and performance baseline, not a finished visual
identity.

Essential information must remain ordinary DOM content above the field. A field
may support atmosphere and product identity, but it must not encode live status,
provider truth, operational evidence, or private-system state.

## Approved compositions

| Composition | Route | Selector | State key | Seed |
| --- | --- | --- | --- | --- |
| `identity-field` | `/about/` | `.page-header` | `atlasCompositionState` | `atlas-about-identity-field-v2` |
| `proof-trace` | `/systems/evidence/` | `.focus-hero` | `atlasCompositionState` | `atlas-evidence-proof-trace-v1` |
| `pulse-horizon` | `/systems/reliability/` | `.focus-hero` | `atlasCompositionState` | `atlas-reliability-pulse-horizon-v2` |
| `signal-bloom` | `/lab/` | `.page-intro` | `atlasIntroFieldState` | `atlas-lab-signal-bloom-v2` |
| `telemetry-lattice` | `/systems/observability/` | `.focus-hero` | `atlasCompositionState` | `atlas-observability-telemetry-lattice-v1` |

### `identity-field`

The About field is a warm identity orbit behind the page header. It is
decorative only and preserves the About route's content semantics.

### `proof-trace`

The Evidence field is a skewed proof-flow treatment for the Evidence focus
hero. It may suggest evidence texture, but it is not itself a data guarantee.

### `pulse-horizon`

The Reliability field is a monitoring-cadence treatment with amber routing
accents. Its colour and motion must never be used as a live operational status
signal.

### `signal-bloom`

The Lab field supports the Lab directory introduction while preserving the
individual identity of each Lab experiment route. It must not flatten Lab tools
into one shared visual treatment.

### `telemetry-lattice`

The Observability field is a vertical telemetry-lattice treatment for the
Observability focus hero. It is decorative context, not provider telemetry.

## Change rules

1. A new composition requires a real product need and a catalogue revision
   before source adoption.
2. A route remap, selector change, seed change, density change, colour-domain
   change, or light-parameter change must update the machine-readable catalogue
   and fingerprint in the same review.
3. Route-specific product identity remains local. Reuse is allowed only where it
   preserves the route's actual character.
4. Generated or canonical AtlasField source must not be hand-edited downstream.
5. Interface-kit release creation and consumer adoption remain separate gates if
   a later phase moves any AtlasField primitive into the shared kit.

## Evidence requirements

Each routed consumer must provide route-local browser evidence that proves:

- exactly one decorative AtlasField canvas for the host;
- non-zero CSS and bitmap dimensions;
- visible-pixel sampling at a route-appropriate threshold;
- animated frame advancement or a reduced-motion static frame;
- pointer transparency and non-interference with route content;
- no horizontal overflow;
- no AtlasField console errors or page errors.

## Validation

Run the catalogue validator from `atlas-infra`:

```bash
python3 scripts/validate_atlasfield_composition_catalogue.py
```

The validator checks bounded composition names and routes, canonical absolute
paths, selectors, presets, host classes, density, domain breaks, colour-domain
values, light parameters, scope boundaries, and the deterministic fingerprint.
