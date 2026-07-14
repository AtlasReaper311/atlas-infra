# Backup audit: target owner missing

Use this runbook when an enabled backup target lacks an accountable owner.

## Safe triage

1. Compare the target repository and service with the Phase 6 registry owner and escalation fields.
2. Confirm ownership rather than inferring it from a file author or workflow actor.
3. Keep the target non-healthy until an owner is approved.

## Recovery

Add the approved owner identifier to the backup policy and re-run all offline validation. Do not add credentials or personal contact data to the policy.

## Escalation and rollback

Escalate to the estate owner when responsibility is unclear. Revert an unowned target instead of enabling unactionable scheduled assurance.
