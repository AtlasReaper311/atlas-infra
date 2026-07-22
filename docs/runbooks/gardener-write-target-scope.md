# Atlas Gardener write-target scope

## Purpose

Atlas Gardener write modes must not treat verified GitHub App coverage as permission to modify every covered repository in one run.

`ATLAS_GARDENER_WRITE_TARGETS_JSON` is an independent run-scoped allowlist. It is required whenever `ATLAS_GARDENER_MODE` is `pr-only` or `automerge-low-risk`.

## Contract

The repository variable value must be a JSON array of full repository names:

```json
["AtlasReaper311/atlas-dora"]
```

The controller accepts the value only when it is:

- non-empty in a write mode;
- sorted and free of duplicates;
- restricted to repositories in verified public GitHub App coverage;
- expressed as exact `AtlasReaper311/<repository>` identities.

An absent, malformed, empty, unsorted, duplicated, or uncovered list fails closed before any repository token is minted.

Findings outside the explicit list are recorded in controller evidence as `repositories_skipped`. They are not checked out, proposed, tokenized, branched, or submitted as pull requests.

## Canary value

The initial live canary is restricted to:

```json
["AtlasReaper311/atlas-dora"]
```

Keep `ATLAS_GARDENER_MODE=disabled` and `ATLAS_GARDENER_WRITE_GATE=disabled` while changing the target list. Enable each control only for an approved bounded run, then return all controls to their disabled state.

## Expansion

A later batch requires a separately reviewed sorted list containing only that approved batch. Verified coverage remains eligibility evidence; it is not the write target list.

## Rollback

Set:

```text
ATLAS_GARDENER_MODE=disabled
ATLAS_GARDENER_WRITE_GATE=disabled
ATLAS_GARDENER_WRITE_TARGETS_JSON=[]
```

Disabling mode or the independent write gate prevents controller writes even if a target list remains configured.
