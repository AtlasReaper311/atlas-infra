# Architecture decision records

One file per decision, capturing why the estate does something a particular way, so the reasoning outlives the memory of making it. These sit beside `decisions.md`: `decisions.md` is the running log of smaller calls, an ADR is a standalone record for a decision with lasting structural weight.

## Format

Each record is Markdown with a `+++` delimited TOML frontmatter block:

```
+++
id = "ADR-0001"
date = 2026-07-02
status = "accepted"
+++
```

`id` is `ADR-NNNN`, zero-padded and sequential. `date` is the day the status last changed. `status` is one of `proposed`, `accepted`, or `superseded`. A record that replaces another carries `supersedes = "ADR-MMMM"`.

The body has three sections: Context (what forced the decision), Decision (the rule now in force), and Consequences (what it makes true, good and bad).

## Lifecycle

A record opens as `proposed`, becomes `accepted` when the estate adopts it, and moves to `superseded` when a later record replaces it. A superseded record is never deleted; the decision was real and its reasoning still explains the shape of what came after.

## Ingestion

`atlas-corpus` fetches this directory on every ingest and indexes each record with its id, status, and date as metadata, so the estate's search can answer why a thing is the way it is. `TEMPLATE.md` and this `README.md` are skipped. A record with malformed frontmatter is logged and skipped rather than indexed, so a broken file never poisons the corpus.

## Adding one

Copy `TEMPLATE.md` to `ADR-NNNN-short-slug.md`, take the next free number, write the three sections, and set `status = "accepted"` when it is adopted. The next corpus refresh picks it up.
