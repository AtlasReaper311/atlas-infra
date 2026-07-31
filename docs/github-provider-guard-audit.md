# GitHub provider guard audit

## Status

Phase III has completed the owner-authenticated read-only provider inspection and is awaiting approval for a one-repository canary.

Phase II closed the public-repository source-conformance work with zero required source failures. This phase resolves the 27 remaining `default_branch_guard` outcomes that the scheduled scoreboard could not read.

No ruleset, branch-protection, token, repository, release, tag, workflow, deployment, or secret change is authorised by this document.

## Part 0 inspection

The closing scoreboard run was GitHub Actions run [`30535544793`](https://github.com/AtlasReaper311/atlas-infra/actions/runs/30535544793). It checked the authoritative 33-repository public projection and recorded:

- 233 required passes;
- 0 required failures;
- 27 required unknown outcomes;
- 68 not-applicable outcomes;
- 1 approved exception;
- 1 deferred outcome.

All 27 unknown outcomes were `default_branch_guard`. The scheduled report message was `GitHub ruleset or branch-protection evidence was unavailable.` This was an evidence-access result and did not prove that a guard was present or absent.

The existing scoreboard implementation uses these read-only provider paths:

- `GET /repos/{owner}/{repo}/rulesets`;
- the returned ruleset detail endpoint when the list response omits conditions or rules;
- `GET /repos/{owner}/{repo}/branches/{default_branch}/protection` as the classic-protection fallback.

The accepted pass conditions are:

- an active branch ruleset that targets the default branch and contains `pull_request`, `deletion`, and `non_fast_forward`; or
- classic branch protection with pull-request review protection.

The scheduled workflow uses the repository-scoped `GITHUB_TOKEN`. It could read normal repository contents but could not establish provider-state evidence for these 27 repositories. The connected ChatGPT GitHub application also does not expose a ruleset or branch-protection read action. The initial audit therefore required an owner-authenticated local read using the existing Atlas Infra tooling.

## Owner-authenticated evidence receipt

Atlas supplied the generated JSON and Markdown reports on 31 July 2026. The report contract and policy inputs match the Phase II closing evidence:

- schema: `atlas-github-conformance-scoreboard/report/v2`;
- repositories checked: 33;
- projection fingerprint: `sha256:30f47de465c1117fda375b70b7d156d73f4b39622873133c756f7fa06539c6a0`;
- requirements fingerprint: `sha256:b05e2fe568018d1bf491665237f092e4bcfb6c70d81e237da7efa8cc78ec6ed7`;
- JSON file digest: `sha256:8250292fa3865b04e2a5d5a56a036a44bfb5648bae9b16c01efe944fcbd2111c`;
- Markdown file digest: `sha256:30ee4ac5864268648e85aef9028579ee03f214f5a966c206d45f45cd31a17a46`.

The reports contain no token value and no unreadable provider outcome.

The current generator does not embed the local git source commit or collection timestamp. This document does not invent either value. A later evidence run used for final Phase III closure must stamp the source commit, collection time, and report fingerprint.

## Classified provider result

The owner-authenticated audit changed the provider result from 27 unknown outcomes to:

| Classification | Count |
| --- | ---: |
| `proved_ruleset` | 6 |
| `proved_classic` | 0 |
| `readable_insufficient_classic` | 5 |
| `readable_insufficient_absent` | 22 |
| `unreadable` | 0 |
| `scope_changed` | 0 |

The complete policy result is now 233 required passes, 27 required failures, and zero required unknowns.

### Active qualifying ruleset observed

- `AtlasReaper311/atlas-api-public`
- `AtlasReaper311/atlas-dep-audit`
- `AtlasReaper311/atlas-infra`
- `AtlasReaper311/atlas-kit-python-rag`
- `AtlasReaper311/atlas-systems`
- `AtlasReaper311/worker-meta-kit`

### Classic protection present without pull-request review protection

- `AtlasReaper311/atlas-doc-viewer`
- `AtlasReaper311/atlas-quota-watch`
- `AtlasReaper311/site-pulse`
- `AtlasReaper311/specular-sonify`
- `AtlasReaper311/status`

### No qualifying ruleset or classic pull-request guard observed

- `AtlasReaper311/.github`
- `AtlasReaper311/atlas-api-index`
- `AtlasReaper311/atlas-badges`
- `AtlasReaper311/atlas-blackbox`
- `AtlasReaper311/atlas-bootstrap`
- `AtlasReaper311/atlas-corpus`
- `AtlasReaper311/atlas-daily-digest`
- `AtlasReaper311/atlas-dora`
- `AtlasReaper311/atlas-gardener`
- `AtlasReaper311/atlas-interface-kit`
- `AtlasReaper311/atlas-journey-watch`
- `AtlasReaper311/atlas-notify`
- `AtlasReaper311/atlas-resource-audit`
- `AtlasReaper311/AtlasReaper311`
- `AtlasReaper311/deploy-watch`
- `AtlasReaper311/github-pulse`
- `AtlasReaper311/ollama-rag-kit`
- `AtlasReaper311/ramone-edge`
- `AtlasReaper311/ramone-memory`
- `AtlasReaper311/ramone-voice-trigger`
- `AtlasReaper311/specular-sentinel`
- `AtlasReaper311/specular-telemetry`

The 27 policy failures are current readable provider findings. They are not repository-source defects and must not reopen Phase II.

## Canary recommendation

Use `AtlasReaper311/atlas-badges` as the first provider canary.

Current evidence:

- lifecycle: `active`;
- scope: `public`;
- runtime service: `false`;
- default branch: `main`;
- current main commit: `2ddf0f410e4967871ecf1bf8de0f005909bce0b7`;
- repository auto-merge: disabled;
- open pull requests: none observed;
- default-branch deployment or publication workflow: none observed;
- repository-native workflow: `CI`;
- native validation job: `test`;
- validation commands: `python -m pytest -q` and `python -m ruff check .`;
- workflow permissions: `contents: read`.

This is lower risk than a production runtime repository, a shared interface distribution repository, the owner-wide `.github` defaults repository, or a repository with existing partial classic protection.

## Proposed canary provider state

The canary should create one active ruleset named `Atlas default branch PR guard` targeting `~DEFAULT_BRANCH` in `AtlasReaper311/atlas-badges`.

Required rules:

- require changes through a pull request;
- block branch deletion;
- block non-fast-forward updates;
- require the exact repository-native CI status context observed from the canary pull request;
- require zero approving reviews because the repository has one owner and GitHub does not permit self-approval to satisfy an approval requirement;
- do not enable repository auto-merge;
- do not add a bypass actor unless the canary review explicitly accepts one.

The exact status-check context must be captured from a fresh canary pull request before the ruleset is activated. Do not guess whether GitHub records the context as `test` or `CI / test`.

## Canary validation sequence

1. Record the pre-change ruleset and classic-protection responses.
2. Open a bounded documentation-only pull request in `atlas-badges` to capture the exact CI context.
3. Create the one-repository ruleset with the approved rule set and captured status context.
4. Confirm a direct update to `main` is rejected.
5. Confirm pull-request creation still works.
6. Confirm the ruleset blocks merging while the native CI check is pending or failing.
7. Confirm merging becomes available after the required check passes.
8. Confirm force-push and default-branch deletion protections are active.
9. Confirm Dependabot pull requests remain compatible while auto-merge stays disabled.
10. Re-run the owner-authenticated scoreboard and confirm `atlas-badges` changes from failed to passed.
11. Record the provider response, ruleset identifier, exact configuration, validation PR, rollback evidence, and report fingerprints before proposing a wider wave.

## Rollback

If the canary blocks the intended owner workflow or produces an unexpected check dependency:

1. disable or delete only the new `atlas-badges` ruleset;
2. verify the pre-change provider response is restored;
3. close the canary pull request if it is no longer needed;
4. rerun the owner-authenticated audit;
5. record the failure and stop the rollout.

Rollback does not include weakening any pre-existing protection because `atlas-badges` currently has no qualifying guard.

## Later rollout grouping

Do not expand until the canary is accepted.

Suggested order after a successful canary:

1. active, public, non-runtime repositories with no guard;
2. active or production repositories with partial classic protection, handled as migrations rather than fresh rulesets;
3. production runtime repositories without a guard;
4. owner-wide defaults and profile repositories after their special behavior is reviewed.

Each wave requires a current read-only inventory, an exact repository list, a rollback plan, provider-write approval, and a fresh policy-aware scoreboard result.

## Separate release boundary

The first owner-approved `worker-meta-kit` release remains independent from this provider audit. Do not create a tag, GitHub Release, or release artifact as part of Phase III.

## Completion criteria

Phase III can close only when:

- every one of the 27 former unknown repositories has current provider evidence;
- every result is classified without converting unknown into pass or failure by assumption;
- any required provider corrections have separately approved rollout and rollback evidence;
- a fresh policy-aware scoreboard run records the resulting state with source commit, collection time, and report fingerprint;
- the final evidence and residual boundaries are committed to Atlas Infra.
