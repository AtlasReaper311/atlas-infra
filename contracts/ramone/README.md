# RAMONE control-plane contracts

This directory contains the bounded contracts used by the RAMONE read-only
control-plane integration. The canonical aggregate remains
`contracts/v1/control-plane-summary.schema.json`.

- `v1/control-plane-read-model-source.schema.json` defines one policy-declared
  collection source for the offline producer.
- `v1/control-plane-read-model.schema.json` defines the deterministic wrapper
  consumed by the future `atlas-api-public` route reconstruction.
- `v1/control-plane-read-model-publication-receipt.schema.json` defines the
  redacted preflight and successful-publication evidence emitted by the manual
  exact-digest publisher.

The producer writes only local files. The publisher may write one fixed KV key
only after a separate protected workflow approval. Neither contract grants
RAMONE, Home Assistant, Open WebUI, or the public API provider credentials.
