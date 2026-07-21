# Wave 3.1 governance contracts

Wave 3.1 establishes the remaining offline contracts required before Atlas Systems gains new runtime evidence capability. These contracts are data and validation only. They do not deploy, delete, archive, install a model, alter a provider, or grant a component new write authority.

## Contract location

The contracts live under `contracts/v1/wave3/` and reuse the canonical JSON and SHA-256 rules in `contracts/v1/fingerprint-rules.json`.

`wave3_rules` is deliberately separate from the closed root contract fingerprint inventory and from Atlas Trace's `trace_rules`. The hashing implementation is still the same `scripts/control_plane_contracts.py` authority.

Validation is provided by:

```bash
python3 scripts/wave3_contracts.py check --root .
```

The validator is standard-library only and performs no network calls.

## Retirement evidence

`retirement-evidence.schema.json` records how far a repository or service has progressed through retirement.

States are:

- `active`;
- `deprecation-proposed`;
- `deprecated`;
- `dependency-clear`;
- `runtime-removed`;
- `publication-removed`;
- `archived`.

GitHub `archived=true` is not treated as proof that a runtime is retired. An `archived` evidence record fails closed unless dependency, route, binding, manifest, Worker allowlist, production PR, historical evidence, and recovery implications are all `verified` or explicitly `not-applicable`.

The contract is evidence only. It cannot archive a GitHub repository, delete a Worker, remove DNS, remove secrets, or destroy storage.

## ADR-to-runtime relationships

`adr-runtime-relationship.schema.json` is the machine-readable projection of scope declared in the existing Markdown ADR frontmatter.

ADRs remain the decision authority. Their frontmatter now declares affected:

- repositories;
- services;
- contracts;
- policies;
- visibility.

`scripts/adr_trace.py` validates those references against current Atlas Infra authority and emits deterministic relationship records. Unknown references fail closed.

Two accepted authority documents predate the `ADR-NNNN-*` filename convention. Their established paths remain unchanged because current source refers to those names. A bounded `slug` frontmatter field identifies those legacy filenames; new ADRs continue using the normal numbered filename convention.

Run:

```bash
python3 scripts/adr_trace.py check --root .
```

or emit a canonical local projection:

```bash
python3 scripts/adr_trace.py emit --root . --output /tmp/adr-runtime-index.json
```

No provider or runtime access is involved.

## Model promotion contract

`model-promotion.schema.json` defines the evidence card that `atlas-eval-harness` will use in the next programme stage.

A promotion record binds one capability to:

- exact model identity where available;
- prompt/configuration fingerprints;
- retrieval and corpus identity where relevant;
- exact evaluation-suite revision;
- evaluation evidence fingerprint and stable reference;
- observed pass rate and required threshold;
- explicit human approval;
- supersession history where applicable.

A candidate below its declared minimum pass rate is invalid.

This contract does not pull or delete an Ollama model, alter Open WebUI, modify Home Assistant, restart services, or change a model routing table. Those remain separate owner-approved rollout actions.

## Privacy boundary

The recursive control-plane secret-key check applies to all three contracts.

The ADR validator accepts only repository and service identities present in current public Atlas authority because the ADR source itself is held in the public `atlas-infra` repository. Private identities therefore cannot be smuggled into a public ADR relationship.

Model promotion records default to an internal evidence use case. A later public projection must be separately bounded and sanitized before any portfolio surface exposes promotion evidence.

## Gate

Wave 3.1 is ready to close when:

1. Atlas Trace contracts and assembler remain green;
2. all three governance contracts pass positive and negative fixtures;
3. current ADR scope validates deterministically;
4. repository-native CI is green;
5. no live integration or provider mutation is required to prove the contract layer.
