# Atlas Trace contracts and offline assembler

Wave 3.1 defines the read-oriented evidence relationship model used by later Atlas Trace runtime and portfolio work.

## Scope

Atlas Trace connects evidence that already exists across Atlas Systems. It does not create deployment authority, incident-response authority, or a mutable graph database.

The Wave 3.1 implementation is deliberately offline:

- contracts live under `contracts/v1/atlas-trace/`;
- stable identity rules extend the existing `contracts/v1/fingerprint-rules.json`;
- `scripts/atlas_trace.py` validates contracts and saved evidence;
- the assembler reads local JSON documents only;
- no network request is required;
- no provider credential is required;
- no production state can be changed.

The later bounded public API is a separate programme gate.

## Evidence nodes

`evidence-node.schema.json` defines bounded nodes for existing evidence classes, including repositories, commits, workflow runs, build validation, deployments, live releases, release verification, journeys, reliability results, incidents, recovery, SBOMs, provenance, postmortems and ADRs.

A node carries:

- a deterministic `node_id`;
- a bounded `kind`;
- explicit identity fields;
- visibility classification;
- evidence state;
- one or more digest-protected evidence references.

Repository and commit nodes have additional semantic identity checks. A commit key is the exact `repository@commit_sha` identity.

## Evidence edges

`evidence-edge.schema.json` defines the allowed Atlas Trace relationship vocabulary:

- `SOURCE_OF`;
- `VALIDATED_BY`;
- `DEPLOYED_AS`;
- `VERIFIED_BY`;
- `OBSERVED_BY`;
- `CORRELATED_WITH`;
- `TRIGGERED`;
- `RECOVERED_BY`;
- `DOCUMENTED_BY`;
- `PRODUCED_SBOM`;
- `GOVERNED_BY`;
- `SUPERSEDES`.

Every edge includes a deterministic `edge_id`, an explicit evidence basis, and one or more evidence references.

There is no timestamp-proximity relationship method. `CORRELATED_WITH` is the only relation allowed to use `correlation-with-explicit-evidence`. Other relationships require a stronger named basis such as exact identity, verified runtime identity, release-watch identity, signed provenance, declared governance, or manual attestation.

This prevents temporal proximity from silently becoming causation.

## Evidence graph

`evidence-graph.schema.json` is a bounded deterministic projection.

The graph is limited to:

- 1,000 nodes;
- 4,000 edges.

Validation requires:

- deterministic graph fingerprint;
- exact node and edge counts;
- unique stable identifiers;
- nodes sorted by `node_id`;
- edges sorted by `edge_id`;
- every edge endpoint present in the graph;
- nested node and edge contracts to pass;
- graph visibility to be at least as restrictive as every included node and edge.

The graph fingerprint is derived from graph visibility plus canonical node and edge content. Reordering equivalent inputs therefore cannot change graph identity.

## Canonicalisation and identity

Atlas Trace does not define a second hashing convention.

It reuses the existing control-plane rules:

- UTF-8;
- RFC 8259 JSON;
- lexicographically sorted object keys;
- compact separators;
- Unicode preserved;
- SHA-256 lowercase hexadecimal.

The existing `fingerprint-rules.json` now carries a dedicated `trace_rules` section for node, edge and graph identities. The Wave 3.1 validator treats those v1 rules as fixed. A stable identity input change requires a new major contract version under the existing compatibility policy.

## Privacy boundary

Evidence documents carry `public`, `internal`, or `restricted-metadata` visibility.

A container cannot reference evidence with a more restrictive visibility than its own. A public graph therefore cannot contain an internal or restricted node, edge, or evidence reference.

Wave 3.1 still does not have enough authority to decide whether an arbitrary repository or service identity is approved for public publication. For that reason, the offline assembler refuses to emit `public` graphs.

The later bounded public Atlas Trace projection must cross-check identities against the explicit public estate authority before emitting them. This keeps private repository names, private service identities, routes, deployment identities, provider payloads and incident details out of public output by construction rather than assumption.

## Secret boundary

The assembler reuses the existing control-plane recursive sensitive-key check. Secret-bearing properties such as authorization, cookies, passwords, private keys, secrets and tokens are rejected.

Evidence references are bounded to digest metadata and optional HTTPS references without query strings. Raw provider payloads have no field in the Atlas Trace contracts.

## Offline input layout

The assembler consumes saved node and edge documents:

```text
input/
  nodes/
    *.json
  edges/
    *.json
```

Each document must already satisfy its standalone contract.

Example:

```bash
python3 scripts/atlas_trace.py validate-contracts

python3 scripts/atlas_trace.py assemble \
  --input-dir ./saved-trace-input \
  --output /tmp/atlas-trace.json \
  --visibility internal

python3 scripts/atlas_trace.py check \
  --input /tmp/atlas-trace.json
```

`assemble` accepts only `internal` and `restricted-metadata` output in Wave 3.1.

The emitted graph uses canonical JSON bytes. Re-running the assembler with identical evidence, including different source-file ordering, produces byte-identical output.

## Failure behaviour

Atlas Trace fails closed when:

- a contract or fixture is malformed;
- a deterministic identifier does not match its canonical inputs;
- a secret-bearing property appears;
- a correlation relation lacks explicit correlation evidence;
- a non-correlation relation uses correlation basis;
- an edge references a missing node;
- a visibility boundary is crossed;
- graph ordering or counts are inconsistent;
- assembled graph bytes are changed from canonical output;
- public assembly is requested before the later publication-authority gate exists.

Missing or unknown evidence is not converted into healthy evidence. The node vocabulary carries explicit `unverified`, `stale`, `unavailable`, and `unknown` states for that purpose.

## Programme boundary

Wave 3.1 provides the contracts and deterministic offline architecture only.

It does not:

- call GitHub, Cloudflare, Ollama, Open WebUI, or Home Assistant;
- collect live topology;
- expose a public Atlas Trace endpoint;
- create a Proof Chain UI;
- modify a model or configuration;
- create a deployment, rollback, remediation, or repository mutation path.

Those capabilities remain behind their later programme gates.
