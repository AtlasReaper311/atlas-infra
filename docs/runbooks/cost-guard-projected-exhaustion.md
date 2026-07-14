# Cost guard: projected exhaustion

## Trigger

Deterministic fixed/rolling burn projects quota exhaustion inside the policy
horizon.

## Safe response

1. Confirm at least two valid snapshots exist for the selected rolling rate.
2. Review fixed and rolling rates separately and note any acceleration flag.
3. Check for a billing-period boundary, reset, partial data, or changed quota.
4. Recommend owner-reviewed mitigation and schedule a fresh read-only snapshot.

Treat the date as a linear projection, not a forecast guarantee. If history is
insufficient, the correct state is `unknown`, not projected exhaustion.
