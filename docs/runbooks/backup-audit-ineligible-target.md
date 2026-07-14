# Backup audit: ineligible target

Use this runbook when a deprecated, archived, external-derived, or explicitly excluded service is configured for an active default drill.

## Safe triage

1. Compare lifecycle, scope, and provenance independently with the Phase 6 registry.
2. Confirm the target is not `simple-proxy`, which is deprecated, internal, external-derived, and explicitly excluded.
3. Preserve historical visibility without running a drill.

## Recovery

Disable or remove the active target declaration. Any exception requires explicit owner approval and must not imply new features, deployment ownership, or automatic remediation for excluded code.

## Escalation and rollback

Escalate classification disputes to the estate owner. Roll back by reverting the policy declaration; no backup store or provider needs mutation.
