# Architecture decision records

One file per decision, capturing why the estate does something a particular way, so the reasoning outlives the memory of making it. These sit beside `decisions.md`: `decisions.md` is the running log of smaller calls, an ADR is a standalone record for a decision with lasting structural weight.

## Format

Each record is Markdown with a `+++` delimited TOML frontmatter block:

```toml
+++
id = "ADR-0001"
date = 2026-07-02
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-index"]
services = ["atlas-api-index"]
contracts = ["atlas-control-plane/service-contract/v1"]
policies = ["policy/estate-registry.json"]
+++
```

`id` is `ADR-NNNN`, zero-padded and sequential. `date` is the day the status last changed. `status` is one of `proposed`, `accepted`, or `superseded`. A record that replaces another carries `supersedes = "ADR-MMMM"`.

Wave 3 adds machine-readable scope without creating another ADR authority. `repositories`, `services`, `contracts`, and `policies` declare the exact current Atlas identifiers affected by the decision. `visibility` is `public`, `internal`, or `restricted-metadata`. The offline ADR validator fails closed when a declared repository, service, contract, or policy does not exist in the current public Atlas authorities.

Normal ADR filenames still begin with their `ADR-NNNN` id. Two pre-existing accepted authority documents keep their established filenames because other source refers to those paths; those records carry a `slug` equal to the filename stem. `slug` is a compatibility exception for those existing paths, not the normal naming convention for new ADRs.

The body has three sections: Context (what forced the decision), Decision (the rule now in force), and Consequences (what it makes true, good and bad).

## Lifecycle

A record opens as `proposed`, becomes `accepted` when the estate adopts it, and moves to `superseded` when a later record replaces it. A superseded record is never deleted; the decision was real and its reasoning still explains the shape of what came after.

## Traceability

`scripts/adr_trace.py` parses the same Markdown files, verifies the scope against current Atlas Infra authority, and deterministically emits `atlas-control-plane/adr-runtime-relationship/v1` records. Atlas Trace can consume those records as `GOVERNED_BY` evidence. The Markdown remains the decision authority; the generated relationship is a validated projection of its frontmatter.

The parser uses local repository state only. It performs no GitHub, Cloudflare, or other provider calls and cannot mutate runtime state.

## Ingestion

`atlas-corpus` fetches this directory on every ingest and indexes each record with its id, status, and date as metadata, so the estate's search can answer why a thing is the way it is. `TEMPLATE.md` and this `README.md` are skipped. A record with malformed frontmatter is logged and skipped rather than indexed, so a broken file never poisons the corpus.

## Adding one

Copy `TEMPLATE.md` to `ADR-NNNN-short-slug.md`, take the next free number, write the three sections, declare only scope identifiers that current Atlas authority can prove, and set `status = "accepted"` when it is adopted. Run `python3 scripts/adr_trace.py check --root .` before review. The next corpus refresh picks up the source document after a separate rollout where applicable.
