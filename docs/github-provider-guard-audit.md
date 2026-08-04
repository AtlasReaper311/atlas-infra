# GitHub provider guard audit

## Status

Phase III completed the owner-authenticated provider inspection and the bounded `atlas-badges` canary write. The normal protected pull-request path and a genuine Dependabot pull request have both succeeded under the active rule.

A stamped owner-authenticated scoreboard rerun and final canary receipt remain pending. No wider rollout or destructive branch test has begun.

Phase II remains closed. The provider findings in this document do not reopen its source-conformance result.

## Part 0 inspection

The Phase II closing scoreboard was GitHub Actions run `30535544793`. It checked the authoritative 33-repository public projection and recorded:

- 233 required passes;
- 0 required failures;
- 27 required unknown outcomes;
- 68 not-applicable outcomes;
- 1 approved exception;
- 1 deferred outcome.

All 27 unknown outcomes were `default_branch_guard`. The report message was `GitHub ruleset or branch-protection evidence was unavailable.` This was an evidence-access result and did not prove that a guard was present or absent.

The scoreboard reads:

- `GET /repos/{owner}/{repo}/rulesets`;
- the ruleset detail endpoint when the list response omits conditions or rules;
- `GET /repos/{owner}/{repo}/branches/{default_branch}/protection` as the classic-protection fallback.

A default-branch guard passes when either:

- an active branch ruleset targets the default branch and contains `pull_request`, `deletion`, and `non_fast_forward`; or
- classic branch protection requires pull-request reviews.

## Initial owner-authenticated evidence

Atlas supplied the generated JSON and Markdown reports on 31 July 2026. Their policy inputs matched the Phase II closing evidence:

- schema: `atlas-github-conformance-scoreboard/report/v2`;
- repositories checked: 33;
- projection fingerprint: `sha256:30f47de465c1117fda375b70b7d156d73f4b39622873133c756f7fa06539c6a0`;
- requirements fingerprint: `sha256:b05e2fe568018d1bf491665237f092e4bcfb6c70d81e237da7efa8cc78ec6ed7`;
- JSON file digest: `sha256:8250292fa3865b04e2a5d5a56a036a44bfb5648bae9b16c01efe944fcbd2111c`;
- Markdown file digest: `sha256:30ee4ac5864268648e85aef9028579ee03f214f5a966c206d45f45cd31a17a46`.

The reports contained no token value and no unreadable provider outcome. The generator did not yet embed the Atlas Infra source commit, collection timestamp, or a report fingerprint. The scoreboard-stamping change prepared with this closeout corrects that evidence gap without changing the provider checks or policy rules.

## Classified provider result before the canary

| Classification | Count |
| --- | ---: |
| `proved_ruleset` | 6 |
| `proved_classic` | 0 |
| `readable_insufficient_classic` | 5 |
| `readable_insufficient_absent` | 22 |
| `unreadable` | 0 |
| `scope_changed` | 0 |

The policy result was 233 required passes, 27 required failures, and zero required unknowns.

### Active qualifying ruleset observed

- `AtlasReaper311/atlas-api-public`
- `AtlasReaper311/atlas-dep-audit`
- `AtlasReaper311/atlas-infra`
- `AtlasReaper311/atlas-kit-python-rag`
- `AtlasReaper311/atlas-systems`
- `AtlasReaper311/worker-meta-kit`

### Classic protection without pull-request review protection

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

## Canary selection

`AtlasReaper311/atlas-badges` was selected because it was:

- active and public;
- not a runtime service;
- on default branch `main`;
- without an existing guard;
- without a deployment or publication workflow;
- protected by a repository-native `CI` workflow with job context `test`;
- configured with repository auto-merge disabled.

The native `test` job runs pytest and Ruff with read-only workflow permissions.

## Canary provider write

Atlas separately approved one ruleset write. GitHub created ruleset `20126389` at `2026-07-31T14:52:44.173+01:00` with this exact state:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- pull request required;
- required approving reviews: 0;
- required status context: `test`;
- required status integration ID: `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- bypass actors: none;
- current-user bypass: `never`;
- repository auto-merge: disabled.

The create response and ruleset read-back were identical. The active-rules endpoint independently returned `deletion`, `non_fast_forward`, `pull_request`, and `required_status_checks` from ruleset `20126389`.

Owner-authenticated evidence file digests:

- `repository-after.json`: `sha256:e074e92e7979e697dbd8d6f87dbd9338b430c09e44880b1a3a3b3d45e59aab40`;
- `ruleset-created.json`: `sha256:0184166c46f2dac05d105276f3e650e25cbf63d0847d734d9d4aaa47a78d744a`;
- `ruleset-readback.json`: `sha256:0184166c46f2dac05d105276f3e650e25cbf63d0847d734d9d4aaa47a78d744a`;
- `active-rules-after.json`: `sha256:3f1a73725bc54f89196cdb3d43b64c3f5556024d5cbe39e96e283d588e2e78d1`.

## Protected owner pull-request path

Canary pull request `atlas-badges#5` captured the native status context before the provider write, then received the post-write evidence documentation.

