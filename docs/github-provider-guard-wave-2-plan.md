# GitHub provider guard wider rollout: Wave 2 plan

Status: Wave 2A is complete for `atlas-gardener` and `atlas-interface-kit`. `atlas-journey-watch` remains held for separate migration/reconciliation work. Wave 3 and all later waves remain unstarted.

## Scope

Wave 2 covers three specialist active public non-runtime repositories:

### Wave 2A complete

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`.

### Wave 2B held

- `AtlasReaper311/atlas-journey-watch`.

ADR-0004 authority in `policy/public-assurance-repositories.json` classifies all three as active, public, original repositories. None is classified as a public runtime-service repository by `policy/estate-registry.json`.

## Inspection authority

Owner-authenticated inspection authority merged through `atlas-infra#133` as `1a5be84456861e5d0cd09b13db207f2e81a1f007`.

Inspection evidence:

- uploaded archive SHA-256: `44cdbb9171c4cf9aaf0a3240836d744ec9ef5e19c1c9790ebc4c654e8b385b62`;
- evidence payloads covered by `SHA256SUMS.txt`: `40`;
- digest mismatches: `0`;
- provider writes performed: `false`.

The inspection established the Wave 2A native gates and identified Journey Watch as a reconciliation case rather than a fresh guard-addition candidate.

## Wave 2A provider authority

Wave 2A apply authority merged through `atlas-infra#134` as `487c7ba6ea6ffaf5e5a3e9bcc756435d075ba0f3`.

Merging Wave 2A apply source authority is not provider-write approval.

Atlas separately approved provider writes for exactly:

- `AtlasReaper311/atlas-gardener`;
- `AtlasReaper311/atlas-interface-kit`.

`atlas-journey-watch`, Wave 3, and all later waves were excluded.

The intended ruleset shape was:

- name `Atlas default branch PR guard`;
- target `~DEFAULT_BRANCH`;
- active enforcement;
- pull request required;
- zero required approvals;
- no required review-thread resolution;
- exact repository-native GitHub Actions status check bound to integration ID `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch-update policy disabled.

## Wave 2A provider result

### atlas-gardener

The approved provider apply created ruleset `20576711`.

Final verified state:

- ruleset name `Atlas default branch PR guard`;
- required context `test`;
- GitHub Actions integration ID `15368`;
- pull requests required with zero approvals;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- repository auto-merge disabled.

The initial two-repository apply stopped after the Gardener write because a shell helper overwrote the shared `repo_dir` variable during local post-write verification. This was a verifier-path defect after a successful provider write, not a failed Gardener ruleset operation.

Owner-authenticated recovery inspection proved ruleset `20576711` was active and semantically correct, Interface Kit remained untouched, and Gardener controller state remained unchanged.

Recovery inspection archive SHA-256:

`1e005646386cfd15d000f61a85520d6faa1f05da4f6252e845274bd63204eac4`

Recovery source merged through `atlas-infra#135` as `57cba128ea6f8e09ff293f84aec803e59ac8ecfe`.

### atlas-interface-kit

The one-shot recovery operator created ruleset `20583644`.

Final verified state:

- ruleset name `Atlas default branch PR guard`;
- required context `Validate interface kit`;
- GitHub Actions integration ID `15368`;
- pull requests required with zero approvals;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- repository auto-merge disabled.

Interface Kit recovery archive SHA-256:

`5c83a652ab46367f6a9ab554ed9dfe2f6329874e113d59eb98b0e008ceffbf47`

Gardener ruleset `20576711` was re-read before and after the Interface Kit recovery and was not recreated or changed.

## Owner-path validation

Protected owner validation completed through real pull requests.

### atlas-gardener

- PR: `atlas-gardener#25`;
- reviewed head: `4fbebdaef6e3a3f9009e58ad9716cbb738bd9611`;
- required native context: `test`;
- merge commit: `7e2b719c106f6da40c270a5aa2cf5b050ef05658`.

### atlas-interface-kit

- PR: `atlas-interface-kit#15`;
- reviewed head: `a3ab405c1ad7e8c2f6bc71d4523aebe53a27a527`;
- required native context: `Validate interface kit`;
- merge commit: `cd3f7223960a75e9344116e3960e613cdf267d90`.

Both exact native contexts completed successfully before merge and both protected owner paths merged successfully.

## Final scoreboard

The owner-authenticated final scoreboard was collected at `2026-08-08T09:32:52Z` against authority commit `57cba128ea6f8e09ff293f84aec803e59ac8ecfe`.

Canonical fingerprint:

`sha256:4ff745278465998eeffdf6d8f8b7b4789df4c0414950eba880614dc65624295b`

Final required-policy movement:

- required passes: `237` to `239`;
- required failures: `23` to `21`;
- required unknowns: `0`;
- repositories checked: `33`.

Both `AtlasReaper311/atlas-gardener/default_branch_guard` and `AtlasReaper311/atlas-interface-kit/default_branch_guard` pass.

## Final evidence packaging note

The final evidence ZIP SHA-256 is:

`34526b10ea7ebcb873aec47b0ab40f35d56b98b84a945689f207a0da4427f812`

Its `SHA256SUMS.txt` contains 19 payload entries. Fourteen packaged payloads were present and matched their listed SHA-256 identities. Five read-only snapshots were omitted by the packaging copy list:

- `atlas-gardener-repository.json`;
- `atlas-gardener-variable-mode.json`;
- `atlas-gardener-variable-write-gate.json`;
- `atlas-gardener-variable-write-targets.json`;
- `atlas-interface-kit-repository.json`.

The three Gardener variable payload hashes match byte-for-byte copies already preserved in the reviewed recovery evidence archives. Fresh GitHub repository read-back after upload confirmed repository auto-merge remains disabled for both Gardener and Interface Kit. The scoreboard fingerprint independently recomputed exactly using `scripts/github_conformance_stamp.py` at the pinned authority commit.

This is recorded as an evidence-packaging defect only. It did not trigger or conceal a provider mutation and does not invalidate the provider ruleset, owner-path, or scoreboard evidence chain.

## Journey Watch hold

Journey Watch remains intentionally held.

Current reviewed provider and automation identity:

- existing active ruleset ID: `19154613`;
- ruleset name: `Require native pull request validation`;
- repository auto-merge enabled;
- `DEPENDABOT_AUTOMERGE_ENABLED`: `true`;
- native context: `Offline journey validation`.

Journey Watch is not a fresh ruleset-addition case. Its existing provider protection and selective Dependabot auto-merge must be reconciled deliberately before any mutation is proposed.

Wave 2A did not create, replace, update, disable, or delete Journey Watch ruleset `19154613` and did not change its auto-merge setting or variable.

## Closure

Wave 2A is closed.

No Dependabot PR was merged implicitly. No release or tag was created. No workflow was dispatched. No deployment, runtime restart, publication, rollback, secret change, Gardener controller change, or Journey Watch provider write was performed as part of Wave 2A.

Any Journey Watch reconciliation is a separate Wave 2B decision requiring fresh inspection and separate provider-write approval. Wave 3 and all later waves remain unstarted.
