# Cost guard: warning threshold exceeded

## Trigger

A fresh, valid snapshot is at or above the configured warning percentage but
below the critical percentage.

## Safe response

1. Re-run the same fixture/report command and confirm the fingerprint is stable.
2. Check the evidence timestamp, quota type, configured limit, and period dates.
3. Compare the top contributors in the existing `/quota` response if available.
4. Recommend a bounded usage reduction or an owner review of the declared limit.

Do not change limits, billing, routes, deployments, or service availability.
Resolve the finding only after a later fresh snapshot is below the threshold.
