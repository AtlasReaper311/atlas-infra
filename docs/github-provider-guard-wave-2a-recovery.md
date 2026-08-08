# GitHub provider guard Wave 2A recovery

## Incident state

The approved Wave 2A provider apply at `20260808T014026Z` created the `atlas-gardener` ruleset successfully, then failed during local post-write verification before the `atlas-interface-kit` provider write.

The root cause is shell variable scope in the two-repository Wave 2A operator. `verify_gardener_controller_state()` assigned its path argument to the shared `repo_dir` variable. After post-write controller-state capture, the apply loop therefore looked for `ruleset-created.json` under `after-controller-state/` instead of the repository evidence directory.

This was a verifier-path defect after the Gardener write, not a failed Gardener provider operation.

## Recovery evidence

Owner-authenticated read-only recovery inspection verified:

- `atlas-gardener` ruleset ID `20576711` exists and is active;
- ruleset name `Atlas default branch PR guard`;
- target `~DEFAULT_BRANCH`;
- pull requests required with zero approvals;
- native required context `test` from GitHub Actions integration ID `15368`;
- deletion and non-fast-forward updates blocked;
- no bypass actors;
- repository auto-merge remains disabled;
- `main` remains `319465dcea68a8fefead3e7d90e82b79078cb34d`;
- Gardener controller mode remains `automerge-low-risk`;
- Gardener write gate remains `enabled`;
- Gardener write targets remain the five previously approved partial-protection repositories;
- `atlas-interface-kit` still has no active branch ruleset;
- Interface Kit auto-merge remains disabled;
- Interface Kit `main` remains `21a1a168e3b25e916555ce4edd4229bd7c061ecb`;
- `atlas-journey-watch` was not touched;
- Wave 3 was not started.

The recovery archive contained 39 SHA-256-covered payloads with zero digest mismatches.

## Recovery operator

`scripts/github-provider-guard-wave-2a-recovery.sh` is a one-shot recovery operator for the remaining approved `atlas-interface-kit` provider write.

It defaults to read-only `inspect` mode.

The only write mode is `apply-interface-kit`, gated by the exact confirmation phrase:

`APPLY GITHUB PROVIDER GUARD WAVE 2A INTERFACE KIT RECOVERY`

Before that write it must re-prove Gardener ruleset `20576711` and controller state, then prove Interface Kit still has no active branch ruleset or classic protection and that its pinned validation evidence remains valid.

Its only provider mutation is one `POST` to the `atlas-interface-kit` rulesets endpoint. After the write it reads back the created ruleset, verifies effective `main` rules, rechecks Interface Kit repository state, and re-verifies Gardener remained unchanged.

It cannot create or replace the Gardener ruleset, change Actions variables or secrets, touch Journey Watch provider state, merge pull requests, dispatch workflows, create releases, or begin Wave 3.

## Approval boundary

The owner already approved Wave 2A provider writes for exactly `atlas-gardener` and `atlas-interface-kit`. The Gardener write consumed the first half of that authority. This recovery operator exists only to finish the still-unconsumed Interface Kit write after source repair and exact-head validation.
