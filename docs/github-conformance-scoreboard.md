# GitHub conformance scoreboard

The GitHub conformance scoreboard is a read-only assurance report for repositories listed in `policy/public-repository-classifications.json`.

## Programme state

Phase II of the July 2026 GitHub conformance programme is complete. Phase III resolved the former provider-evidence unknowns, created and validated the bounded `atlas-badges` default-branch guard canary, and is preparing a stamped owner-authenticated rerun before any wider rollout is proposed.

The Phase II evidence and residual boundaries are recorded in [`github-conformance-phase-ii-closeout.md`](github-conformance-phase-ii-closeout.md). The provider audit, canary state, and remaining approval gates are recorded in [`github-provider-guard-audit.md`](github-provider-guard-audit.md).

The scoreboard reports two related views:

- raw evidence inventory, which records whether GitHub evidence was observed;
- policy conformance, which evaluates that evidence against `policy/github-conformance-requirements.json`.

The separation prevents an intentionally non-releaseable repository from appearing non-compliant merely because it has no release workflow or tag. It also preserves missing evidence instead of hiding it behind policy exceptions.

The scoreboard does not enumerate the GitHub account, discover private repositories, change settings, open pull requests, merge code, create releases, or deploy services.

## Evidence identity

The policy-aware v2 JSON report is stamped after collection with:

- `collected_at`: the UTC collection timestamp;
- `source.repository`: `AtlasReaper311/atlas-infra`;
- `source.commit`: the exact 40-character Atlas Infra commit used for the run;
- `fingerprint`: a canonical SHA-256 digest of the complete stamped report, excluding the fingerprint field itself.

The Markdown report receives the same identity values. The stamper replaces any previous fingerprint and fails closed when the report schema, source commit, timestamp, JSON root, or Markdown heading is invalid.

The fingerprint identifies the report contents. It is not a signature and does not replace the workflow artifact digest or an owner-authenticated provider read.

## Evidence checks

The report observes:

- repository description;
- repository topics;
- licence evidence;
- Dependabot configuration;
- CodeQL workflow;
- OpenSSF Scorecard workflow;
- security contact, including inherited owner defaults from `AtlasReaper311/.github`;
- release workflow;
- existing release or tag history;
- default branch pull-request guard from a repository ruleset or classic branch protection.

Raw evidence is reported as:

- `passed`: evidence was observed;
- `failed`: evidence was readable and absent;
- `unknown`: GitHub did not return enough evidence, usually because the token cannot read that provider surface.

## Policy outcomes

Each raw check is evaluated by the Atlas Infra requirements policy:

- `passed`: required evidence was observed;
- `failed`: required evidence was readable and absent;
- `unknown`: required evidence could not be proved;
- `not_applicable`: the check does not describe this repository class;
- `exception`: accepted policy permits the missing evidence;
- `deferred`: evidence is intentionally postponed until a separately approved milestone.

A passed observation satisfies an `exception` or `deferred` rule automatically. Raw evidence remains in the JSON report regardless of policy outcome.

`policy/github-conformance-requirements.json` owns the applicability rules. Repository-specific overrides must name a repository already present in the public projection and include a concrete reason. Release workflows and release history are not estate-wide defaults; they are required or deferred only for repositories classified as distributable libraries.

## Run locally

Validate the tooling first:

```bash
python3 -m py_compile \
  scripts/github_api.py \
  scripts/github_conformance_scoreboard.py \
  scripts/github_conformance_policy.py \
  scripts/github_conformance_stamp.py

python3 -m unittest \
  scripts.tests.test_github_conformance_scoreboard \
  scripts.tests.test_github_conformance_policy \
  scripts.tests.test_github_conformance_stamp \
  -v

python3 scripts/public_repository_classifications.py --check
```

Build an owner-authenticated report from a clean Atlas Infra checkout:

```bash
set -eu

SOURCE_COMMIT="$(git rev-parse HEAD)"
mkdir -p reports

GITHUB_TOKEN="$(gh auth token)" \
python3 scripts/github_conformance_policy.py \
  --json-out reports/github-conformance-scoreboard.json \
  --markdown-out reports/github-conformance-scoreboard.md

python3 scripts/github_conformance_stamp.py \
  --json reports/github-conformance-scoreboard.json \
  --markdown reports/github-conformance-scoreboard.md \
  --source-commit "${SOURCE_COMMIT}"
```

The token is passed only to the collection process and must not be printed, copied into a report, or written to disk. The local report is written under `reports/`, which is not committed.

## GitHub Actions

`.github/workflows/github-conformance-scoreboard.yml` runs weekly and on demand. It builds the policy-aware report, stamps it with `${GITHUB_SHA}`, uploads the JSON and Markdown as a short-retention workflow artifact, and writes the stamped Markdown report to the workflow summary.

The workflow uses the repository-scoped `GITHUB_TOKEN` with read-only `contents` permission. Branch rulesets or classic protection can therefore remain `unknown`; unknown must not be rewritten as failed. Owner-authenticated provider evidence remains a separate local read unless a narrowly scoped read token is later approved through its own provider-change review.
