+++
id = "ADR-0019"
date = 2026-09-15
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-infra"]
services = []
contracts = ["atlas-control-plane/public-model-promotion-projection/v1"]
policies = ["policy/model-promotion-public-projection.json"]
+++

# ADR-0019: Public Model Promotion projection authority

## Context

Roadmap Phase 4 needs a public, read-only explanation of how a model was
evaluated and approved for a named capability. The existing Wave 3
`model-promotion` contract is internal evidence. It contains configuration
and evidence references that are not a public presentation contract. Reusing
that record would make private evaluation inputs part of the public boundary.

The accepted lifecycle remains the one defined by ADR-0013 and ADR-0014:

`EVAL PREPARED -> EVAL PASSED -> HUMAN REVIEWED -> PROMOTION APPROVED`

The mapping is `SOURCE -> CHECKED`, with `HUMAN REVIEWED` as an observation
gate on `CHECKED`, and `PROMOTION APPROVED -> MERGED`. The promotion profile
has `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, and `LIVE VERIFIED`
as `NOT APPLICABLE`. A promoted model can still be absent from, or differ
from, a runtime. That is a separate runtime-model observation subject.

## Decision

`AtlasReaper311/atlas-infra` owns the public contract, compatibility rules,
public allowlist policy, lifecycle mapping, regression vocabulary, and
fail-closed validation at
`contracts/v1/public-model-promotion-projection.schema.json` and
`policy/model-promotion-public-projection.json`.

The public contract contains only:

- a capability identifier from the explicit public capability allowlist;
- a public model identifier from the explicit public model allowlist, or
  `null` when no accepted evaluation, exemption, or observation exists;
- a public suite version and a suite fingerprint that identifies the
  public-safe suite description, not a private source revision;
- case count, passed count, failed count, pass rate, and minimum threshold as
  one aggregate result object;
- bounded evaluation categories and the versioned known-regression
  vocabulary;
- evaluation, human-review, promotion, freshness, and explicit gap states;
- public projection fingerprints for this public object and safe supersession
  links between public projections;
- a separate current-model observation subject when later evidence is
  intentionally represented; and
- fixed privacy and deployment-boundary declarations.

The contract is an allowlist. Every object rejects additional properties.
Unknown or unclassified source fields are dropped before projection and fail
validation if they appear in the public document. Prompts, raw answers,
reasoning traces, private source context, private identities, local paths,
hosts, endpoints, IP addresses, runtime configuration, internal evidence
URIs, secret-like values, and private provider evidence are outside the
contract. The schema does not provide a field through which those values can
pass.

The public regression vocabulary is deliberately small and versioned:

- `unsupported-fabrication`;
- `failed-abstention`;
- `grounding-failure`;
- `unsupported-causal-claim`; and
- `format-contract-failure`.

The vocabulary contains category codes only. It does not expose prompts,
answers, or model-specific prose.

The projection fingerprint is a SHA-256 digest of the public fields selected
by `contracts/v1/fingerprint-rules.json`, after the repository canonical JSON
rules are applied. It identifies the public projection content. It does not
identify the private model configuration, prompt, runtime options, or source
evidence. Set-like category and gap arrays are sorted before hashing.

Freshness describes evaluation and promotion evidence only. `CURRENT`,
`STALE`, `SUPERSEDED`, and `UNKNOWN` do not describe deployment, runtime
health, or live behaviour. The `deployment_boundary` object fixes promotion
records to:

`PROMOTION APPROVED != DEPLOYED`

and marks deployment, deployed identity, runtime verification, and live
verification as `NOT APPLICABLE` for this subject.

No generated production artifact is registered in
`policy/public-boundary-projections.json` by this decision because no such
artifact exists yet. Registration becomes a separate change when a real
public file and serving owner exist.

## Ownership and sequencing

`atlas-eval-harness` owns private evaluation and promotion evidence. Its later
deterministic sanitizer may produce this projection, but this ADR does not
change that repository or approve a model.

`atlas-systems` may present a future accepted projection. It does not become
the evidence or lifecycle authority.

No current evaluation result, model promotion, routing decision, deployment,
provider mutation, runtime change, or publication is part of this contract
change. Synthetic fixture values are used for validation only.

## Consequences

The future Observatory can compare capability-scoped public summaries without
receiving private evaluation material or treating approval as deployment. A
pass rate cannot be shown without its capability, relevant case count, and
minimum threshold. Missing evidence remains explicit as `UNKNOWN`,
`NOT OBSERVED`, `STALE`, `SUPERSEDED`, or `NOT APPLICABLE`; it is never
converted into `FAIL`.

The first production projection will require a separately reviewed producer
change, a public-safe artifact registration, and downstream presentation work.
This ADR defines those boundaries but does not perform them.
