# Backup audit: retention violation

Use this runbook when retention metadata is absent or does not cover the declared expectation.

## Safe triage

1. Compare `retention.expected_days` with `retention_expectation_days`.
2. Confirm `retained_until` is no earlier than `backup_at + expectation` and is not already past.
3. Treat an unknown provider lifecycle rule as missing metadata, not compliance.

## Recovery

Correct fixture metadata only when the synthetic retention fact is wrong. Future provider validation must read policy metadata using a separately approved, target-scoped read credential. This audit does not change lifecycle rules or extend/delete stored objects.

## Escalation and rollback

Escalate to the backup target owner. Revert an incorrect declaration through normal review; provider state remains untouched.
