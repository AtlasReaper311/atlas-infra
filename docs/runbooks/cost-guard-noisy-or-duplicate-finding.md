# Cost guard: noisy or duplicate finding

## Trigger

The same fingerprint/state appears repeatedly inside a cooldown, or a source
produces equivalent records in unstable order.

## Safe response

1. Compare fingerprints, state keys, evidence timestamps, and policy cooldown.
2. Supply the prior report to the offline CLI and inspect its dry-run decision.
3. Confirm inputs are sorted and fingerprints exclude volatile timestamps.
4. Change a cooldown only through a reviewed policy pull request with evidence.

Never suppress a different fingerprint or a genuine state transition. Phase 5
does not send notifications, so rollback is deleting the local generated report.
