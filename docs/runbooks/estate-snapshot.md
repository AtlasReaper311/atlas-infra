# Estate snapshot generation

## Purpose

Use this runbook to regenerate the machine-readable and human-readable Atlas estate snapshot from current classification authority and optional GitHub or topology observation.

The snapshot is generated evidence. It is not classification authority, not deployment evidence, and not live verification.

## Authority

Use sources in this order:

1. GitHub owner listing, when an observation file or authorised discovery route is supplied;
2. `policy/estate-registry.json`;
3. `policy/public-assurance-repositories.json`;
4. `policy/public-repository-classifications.json` as the deterministic projection of those two inputs;
5. `atlas-api-public/data/estate.manifest.json` for topology and presentation only, when a local copy is supplied.

Do not edit the generated snapshot to change a classification. Change the authority input and regenerate the projection first.

Do not treat topology `lifecycle` as repository governance.

## Generate

From `atlas-infra`:

```bash
python3 scripts/estate_snapshot.py \
  --json-out reports/estate-snapshot.json \
  --markdown-out reports/estate-snapshot.md
```

That command reads local classification authority. GitHub discovery and presentation stay `UNKNOWN / NOT OBSERVED` unless you pass `--github-observation`, `--discover-github`, or `--presentation`.

To include a recorded GitHub owner listing:

```bash
python3 scripts/estate_snapshot.py \
  --github-observation path/to/github-observation.json \
  --json-out reports/estate-snapshot.json \
  --markdown-out reports/estate-snapshot.md
```

`--discover-github` uses the same authenticated owner listing as `scripts/estate_repo_diff.py`. It requires an already-present token in `ATLAS_ESTATE_READ_TOKEN` or `GITHUB_TOKEN`. Do not print, store, or invent that value.

## Validate

```bash
python3 scripts/public_repository_classifications.py --check
python3 scripts/estate_snapshot.py --check
python3 -m unittest scripts.tests.test_estate_snapshot -v
git diff --check
```

`--check` proves that the snapshot regenerates deterministically from unchanged inputs, that JSON matches the snapshot schema, and that Markdown is produced from the same model as JSON.

## Failure modes

Generation fails when classification inputs overlap, when a classification axis is invalid, or when the committed projection does not match the authority inputs.

Missing GitHub or presentation observation is not a failure. It is recorded as `UNKNOWN / NOT OBSERVED`.

GitHub-owned repositories without classification, classified repositories missing from an observed GitHub listing, and presentation lifecycle values that disagree with Atlas Infra classification are written into the snapshot. They are not silently reconciled.

This snapshot does not prove `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`.

## Rollback

Discard the branch, or restore the authority inputs, regenerate `policy/public-repository-classifications.json`, and regenerate the snapshot.

No step in this runbook deploys a service, modifies provider state, or changes repository settings.
