# Backup audit: unknown service ID

Use this runbook when a target or coverage declaration does not match the Phase 6 registry and ServiceContract set.

## Safe triage

1. Run the contract registry validator offline.
2. Compare the exact `service_id`, repository, and independent classification axes.
3. Do not invent a new service ID or route to make validation pass.

```bash
python3 scripts/validate_contract_registry.py --report /tmp/registry.json --markdown /tmp/registry.md --graph /tmp/graph.json --catalog /tmp/catalog.json
```

## Recovery

Correct the backup declaration when the registry already proves the intended owner. Changes to the canonical registry require a separate reviewed decision when ownership is genuinely new or uncertain.

## Escalation and rollback

Escalate ambiguous ownership to `AtlasReaper311/atlas-infra`. Revert the incorrect target declaration if no canonical service exists.
