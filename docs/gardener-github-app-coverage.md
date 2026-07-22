# Atlas Gardener GitHub App coverage

Atlas Gardener uses a selected-repository GitHub App installation. Coverage was expanded in reviewed batches so repository access did not grow faster than the evidence supporting it.

The authoritative public coverage policy is [`policy/gardener-github-app-coverage.json`](../policy/gardener-github-app-coverage.json). Its validator derives the eligible set from [`policy/estate-registry.json`](../policy/estate-registry.json), checks the exact permission contract, and fails if a public runtime repository is missing, duplicated, or added from outside that authority.

## Fixed provider boundary

The App permission contract remains:

```text
Metadata: read
Contents: write
Pull requests: write
```

The installation remains in selected-repository mode. Coverage does not grant Actions, Checks, Administration, Deployments, Environments, Issues, Secrets, Variables, Members, Billing, merge, approval, workflow-dispatch, settings, branch-deletion, or non-GitHub provider authority.

Adding a repository to the installation does not create a branch, commit, pull request, workflow run, merge, or deployment. Gardener still requires one current proposal, one digest-bound plan, local and remote base checks, classification revalidation, a short-lived installation token, and interactive confirmation before it can open one draft pull request.

## Verified public runtime coverage

The canary and all four public-runtime batches were verified on 22 July 2026. Every selected repository authenticated successfully with both GitHub installation-token formats, retained the exact permission boundary, and revoked each short-lived test token.

The verified canary is:

- `AtlasReaper311/atlas-dora`

The verified low-blast-radius batch is:

- `AtlasReaper311/atlas-doc-viewer`
- `AtlasReaper311/atlas-quota-watch`
- `AtlasReaper311/site-pulse`
- `AtlasReaper311/specular-sonify`
- `AtlasReaper311/status`

The verified observability batch is:

- `AtlasReaper311/atlas-api-index`
- `AtlasReaper311/atlas-blackbox`
- `AtlasReaper311/atlas-corpus`
- `AtlasReaper311/github-pulse`
- `AtlasReaper311/specular-telemetry`

The verified operational runtime batch is:

- `AtlasReaper311/atlas-daily-digest`
- `AtlasReaper311/atlas-notify`
- `AtlasReaper311/deploy-watch`
- `AtlasReaper311/ramone-edge`
- `AtlasReaper311/ramone-memory`
- `AtlasReaper311/ramone-voice-trigger`
- `AtlasReaper311/specular-sentinel`

The verified primary public surfaces are:

- `AtlasReaper311/atlas-api-public`
- `AtlasReaper311/atlas-systems`

The policy now records complete verified coverage for all 20 repositories in the declared public runtime registry. This proves installation scope and token compatibility. It does not grant unattended remediation, merge, deployment, or provider authority.

## Public and private boundary

This public policy lists only repositories already declared by the public runtime registry. Private repository identities are not copied into Atlas Infra.

Private repositories remain source-owned through `.atlas/governance.json`. Any future private installation expansion requires a separate authenticated review and explicit owner approval. It must not be represented in this public policy or documentation.

## Operating model

For each future Gardener remediation:

1. produce a current finding;
2. generate a deterministic proposal;
3. review the exact patch and plan digest;
4. revalidate classification and the target base commit;
5. mint one short-lived installation token restricted to the target repository;
6. open one draft pull request after interactive confirmation;
7. let repository-owned CI run independently;
8. leave merge and any resulting deployment to a separate human decision.

The App installation itself is passive. No webhook or automatic trigger starts Gardener.

## Validation

Run without provider access:

```bash
python3 scripts/validate_gardener_github_app_coverage.py \
  --report /tmp/gardener-github-app-coverage.json
```

The validator confirms complete public runtime coverage, a current registry fingerprint, canonical batch order, the exact permission contract, and the source-owned private repository boundary.
