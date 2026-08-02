# Public interface programme Phase 13 coordination

Status: active; catalogue and validator drafted.

Started: 2 August 2026.

## Purpose

Phase 13 creates the normative AtlasField composition catalogue and validation
gate required before later visual or performance phases. It records the current
approved compositions, their route bindings, their source authority, and the
minimum evidence a future consumer change must provide.

This phase is documentation and validation only. It does not create a public
route, alter product runtime code, move renderer ownership, publish an
interface-kit release, change provider settings, change bindings, touch
secrets, dispatch workflows, or deploy production.

## Current source baseline

- `atlas-infra/main`: `e5826586e77b26d50b0f4c78511db46a4a535fc7`.
- `atlas-systems/main`: `0fd7a98aeaea523f18914c3c7f134fa96607406b`.
- `atlas-interface-kit/main`: inspected as clean; no AtlasField runtime source
  exists there at Phase 13 start.
- Open `atlas-infra` pull requests at start: `#105`, `#109`, `#110`, `#111`,
  and draft `#112`; none touch the AtlasField catalogue path.
- Open `atlas-systems` pull requests at start: draft `#179` and Dependabot
  `#123`; Phase 13 does not edit `atlas-systems` source.

## Accepted authority

Phase 13 follows:

1. `docs/public-interface-programme.md` Phase 13, which limits the outcome to a
   normative AtlasField composition catalogue and validation;
2. `atlas-systems/docs/ATLAS_FIELD.md`, the current consumer contract;
3. `atlas-systems/static/js/atlas-field-composition-registry.js`, the current
   runtime composition registry;
4. accepted public-interface ADR and policy in `atlas-infra`;
5. the repository operating rules in `AGENTS.md`.

## Protected contracts

- AtlasField remains decorative; essential information stays in ordinary DOM
  content above the canvas.
- Route-specific product identity remains local. Reuse must not flatten
  Systems, Lab, About, or directory surfaces into a single generic treatment.
- Colour and motion must not be treated as live status, provider truth, private
  state, or operational evidence.
- New compositions require a real product need and a catalogue update before
  source adoption.
- Generated or canonical AtlasField source must not be hand-edited downstream.
- Interface-kit release creation and consumer adoption remain separate approval
  gates if a later phase moves any AtlasField primitive into the shared kit.

## Draft implementation

| Artefact | Path | Purpose |
| --- | --- | --- |
| Human catalogue | `docs/atlasfield-composition-catalogue.md` | Records approved compositions, source authority, change rules, and evidence requirements. |
| Machine catalogue | `policy/atlasfield-composition-catalogue.json` | Provides the deterministic control-plane record and fingerprint. |
| Validator | `scripts/validate_atlasfield_composition_catalogue.py` | Fails closed on scope drift, unbounded composition changes, route drift, parameter drift, and fingerprint drift. |
| Unit tests | `scripts/tests/test_validate_atlasfield_composition_catalogue.py` | Validates the committed catalogue and negative cases. |

## Current catalogue

| Composition | Route | Selector | Source seed |
| --- | --- | --- | --- |
| `identity-field` | `/about/` | `.page-header` | `atlas-about-identity-field-v2` |
| `proof-trace` | `/systems/evidence/` | `.focus-hero` | `atlas-evidence-proof-trace-v1` |
| `pulse-horizon` | `/systems/reliability/` | `.focus-hero` | `atlas-reliability-pulse-horizon-v2` |
| `signal-bloom` | `/lab/` | `.page-intro` | `atlas-lab-signal-bloom-v2` |
| `telemetry-lattice` | `/systems/observability/` | `.focus-hero` | `atlas-observability-telemetry-lattice-v1` |

Catalogue fingerprint:
`sha256:9a739d2588a851b7e5918ea9545c831c8676e8eebee717bd223abfc1d86e1fdb`.

## Validation receipts

Local checks before pull-request review:

- `python3 scripts/validate_atlasfield_composition_catalogue.py`: pass.
- `python3 -m unittest scripts.tests.test_validate_atlasfield_composition_catalogue -v`: 5 tests, pass.

Full repository validation, pull request checks, and merge receipts must be
added before the phase is called complete.

## Approval boundary

The Phase 13 branch may proceed as a documentation and validation pull request.
It must stop if validation shows a current AtlasField source defect, if a later
source change is required, or if any work would alter product runtime code,
public routes, provider configuration, secrets, bindings, release publication,
or production deployment.
