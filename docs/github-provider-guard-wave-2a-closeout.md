# GitHub provider guard Wave 2A closeout

Status: closed on 2026-08-08.

## Outcome

Wave 2A is complete for:

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`.

`AtlasReaper311/atlas-journey-watch` remains held for separate reconciliation. Wave 3 has not started.

## Final provider state

### atlas-gardener

Ruleset `20576711` is active with the standard Atlas default-branch guard shape:

- pull requests required;
- required native context `test`;
- GitHub Actions integration ID `15368`;
- zero required approvals;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- repository auto-merge disabled.

Owner validation completed through `atlas-gardener#25` at reviewed head `4fbebdaef6e3a3f9009e58ad9716cbb738bd9611`, merged as `7e2b719c106f6da40c270a5aa2cf5b050ef05658`.

Gardener controller mode, write gate, and five write targets remained unchanged throughout the rollout.

### atlas-interface-kit

Ruleset `20583644` is active with the standard Atlas default-branch guard shape:

- pull requests required;
- required native context `Validate interface kit`;
- GitHub Actions integration ID `15368`;
- zero required approvals;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- repository auto-merge disabled.

Owner validation completed through `atlas-interface-kit#15` at reviewed head `a3ab405c1ad7e8c2f6bc71d4523aebe53a27a527`, merged as `cd3f7223960a75e9344116e3960e613cdf267d90`.

No Interface Kit release, tag, publication, deployment, or consumer-adoption action was performed.

## Partial-apply incident and recovery

The first approved Wave 2A provider apply created the Gardener ruleset successfully, then stopped during local post-write verification before Interface Kit was written.

Root cause:

`verify_gardener_controller_state()` reused the shell variable `repo_dir`. During post-write controller-state capture, that helper changed the caller's path so the final local verifier searched for `ruleset-created.json` under `after-controller-state/`.

This was a verifier-path defect after the Gardener provider write.

Recovery inspection proved:

- Gardener ruleset `20576711` was active and correct;
- Gardener auto-merge and controller state were unchanged;
- Interface Kit still had no active branch ruleset;
- Journey Watch was untouched;
- Wave 3 was not started.

Recovery authority merged through `atlas-infra#135` as `57cba128ea6f8e09ff293f84aec803e59ac8ecfe`. A one-shot recovery operator then created only Interface Kit ruleset `20583644`, re-verifying Gardener before and after the write.

No rollback was required.

## Final scoreboard

The owner-authenticated scoreboard was collected at `2026-08-08T09:32:52Z`.

Evidence identity:

- source: `AtlasReaper311/atlas-infra@57cba128ea6f8e09ff293f84aec803e59ac8ecfe`;
- fingerprint: `sha256:4ff745278465998eeffdf6d8f8b7b4789df4c0414950eba880614dc65624295b`;
- repositories checked: `33`;
- required passes: `239`;
- required failures: `21`;
- required unknowns: `0`.

Compared with the Wave 1B closeout:

- required passes increased from `237` to `239`;
- required failures fell from `23` to `21`;
- required unknowns remained `0`.

Both Wave 2A repositories pass `default_branch_guard`.

## Final evidence packaging note

The uploaded final evidence ZIP has SHA-256:

`34526b10ea7ebcb873aec47b0ab40f35d56b98b84a945689f207a0da4427f812`

Its manifest listed 19 read-only evidence payloads. Fourteen packaged payloads were present and all fourteen matched their listed SHA-256 hashes. The packaging copy list omitted five payloads:

- `atlas-gardener-repository.json`;
- `atlas-gardener-variable-mode.json`;
- `atlas-gardener-variable-write-gate.json`;
- `atlas-gardener-variable-write-targets.json`;
- `atlas-interface-kit-repository.json`.

The three Gardener variable hashes match byte-for-byte payloads already preserved in the reviewed recovery evidence. Fresh GitHub repository read-back after upload confirmed `allow_auto_merge=false` for both Gardener and Interface Kit. The final scoreboard fingerprint also recomputed exactly using the canonical stamper at the pinned authority commit.

This omission is therefore recorded as an evidence-packaging defect only. It is not treated as proof of missing provider verification and did not cause another provider write.

## Journey Watch hold

Journey Watch remains outside the completed Wave 2A scope.

Reviewed held state:

- active ruleset ID `19154613`;
- ruleset name `Require native pull request validation`;
- repository auto-merge enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED=true`;
- native context `Offline journey validation`.

Any reconciliation of Journey Watch's existing ruleset and selective Dependabot auto-merge is separate Wave 2B work. It requires fresh inspection and separate provider-write approval.

## Boundaries preserved

Wave 2A did not:

- merge a Dependabot PR implicitly;
- change Gardener controller variables or write targets;
- change Journey Watch provider or automation state;
- create or publish a release or tag;
- dispatch a workflow;
- deploy, restart, or publish a runtime service;
- change secrets;
- perform a rollback;
- begin Wave 3.

Wave 2A is closed.
