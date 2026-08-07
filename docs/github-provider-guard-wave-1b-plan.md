# GitHub provider guard wider rollout: Wave 1B plan

Status: source authority prepared. No Wave 1B provider write has been performed.

## Scope

Wave 1B is limited to exactly one repository:

- `AtlasReaper311/ollama-rag-kit`.

Wave 1A is complete and evidenced. Wave 2 and all later waves remain unstarted.

## Part 0 evidence

Part 0 was refreshed against current GitHub state on 2026-08-07.

### Repository classification

ADR-0004 authority places `AtlasReaper311/ollama-rag-kit` in `policy/public-assurance-repositories.json` with:

- lifecycle: `active`;
- scope: `public`;
- provenance: `original`.

It is not present in `policy/estate-registry.json`, so it is not classified as a public runtime-service repository by the current authoritative policy.

The repository README describes a runnable local containerised Ramone RAG service and a deployed service shape. That execution detail does not override ADR-0004 classification authority. The repository has no `.github/workflows/deploy.yml` on current `main`.

### Current repository state

Observed repository state:

- default branch: `main`;
- current `main`: `d0060829dd474d8d8a57b11694ca03411927bf9f`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled;
- no provider write was performed during Part 0.

### Native pull-request gate

Current `.github/workflows/ci.yml` defines one repository-native pull-request job:

- workflow: `CI`;
- job/context: `Build and smoke-check`;
- Python syntax validation: `python -m compileall app`;
- container validation: `docker compose build`;
- GitHub Actions integration ID: `15368`.

The notification job is push-only for `main` and is not a pull-request gate.

### Genuine Dependabot proof

`ollama-rag-kit#16` is a current genuine Dependabot pull request:

- state: open;
- base: `main`;
- base SHA: `d0060829dd474d8d8a57b11694ca03411927bf9f`;
- head SHA: `c88e6277f1f2b9bebc8f607bbb59a7d37860e92a`;
- mergeable: true.

Exact-head workflow evidence:

- `CI` run `30681522121`: success;
- required `Build and smoke-check` job: success;
- `Dependabot review policy` run `30681521978`: success;
- `OpenSSF Scorecard` run `30681521987`: success;
- `CodeQL` run `30681522000`: success.

This provides current automation compatibility evidence before any ruleset write. No Dependabot pull request is approved for merge by this plan.

## Proposed ruleset

Wave 1B proposes one repository ruleset using the canary and Wave 1A pattern:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- require changes through a pull request;
- required approving reviews: 0;
- required review thread resolution: false;
- required status context: `Build and smoke-check`;
- required status integration ID: `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- no bypass actors;
- strict required-status branch update policy disabled;
- repository auto-merge remains disabled.

## Fail-closed runner

`scripts/github-provider-guard-wave-1b.sh` owns the operator path.

It defaults to read-only `MODE=inspect` and is pinned to:

- repository `ollama-rag-kit`;
- current `main` `d0060829dd474d8d8a57b11694ca03411927bf9f`;
- validation PR `#16`;
- validation head `c88e6277f1f2b9bebc8f607bbb59a7d37860e92a`;
- required context `Build and smoke-check`;
- integration ID `15368`.

Inspection refuses to continue if:

- authentication is not `AtlasReaper311`;
- repository identity, visibility, archival state, default branch, main SHA, or auto-merge state drifts;
- an active branch ruleset already exists;
- classic branch protection exists or its absence cannot be proved;
- a repository deploy workflow appears at `.github/workflows/deploy.yml`;
- the validation pull request closes, changes base, changes head, or stops targeting the expected main revision;
- the required check is not uniquely successful under integration `15368`.

Provider writes require both:

```text
MODE=apply
ATLAS_PROVIDER_WRITE_CONFIRMATION=APPLY GITHUB PROVIDER GUARD WAVE 1B
```

The apply path can create only one ruleset in `AtlasReaper311/ollama-rag-kit`. It records provider request, create response, read-back, active-rule projection, repository settings, pull-request evidence, check-run evidence, and SHA-256 digests under ignored `reports/` output.

## Validation sequence

After this source authority is reviewed and merged:

1. obtain separate approval for the single `ollama-rag-kit` provider write;
2. run the merged runner in read-only inspection mode from the exact approved Atlas Infra commit;
3. review the inspection evidence and digests;
4. run apply mode only if the baseline remains identical;
5. verify create response and provider read-back are equivalent in meaning;
6. verify the four intended active rules apply to `main`;
7. verify repository auto-merge remains disabled;
8. re-read Dependabot PR `#16` and its required check;
9. open one harmless owner validation pull request in `ollama-rag-kit`;
10. merge it only after the required context and all repository checks settle successfully or skip as expected;
11. run a stamped owner-authenticated scoreboard;
12. commit a machine-readable receipt and human-readable Wave 1B closeout in a separate Atlas Infra pull request.

The last Wave 1A scoreboard recorded 236 required passes, 24 required failures, and 0 required unknowns. A move to 237 passes and 23 failures is planning arithmetic only. The actual stamped result is the closure evidence.

## Rollback

If the new rule blocks an intended owner or automation path:

1. stop Wave 1B immediately;
2. identify only the new `ollama-rag-kit` ruleset ID from provider evidence;
3. obtain separate rollback approval;
4. disable or delete only that ruleset;
5. verify auto-merge and unrelated repository settings remain unchanged;
6. rerun the owner-authenticated scoreboard;
7. record the failed rollout and do not begin Wave 2.

Rollback is a provider write and is not pre-approved.

## Boundaries

This source plan does not:

- create, update, disable, or delete a ruleset;
- edit classic branch protection;
- change repository auto-merge;
- merge a Dependabot pull request;
- dispatch a workflow;
- deploy or restart the local Ramone service;
- change Ollama, ChromaDB, atlas-corpus, ramone-edge, or SPECULAR-CORE;
- create a release or tag;
- change a secret or token;
- begin Wave 2 or any later wave.
