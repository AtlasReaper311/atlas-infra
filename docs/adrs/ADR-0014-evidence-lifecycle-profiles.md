+++
id = "ADR-0014"
date = 2026-09-07
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-infra"]
services = []
contracts = []
policies = []
+++

# ADR-0014: Apply ADR-0013 with subject-type evidence lifecycle profiles

## Context

ADR-0013 owns the estate-wide delivery and evidence lifecycle. It defines ordered shipping stages, a separate observation-result axis, and the non-implication rule that `MERGED` is not deployment, runtime, or live proof.

That record names lifecycle profiles as later work. Without them, a reviewer can recite the vocabulary and still not know which ADR-0013 stages apply to a Worker, a Pages site, a toolkit, a policy change, a model-promotion record, or an article.

Current repository evidence already splits those subjects, but not as one profile catalog:

- `.github/workflows/deploy-worker.yml` is the canonical Worker pipeline: validate, including optional bundle `/_meta` checks, then deploy. Bundle contract checks do not call a live endpoint.
- `.github/workflows/validate-static.yml` is the canonical Pages pipeline for `atlas-systems`, `status`, and `atlas-doc-viewer`. It validates HTML, deploys Pages, and may purge cache. It has no Worker health or `/_meta` probe.
- `.github/workflows/publish-container-image.yml` publishes a GHCR artifact and never touches a running service. `atlas-interface-kit` and `worker-meta-kit` use git-tag plus GitHub Release contracts when an owner-approved release exists.
- Documentation and policy in `atlas-infra` become public source at merge. Some records also have a real projection or publication contract, such as `policy/public-repository-classifications.json` generation or ADR Trace projection dispatch.
- Model promotion is owned by `atlas-eval-harness` evidence plus `contracts/v1/wave3/model-promotion.schema.json`. A promotion record is evidence only. It does not install a model or change routing.
- Article publication is the three-repository pipeline in `docs/agent-conventions.md`: `atlas-article-gen` authors and validates, `atlas-scheduler` is the only write path to the live site, and `atlas-systems` owns the published pages. Publication is proven only after scheduler execution and live-site verification.

Roadmap item 1.3 and issue `#182` list domain labels such as `RELEASED`, `PUBLISHED/PROJECTED`, `EVAL PREPARED`, and `AUTHORED`. Those labels already exist in current Atlas authority. They must map onto ADR-0013. They must not become a second lifecycle.

This ADR does not rewrite Trace, ledger, retirement, hygiene, public-interface, or rollout-board contracts. It does not implement snapshots, drift detection, or the Evidence Console.

## Decision

`AtlasReaper311/atlas-infra` owns six subject-type profiles that apply ADR-0013. ADR-0013 remains the only delivery-stage authority. A profile selects applicability and required evidence. It does not add estate-wide stages.

A profile attaches to a named subject (repository, change, service, promotion record, article, or equivalent exact identity), not to a repository as a whole. One repository may host more than one subject type. `estate-registry.json` `runtime_service` and `public_surface` are classification fields. They help choose a profile. They are not ADR-0013 stages.

### Standing rules for every profile

