# Backup audit: missing evidence

Use this runbook when a declared target has no readable metadata document. Missing evidence is `unavailable`, never healthy.

## Safe triage

1. Confirm the target ID and `evidence_source` in `policy/backup-audit.json`.
2. Run the offline audit with the pinned review timestamp.
3. Check only whether the declared local fixture path exists; do not query or download from a provider.

```bash
python3 scripts/backup_audit.py --now 2026-07-14T12:00:00Z --report /tmp/backup-audit.json --markdown /tmp/backup-audit.md
```

## Recovery

Restore or regenerate the synthetic metadata fixture from reviewed, non-sensitive fixture data. A future provider adapter needs separate approval and read-only target-specific credentials. Never substitute the current audit time for an unknown backup time.

## Escalation and rollback

Escalate to the declared target owner. Revert the focused fixture/policy change if it introduced the missing path; provider backups are not changed by this audit.
