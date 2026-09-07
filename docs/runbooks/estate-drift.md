# Estate drift validation

## Purpose

Use this runbook to compare current Atlas Infra classification authority, its deterministic projection, generated estate snapshot truth, optional GitHub owner observation, and optional presentation or topology evidence.

The report says whether those sources agree, disagree, or are `UNKNOWN / NOT OBSERVED`. It is source validation. It does not prove `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`.

## Authority

Use sources in this order:

1. `policy/estate-registry.json`;
2. `policy/public-assurance-repositories.json`;
3. `policy/public-repository-classifications.json` as the deterministic projection of those two inputs, checked with `scripts/public_repository_classifications.py`;
4. the Phase 1.4 estate snapshot model from `scripts/estate_snapshot.py`;
5. GitHub owner listing, when an observation file or authorised discovery route is supplied;
6. `atlas-api-public/data/estate.manifest.json` for topology and presentation only, when a local copy is supplied.

Do not treat presentation data as classification authority. Do not invent a second classification engine. Do not silently choose a winner when ownership is duplicate or ambiguous.

The only current-truth hand-maintained estate count currently owned in this repository is `approved_repository_count` in `policy/estate-registry.json`. Roadmaps, architecture-task notes, examples, fixtures, and dated evidence are not current estate truth.

## Validate committed authority

From `atlas-infra`, with no network requirement:

```bash
python3 scripts/public_repository_classifications.py --check
python3 scripts/estate_snapshot.py --check
python3 scripts/estate_drift.py --check
```

That path reads local classification authority only. GitHub discovery and presentation stay `UNKNOWN / NOT OBSERVED` unless you pass `--github-observation`, `--discover-github`, or `--presentation`.

To include recorded observation:

```bash
python3 scripts/estate_drift.py \
  --github-observation path/to/github-observation.json \
  --presentation path/to/estate.manifest.json \
  --json-out reports/estate-drift.json \
  --markdown-out reports/estate-drift.md
```

`--discover-github` uses the same authenticated owner listing as `scripts/estate_repo_diff.py`. It requires an already-present token in `ATLAS_ESTATE_READ_TOKEN` or `GITHUB_TOKEN`. Do not print, store, or invent that value.

## Failure modes

Validation fails closed when:

- the committed classification projection does not match the owning generator;
- committed authority contains duplicate identities, overlapping runtime and non-runtime ownership, or other ambiguity that prevents one deterministic classification;
- snapshot or schema state is malformed;
- `approved_repository_count` disagrees with the runtime registry list;
- GitHub or presentation observation is supplied and that observation disagrees with Atlas Infra classification.

Missing optional GitHub or presentation observation is not a failure. It remains `UNKNOWN / NOT OBSERVED`. Absence is not proof of conformance.

Private GitHub repositories are not required to have public classification. Only owned public repositories missing Atlas Infra classification are reported for that class.

The validator does not repair `atlas-api-public` presentation source, change classification authority to obtain a clean result, or infer later ADR-0013 stages.

## Rollback

Discard the branch, or restore the authority inputs, regenerate `policy/public-repository-classifications.json`, and rerun `--check`.

No step in this runbook deploys a service, modifies provider state, or changes repository settings.
