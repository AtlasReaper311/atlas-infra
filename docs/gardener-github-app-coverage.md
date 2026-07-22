# Atlas Gardener GitHub App coverage

Atlas Gardener uses a selected-repository GitHub App installation. Coverage is expanded in reviewed batches so repository access does not grow faster than the evidence supporting it.

The authoritative public coverage policy is [`policy/gardener-github-app-coverage.json`](../policy/gardener-github-app-coverage.json). Its validator derives the eligible set from [`policy/estate-registry.json`](../policy/estate-registry.json), checks the exact permission contract, and fails if a public runtime repository is missing, duplicated, or added from outside that authority.

## Fixed provider boundary

The App permission contract remains:

```text
Metadata: read
Contents: write
Pull requests: write
```

The installation must remain in selected-repository mode. Coverage does not grant Actions, Checks, Administration, Deployments, Environments, Issues, Secrets, Variables, Members, Billing, merge, approval, workflow-dispatch, settings, branch-deletion, or non-GitHub provider authority.

Adding a repository to the installation does not create a branch, commit, pull request, workflow run, merge, or deployment. Gardener still requires one current proposal, one digest-bound plan, local and remote base checks, classification revalidation, a short-lived installation token, and interactive confirmation before it can open one draft pull request.

## Current phased plan

The verified canary is `AtlasReaper311/atlas-dora`.

The first low-blast-radius batch was verified on 22 July 2026 after all five selected repositories authenticated successfully with both GitHub installation-token formats:

- `AtlasReaper311/atlas-doc-viewer`
- `AtlasReaper311/atlas-quota-watch`
- `AtlasReaper311/site-pulse`
- `AtlasReaper311/specular-sonify`
- `AtlasReaper311/status`

The next ready batch contains public observability and evidence services:

- `AtlasReaper311/atlas-api-index`
- `AtlasReaper311/atlas-blackbox`
- `AtlasReaper311/atlas-corpus`
- `AtlasReaper311/github-pulse`
- `AtlasReaper311/specular-telemetry`

Later batches cover operational runtimes and finally the primary public API and portfolio surface. The policy file is the canonical grouping and order.

Only one batch may have status `ready`. Completed batches move to `verified` before the next batch becomes ready. The primary public surfaces retain `separate-approval` status until an explicit owner decision changes it.

## Public and private boundary

This public policy lists only repositories already declared by the public runtime registry. Private repository identities are not copied into Atlas Infra.

Private repositories remain source-owned through `.atlas/governance.json`. Any future private installation expansion requires a separate authenticated review and explicit owner approval. It must not be represented in this public policy or documentation.

## Owner rollout sequence

After the policy pull request is merged and current CI is green:

1. Open the Atlas Gardener GitHub App installation settings.
2. Keep repository access set to selected repositories only.
3. Add exactly the repositories in the single `ready` batch.
4. Confirm the permission screen still shows only Metadata read, Contents write, and Pull requests write.
5. Confirm no webhook or automatic trigger has been enabled.
6. From the current `atlas-gardener/main`, run the checked-in token-format and installation probe once for each newly selected repository.
7. Confirm each probe authenticates both token formats and revokes both tokens.
8. Do not run a remediation apply merely to test installation coverage.
9. Record the provider result, then update the completed batch to `verified` in a separate source pull request.

Example local verification loop for the current ready batch:

```bash
cd "$HOME/Personal/atlas-gardener"
git switch main
git pull --ff-only

printf 'Enter the numeric Atlas Gardener GitHub App ID: '
read -r ATLAS_GARDENER_APP_ID
export ATLAS_GARDENER_APP_ID

for repository in \
  AtlasReaper311/atlas-api-index \
  AtlasReaper311/atlas-blackbox \
  AtlasReaper311/atlas-corpus \
  AtlasReaper311/github-pulse \
  AtlasReaper311/specular-telemetry
do
  bash scripts/check-github-app-token-formats.sh "$repository"
done

unset ATLAS_GARDENER_APP_ID
```

The App ID is not secret. The private key and installation tokens remain outside source, logs, issues, pull requests, and chat.

## Validation

Run without provider access:

```bash
python3 scripts/validate_gardener_github_app_coverage.py \
  --report /tmp/gardener-github-app-coverage.json
```

The validator confirms complete public runtime coverage, a current registry fingerprint, canonical batch order, one ready batch at most, the exact permission contract, and the source-owned private repository boundary.
