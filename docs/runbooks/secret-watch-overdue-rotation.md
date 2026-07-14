# Runbook: overdue owner-attested rotation

1. Confirm `last_rotated_at`, `max_age_days`, owner, and scope from policy.
   GitHub update timestamps do not prove upstream rotation.
2. Schedule owner-approved rotation through the provider's protected
   interactive interface and update every dependent consumer.
3. Verify the old credential is rejected without displaying either value.
4. Update only `last_rotated_at` in policy and re-run secret watch.

Rollback: restore consumer configuration through protected provider controls
if the new credential fails. Do not reintroduce a credential into Git or logs.
