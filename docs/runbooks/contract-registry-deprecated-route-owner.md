# Deprecated repository claiming a route

Owner: `AtlasReaper311/atlas-infra`

## Trigger

A deprecated repository claims an active route, or `simple-proxy` gains active
control-plane ownership.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py
git diff -- policy/estate-registry.json policy/service-contracts/simple-proxy.json
```

## Response

Remove the active route claim from the deprecated contract. If a public route
still exists, record the mismatch as unresolved and plan migration or
retirement in the owning repository through a separate approved change.
`simple-proxy` cannot receive a new feature, assurance schedule, Gardener
action, deployment orchestration, metadata route, or route exception.

## Rollback

Restore the last historical-only declaration. Do not deploy, redirect, or
delete a live route from this runbook.
