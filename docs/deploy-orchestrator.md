# Deploy orchestrator architecture

## Ownership and boundary

`AtlasReaper311/atlas-infra` owns the Phase 7 deployment policy, dependency
graph, deterministic planner, approval gates, dispatch data shape, aggregate
evidence references, and recovery runbooks. Participating repositories retain
their existing deployment workflows and provider credentials.

`AtlasReaper311/atlas-journey-watch` retains post-deploy release verification
and journey ownership through its existing `release-watch.yml` workflow. No
Phase 7 adapter or service-repository change is required.

Phase 7 is planning-only. The implementation contains no GitHub API client,
Cloudflare client, provider writer, polling loop, or workflow-dispatch
executor. The configured executor is `noop`, policy execution is disabled, and
`--execute` is an explicit tested refusal. This is the smallest reversible
layer that can prove policy and dependency behavior without deploying.

## Licence, dependencies, and registration

The planner uses only the Python standard library and the repository-owned
contract helpers. It adds no package, action, or runtime dependency and is
covered by the repository's MIT licence. No external-derived implementation
code is copied. The orchestrator is not a deployed service, public route, or
scheduled runtime, so it does not receive a ServiceContract or estate-registry
service entry.

## Policy format

[`policy/deploy-orchestrator.json`](../policy/deploy-orchestrator.json) validates
against
[`policy/deploy-orchestrator.schema.json`](../policy/deploy-orchestrator.schema.json).
Each target declares:

- stable service ID, source repository, and environment;
- existing deploy workflow name, ref, inert inputs, token capabilities, and
  expected evidence;
- deployment dependencies and required preflight checks;
- a planned release-watch repository, workflow, ref, journey target, and
  timeout;
- required approvals, aggregate timeout, rollback runbook, and owner;
- explicit `disabled` and `dry_run_only` flags.

The planner cross-checks every target with the Phase 6 estate registry and
ServiceContract. Repository, service ownership, environment, lifecycle, scope,
provenance, deployment ownership, orchestration policy, metadata endpoint, and
classification must agree. `simple-proxy` is always refused. Deprecated,
archived, experimental, and external-derived targets are ineligible for
default orchestration.

The first committed target is `atlas-api-public` production. It points at the
existing `deploy.yml` and remains `dry_run_only: true`. Adding a policy target
does not grant execution authority.

## Dependency graph

Dependencies are deployment-order dependencies, not an automatic copy of all
runtime dependencies. A requested service includes its policy dependency
closure. The planner uses a stable lexical topological sort, so dependencies
always precede dependants and identical input produces byte-identical output.

Missing dependency targets and cycles are Finding-compatible failures. The
planner emits no dispatch list when the graph is invalid.

## Dry-run behavior

Dry-run is the only successful mode:

```bash
python3 scripts/deploy_orchestrator.py validate \
  --policy policy/deploy-orchestrator.json \
  --registry policy/estate-registry.json

python3 scripts/deploy_orchestrator.py plan \
  --service atlas-api-public \
  --environment production \
  --policy policy/deploy-orchestrator.json \
  --registry policy/estate-registry.json \
  --output /tmp/deploy-plan.json \
  --markdown /tmp/deploy-plan.md
```

`--commit` accepts only a full lowercase 40- or 64-character commit. Without
it, the plan uses the explicit `FULL_COMMIT_REQUIRED` sentinel value in inert
release-watch inputs. A future approved dispatcher must resolve the ref and
prove all required checks are green before dispatch.

JSON and Markdown reports use the registry `reviewed_at` timestamp rather than
wall-clock time. Plan IDs and Finding fingerprints are deterministic SHA-256
values. The CLI executes validation and planning twice and reports
`idempotent: true` only when both results match.

## Approval model

- dry-run is the default and only enabled mode;
- production dispatch requires human approval;
- a protected GitHub environment is the preferred production gate;
- no approval input exists in the Phase 7 dry-run workflow;
- no auto-merge, auto-rollback, provider write, secret access, branch
  protection change, protection bypass, or force push is permitted.

If protected-environment reviewers are unavailable, the approved fallback is
two distinct owner actions: one owner reviews and records the immutable plan,
then a second owner performs a separate manual dispatch of the target
workflow. This is documentation only. The planner does not count approvals,
accept an approval boolean, or bypass an environment.

