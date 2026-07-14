# Cost guard: critical threshold exceeded

## Trigger

A fresh, valid snapshot is at or above the configured critical percentage.

## Safe response

1. Confirm the snapshot and policy independently; do not infer a bill from a percentage.
2. Identify the owner and the highest bounded contributors already present in read-only evidence.
3. Prepare advisory options with their service impact and owner approval requirements.
4. Escalate to the declared owner using the existing human channel.

Phase 5 never shuts down a service, changes a quota, contacts billing, opens an
issue, or deploys. A false threshold is corrected by reviewing the policy in a
pull request; the runtime is not mutated.
