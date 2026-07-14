# Runbook: malformed secret declaration

1. Stop names comparison; a partial policy must not produce a healthy result.
2. Run the local validator and use only its bounded path/reason diagnostics.
3. Correct the schema version, types, duplicate names/scopes, undeclared name
   references, lifecycle/replacement rule, or classification conflict.
4. Run valid, invalid, Finding-schema, and idempotency tests before review.

Rollback: revert the malformed policy commit. The prior declaration remains
authoritative and no provider secret is changed.
