# GitHub provider guard wider rollout: Wave 1B plan

Status: completed and evidenced. Wave 2 and all later waves remain unstarted.

## Scope

Wave 1B was limited to exactly one repository:

- `AtlasReaper311/ollama-rag-kit`.

Wave 1A was already complete before this wave began. Wave 2 did not begin implicitly from Wave 1B completion.

## Part 0 authority

Part 0 was refreshed against current GitHub state on 2026-08-07.

ADR-0004 authority placed `AtlasReaper311/ollama-rag-kit` in `policy/public-assurance-repositories.json` with lifecycle `active`, scope `public`, and provenance `original`. It was not present in `policy/estate-registry.json`, so current policy did not classify it as a public runtime-service repository.

The repository README described a runnable local containerised Ramone RAG service and deployed service shape. That execution detail did not override ADR-0004 classification authority. No `.github/workflows/deploy.yml` existed on the inspected `main`.

The inspected baseline was:

- default branch: `main`;
- inspected `main`: `d0060829dd474d8d8a57b11694ca03411927bf9f`;
- visibility: public;
- archived: false;
- repository auto-merge: disabled;
- active branch rulesets: none;
- classic branch protection: absent.

## Native pull-request gate

Current `.github/workflows/ci.yml` defined the repository-native pull-request gate:

- workflow: `CI`;
- job/context: `Build and smoke-check`;
- Python syntax validation: `python -m compileall app`;
- container validation: `docker compose build`;
- GitHub Actions integration ID: `15368`.

The notification job remained push-only for `main` and was not used as a pull-request gate.

## Genuine Dependabot proof

`ollama-rag-kit#16` provided the genuine automation path used for pre-write compatibility evidence:

- base: `main`;
- base SHA: `d0060829dd474d8d8a57b11694ca03411927bf9f`;
- head SHA: `c88e6277f1f2b9bebc8f607bbb59a7d37860e92a`;
- exact-head `CI`: success;
- required `Build and smoke-check`: success;
- Dependabot review policy: success;
- OpenSSF Scorecard: success;
- CodeQL: success.

No Dependabot pull request was merged as part of Wave 1B.

## Source authority

Wave 1B source authority merged through `atlas-infra#131` as:

```text
1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3
```

`scripts/github-provider-guard-wave-1b.sh` was the approved operator path. It defaulted to read-only inspection and was pinned to the single repository, inspected main SHA, genuine Dependabot PR head, native check, and GitHub Actions integration.

Provider apply required the exact confirmation phrase:

```text
APPLY GITHUB PROVIDER GUARD WAVE 1B
```

## Provider outcome

After separate Atlas approval, the owner-authenticated runner created exactly one ruleset:

- repository: `AtlasReaper311/ollama-rag-kit`;
- ruleset ID: `20573090`;
- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- require changes through a pull request;
- required approving reviews: `0`;
- required review-thread resolution: false;
- required status: `Build and smoke-check`;
- required status integration ID: `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- bypass actors: none;
- strict required-status branch-update policy: false;
- repository auto-merge remained disabled.

Provider evidence archive SHA-256:

```text
623e5b5629502165122b871a0bb40df5f1e3e8d06f17dd3208bb85be1bf2832b
```

## Owner validation outcome

A harmless documentation-only validation PR proved the Atlas owner path through the new guard:

- PR: `ollama-rag-kit#18`;
- reviewed head: `a46a83fd3a28807fbb9d3a2d5b4f96ae504a5e19`;
- required `Build and smoke-check` run: `31226704393`, success;
- CodeQL run: `31226704152`, success;
- OpenSSF Scorecard run: `31226704146`, success;
- Dependabot review policy run: `31226704148`, skipped as expected for the owner PR;
- merge commit: `e2cc5f4dadd3cc1bee5e8f72a6b710c8851c9657`.

No unresolved review threads remained before merge.

## Final scoreboard

The owner-authenticated scoreboard collected at `2026-08-07T23:29:47Z` recorded:

- source: `AtlasReaper311/atlas-infra@1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3`;
- fingerprint: `sha256:16b63950fb860bb38fb8b4e7473b5ed8737b985f55d7a0024701d73e00b80322`;
- repositories checked: `33`;
- required checks: `260`;
- required passes: `237`;
- required failures: `23`;
- required unknowns: `0`;
- `ollama-rag-kit/default_branch_guard`: passed.

The canonical fingerprint was independently recomputed and matched the stamped report exactly.

Compared with the Wave 1A closeout scoreboard, Wave 1B moved exactly one required guard from failed to passed:

- required passes: `236 -> 237`;
- required failures: `24 -> 23`;
- required unknowns: `0 -> 0`.

Permanent evidence is recorded in:

- `docs/github-provider-guard-wave-1b-final-receipt.json`;
- `docs/github-provider-guard-wave-1b-closeout.md`.

## Rollback boundary

If the Wave 1B rule later blocks an intended owner or automation path, rollback remains a separate provider write. It requires fresh evidence and explicit approval before ruleset `20573090` is disabled or deleted.

## Preserved boundaries

Wave 1B did not:

- merge a Dependabot pull request;
- change repository auto-merge;
- edit classic branch protection;
- dispatch a workflow;
- deploy or restart the local Ramone service;
- change Ollama, ChromaDB, atlas-corpus, ramone-edge, or SPECULAR-CORE;
- create a release or tag;
- change a secret or token;
- begin Wave 2 or any later wave.

## Closeout

Wave 1B is fully closed and requires no further work.

Wave 2 is a separate optional stage and must begin with fresh Part 0 inspection of the exact specialist repository scope before any new provider-write approval is requested.
