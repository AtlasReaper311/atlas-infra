# Backup audit: digest mismatch

Use this runbook when the declared SHA-256 digest differs from the local fixture bytes.

## Safe triage

1. Confirm the digest path resolves inside the target fixture directory without symlinks.
2. Recalculate SHA-256 locally.
3. Determine whether the fixture changed intentionally; never update the digest merely to silence an unexplained mismatch.

```bash
shasum -a 256 tests/fixtures/backup-audit/TARGET/FILE
```

## Recovery

Review the fixture content, then update the digest in the same focused change only when the content is approved. A future provider adapter must compare redacted metadata or an approved digest without downloading private content by default.

## Escalation and rollback

Treat unexplained mismatches as integrity failures. Revert the changed fixture and metadata together if provenance cannot be established.