Its reviewed exact head was `627177aaa60fdf3830578b6582dc5798142171e9`. The post-write runs were:

| Workflow | Run | Result |
| --- | ---: | --- |
| `CI` | `30637955337` | success |
| `CodeQL` | `30637953723` | success |
| `OpenSSF Scorecard` | `30637953787` | success |
| `Dependabot review policy` | `30637954640` | skipped as expected for a non-Dependabot pull request |

The pull request had no unresolved review threads and merged through the active ruleset as `21cb45aff47183b86258c5a23a354d66c65137bb`.

This proves that the normal owner pull-request path remains available and that the required `test` context can satisfy the protected merge path.

## Genuine Dependabot compatibility

A genuine Dependabot pull request now exists under the canary ruleset:

- pull request: `atlas-badges#6`;
- head: `238dbc95d55da73c19310609480e1f63d217cd1c`;
- state at inspection: open and mergeable;
- repository auto-merge: disabled.

Exact-head workflow evidence:

| Workflow | Run | Result |
| --- | ---: | --- |
| `Dependabot review policy` | `30681518607` | success |
| `CI` | `30681518624` | success |
| `CodeQL` | `30681518610` | success |
| `OpenSSF Scorecard` | `30681518620` | success |

This proves that Dependabot can create a pull request, obtain the required native check, and pass the repository review policy while auto-merge remains disabled. No synthetic Dependabot event or merge is required for the canary closeout.

## Validation sequence status

| Step | Status | Evidence or boundary |
| --- | --- | --- |
| Record pre-change provider state | complete | Initial owner-authenticated audit and file digests |
| Capture exact native check context | complete | `atlas-badges#5`, workflow `CI`, job `test` |
| Create bounded ruleset | complete | Ruleset `20126389` and identical read-back |
| Confirm direct update to `main` is rejected | not attempted | Intentional prohibited write; excluded by owner instruction |
| Confirm pull-request creation works | complete | `atlas-badges#5`, `#6`, and `#7` |
| Prove pending or failing required check blocks merge | not injected | No failing workflow or merge race manufactured |
| Prove passing required check allows merge | complete | `atlas-badges#5` merged as `21cb45aff47183b86258c5a23a354d66c65137bb` |
| Confirm force-push and deletion rules are active | provider state proved | Active-rules read-back; destructive attempts not made |
| Confirm Dependabot compatibility | complete | Genuine `atlas-badges#6` exact-head runs |
| Rerun stamped owner-authenticated scoreboard | pending | Requires merged stamping source and a local read-only run |
| Record final canary closeout | pending | Requires stamped report files and digests |

The incomplete destructive and synthetic rejection tests are explicit residual evidence boundaries. They are not silently recorded as successful.

## Scoreboard stamping

The closeout source adds a post-collection stamper for policy-aware v2 reports. It records:

- UTC `collected_at`;
- exact `AtlasReaper311/atlas-infra` source commit;
- canonical SHA-256 report fingerprint.

The fingerprint excludes only the fingerprint field itself. The stamper fails closed on an unexpected schema, invalid source commit, invalid timestamp, malformed JSON root, or malformed Markdown heading. Scheduled and manual workflow runs pass `${GITHUB_SHA}` after the policy report is built.

The owner-authenticated rerun must use a clean checkout of the merged stamping source. It must retain both output files and their file digests alongside the embedded report fingerprint.

Expected provider-only movement, assuming no unrelated estate drift:

- `atlas-badges` changes from failed to passed for `default_branch_guard`;
- required passes change from 233 to 234;
- required failures change from 27 to 26;
- required unknowns remain 0.

These counts are expectations, not evidence. The final closeout must use the actual stamped result.

## Rollback

If the canary later blocks the intended owner workflow or produces an unexpected check dependency:

1. disable or delete only ruleset `20126389`;
2. verify the pre-change provider result is restored for `atlas-badges`;
3. rerun the owner-authenticated scoreboard;
4. record the failure and stop the programme.

Rollback has not been executed because the protected owner and Dependabot paths both work. A rollback test would itself change provider state and remains separately approval-gated.

## Wider rollout boundary

Do not expand from `atlas-badges` until the stamped rerun and final canary receipt are reviewed and merged.

A later wave requires:

- a current read-only inventory;
- an exact repository list;
- repository-native required-check discovery;
- a migration plan for partial classic protections;
- rollback instructions;
- separate provider-write approval;
- a new stamped policy-aware scoreboard result.

Suggested order remains:

1. active public non-runtime repositories with no guard;
2. repositories with partial classic protection, treated as migrations;
3. production runtime repositories without a guard;
4. owner-wide defaults and profile repositories after special-behaviour review.

## Separate boundaries

The first owner-approved `worker-meta-kit` release remains independent. Do not create a tag, GitHub Release, or release artifact as part of Phase III.

Phase III can close only after the stamped owner-authenticated rerun and final receipt are committed. Wider provider correction remains a later programme rather than an implicit part of this canary.
