# Registry lifecycle conflict

Owner: `AtlasReaper311/atlas-infra`

## Trigger

The registry reports `lifecycle-conflict` between repository and service
declarations, or the fixed `simple-proxy` classification is changed.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py --markdown /tmp/registry-report.md
git diff -- policy/estate-registry.json policy/service-contracts
```

## Response

Compare lifecycle, scope, and provenance independently. Update the repository
entry and every service contract owned by it in one reviewable change. Do not
turn an archived or deprecated repository active merely to clear a finding.
`simple-proxy` must remain deprecated, internal, and external-derived.

## Rollback

Restore the last matching registry and contract classifications.
