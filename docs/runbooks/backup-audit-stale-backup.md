# Backup audit: stale backup

Use this runbook when `audit_timestamp - backup_timestamp` exceeds the target's `maximum_allowed_age_hours`.

## Safe triage

1. Verify the audit and backup timestamps are UTC RFC 3339 values.
2. Confirm the target's frequency and maximum age were not weakened to hide a failure.
3. Inspect the redacted evidence reference only; do not fetch private backup contents.

## Recovery

For fixtures, update the synthetic scenario only when intentionally testing a new review window. For a future live adapter, ask the producer owner to run its existing backup procedure and publish new redacted metadata. This auditor never triggers a backup.

## Escalation and rollback

Escalate according to target criticality and owner. Roll back a policy-window change by reverting the focused commit; do not delete or alter stored backups.
