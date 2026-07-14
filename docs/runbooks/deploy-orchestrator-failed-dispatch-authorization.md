# Deploy orchestrator: failed dispatch authorization

## Trigger

Execution is requested while policy is disabled, the executor is `noop`, or a
future selected-repository token lacks workflow-dispatch authority.

## Recover

For Phase 7, return to dry-run; execution is intentionally unavailable. For a
future approved phase, verify only token name, repository selection, and
permission metadata: `Metadata: read`, `Contents: read`, and `Actions: read and
write`. Never print a token value, broaden to all repositories, reuse a deploy
credential, or bypass environment protection.

