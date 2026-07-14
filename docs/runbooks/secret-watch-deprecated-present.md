# Runbook: deprecated secret name still present

1. Read the declaration's replacement guidance and identify every declared
   repository/environment by name only.
2. Prove dependent workflows or runtimes use the replacement name.
3. Have the owner revoke/remove the deprecated provider entry manually after
   consumers have migrated.
4. Re-run names-only metadata comparison and retain the deprecated declaration
   until the old name is absent everywhere.

Rollback: restore the dependent consumer to the previous reviewed name if the
migration fails. Provider changes remain manual and must not expose values.
