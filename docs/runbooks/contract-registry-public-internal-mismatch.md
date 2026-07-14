# Public and internal route mismatch

Owner: `AtlasReaper311/atlas-infra`

## Trigger

An internal service claims a public route without an exact approved exception.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py --report /tmp/registry-report.json
git diff -- policy/service-contracts
```

## Response

Confirm whether the route is deliberately public and bounded. If approved,
record an exact origin/path exception with the owner and reason. If not, remove
the declaration or correct the route visibility from committed evidence. Do
not expose a route, weaken authentication, or publish private service names to
clear the registry finding.

## Rollback

Remove the unapproved exception or restore the previous route declaration. No
live access policy is changed by this registry action.
