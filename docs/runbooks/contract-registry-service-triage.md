# Contract registry service triage

Owner: `AtlasReaper311/atlas-infra`

## Trigger

Use this registry-owned first-response runbook when a production runtime
service contract has no more specific repository runbook. It is a routing
fallback, not proof that the target service is healthy.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py \
  --report /tmp/registry-report.json \
  --markdown /tmp/registry-report.md
git diff -- policy/estate-registry.json policy/service-contracts
```

Read the affected repository's README, deployment configuration, tests, and
runbooks before proposing a service change. Do not probe a live endpoint unless
that read has been separately approved.

## Response

Confirm the service ID, repository owner, classification, environment, route,
metadata state, and current deployment owner from committed evidence. If an
operational runbook exists in the source repository, update the contract to
reference it in a focused follow-up. Unknown evidence stays unknown.

## Rollback

Revert only the registry or contract declaration that introduced the mismatch.
Do not change a live route, deployment, secret, or provider from this runbook.
