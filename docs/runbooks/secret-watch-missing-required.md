# Runbook: missing required secret name

1. Confirm the Finding repository, environment/store, secret name, and
   fingerprint. Do not ask for or print a value.
2. Confirm metadata is `available`; if not, use the metadata-unavailable
   runbook instead of treating absence as proof.
3. Review the declaring workflow/runtime documentation and decide whether the
   name is genuinely required or the policy is stale.
4. If required, have the owner create the secret through the provider's
   protected interactive interface with the declared least privilege.
5. Re-run names-only comparison. Close the finding only when the name is
   present; this does not prove the value or its permissions are correct.

Rollback: remove an incorrect policy requirement in a reviewed change. Never
delete or replace a provider secret as an automated rollback.
