# Stale registry entry

Owner: `AtlasReaper311/atlas-infra`

## Trigger

The registry contains an unapproved repository or a ServiceContract names a
repository outside the approved estate.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py --report /tmp/registry-report.json
git diff -- policy/estate-registry.json policy/service-contracts
```

## Response

Confirm owner approval and repository history. Add a genuinely approved
repository through the documented registry procedure. Otherwise remove the
stale declaration only after confirming that no active service ID or dependency
edge still needs historical visibility. Do not delete the repository itself.

## Rollback

Restore the previous registry entry or contract reference. Repository and
provider state remain untouched.
