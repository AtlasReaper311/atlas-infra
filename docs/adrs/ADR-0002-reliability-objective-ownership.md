+++
id = "ADR-0002"
date = 2026-07-19
status = "proposed"
+++

# ADR-0002: reliability objectives are canonical in atlas-infra

## Context

The estate's only approved availability targets lived in `status/slo.json`, a presentation repository, while the canonical service contracts in `atlas-infra` carried empty `slo_refs` on every service. The reliability-intelligence work needs objectives beside the evaluator configuration and the contracts that reference them, and it must not leave two independently editable target sets: the first disagreement between a policy copy and a presentation copy would make every derived number untrustworthy.

Two options were viable. Keep `status/slo.json` canonical and point contracts at it across repositories, or migrate ownership to `atlas-infra` and generate the status file deterministically. The first keeps estate policy inside a static site repository whose review habits are presentation-focused, and makes `slo_refs` point outside the repository that owns every other policy declaration.

## Decision

Reliability objectives are canonical in `atlas-infra`, one file per measured service under `policy/reliability/objectives/`, validating against the `reliability-objective` v1 contract. Evaluator constants live in `policy/reliability/evaluator-config.json`. Every other form is a deterministic projection: `status/slo.json` is rendered by `scripts/reliability_policy.py emit-status-slo` and carries `generated_from` plus the policy fingerprint; the published `atlas-reliability-policy/v1` document is rendered by `emit-policy-document` and delivered to `atlas-api-public` through the existing fingerprint-verified evidence ingest pattern. The initial objectives carry exactly the ten previously approved targets, unchanged, with provenance recording the migration.

## Consequences

Target changes now happen in one reviewed place, and a target edit made directly in `status/slo.json` is drift that regeneration exposes rather than a second truth. The status repository keeps its public `slo.json` URL and shape, so existing consumers continue working. The Worker never bundles targets and fails closed to `unavailable_source` when the published policy is missing or aged out, which is the honest state for an unpublished policy. The cost is a regeneration step when targets change: edit the objective, re-run the emitter, and ship both files in their own repositories, with the shared fingerprint proving they agree.
