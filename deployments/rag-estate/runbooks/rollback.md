# Rollback

Rollback is triggered by count, ID, metadata, embedding, retrieval, privacy,
TLS, authentication, health, or write-loss failure.

1. Re-apply the freeze overlay and record the failure time.
2. Stop or isolate Qdrant without deleting its volume.
3. Restore the pre-cutover application image references and configuration from
   the verified deployment backup.
4. Restore Chroma only from the verified backup if the original volume is not
   intact. Never overwrite the original backup.
5. Restart only the affected private applications after their health checks are
   configured for the restored backend.
6. Verify counts, retrieval, memory/session separation, and public/private
   boundaries.
7. Preserve the failed Qdrant evidence and record the exact rollback receipt.

The old Chroma volumes and backups remain retained until owner acceptance closes
the cutover window.
