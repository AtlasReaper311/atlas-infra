# Cost guard: stale data

## Trigger

The newest valid evidence is older than `max_data_age_hours`.

## Safe response

1. Check the source job/run status without retrieving token values.
2. Confirm UTC timestamps and the policy freshness window.
3. Preserve the last observation as stale; do not present it as current.
4. Re-run the approved read-only producer or fixture validation when available.

Do not loosen freshness merely to produce green output. No provider write is
required to diagnose this state.
