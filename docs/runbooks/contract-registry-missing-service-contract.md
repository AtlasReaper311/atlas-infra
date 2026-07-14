# Missing service contract

Owner: `AtlasReaper311/atlas-infra`

## Trigger

The registry reports `missing-service-contract` for a runtime repository or
declared service ID.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py
python3 -m json.tool policy/estate-registry.json >/dev/null
ls policy/service-contracts
```

## Response

Confirm that the repository is a real runtime service. If it is, create a
ServiceContract from committed source evidence and encode missing facts as
unknown. If it is not, set the runtime and contract flags to false and remove
the service ID. A contract for a non-runtime tool requires an explicit owner
exception.

## Rollback

Revert the registry entry and contract file together so the mapping cannot be
left half-migrated.
