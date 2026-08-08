# GitHub provider guard wider rollout: Wave 2B plan

Status: complete and evidenced.

Wave 2B is limited to `AtlasReaper311/atlas-journey-watch`.

Wave 2A is closed. Wave 3 and all later waves remain unstarted.

## Final outcome

Existing Journey Watch ruleset `19154613`, `Require native pull request validation`, was reconciled in place under separately approved provider authority. No second ruleset was created.

Final guard semantics:

- selector: `~DEFAULT_BRANCH`;
- rule types: `deletion`, `non_fast_forward`, `pull_request`, `required_status_checks`;
- zero required approvals;
- review-thread resolution not required;
- native required context: `Offline journey validation`;
- GitHub Actions integration ID: `15368`;
- strict required-status policy: false;
- bypass actors: none.

Repository auto-merge remains enabled and `DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged.

Provider archive SHA-256:

`c082eee92abe60e344c4483e70c40310b222bd7fd3966947b676a1edc1c97572`

Owner-path validation completed through `atlas-journey-watch#13`:

- reviewed head: `12f11cfcbe07bdb2e71ee4bb14f5411e33a1de7c`;
- exact required context: `Offline journey validation`, successful;
- merge commit: `40c77bd6926833fccc09fe0db098a38b1ea507f8`.

PR `#12` remains a genuine ineligible Dependabot specimen and was not merged. Its reviewed head is `acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`; its final evidence records no auto-merge request.

The final owner-authenticated scoreboard recorded 240 policy-required passes, 20 policy-required failures, and zero unknowns across 33 repositories. `atlas-journey-watch/default_branch_guard` passed. Canonical fingerprint:

`sha256:ecafca3af211aeb75a3150d76cfdf717a9098dd86d123b0c3f7b0f2e14217d3f`

Wave 2B requires no further work.

## Historical inspection authority

Inspection authority merged through `atlas-infra#137` as `6c828ea1e98d4a731ffed3ee3def448212eb15df`.

The reviewed owner-authenticated inspection archive had:

- SHA-256: `abf7f135257a5b842188ea8ffae6cc9e2be28b0a0e60bbcba06d46c83bef0141`;
- 18 manifest entries;
- digest mismatches: zero;
- provider writes: none;
- variables written: none;
- secrets read: none;
- `qualifies_standard_guard_semantics: false`.

The pinned inspection source state was:

- Journey Watch `main`: `a124d23ba4444522c206ae3c169165b4e0ef8019`;
- existing ruleset: `19154613`, `Require native pull request validation`;
- genuine Dependabot PR head: `acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022`;
- native context: `Offline journey validation`;
- integration: `15368`;
- repository auto-merge enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED=true`.

Before reconciliation, the existing ruleset condition was `refs/heads/main`, its rule types: `required_status_checks` only, and strict required-status policy was true.

The inspection supported a narrow in-place reconciliation. Replacement, deletion, disablement, or creation of a second overlapping ruleset is not an assumed outcome.

## Historical apply authority

Apply authority merged through `atlas-infra#138` as `4b91cdb43734ddf507193022aa0ce847aadcee11`.

The fail-closed runner was `scripts/github-provider-guard-wave-2b-reconcile.sh`. It preserved the ruleset ID and name, changed only the deficient guard semantics, and contained one provider mutation path:

`PUT /repos/AtlasReaper311/atlas-journey-watch/rulesets/19154613`

The historical approval contract remains part of the regression record: Any provider mutation requires a new explicit approval after the proposal is reviewed. That approval was subsequently provided for this exact in-place update and has now been consumed.

The runner did not write repository auto-merge, Actions variables, secrets, PR state, releases, workflows, deployments, or runtime state.

## Selective auto-merge boundary

The pinned reusable Dependabot policy remains unchanged. It permits only its narrow eligible npm direct-development patch shape after its existing policy checks.

PR `#12` is a GitHub Actions dependency update, so its null auto-merge request is expected fail-closed behavior rather than evidence that the pilot is broken.

No artificial eligible dependency update was manufactured solely for this provider reconciliation.

## Final evidence

Final evidence archive SHA-256:

`ef4a67cb667aec39f9b3ce77c3c7a4c7666890c708bedb104018d9adfd12ae64`

Its manifest contains 14 entries. Twelve packaged payloads match their SHA-256 values with zero mismatches. Two pre-existing `atlas-infra` reports listed by the manifest were not copied into the final ZIP:

- `github-provider-guard-wave-2a-closeout-receipt.json`;
- `github-provider-guard-wave-2b-inspection-receipt.json`.

Both exist at the exact authority commit. The omission is classified as an evidence-packaging-scope defect only. All Wave 2B provider, owner-validation, scoreboard, and final-receipt payloads are present, and the canonical scoreboard fingerprint recomputes exactly.

## Closed boundaries

Wave 2B did not:

- create a second Journey Watch ruleset;
- delete or disable ruleset `19154613`;
- change repository auto-merge;
- change `DEPENDABOT_AUTOMERGE_ENABLED`;
- enable auto-merge on or merge Dependabot PR `#12`;
- change Journey Watch runtime, release, schedule, secret, or deployment state;
- dispatch workflows;
- deploy or publish anything;
- begin Wave 3 or any later wave.
