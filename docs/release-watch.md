# Release watch architecture

## Ownership

`atlas-journey-watch` owns release verification execution, metadata comparison,
targeted public journeys, and `ReleaseEvidence` production. `atlas-infra` owns
the v1 evidence contract, release policy, calling example, state meanings, and
runbook. No Phase 3 component deploys, rolls back, stores secrets, or mutates a
public service. `atlas-api-public` requires no Phase 3 change.

## Inputs

A release request supplies:

- `repository` in `AtlasReaper311/name` form;
- a full lowercase 40- or 64-character commit SHA;
- stable `service_id`, environment, deployment target, and deployment ID;
- an allowlisted HTTPS metadata URL;
- deployment start time and a repository-relative Markdown rollback reference.

`workflow_dispatch` and `repository_dispatch` with event type `release-watch`
are supported. Canonical request bodies are
[`examples/release-watch.workflow-dispatch.json`](../examples/release-watch.workflow-dispatch.json)
and
[`examples/release-watch.repository-dispatch.json`](../examples/release-watch.repository-dispatch.json).
Participating deployment workflows send the event after their deploy step
succeeds. They must not start a second release verification workflow for the
same release. Workflow concurrency is keyed by service, environment, and
commit, and supersedes an identical in-progress request.

The preferred caller uses a fine-grained `RELEASE_WATCH_DISPATCH_TOKEN`, scoped
only to `AtlasReaper311/atlas-journey-watch` with repository `Metadata: read`
and `Actions: write`, to invoke `workflow_dispatch`. GitHub's
`repository_dispatch` endpoint requires `Contents: write` on the target, so it
is supported for compatibility but is not the least-privilege default. The
release workflow itself uses only `contents: read` and consumes no secret.

## Verification flow

1. Validate the service ID, repository ownership, commit, environment,
   metadata URL, deployment identity, and rollback reference.
2. Refuse deprecated external-derived `simple-proxy` and any unknown target.
3. Fetch `/_meta` or read an offline fixture with a bounded timeout.
4. Require explicit repository, commit, service ID, and environment fields.
   Nested `release` and `source` objects are accepted; display names and short
   versions are never inferred as release identity. Equivalent HTML may expose
   `build-repository`, `build-commit`, `service-id`, and `build-environment`
   meta tags; all four remain mandatory.
5. Run the existing Playwright journeys mapped to the service ID.
6. Compare a latency/error baseline only when a caller supplies baseline,
   observation, freshness timestamps, and thresholds. With no baseline source
   in the current owners, emit `baseline-comparison` with shared state
   `unavailable` and check status `unknown`; this does not by itself block
   `live`. Expired input uses shared state `stale` and is also not compared.
7. Produce deterministic JSON in fixture mode and validate it against
   `contracts/v1/release-evidence.schema.json`.
8. Upload evidence for 30 days, then fail the workflow unless status is `live`.

## Evidence and state meanings

Every evidence document includes repository, service ID, commit, environment,
deployment target/ID, timestamps, live-identity, targeted journey, baseline
checks, final status, and rollback reference. Check evidence references point
to the exact GitHub Actions run.

| Release status | Meaning |
|---|---|
| `pending` | Verification has not completed; it is not healthy. |
| `live` | All required live identity fields match and targeted journeys pass. Optional missing baseline data is explicit and non-blocking. |
| `mismatch` | At least one explicit live identity field differs from the request. |
| `degraded` | Identity matches, but a journey is unavailable/unknown or supplied baseline thresholds are exceeded. |
| `failed` | Metadata is malformed/incomplete or a targeted journey explicitly fails. |
| `rolled-back` | A caller reports that a separate human-controlled rollback completed. Release watch never creates this condition itself. |
| `unknown` | The endpoint is unavailable or the release cannot be proved. |

Transport/source absence uses the shared `unavailable` state internally and
maps to `live_identity: unavailable` plus release status `unknown`, because
`unavailable` is not a v1 release status. Missing data never maps to `live`.

## Local use

From `atlas-journey-watch`, use local fixture files only:

```bash
node scripts/release-watch.mjs verify \
  --request tests/fixtures/release-watch/request.json \
  --metadata-file tests/fixtures/release-watch/metadata.match.json \
  --journey tests/fixtures/release-watch/journey.passed.json \
  --fixture \
  --output release-evidence.json
python3 ../atlas-infra/scripts/validate_release_evidence.py \
  --instance release-evidence.json
```

Live endpoint access is opt-in through a validated `metadata_url` in the
request. No test requires it.

## Rollback limitations

Phase 3 can only report `rollback_ref` and a caller-observed `rolled-back`
state. It has no deploy token, environment write access, provider write scope,
or rollback command. `--auto-rollback` is deliberately rejected. Human review
decides whether and how a target repository's documented rollback is run.

## Migration order

1. Review and merge the `atlas-infra` policy/contract branch first so `main`
   exposes the single-instance validator and additive v1 fields.
2. Rebase the `atlas-journey-watch` branch on current `main`, re-run offline
   tests, then merge it. Its workflow deliberately checks out
   `AtlasReaper311/atlas-infra@main` for canonical validation.
3. Add one `release-watch` repository-dispatch call to a participating deploy
   workflow after that workflow reports a successful deployment. Do not add a
   second release verifier for the same deployment path.
4. Start with fixture/manual dispatch. A live verification or deploy remains a
   separate owner-approved action.

## Known limitations

- The seven-service target map is curated in `atlas-journey-watch` until Phase
  6 supplies a validated contract registry. Unknown services fail closed.
- Several existing services do not yet publish all four release identity
  fields. They will remain `failed`/`unknown`, never `live`, until their normal
  owner adds compatible metadata in a separately approved change.
- Neither approved Phase 3 owner has a persisted latency/error baseline.
  Optional absent or stale baseline data is explicit and non-blocking.
- Workflow concurrency removes duplicate in-progress checks for the same
  service/environment/commit. It does not persist a completed-event ledger, so
  a later duplicate dispatch can produce another valid evidence artifact.
- The generic `docs/runbooks/release-watch.md` rollback reference covers the
  decision path only. A participating repository should pass its more specific
  rollback runbook when one exists.
