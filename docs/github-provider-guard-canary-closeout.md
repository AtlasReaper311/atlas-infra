# GitHub provider guard canary closeout

Status: complete for the bounded `atlas-badges` canary. Wider rollout remains unapproved and has not started.

## Scope

This record closes the one-repository `AtlasReaper311/atlas-badges` provider-guard canary. It records the approved provider write, the normal protected owner path, a genuine Dependabot path, and the final owner-authenticated scoreboard result.

It does not close the wider Phase III provider programme. Twenty-six readable default-branch-guard failures remain elsewhere in the public projection and require separately approved rollout waves.

Authority:

- provider audit and canary plan: `atlas-infra#103`;
- scoreboard stamping and closeout tooling: `atlas-infra#123`;
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

A genuine Dependabot pull request supplied compatibility evidence without creating a synthetic event.

- pull request: `atlas-badges#6`;
- head: `238dbc95d55da73c19310609480e1f63d217cd1c`;
- state at inspection: open and mergeable;
- Dependabot review policy run `30681518607`: success;
- `CI` run `30681518624`: success;
- `CodeQL` run `30681518610`: success;
- OpenSSF Scorecard run `30681518620`: success;
- repository auto-merge: disabled.

No Dependabot pull request was merged as part of the canary.

## Final scoreboard receipt

The owner-authenticated report was collected on `2026-08-04T23:22:02Z` from exact Atlas Infra source commit `da0de618a70603a1989d0b03c6f7d8659fa458f3`.

Report identity:

- schema: `atlas-github-conformance-scoreboard/report/v2`;
- report fingerprint: `sha256:cfb03af45343602dfa5bcc1c6180d2e054242a14a6295695ffda99d7ae5427bd`;
- repositories checked: 33;
- required checks passed: 234;
- required checks failed: 26;
- required checks unknown: 0;
- not applicable: 68;
- approved exceptions: 1;
- deferred: 1.

The report moved exactly one required provider check from failed to passed:

- previous policy result: 233 passed, 27 failed, 0 unknown;
- final policy result: 234 passed, 26 failed, 0 unknown;
- `AtlasReaper311/atlas-badges` `default_branch_guard`: `passed`;
- provider message: `An active default-branch ruleset was observed.`

The canonical fingerprint was independently recomputed from the complete stamped JSON after removing only the fingerprint field. It matched the embedded value.

## Final evidence identity

Generated reports remain under the ignored `reports/` path and are not committed as ordinary repository source. Their complete identity is preserved in `docs/github-provider-guard-canary-final-receipt.json`.

| Evidence | Bytes | SHA-256 |
| --- | ---: | --- |
| `github-conformance-scoreboard.json` | 129283 | `df9b2744a0e2adab81550a825833d7baec80ab24678ff5cd31157767868e330c` |
| `github-conformance-scoreboard.md` | 6929 | `d797d7a8b366367dffa7e4fe06a405bbafa16b6989e890e15dfb750a1068f140` |
| `atlas-badges-canary-final-receipt.json` | 1022 | `298726c75d84ffb6954fd4d437eb786471f73fc40336f087c72f6def620f5e70` |
| `atlas-badges-final-scoreboard-evidence.zip` | 6447 | `9c95ffe17159e8e67d91136435d370842d886d06d1da27906260c670cad4eca6` |

The uploaded `SHA256SUMS.txt` matched all three contained evidence files.

## Residual evidence boundaries

The following were not performed:

- direct push to `main`;
- force push to `main`;
- deletion attempt against `main`;
- manufactured failing required check;
- rollback provider write;
- wider ruleset rollout.

The provider read-back proves the force-push and deletion rules are configured and active, but no destructive rejection claim is made. These boundaries remain explicit rather than being converted into passes by inference.

## Closeout decision

The bounded `atlas-badges` canary is complete.

It proved:

- the approved default-branch ruleset was stored exactly as intended;
- repository auto-merge remained disabled;
- the owner pull-request path remained usable;
- the required native `test` context gates the protected path;
- a genuine Dependabot pull request remains compatible;
- the owner-authenticated scoreboard now records `atlas-badges` as passed;
- the final report has a source commit, UTC collection timestamp, canonical fingerprint, file digests, and a machine-readable receipt.

No further action is required for this canary.

Any wider rollout must begin with a fresh provider inventory, an exact repository list, repository-specific required check discovery, rollback instructions, separate provider-write approval, and a new stamped scoreboard result.
