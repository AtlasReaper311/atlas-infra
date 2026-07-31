# GitHub conformance Phase II closeout

## Decision

Phase II of the July 2026 GitHub conformance programme is complete.

The scheduled policy-aware scoreboard produced zero policy failures across the 33 public repositories in the authoritative projection. No repository source remediation is required from this phase.

This decision closes the read-only source-conformance phase only. Provider-side branch-guard verification and the first owner-approved `worker-meta-kit` release remain separate approval-gated work.

## Verified run

The closing evidence is GitHub Actions run [`30535544793`](https://github.com/AtlasReaper311/atlas-infra/actions/runs/30535544793), completed successfully on 30 July 2026.

- workflow: `GitHub conformance scoreboard`
- source branch: `main`
- source commit: `48138e7256a39a1f9f6e1b1493bb7bb2c4083709`
- repositories checked: 33
- report schema: `atlas-github-conformance-scoreboard/report/v2`
- public projection fingerprint: `sha256:30f47de465c1117fda375b70b7d156d73f4b39622873133c756f7fa06539c6a0`
- requirements fingerprint: `sha256:b05e2fe568018d1bf491665237f092e4bcfb6c70d81e237da7efa8cc78ec6ed7`
- retained artifact: `github-conformance-scoreboard-30535544793`
- artifact ID: `8756488429`
- artifact digest: `sha256:2495e2ab8d1ed320f5f248f40e40074a721e03e247c7b6a41bfb259d29438cdf`
- artifact expiry: 29 August 2026

The workflow validated the scoreboard tooling, ran ten focused tests, verified the 33-repository classification projection, built both report formats, and uploaded the retained artifact.

## Policy result

| Outcome | Count |
| --- | ---: |
| Required evidence passed | 233 |
| Required evidence failed | 0 |
| Required evidence unknown | 27 |
| Not applicable | 68 |
| Approved exception | 1 |
| Deferred | 1 |
| Total checks | 330 |

The closing condition for Phase II is the absence of readable required source failures. That condition is satisfied.

## Interpretation of the remaining outcomes

### Provider evidence unknown

All 27 unknown outcomes are the `default_branch_guard` check. The repository-scoped read-only `GITHUB_TOKEN` could not prove ruleset or classic branch-protection state for those repositories.

Unknown is not rewritten as failed or passed. These outcomes move to the separate provider-state phase, where current rulesets and branch protections must be inspected with appropriately scoped read access before any setting change is proposed.

### Approved exception

`AtlasReaper311/atlas-dep-audit` remains exempt from Dependabot under the accepted scanner-independence policy. The scoreboard classified this as an approved exception rather than a failure.

### Deferred release evidence

`AtlasReaper311/worker-meta-kit` has the required release workflow but no owner-approved release or tag. Its first release remains deferred because creating a tag and GitHub Release is a provider write requiring separate approval.

`AtlasReaper311/atlas-interface-kit` now satisfies its release-history requirement and is not part of the remaining release action.

## Contract continuity

The closing run used source commit `48138e7256a39a1f9f6e1b1493bb7bb2c4083709`. Comparison with the Phase I closing baseline `a80d536d0ff36cbfd286c9100de2780c9bf20d5f` shows no intervening changes to:

- `.github/workflows/github-conformance-scoreboard.yml`
- `scripts/github_api.py`
- `scripts/github_conformance_scoreboard.py`
- `scripts/github_conformance_policy.py`
- `policy/github-conformance-requirements.json`
- `policy/public-repository-classifications.json`

Later commits therefore do not invalidate the evaluation contract or repository scope used by the closing report.

## Closure boundary

Phase II completion means:

- the policy-aware scheduled scoreboard ran successfully;
- the authoritative public repository scope was verified;
- policy interpretation distinguished required checks from not-applicable checks, approved exceptions, deferred evidence, and unreadable provider state;
- no required source remediation remains from the report;
- residual provider and release work is explicitly separated rather than hidden.

Phase II completion does not mean:

- the 27 branch guards were proved absent or present;
- rulesets or branch protection were changed;
- a GitHub token received broader permissions;
- `worker-meta-kit` was tagged or released;
- private repositories entered the public scoreboard;
- any service was deployed.

## Next phases

1. Inspect provider-side ruleset and branch-protection evidence for the 27 unknown repositories. Treat this as a read-only audit first, followed by a separately approved canary if settings changes are required.
2. Create the first `worker-meta-kit` release only after owner approval, immutable tag selection, release artifact verification, and rollback planning.
3. Run the scheduled scoreboard again after those independent actions to prove the resulting evidence state.
