# RAMONE control-plane contracts

This directory contains the bounded wrapper contracts used by the RAMONE
read-only control-plane integration. The canonical aggregate remains
`contracts/v1/control-plane-summary.schema.json`.

- `v1/control-plane-read-model-source.schema.json` defines one policy-declared
  collection source for the offline producer.
- `v1/control-plane-read-model.schema.json` defines the deterministic wrapper
  consumed by the future `atlas-api-public` route reconstruction.

The contracts grant no runtime or provider authority. The producer writes only
local files. A future KV publisher is a separate source and rollout approval.
