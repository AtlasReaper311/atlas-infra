# Missing metadata endpoint

Owner: `AtlasReaper311/atlas-infra`

## Trigger

A service is marked release-watch eligible but has no known metadata endpoint
and expected shape.

## First diagnostics

```bash
python3 scripts/validate_contract_registry.py
git diff -- policy/service-contracts policy/release-watch.json
```

## Response

Confirm whether committed source exposes all required release identity fields.
If it does, declare the exact endpoint and shape. If it does not, set
`release_watch_eligible` false and retain the endpoint state as unknown until
the owning repository adds compatible metadata in a separate approved change.
Never infer a commit from a display version.

## Rollback

Restore the previous eligibility and metadata declaration together.
