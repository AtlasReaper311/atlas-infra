# GitHub conformance scoreboard

The GitHub conformance scoreboard is a read-only assurance report for repositories listed in `policy/public-repository-classifications.json`.

It reports two related views:

- raw evidence inventory, which records whether GitHub evidence was observed;
- policy conformance, which evaluates that evidence against `policy/github-conformance-requirements.json`.

The separation prevents an intentionally non-releaseable repository from appearing non-compliant merely because it has no release workflow or tag. It also preserves missing evidence instead of hiding it behind policy exceptions.

The scoreboard does not enumerate the GitHub account, discover private repositories, change settings, open pull requests, merge code, create releases, or deploy services.

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
- `not_applicable`: the check does not describe that repository class;
- `exception`: accepted policy permits the missing evidence;
- `deferred`: evidence is intentionally postponed until a separately approved milestone.

A passed observation satisfies an `exception` or `deferred` rule automatically. Raw evidence remains in the JSON report regardless of policy outcome.

`policy/github-conformance-requirements.json` owns the applicability rules. Repository-specific overrides must name a repository already present in the public projection and include a concrete reason. Release workflows and release history are not estate-wide defaults; they are required or deferred only for repositories classified as distributable libraries.

## Run locally

```bash
python3 -m py_compile scripts/github_api.py scripts/github_conformance_scoreboard.py scripts/github_conformance_policy.py
python3 -m unittest scripts.tests.test_github_conformance_scoreboard scripts.tests.test_github_conformance_policy -v
python3 scripts/public_repository_classifications.py --check
GITHUB_TOKEN="$(gh auth token)" python3 scripts/github_conformance_policy.py \
  --json-out reports/github-conformance-scoreboard.json \
  --markdown-out reports/github-conformance-scoreboard.md
```

The local report is written under `reports/`, which is not committed.

## GitHub Actions

`.github/workflows/github-conformance-scoreboard.yml` runs weekly and on demand. It uploads the JSON and Markdown report as a short-retention workflow artifact and writes the Markdown report to the workflow summary.

The workflow uses the repository-scoped `GITHUB_TOKEN` with read-only `contents` permission. Branch rulesets or classic protection can therefore remain `unknown`; unknown must not be rewritten as failed. If broader evidence is needed later, add a narrowly scoped read token as a separately reviewed provider change rather than expanding the default workflow authority.
