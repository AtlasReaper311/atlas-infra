# Backup audit: restore drill failed

Use this runbook when a fixture cannot be copied, parsed, extracted, or validated in a new system temporary directory.

## Safe triage

1. Re-run the focused backup-audit unit test and CLI offline.
2. Review the target's declared drill type, fixture shape, checksum, file count, and byte count.
3. Confirm the source and destination are non-symlink paths and that no executable bit is set.

```bash
python3 -m unittest scripts.tests.test_backup_audit -v
python3 scripts/backup_audit.py --now 2026-07-14T12:00:00Z --report /tmp/backup-audit.json --markdown /tmp/backup-audit.md
```

## Recovery

Repair only the synthetic export or the bounded validator. Do not point the drill at an application data directory, provider namespace, or existing destination. Temporary directories are deleted automatically.

## Escalation and rollback

Escalate malformed producer formats to the data owner. Revert the focused Phase 8 commit to remove the auditor; no live data rollback is required.
