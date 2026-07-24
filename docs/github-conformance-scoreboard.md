# GitHub conformance scoreboard

The GitHub conformance scoreboard is a read-only assurance report for repositories listed in `policy/public-repository-classifications.json`.

It answers a simple question: which public Atlas Systems repositories have the expected GitHub hygiene, security, CI, release, and branch-guard evidence?

The scoreboard does not enumerate the GitHub account, discover private repositories, change settings, open pull requests, merge code, create releases, or deploy services.

## Evidence checks

The report checks:

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

Each check is reported as:

- `passed`: evidence was observed;
- `failed`: evidence was readable and absent;
- `unknown`: GitHub did not return enough evidence, usually because the token cannot read that surface.

Unknown is intentionally separate from failed so permission gaps do not get misreported as policy drift.

## Run locally

```bash
python3 -m py_compile scripts/github_api.py scripts/github_conformance_scoreboard.py
python3 -m unittest scripts.tests.test_github_conformance_scoreboard -v
GITHUB_TOKEN="$(gh auth token)" python3 scripts/github_conformance_scoreboard.py \
  --json-out reports/github-conformance-scoreboard.json \
  --markdown-out reports/github-conformance-scoreboard.md
```

The local report is written under `reports/`, which is not committed.

## GitHub Actions

`.github/workflows/github-conformance-scoreboard.yml` runs weekly and on demand. It uploads the JSON and Markdown report as a short-retention workflow artifact and writes the Markdown report to the workflow summary.

The workflow uses the repository-scoped `GITHUB_TOKEN` with read-only `contents` permission. If broader evidence is needed later, add a narrowly scoped read token as a deliberate follow-up rather than expanding the default workflow authority.
