# Public interface successor evidence-mode authority

Status: accepted source authority on the successor programme authority branch. Merge remains separately approval-gated.

## Purpose

This record converts source-confirmed trust defects in Atlas Systems evidence surfaces into a bounded additive extension under ADR-0008.

It defines how an interface states the origin and confidence boundary of displayed evidence. It does not change runtime-state calculation, maturity, endpoint contracts, anomaly calculations, conformance calculations, product-generated output, or provider state.

## Evidence basis

The inspected Atlas Systems baseline is:

- repository: `AtlasReaper311/atlas-systems`;
- commit: `3971669be15d2cc26f7ba0dd0a644716578ef88d`.

The source-confirmed findings are:

- `LAB-007a`: Estate Conformance uses literal zero values for errors, warnings, and unknown findings when no report was loaded;
- `LAB-007b`: Shape Detector generates a synthetic telemetry history after a failed fetch, then presents the generated state, score, metrics, and chart with live runtime-state semantics;
- the Lab and Systems directories describe Shape Detector as recorded replay even though its fallback is generated in the browser and stands in for measurements that were not taken.

The five-PR repair tranche that precedes this authority fixed responsive, accessibility, diagnostic, and initialisation defects. It intentionally did not change evidence meaning.

## Authority model

The base authority remains:

- `docs/adrs/ADR-0008-public-interface-system-v2.md`;
- `policy/public-interface-system-v2.json`;
- `policy/public-interface-contract.json`.

The additive evidence-mode authority is:

- `policy/public-interface-evidence-mode-extension-v1.json`;
- `contracts/v1/public-interface/public-interface-evidence-mode-extension.schema.json`;
- `scripts/validate_public_interface_evidence_mode_extension.py`.

A new ADR is not required. ADR-0008 already requires experiments to identify live, replayed, or simulated data and assigns shared interface governance to Atlas Infra. This extension makes that accepted direction executable without silently changing the base `2.0.0` policy.

## Separate axes

The interface must keep three questions separate:

1. Maturity: what public commitment does the surface make?
2. Runtime state: what condition is the system in?
3. Evidence mode: how was the displayed claim obtained?

A surface may be an Experiment while displaying Measured evidence. A Production surface may display Unavailable evidence. A simulated scenario may describe a warning condition without claiming that the live estate is degraded.

## Evidence modes

The accepted evidence-mode vocabulary is:

1. `measured`: current evidence from a live bounded source;
2. `stale-measured`: previously measured evidence retained after its freshness window;
3. `recorded-replay`: captured evidence played back without a claim about the current condition;
4. `simulated`: synthetic values standing in for measurements that were not taken;
5. `unavailable`: the expected evidence source did not provide evidence;
6. `unknown`: the source, meaning, or state cannot be determined;
7. `not-applicable-unscored`: the measure does not apply or is excluded from scoring.

Measured and stale-measured evidence may carry semantic runtime-state colour on evidence-bearing operational surfaces. Recorded replay, simulated, unavailable, unknown, and not-applicable or unscored evidence use neutral treatment.

Colour is never the only signal.

## Generated output is not evidence

The directory data-mode vocabulary remains:

- Live;
- Replay;
- Generated;
- Simulated.

Generated output is the product's output and does not stand in for a measurement. Signal Garden audio, a drawing produced in the browser, or a seeded product score can retain product-specific visual identity when they make no claim about a real system.

Generated is therefore not an eighth evidence mode. Simulated evidence is different because it manufactures a value that stands in for an unobserved measurement.

## Presentation contract

Evidence-bearing operational surfaces require:

- a visible evidence-mode label;
- `data-evidence-mode` with one accepted machine-readable value;
- a separate `data-runtime-state` attribute when runtime state is presented;
- text, surface treatment, and numeral convention as redundant signals;
- source and age for measured, stale-measured, and recorded replay evidence;
- a persistent fallback-mode treatment across the primary state, metrics, tables, and charts;
- agreement between directory labels and destination behaviour.

The following claims are forbidden:

- representing unavailable evidence as zero;
- representing unknown evidence as zero;
- representing not-applicable or unscored evidence as zero;
- applying live runtime-state colour to replayed or simulated values;
- describing browser-generated synthetic measurements as recorded replay;
- hiding the evidence mode only in supporting prose while the primary state appears authoritative.

Unavailable and unknown numeric evidence uses an em dash. Not-applicable or unscored evidence uses an explicit text label.

## Implementation ownership

`AtlasReaper311/atlas-interface-kit` owns the shared selectors, neutral evidence-mode foundations, machine-readable component contract, and release fingerprints.

Consumers own:

- evidence source selection;
- runtime-state calculation;
- mode selection from real source conditions;
- wording and source metadata;
- product-specific rendering;
- repository-native tests;
- preview and visual approval.

The intended Interface Kit release is `0.5.0`. Release source, tag creation, workflow execution, GitHub Release publication, consumer adoption, and consumer production rollout remain separate approval gates.

## First consumer sequence

After immutable Interface Kit release publication, the first Atlas Systems consumer work is:

1. correct Estate Conformance unavailable counts without changing its endpoint or score calculation;
2. give Shape Detector's generated fallback persistent Simulated treatment without deleting its demonstration value;
3. align Lab and Systems directory data-mode wording with the destination;
4. add executable browser assertions for the evidence-mode attributes, visible labels, neutral fallback treatment, and zero prohibition.

These consumer changes require independent pull requests, deterministic preview evidence, and manual visual approval.

## Excluded work

This authority change excludes:

- consumer source changes;
- consumer deployment;
- provider settings and secrets;
- runtime routing;
- endpoint changes;
- anomaly or conformance calculation changes;
- generated product-output reclassification;
- System Symphony scenario palette changes;
- maturity or runtime-state taxonomy changes;
- directory layout changes;
- global navigation redesign.

## Open pull-request boundary

Open `atlas-infra#105` owns `docs/work-allocation.md`, so this authority change does not edit that file.

Open `atlas-infra#112` changes RAMONE control-plane publisher files and does not overlap this extension.

## Rollback

Revert the authority pull request.

No provider rollback, consumer rollback, deployment rollback, data migration, secret rotation, Interface Kit release rollback, or publication rollback is required because this gate changes source authority only.
