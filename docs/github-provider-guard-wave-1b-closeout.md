# GitHub provider guard Wave 1B closeout

Status: complete.

## Scope

Wave 1B was limited to exactly one repository:

- `AtlasReaper311/ollama-rag-kit`.

Wave 2 and all later waves were not started.

## Source authority

Wave 1B source authority merged through `atlas-infra#131` as:

```text
1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3
```

The reviewed plan and fail-closed runner pinned the rollout to `ollama-rag-kit`, current `main`, genuine Dependabot PR `#16`, repository-native context `Build and smoke-check`, and GitHub Actions integration ID `15368`.

## Provider result

Atlas approved one provider write for `ollama-rag-kit` only.

The owner-authenticated apply run created and verified:

- ruleset ID: `20573090`;
- ruleset name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- pull request required;
- required approving reviews: `0`;
- required review-thread resolution: false;
- required status: `Build and smoke-check`;
- required status integration ID: `15368`;
- deletion blocked;
- non-fast-forward updates blocked;
- bypass actors: none;
- strict required-status branch-update policy: false.

Repository auto-merge was false before and after the write.

Provider evidence archive SHA-256:

```text
623e5b5629502165122b871a0bb40df5f1e3e8d06f17dd3208bb85be1bf2832b
```

## Automation compatibility

Existing genuine Dependabot PR `ollama-rag-kit#16` remained open and mergeable after the ruleset was created.

Its reviewed head remained:

```text
c88e6277f1f2b9bebc8f607bbb59a7d37860e92a
```

The repository-native `Build and smoke-check` gate and the associated assurance workflows had already passed on that exact head. No Dependabot pull request was merged as part of Wave 1B.

## Owner-path validation

A harmless documentation-only owner validation PR was opened after the ruleset became active:

- PR: `ollama-rag-kit#18`;
- reviewed head: `a46a83fd3a28807fbb9d3a2d5b4f96ae504a5e19`;
- required CI run: `31226704393`;
- CodeQL run: `31226704152`;
- OpenSSF Scorecard run: `31226704146`;
- Dependabot review policy run: `31226704148`;
- merge commit: `e2cc5f4dadd3cc1bee5e8f72a6b710c8851c9657`.

`Build and smoke-check` passed on the reviewed head. CodeQL and Scorecard completed successfully, and the owner-only Dependabot policy skipped as expected. The PR had no unresolved review threads and merged successfully through ruleset `20573090`.

## Final scoreboard

The owner-authenticated conformance scoreboard was collected at:

```text
2026-08-07T23:29:47Z
```

Evidence identity:

```text
Source: AtlasReaper311/atlas-infra@1c3f63c9a30dd28ffec3ebe77a87d7a254f199c3
Fingerprint: sha256:16b63950fb860bb38fb8b4e7473b5ed8737b985f55d7a0024701d73e00b80322
```

The canonical fingerprint was independently recomputed from the uploaded report and matched exactly.

Final policy summary:

- repositories checked: `33`;
- required checks: `260`;
- required passes: `237`;
- required failures: `23`;
- required unknowns: `0`;
- not applicable: `68`;
- exception: `1`;
- deferred: `1`.

`AtlasReaper311/ollama-rag-kit/default_branch_guard` now reports:

```text
passed: An active default-branch ruleset was observed.
```

Compared with the Wave 1A closeout scoreboard, the bounded Wave 1B movement is exactly one required guard correction:

- required passes: `236 -> 237`;
- required failures: `24 -> 23`;
- required unknowns: `0 -> 0`.

The uploaded final-evidence archive SHA-256 is:

```text
fc872852e04f6e81ff3e5cb60154b6676ee7272c60a71de008bc56d7f3a80660
```

## Boundaries preserved

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

Destructive direct-push, force-push, and default-branch deletion tests were not required for closure.

## Closeout decision

Wave 1B is complete and requires no further work.

The next optional programme stage is Wave 2. Wave 2 must begin with fresh Part 0 inspection of its exact repository scope and requires separate provider-write approval before any GitHub protection setting is changed.
