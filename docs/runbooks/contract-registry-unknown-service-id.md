# Unknown service ID

Owner: `AtlasReaper311/atlas-infra`

## Trigger

A dependency or contract references a service ID that the canonical registry
does not index.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py --graph /tmp/service-graph.json
python3 -m json.tool /tmp/service-graph.json >/dev/null
git diff -- policy/estate-registry.json policy/service-contracts
```

## Response

Check spelling, repository ownership, and whether the dependency is an Atlas
runtime service. Add a ServiceContract only for a real runtime owner. External
providers and reusable libraries do not become service IDs solely to satisfy a
dependency edge; document them in contract notes instead.

## Rollback

Restore the prior dependency list or the complete registry/contract mapping.
