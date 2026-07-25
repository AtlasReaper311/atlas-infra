# Chaos assurance I1-I4 verification

This source-only verification reconciles the Atlas chaos policy with the current `specular-edge` target contract. It does not dispatch a workflow, contact the production control endpoint, change a repository variable or secret, or run a live canary.

## I1: repository validation

The existing deterministic simulator remains the source-independent experiment runner. The policy capability validator now runs before simulation and verifies that every supported harness fault has exactly one target capability class.

## I2: contract reconciliation

`specular-edge` authorises `status_503`, `latency`, and `kv_write_reject` for declared live experiments. `stale_response` and `webhook_drop` remain explicit test-only hooks and cannot enter the live experiment list.

The target contract requires one active lease, rejects replacement with HTTP 409, serialises activation within a Worker isolate, removes expired or malformed leases fail-closed, and distinguishes passive expiry from explicit rollback in recovery evidence.

## I3: non-production proof

The target repository proves the control route through in-memory KV and notification bindings, then runs lint, Node tests, a Wrangler dry-run, and the Worker metadata validator. No production hostname is contacted.

The control plane runs deterministic simulation through unit tests and validates the capability registry. No protected environment is entered.

## I4: evidence review

Final JSON and Markdown reports are stamped with:

- policy schema, version, and source path;
- experiment version;
- target capability class;
- source repository, commit, and workflow run when present;
- recalculated experiment and report-set fingerprints.

I5 remains a separate approval boundary. No source change in this batch enables scheduled live execution or performs production fault injection.
