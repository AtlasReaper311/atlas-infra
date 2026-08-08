# GitHub provider guard Wave 2B closeout

Status: complete.

Wave 2B was limited to `AtlasReaper311/atlas-journey-watch`. Wave 3 and all later waves remain unstarted.

## Source authority

- read-only inspection authority: `6c828ea1e98d4a731ffed3ee3def448212eb15df` (`atlas-infra#137`);
- reviewed in-place apply authority: `4b91cdb43734ddf507193022aa0ce847aadcee11` (`atlas-infra#138`).

## Provider result

Existing ruleset `19154613`, `Require native pull request validation`, was reconciled in place. No second ruleset was created.

The final effective guard on the default branch contains:

- `deletion`;
- `non_fast_forward`;
- `pull_request` with zero required approvals and no review-thread-resolution requirement;
- `required_status_checks` requiring `Offline journey validation` from GitHub Actions integration `15368`;
- selector `~DEFAULT_BRANCH`;
- strict required-status policy disabled;
- no bypass actors.

Repository auto-merge remains enabled. `DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged.

Provider evidence archive SHA-256:

`c082eee92abe60e344c4483e70c40310b222bd7fd3966947b676a1edc1c97572`

## Owner-path validation

A documentation-only owner validation PR proved the reconciled guard is usable:

- PR: `atlas-journey-watch#13`;
- reviewed head: `12f11cfcbe07bdb2e71ee4bb14f5411e33a1de7c`;
- required context: `Offline journey validation`, successful on the exact head;
- merge commit: `40c77bd6926833fccc09fe0db098a38b1ea507f8`.

## Dependabot boundary

Genuine Dependabot PR `#12` was not merged and was not used to manufacture an artificial eligible case.

Its reviewed head remains:

`acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`

The selective auto-merge policy remains unchanged. PR `#12` is a GitHub Actions update and therefore remains outside the narrow eligible npm direct-development patch shape. Its final evidence records no auto-merge request.

## Final scoreboard

The owner-authenticated final scoreboard recorded:

- collected at: `2026-08-08T12:47:38Z`;
- repositories checked: `33`;
- policy-required passes: `240`;
- policy-required failures: `20`;
- policy-required unknowns: `0`;
- canonical fingerprint: `sha256:ecafca3af211aeb75a3150d76cfdf717a9098dd86d123b0c3f7b0f2e14217d3f`;
- `atlas-journey-watch/default_branch_guard`: passed.

This realizes the expected Wave 2B movement from `239 / 21 / 0` to `240 / 20 / 0`.

## Final evidence packaging note

Final evidence archive SHA-256:

`ef4a67cb667aec39f9b3ce77c3c7a4c7666890c708bedb104018d9adfd12ae64`

Its `SHA256SUMS.txt` contains 14 entries. Twelve referenced payloads are packaged and all twelve independently matched their SHA-256 values. Two manifest entries were not copied into the ZIP:

- `github-provider-guard-wave-2a-closeout-receipt.json`;
- `github-provider-guard-wave-2b-inspection-receipt.json`.

Both are pre-existing `atlas-infra` report files and GitHub confirms both exist at the exact Wave 2B authority commit. They are not missing Wave 2B provider, owner-validation, scoreboard, or final-receipt evidence. This is recorded as an evidence-packaging-scope defect only, not a provider or validation defect.

The scoreboard fingerprint was independently recomputed from its canonical JSON content and matched exactly.

## Boundaries preserved

Wave 2B did not:

- create a second Journey Watch ruleset;
- change repository auto-merge;
- change `DEPENDABOT_AUTOMERGE_ENABLED`;
- merge Dependabot PR `#12`;
- change secrets;
- dispatch workflows;
- create releases;
- deploy or publish anything;
- begin Wave 3 or any later wave.

Wave 2B requires no further work.