- Use ADR-0013 stages and observation results exactly.
- Domain-specific names are mappings. They are not replacements.
- `MERGED` never implies `DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, `LIVE VERIFIED`, release, publication, promotion rollout, or live article presence.
- `CHECKED` never implies `MERGED`.
- `NOT APPLICABLE` is valid only where the stage cannot exist for that subject. It is not a substitute for an unobserved stage that does apply.
- When a later applicable stage has no evidence, the required label is `UNKNOWN / NOT OBSERVED`.
- Preview, dev-environment, or non-production deployments are not production `DEPLOYED` or `LIVE VERIFIED`.
- Bundle, HTML, or eval-suite checks are `CHECKED`. They are not runtime or live proof.

### How to classify a subject

1. Name the exact identity.
2. Choose one profile from the six below.
3. Keep the latest ADR-0013 stage that current evidence actually proves.
4. Mark each later applicable stage `UNKNOWN / NOT OBSERVED` until evidence exists, or `NOT APPLICABLE` where the profile says the stage cannot exist.
5. Treat domain-specific states as mapped labels on those ADR-0013 stages.

### Runtime Worker

Applies to a Cloudflare Worker or equivalent deployed runtime service whose shipping path is `deploy-worker.yml` or the same validate-then-deploy shape.

Applicable ADR-0013 chain:

`SOURCE` -> `CHECKED` -> `MERGED` -> `DEPLOYMENT OBSERVED` -> `DEPLOYED` -> `RUNTIME VERIFIED` -> `LIVE VERIFIED`

| Stage | Required evidence | Not applicable when |
| --- | --- | --- |
| `SOURCE` | Named branch, commit, or equivalent identity. | Never. |
| `CHECKED` | Repository-native validation or required checks on that exact head. Bundle `/_meta` or OpenAPI gates count here. They do not call live endpoints. | Never. |
| `MERGED` | Exact head on the default branch, or equivalent integration. | Never. |
| `DEPLOYMENT OBSERVED` | Named production deploy event for a stated identity, such as the `deploy` job in `deploy-worker.yml`. | Never for this profile. |
| `DEPLOYED` | Expected identity is the deployed identity. Seeing some deploy event is not enough. | Never for this profile. |
| `RUNTIME VERIFIED` | The deployed subject answered a stated runtime check (health, `/_meta`, contract probe, or equivalent) for the expected identity. | Never for this profile. |
| `LIVE VERIFIED` | Independent live check of public or operator-facing behaviour for the expected identity after rollout. | The subject has no public or operator-facing surface. Current registry example: `ramone-memory` has `public_surface: false`. |

Missing later evidence stays `UNKNOWN / NOT OBSERVED`. A merged Worker with no named deploy event remains `MERGED`.

### Static / public site

Applies to a Cloudflare Pages or equivalent static public surface whose shipping path is `validate-static.yml` or the same HTML-validate-then-Pages-deploy shape. Current callers named in `docs/CICD-DECISIONS.md` are `atlas-systems`, `status`, and `atlas-doc-viewer`.

Applicable ADR-0013 chain:

`SOURCE` -> `CHECKED` -> `MERGED` -> `DEPLOYMENT OBSERVED` -> `DEPLOYED` -> `LIVE VERIFIED`

| Stage | Required evidence | Applicability |
| --- | --- | --- |
| `SOURCE` | Named source identity. | Applicable. |
| `CHECKED` | Repository-native validation on that head, including HTML and offline link checks. | Applicable. |
| `MERGED` | Exact head integrated. | Applicable. |
| `DEPLOYMENT OBSERVED` | Named Pages deploy event, such as `wrangler pages deploy` in `validate-static.yml`. Cache purge is not this stage. | Applicable. |
| `DEPLOYED` | Expected identity is the deployed Pages identity. | Applicable. |
| `RUNTIME VERIFIED` | A process answering a health or contract probe. | `NOT APPLICABLE`. Static Pages have no Worker runtime probe in the current pipeline. Registry `runtime_service: true` on these sites does not create that stage. |
| `LIVE VERIFIED` | Independent public or browser check of the expected identity after rollout. | Applicable. |

A merged static-site change with no Pages deploy event remains `MERGED`. It is not live-verified.

### Library / toolkit

Applies to a non-runtime source library, kit, or template. Current public-assurance examples include `atlas-interface-kit`, `worker-meta-kit`, and `atlas-kit-python-rag`.

Base ADR-0013 chain:

`SOURCE` -> `CHECKED` -> `MERGED`

If and only if a real release contract exists for that subject (owner-approved git tag, GitHub Release, or the `publish-container-image.yml` artifact contract), the domain label `RELEASED` maps onto later ADR-0013 stages as follows:

| Domain label | ADR-0013 mapping | Required evidence |
| --- | --- | --- |
| `RELEASED` event | `DEPLOYMENT OBSERVED` | Named release or image-publish event for a stated identity. |
| `RELEASED` identity | `DEPLOYED` | Expected tag, release asset, or image identity is the published artifact identity. |

| Stage | With a release contract | Without a release contract |
| --- | --- | --- |
| `DEPLOYMENT OBSERVED` | Applicable via `RELEASED` event. | `NOT APPLICABLE`. |
| `DEPLOYED` | Applicable via `RELEASED` identity. | `NOT APPLICABLE`. |
| `RUNTIME VERIFIED` | `NOT APPLICABLE`. | `NOT APPLICABLE`. |
| `LIVE VERIFIED` | `NOT APPLICABLE`. | `NOT APPLICABLE`. |

`RELEASED` is a mapping, not an estate-wide stage. Publishing a container image is not deploying a running service. Pulling that image into a runtime is a different subject under Runtime Worker, or an equivalent local-runtime profile outside this catalog.

A merged kit with no release event is `MERGED`. If a release contract exists and no release event is observed, later applicable stages are `UNKNOWN / NOT OBSERVED`, not `NOT APPLICABLE`.

### Documentation / policy

Applies to ADRs, policy, runbooks, and other documentation or contract source whose first shipping event is source integration.

Base ADR-0013 chain:

`SOURCE` -> `CHECKED` -> `MERGED`

The domain label `PUBLISHED/PROJECTED` applies only where a real projection or publication contract exists, such as regenerating `policy/public-repository-classifications.json` from authority inputs, or dispatching ADR Trace projection refresh. Source-only docs have no such contract.

| Domain label | ADR-0013 mapping | Required evidence |
| --- | --- | --- |
| `PUBLISHED/PROJECTED` event | `DEPLOYMENT OBSERVED` | Named generation, dispatch, or publication event for a stated identity. |
| `PUBLISHED/PROJECTED` identity | `DEPLOYED` | Expected projection or published-copy identity is present. |

| Stage | With a projection or publication contract | Source-only |
| --- | --- | --- |
| `DEPLOYMENT OBSERVED` | Applicable via `PUBLISHED/PROJECTED` event. | `NOT APPLICABLE`. |
| `DEPLOYED` | Applicable via `PUBLISHED/PROJECTED` identity. | `NOT APPLICABLE`. |
| `RUNTIME VERIFIED` | `NOT APPLICABLE`. | `NOT APPLICABLE`. |
| `LIVE VERIFIED` | Applicable only when a public consumer copy must be independently verified. Otherwise `NOT APPLICABLE`. | `NOT APPLICABLE`. |

Merging an ADR is `MERGED`. A later Trace `GOVERNED_BY` projection, corpus ingest, or downstream verified copy is a separate `PUBLISHED/PROJECTED` mapping when that contract exists. It is not implied by merge.

### Model promotion

Applies to an `atlas-eval-harness` capability promotion record. Current authority is `docs/model-policy.md`, `policy/model-promotion-coverage.json`, and `contracts/v1/wave3/model-promotion.schema.json`.

Promotion-specific states map onto ADR-0013. They are not deployment or live stages:

| Domain state | ADR-0013 mapping | Required evidence |
| --- | --- | --- |
| `EVAL PREPARED` | `SOURCE` | Named eval run against exact suite revision and configuration fingerprints. |
| `EVAL PASSED` | `CHECKED` | Deterministic suite result meets the declared threshold for that identity. `promotion-check` of a candidate record also counts as `CHECKED`. |
| `HUMAN REVIEWED` | Observation gate on `CHECKED`, not a later delivery stage | Explicit human review of the run matrix and failure evidence. Review does not imply `MERGED`. |
| `PROMOTION APPROVED` | `MERGED` | `promotion-approve` with `--confirm-reviewed-evidence` produced an accepted promotion record for that identity. |

| Stage | Applicability for the promotion record |
| --- | --- |
| `DEPLOYMENT OBSERVED` | `NOT APPLICABLE`. |
| `DEPLOYED` | `NOT APPLICABLE`. |
| `RUNTIME VERIFIED` | `NOT APPLICABLE`. |
| `LIVE VERIFIED` | `NOT APPLICABLE`. |

A promotion record grants no install, pull, routing, Open WebUI, Home Assistant, or container-restart authority. Applying a promoted model to a live service is a different subject and must use the Runtime Worker profile, or the owning local-runtime evidence path. Live model identity in `model-promotion-coverage.json` is coverage observation. It is not this profile's `LIVE VERIFIED` stage.

### Article publication

Applies to a case-study or writing subject that travels the `atlas-article-gen` -> `atlas-scheduler` -> `atlas-systems` pipeline.

Publication-specific states map onto ADR-0013 without collapsing into one live label:

| Domain state | ADR-0013 mapping | Required evidence |
| --- | --- | --- |
| `AUTHORED` | `SOURCE` | Named article source identity in `atlas-article-gen`. |
| `VALIDATED` | `CHECKED` | Generator validation on that identity, such as `build_article.py --check-only`. |
| `SCHEDULED` | `MERGED` of the scheduler queue identity | The article is on the scheduler queue with a publish date. This is not merge onto the live writing pages. |
| `SCHEDULER EXECUTED` | `DEPLOYMENT OBSERVED`, then `DEPLOYED` when the expected writing identity is present on `atlas-systems` | Named scheduler run, then expected article identity on the live-site source. |
| `LIVE VERIFIED` | `LIVE VERIFIED` | Independent live-site verification of the expected article after scheduler execution. |

| Stage | Applicability |
| --- | --- |
| `RUNTIME VERIFIED` | `NOT APPLICABLE`. Published writing pages are static. |

Generator build, scheduler dry-run, and source merge of `atlas-article-gen` do not prove `SCHEDULER EXECUTED` or `LIVE VERIFIED`. `SCHEDULER EXECUTED` does not imply `LIVE VERIFIED`.

## Consequences

A reviewer can take one Atlas subject, name its profile, list applicable ADR-0013 stages, list `NOT APPLICABLE` stages, name required evidence for each applicable stage, and keep domain-specific labels as mappings. No profile in this record permits `MERGED` to stand in for deployment, runtime, publication, promotion rollout, or live verification.

This ADR does not replace ADR-0013. It does not edit rollout-board policy, board sync behaviour, Trace schemas, hygiene labels, generated snapshots, drift detectors, or the Evidence Console.

Accepting these profiles does not prove that any current Worker, Pages site, kit, projection, promotion record, or article already has complete later-stage evidence. Absent later evidence remains `UNKNOWN / NOT OBSERVED`.

Costs: operators must choose a profile per subject instead of treating every repository as a Worker chain. Surfaces that still print live language from merge facts remain in disagreement with ADR-0013 until a later authorised mapping change.
