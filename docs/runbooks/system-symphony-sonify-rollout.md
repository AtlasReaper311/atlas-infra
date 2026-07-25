# System Symphony sonification rollout

This runbook records the bounded production rollout for `specular-sonify` after the DORA composition and System Symphony interface changes.

## Preconditions

- `atlas-api-public` serves current DORA evidence.
- `specular-sonify` main contains the twenty-two-service composition contract.
- The caller repository has access to the reusable workflow secrets declared by `atlas-infra/.github/workflows/deploy-worker.yml`.
- Secret values are entered only through GitHub Actions settings or another approved interactive secret prompt. They are never copied into issues, pull requests, logs, or chat.

## Deployment boundary

The canonical reusable Worker workflow deploys the top-level production configuration explicitly with:

```bash
npx wrangler deploy --env=""
```

Named non-production branches continue to target `--env dev`.

## Verification

After the production workflow succeeds, verify all of the following independently:

1. `GET https://api.atlas-systems.uk/sonify` contains the `atlas-dora` service record.
2. `GET https://api.atlas-systems.uk/sonify/_meta` advertises twenty-two services.
3. `https://atlas-systems.uk/systems/observability/` reports thirteen covered services.
4. `https://atlas-systems.uk/lab/system-symphony/` loads the approved interface and starts audio only after a user gesture.

A merged pull request or successful dry-run is not deployment proof.
