# Duplicate route owner

Owner: `AtlasReaper311/atlas-infra`

## Trigger

The registry reports `duplicate-route-owner` for the same HTTPS origin, path,
and method.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py --report /tmp/registry-report.json
python3 -c 'import json; d=json.load(open("/tmp/registry-report.json")); print([f for f in d["findings"] if f["rule_id"] == "duplicate-route-owner"])'
git diff -- policy/service-contracts
```

## Response

Read both repositories' committed routing and deployment configuration. Keep
the owner proven by the most specific current route declaration. If the source
evidence itself conflicts, leave the finding active and request owner review;
do not guess or change production routing in Phase 6.

## Rollback

Restore the last reviewed contract records. A registry rollback changes no live
route.
