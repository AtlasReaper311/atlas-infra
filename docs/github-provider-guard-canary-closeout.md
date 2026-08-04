# GitHub provider guard canary closeout

Status: source and provider evidence prepared; stamped owner-authenticated scoreboard rerun pending.

## Scope

This record closes the implemented and observed portions of the one-repository `atlas-badges` provider-guard canary. It does not close Phase III, approve a wider rollout, or claim destructive tests that were not performed.

Authority:

- provider audit and canary plan: `atlas-infra#103`;
- canary repository: `AtlasReaper311/atlas-badges`;
- active ruleset: `20126389`, `Atlas default branch PR guard`.

## Provider state

The approved ruleset is active on the default branch and contains:

- pull-request requirement;
- zero required approvals;
- required status context `test`, integration ID `15368`;
- deletion protection;
- non-fast-forward protection;
- no bypass actor.

Repository auto-merge remained disabled after the write.

The create response and provider read-back were identical. The active-rules endpoint returned the four expected controls.

## Owner path receipt

`atlas-badges#5` validated the native check context and the normal protected merge path.

- reviewed head: `627177aaa60fdf3830578b6582dc5798142171e9`;
- `CI` run `30637955337`: success;
- `CodeQL` run `30637953723`: success;
- `OpenSSF Scorecard` run `30637953787`: success;
- Dependabot policy run `30637954640`: skipped as expected;
- unresolved review threads: 0;
- merge commit: `21cb45aff47183b86258c5a23a354d66c65137bb`.

The successful merge proves that the owner pull-request path remained available and that the repository-native `test` check satisfied the active rule.

## Dependabot receipt

A genuine Dependabot pull request supplied the compatibility evidence without creating a synthetic event.

- pull request: `atlas-badges#6`;
- head: `238dbc95d55da73c19310609480e1f63d217cd1c`;
- state at inspection: open and mergeable;
- Dependabot review policy run `30681518607`: success;
- `CI` run `30681518624`: success;
- `CodeQL` run `30681518610`: success;
- OpenSSF Scorecard run `30681518620`: success;
- repository auto-merge: disabled.

No Dependabot pull request was merged as part of the canary.

## Evidence files

| File | SHA-256 |
| --- | --- |
| `repository-after.json` | `e074e92e7979e697dbd8d6f87dbd9338b430c09e44880b1a3a3b3d45e59aab40` |
| `ruleset-created.json` | `0184166c46f2dac05d105276f3e650e25cbf63d0847d734d9d4aaa47a78d744a` |
| `ruleset-readback.json` | `0184166c46f2dac05d105276f3e650e25cbf63d0847d734d9d4aaa47a78d744a` |
| `active-rules-after.json` | `3f1a73725bc54f89196cdb3d43b64c3f5556024d5cbe39e96e283d588e2e78d1` |

## Scoreboard identity correction

The existing policy-aware report contract lacks a collection timestamp, exact Atlas Infra source commit, and report-level fingerprint. The closeout source adds a post-collection stamper that records:

- UTC `collected_at`;
- `source.repository` and exact 40-character `source.commit`;
- canonical SHA-256 `fingerprint`.

The stamper updates both JSON and Markdown, rejects malformed inputs, and is called by the existing read-only workflow after policy evaluation.

## Required rerun

After the stamping pull request merges, run the owner-authenticated scoreboard from a clean checkout of that merge commit. Preserve:

- stamped JSON report;
- stamped Markdown report;
- each file digest;
- embedded report fingerprint;
- source commit;
- collection timestamp;
- actual policy summary;
- `atlas-badges` default-branch-guard outcome.

Expected movement is one provider check from failed to passed, but the recorded closeout must use the actual report rather than the expectation.

## Residual evidence boundaries

The following were not performed:

- direct push to `main`;
- force push to `main`;
- deletion attempt against `main`;
- manufactured failing required check;
- rollback provider write;
- wider ruleset rollout.

The provider read-back proves the force-push and deletion rules are active, but no destructive rejection claim is made. These boundaries remain explicit rather than being converted into passes by inference.

## Completion gate

The canary closeout is complete only when the stamped owner-authenticated report and its digests are reviewed and committed to Atlas Infra. Phase III and any wider provider programme remain open until that evidence is accepted through a separate pull request and approval gate.