## Dispatch abstraction

Each planned dispatch contains the target repository, existing workflow,
ref, inputs, exact token capability names, timeout, expected evidence, and
expected full commit when supplied. It is data only.

Future GitHub workflow dispatch would require a selected-repository identity
with repository `Metadata: read`, `Contents: read`, `Actions: read and write`,
restricted to allowlisted repositories and workflow files. Phase 7 creates no
token or secret. It does not need Cloudflare permission because provider
credentials remain in target repositories.

## Release-watch integration

For every dispatch the planner derives:

- expected repository, full commit when supplied, service ID, and environment;
- metadata endpoint from the Phase 6 ServiceContract;
- journey target from orchestration policy;
- an inert `gh workflow run release-watch.yml` command and typed inputs;
- expected `release-evidence.json` output.

The current Phase 6 registry does not yet mark `atlas-api-public` as
`release_watch_eligible` because its metadata does not prove a deployed commit.
The dry-run therefore includes a non-blocking readiness warning. This never
becomes a successful live verification. Any future dispatch must remain
disabled until separately approved and must treat unproved identity as
`unknown`.

No live endpoint or release-watch workflow is called in Phase 7. Fixture mode
is the verification path.

## Evidence convention

The plan carries one aggregate evidence-reference record keyed by plan ID and
one expected `release-evidence.json` record per service. It references the
Phase 1 ReleaseEvidence contract but does not manufacture deployment evidence:
every record remains `not-created` until a real target workflow and release
watch complete.

Dry-run artifacts may be retained by the manual workflow for 14 days. There is
no evidence database, ledger, or large binary storage in this phase.

## Failure handling and partial deployment

Invalid policy, missing dependencies, cycles, disabled or excluded targets,
missing workflow/owner/runbook data, and registry conflicts fail before a
dispatch list is produced. A future dispatcher must stop after the first
failed preflight, dispatch, timeout, or verification check. It must preserve
the completed and pending target list and print repository-specific recovery
steps.

For a partial deployment:

1. stop the remaining dependency chain;
2. retain the exact plan, completed workflow run URLs, and evidence references;
3. run release watch for any service already deployed if safe;
4. assess dependants before taking another action;
5. let the owner choose a target repository rollback or forward fix;
6. create a new dry-run plan before resuming.

There is no automatic compensation or rollback.

## Onboard a service

1. Confirm the repository and ServiceContract are current in the Phase 6
   registry, with `deployment_orchestration: true` and a known metadata
   endpoint.
2. Confirm an existing manual deploy workflow and repository-owned deploy
   credentials. Do not move credentials to `atlas-infra`.
3. Add one sorted policy target with exact environment, dependencies,
   preflights, approvals, timeout, rollback runbook, owner, dispatch data, and
   release-watch target.
4. Start with `dry_run_only: true` and `disabled: false`.
5. Add valid, refusal, dependency, and output-idempotency tests.
6. Run policy, registry, Finding, ReleaseEvidence fixture, workflow safety, and
   CLI validation.
7. Obtain separate owner approval before proposing any execution support.

## Disable a service

Set `disabled: true`, keep the target for audit history, run validation, and
confirm a request produces `disabled-service-requested`. Removing a target is
not equivalent to disabling it because removal also erases dependency context.

## Migration and rollback

Migration is repository-only: review and merge the focused `atlas-infra`
branch, then use the manual dry-run workflow or local CLI. No target caller,
secret, environment, provider, or route changes are part of Phase 7.

Before merge, discard the local feature branch if review rejects it. After
merge, revert the focused Phase 7 commit or disable the manual dry-run workflow.
Existing service deployments and release watch continue independently because
the orchestrator coordinates neither by default.

## Known limitations

- there is no dispatcher, workflow-run waiter, provider client, or live
  preflight reader;
- protected-environment availability is not verified locally;
- the first target lacks proved release identity and stays dry-run-only;
- aggregate evidence is plan metadata, not an evidence ledger;
- target workflow hardening remains repository-owned and needs separate
  approval if a service is not dispatch-ready;
- recovery and rollback are human decisions.
