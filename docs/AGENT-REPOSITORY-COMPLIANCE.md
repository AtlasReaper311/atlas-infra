# Atlas Systems Agent Repository Compliance Contract

## Purpose

This document is the canonical entrypoint for AI agents and human operators creating, adopting, changing, publishing, deploying, deprecating, or retiring an Atlas Systems repository.

It does not replace executable policy, schemas, validators, workflows, ADRs, or repository-local truth. It defines how those authorities compose and the order in which an agent must consult them.

The objective is simple: no repository should pass one Atlas Systems convention while failing another because an agent inspected only a README template, one workflow, or remembered guidance.

## Authority order

Use this order for every repository task:

1. Current files, branches, workflows, tests, settings, and deployment behaviour in the repository being changed.
2. Accepted ADRs under `atlas-infra/docs/adrs/`.
3. Machine-readable policy and schemas under `atlas-infra/policy/` and `atlas-infra/contracts/`.
4. Executable validators and reusable workflows under `atlas-infra/scripts/` and `atlas-infra/.github/workflows/`.
5. Canonical public estate projections and runtime contracts.
6. Repository-local documentation and runbooks.
7. This document.
8. Historical plans, examples, conversation memory, and `decisions.md`.

When two sources disagree, use the higher authority and record the mismatch. Do not combine incompatible versions into a new rule.

## Core rule

Compliance is a set of linked gates, not a visual checklist.

A repository can have a correct README and still be non-compliant because its classification is missing, its workflow actions float on tags, its metadata claims a deployment that has not been verified, its private identity entered a public projection, or its merge path performs an unapproved provider write.

An agent must therefore complete the full lifecycle decision before editing files.

## Part 0: inspect before deciding

Before creating or changing anything, inspect:

- repository identity, owner, visibility, archive state, and default branch;
- current branch, status, remotes, tags, releases, and open pull requests;
- `README.md`, `LICENSE`, `.gitignore`, lockfiles, package manifests, and runtime configuration;
- `.github/workflows/`, reusable workflow callers, action pins, permissions, concurrency, timeouts, environments, and secrets references;
- tests, linters, type checks, build commands, validation scripts, and repository-native developer guidance;
- `.atlas/governance.json` when the repository is private;
- public classification and runtime authority when the repository is public;
- actual deployment triggers from `main`, tags, releases, workflow dispatch, schedules, or external systems;
- live endpoints and generated reports only when live state is part of the claim;
- relevant ADRs, service contracts, policies, schemas, and runbooks;
- cross-repository dependencies and immutable reusable-workflow pins.

Do not infer implementation, deployment, publication, health, or ownership from a repository name, GitHub visibility, merged source, or remembered estate state.

## Part 1: classify the repository

Every repository decision begins with four separate questions.

### Lifecycle

Use only the lifecycle declared by current authority. Typical states include:

- `production`: a primary maintained component with active operational importance;
- `active`: maintained and in current use or development;
- `experimental`: deliberately bounded work that is not yet an adopted production dependency;
- `deprecated`: retained for migration, compatibility, or historical reasons but not extended as normal active work;
- `archived`: read-only historical state with no active maintenance expectation.

Lifecycle controls assurance, dependency treatment, metadata, archive state, rollout eligibility, and retirement requirements. Do not promote or demote lifecycle as a side effect of another task.

### Scope

Determine whether the repository is public, internal, or otherwise bounded by current schema. GitHub visibility alone is not the authority.

Public repositories may enter the approved public classification projection only through Atlas Infra authority. Private repositories remain source-owned and must not be copied into public inventories for convenience.

### Provenance

Determine whether the repository is original, externally derived, vendored, forked, mirrored, or otherwise classified by current policy.

Provenance affects portfolio presentation, dependency automation, licence handling, modification boundaries, and whether Atlas-wide templates may be applied without preserving upstream terms.

### Runtime status

A repository and a deployed service are different identities.

A repository is not a runtime service merely because it contains Worker, Pages, Docker, API, or deployment files. Runtime membership requires current declared authority and supporting contracts. Repository names and service names may differ and both must be documented.

## Part 2: choose the governance path

### Approved public repository

Public repository governance is owned centrally by Atlas Infra.

The agent must inspect:

- `policy/estate-registry.json` for public runtime repositories;
- `policy/public-assurance-repositories.json` for approved public non-runtime repositories;
- `policy/public-repository-classifications.json` as the generated consumer projection;
- `policy/repository-hygiene.json` for README, metadata, topic, archive, and label rules;
- `policy/estate-policy.json` for estate-wide source and workflow checks;
- relevant service contracts and public Cloudflare authorities when the repository owns a runtime.

Generated projections are not authoring surfaces. Change their source authority, regenerate them deterministically, and validate the result.

### Source-owned private repository

Private governance stays in the authenticated repository that owns the identity.

The repository must use `.atlas/governance.json` conforming to `contracts/v1/repository-governance.schema.json` and keep `public_projection: false`.

Use the relevant source-local reusable validators pinned to immutable Atlas Infra commits, including:

- `.github/workflows/validate-private-governance.yml`;
- `.github/workflows/validate-private-readme.yml`;
- `.github/workflows/validate-private-metadata.yml`;
- `.github/workflows/validate-private-labels.yml` when label governance applies.

Do not add a private repository name, count, digest, inferred identity, or provider record to public policy, public reports, public examples, or public fixtures unless an accepted authority explicitly permits that exact publication.

### Excluded repository

Some repositories are intentionally outside default assurance or portfolio presentation.

An exclusion is governance, not a defect to repair. Do not add README shells, Dependabot, metadata, labels, runtime contracts, or public projection entries merely to make a generic audit green.

Inspect the declared exclusion and preserve it unless the task explicitly changes governance authority.

## Part 3: repository creation gate

An agent creating a new repository must not begin by copying a template. It must first produce a repository decision record covering:

- proposed repository name and exact GitHub owner;
- purpose and non-goals;
- lifecycle, scope, provenance, and runtime status;
- public or private governance path;
- owning Atlas Systems capability;
- expected languages, ecosystems, build tools, and package managers;
- dependency and lockfile strategy;
- test and validation commands;
- deployment model and whether `main` causes a live action;
- secrets and provider permissions required, expressed as names and purposes only;
- data ownership, retention, backup, recovery, and deletion implications;
- API, route, metadata, service-binding, storage, and event contracts;
- observability, notification, reliability, and evidence expectations;
- licence evidence and upstream obligations;
- README, GitHub metadata, topics, and label requirements;
- cross-repository dependencies and rollout order;
- retirement and replacement path;
- free-tier or approved fixed-cost fit.

Do not create the repository until unresolved authority questions are presented to the owner. Do not invent classification or publication intent.

## Part 4: baseline repository contents

Create only files justified by the repository type and inspected policy.

Typical source-owned baseline files are:

- `README.md`;
- a real `LICENSE` when an approved licence applies;
- a repository-specific `.gitignore`;
- package or project manifests;
- deterministic lockfiles for declared dependency ecosystems;
- tests and repository-native validation configuration;
- `.github/workflows/` with pull-request assurance;
- Dependabot configuration when lifecycle and ecosystem policy permit it;
- `.atlas/governance.json` for governed private repositories;
- security, contribution, operation, or recovery documentation only when the repository requires it.

Do not add decorative files, empty policy shells, false badges, placeholder tests, unused workflows, speculative deployment configuration, or generated artefacts that have no owning pipeline.

## Part 5: README contract

README work follows this order:

1. current repository implementation and deployment behaviour;
2. `policy/repository-hygiene.json`;
3. `scripts/readme_contract.py`;
4. the current Atlas Systems README Contract and Style Guide;
5. older examples.

For governed standard repositories, verify:

- canonical Atlas icon URL and width;
- H1 exactly matches the repository name;
- `ATLAS SYSTEMS // <repo-name>` banner;
- at least four recognised factual badges;
- every Shields badge contains `labelColor=0a0a0f`;
- opening description states what the repository actually does;
- sections reflect the repository type rather than a universal template;
- no prohibited portfolio wording;
- no em dash in rendered prose;
- no rendered `TODO` or `PLACEHOLDER` content;
- licence claim is present only when a corresponding licence file exists;
- `## How it fits into Atlas Systems` is the final H2;
- the Atlas Systems footer is the final non-empty line;
- public content contains no private identity, endpoint, secret, or provider detail;
- every live claim is backed by current evidence.

The GitHub profile repository is a specific exception. Use its current policy rather than forcing the standard repository H1.

## Part 6: GitHub metadata and labels

For approved public repositories, validate metadata against `policy/repository-hygiene.json` and the executable metadata validator.

Current controlled fields include:

- visibility;
- default branch;
- bounded factual description;
- approved Atlas Systems homepage domain;
- one to eight controlled topics including `atlas-systems`;
- archive state consistent with lifecycle.

Provider metadata is not README content. Fix each through its owning path and do not hide provider drift with prose.

Atlas-specific status labels are centrally defined. Do not duplicate native GitHub states such as draft, CI, open, closed, or merged.

Current governed labels are:

- `status:blocked`;
- `status:live-verified`;
- `status:owner-review`;
- `status:rollout-pending`;
- `status:superseded`.

Names, colours, and descriptions must match policy exactly.

## Part 7: dependency and supply-chain controls

Inspect the ecosystem before adding dependency automation.

Required principles:

- lock dependencies when the ecosystem supports deterministic lockfiles;
- keep archived repositories read-only;
- keep deprecated repositories inside their declared security-only boundary;
- preserve explicit repository exclusions;
- pin third-party GitHub Actions to full 40-character commit SHAs;
- pin Atlas-owned reusable workflows to immutable merged commits;
- use reviewed Node 24 action releases where current authority requires them;
- do not use floating branches or semantic tags for reusable production policy;
- keep ordinary dependency updates manual unless the exact fail-closed Dependabot policy permits automation;
- do not treat grouped, production, indirect, major, minor, unstable, `0.x`, Docker, Python, Actions, vulnerable, stale, or maintainer-modified changes as automatically safe;
- do not grant a dependency bot deployment authority or production secrets.

Dependabot, `atlas-dep-audit`, and Atlas Gardener have distinct responsibilities. Do not collapse detection, review, proposal, merge, and deployment into one permission boundary.

## Part 8: GitHub Actions contract

Every workflow must be inspected as executable production code.

Required defaults:

- explicit top-level `permissions`;
- least privilege, with write permissions restricted to the smallest job that requires them;
- explicit top-level `concurrency`;
- bounded `timeout-minutes` for every runner job;
- immutable full-SHA pins for third-party actions;
- immutable merged-commit pins for Atlas-owned reusable workflows;
- pull-request workflows remain read-only unless a reviewed contract requires a bounded write;
- ordinary PR checks do not deploy, mutate providers, require production secrets, approve, or merge;
- production environments and secrets are unavailable to untrusted pull-request execution;
- generated output and artifacts have bounded retention and contain no secrets;
- failures are visible and not converted into success by permissive shell patterns;
- workflow dispatch and schedules are treated as live control-plane actions;
- caller and reusable workflow permissions are reviewed together.

Do not invent validation commands. Run the repository-native commands discovered during Part 0.

## Part 9: runtime and service contract gate

A public runtime requires explicit Atlas Infra authority.

Inspect and update, where applicable:

- public runtime registry entry;
- ServiceContract record;
- repository and deployed service identity mapping;
- route ownership;
- `/_meta` expectations;
- OpenAPI expectations;
- dependencies and inbound consumers;
- same-zone Worker service bindings;
- KV, D1, R2, Durable Object, or other storage ownership;
- notification and alert contracts;
- runbooks;
- reliability objectives or explicit reviewed unmeasured status;
- release, journey, backup, recovery, cost, secret, and evidence references;
- public Cloudflare topology authority.

Current Atlas Worker defaults include:

- `GET /_meta` follows the estate metadata shape when the service is intentionally public;
- Worker runtime alerts use `{source, level, title, message, fields}` through the `ATLAS_NOTIFY` service binding;
- CI and deployment notifications use their workflow-owned webhook path;
- same-zone Worker calls use service bindings rather than public hostnames;
- KV writes occur only on meaningful state change or bounded staleness;
- Wrangler uses `zone_id`, not `zone_name`.

Unknown account resources remain private by default. Cloudflare account membership is not publication authority.

## Part 10: data, backup, recovery, and reliability

Every stateful component must declare who owns the data and how loss is handled.

An agent must determine whether data is:

- authoritative;
- derived and reproducible;
- cached;
- bounded and relearnable;
- user-owned;
- generated evidence;
- operational state;
- secret or restricted.

Use current Atlas Infra authorities for public Cloudflare resources, backup classification, reliability objectives, unmeasured services, incident evidence, and retirement gates.

Do not claim a backup exists because a fixture passes. Do not claim a reliability objective is met because a health endpoint responds. Do not infer recovery readiness without observed recovery evidence.

## Part 11: public interface and browser surfaces

When the repository owns a browser-facing surface, inspect the current accepted public interface ADRs and machine-readable interface policy.

Preserve:

- global navigation and route contracts;
- status language;
- search and link behaviour;
- browser icon and metadata authority;
- accessibility and focus rules;
- mobile navigation requirements;
- readability and content width rules;
- global footer and product-strip boundaries;
- generated-content ownership;
- product-specific identity where explicitly permitted.

Do not hand-copy a shared visual shell into every repository and call it governance. Use the approved distribution model and preserve independent deployment boundaries.

## Part 12: validation gate

Before committing, run all applicable categories.

### Repository-native validation

Examples include:

- Python compile or import checks and unit tests;
- JavaScript or TypeScript syntax, type, lint, and test checks;
- HTML and accessibility validation;
- build or package verification;
- Wrangler dry-run against the exact deploy bundle;
- shell syntax checks;
- schema checks;
- deterministic generation checks.

Use only commands proven by current repository files.

### Atlas conformance validation

Run the relevant local or reusable checks for:

- estate policy;
- README contract;
- metadata contract;
- label contract;
- private governance;
- contract registry;
- control-plane schemas and fixtures;
- public/private boundary;
- dependency policy;
- Worker contract;
- public interface contract;
- repository-specific authority.

### Diff validation

Always run:

- `git diff --check`;
- changed-path inspection;
- staged-content inspection;
- secret and credential scan appropriate to the repository;
- prose policy scan for changed public documentation;
- workflow pin, permission, timeout, and concurrency review.

A change is not ready while it introduces an Atlas policy warning or error.

## Part 13: branch and pull request workflow

Use the Atlas delivery sequence:

1. complete Part 0 inspection;
2. identify cross-repository dependency order;
3. create a focused branch from current `main`;
4. make the smallest coherent change;
5. run repository-native and Atlas validation;
6. inspect every changed path;
7. fetch and rebase onto current `origin/main`;
8. rerun validation after rebase;
9. commit with an accurate message;
10. push the actual branch name;
11. open a draft pull request;
12. state source impact, deployment impact, provider impact, secrets impact, and rollback;
13. wait for current checks;
14. resolve review findings without broadening scope;
15. merge in dependency order only after owner approval;
16. sync a clean local `main`;
17. perform live rollout as a separate approved stage.

For multi-file or multi-repository operator instructions, prefer one Bash instruction file with `#!/usr/bin/env bash`, `set -eu`, clear `PART` and `STEP` sections, one command per line, no command chaining, and dashboard actions written as comments.

## Part 14: deployment and live-state boundary

Keep these states separate:

- source changed locally;
- commit created;
- branch pushed;
- pull request opened;
- checks passed;
- pull request merged;
- workflow dispatched;
- provider changed;
- deployment completed;
- live endpoint verified;
- evidence published;
- downstream consumer refreshed.

Never claim a later state from an earlier one.

A documentation-only diff may still deploy if the repository deploys every push to `main`. Inspect the real workflow before describing merge impact.

Provider writes requiring separate explicit approval include:

- Cloudflare Worker or Pages deployment;
- DNS, route, binding, storage, secret, or environment changes;
- GitHub repository settings, rulesets, variables, secrets, labels, topics, descriptions, or visibility changes;
- workflow dispatches with live effects;
- Docker restarts or corpus refreshes;
- Open WebUI assignments;
- Home Assistant configuration;
- AWS changes;
- publication scheduler execution.

## Part 15: evidence and claims

Every significant claim must identify its evidence class.

Use precise language:

- `implemented`: source exists;
- `validated`: named checks were observed passing;
- `merged`: GitHub records the merge;
- `deployed`: the deployment run completed successfully;
- `live-verified`: the deployed behaviour was checked independently or by the owner;
- `published`: the owning publication pipeline executed and the public result was verified;
- `configured`: current provider or application state was observed;
- `planned`: no implementation or rollout claim.

Generated evidence must remain deterministic, bounded, privacy-safe, and linked to exact source or runtime identity where the contract requires it.

Correlation is not causation. Time proximity alone is not an acceptable causal basis in Atlas Trace evidence.

## Part 16: deprecation and retirement

Do not archive, delete, unroute, or remove a repository or service from one inventory in isolation.

Use the retirement evidence contract and planner. Resolve:

- inbound dependencies;
- public routes;
- Worker bindings;
- registry and classification membership;
- downstream allowlists;
- production PR and rollout references;
- historical evidence preservation;
- recovery or replacement handling;
- provider resources and data ownership;
- documentation and public navigation;
- secrets, schedules, monitors, alerts, and deployment callers.

Retirement eligibility means evidence is ready for owner review. It does not grant execution authority.

## Part 17: prohibited agent behaviour

An Atlas Systems agent must not:

- create a repository from memory without current authority inspection;
- infer public status from GitHub or Cloudflare account membership;
- publish private repository identities through public policy or reports;
- edit generated projections directly;
- add a runtime contract for code that has not been adopted as a runtime;
- claim deployment from a merge;
- claim health from source state;
- request or expose secret values in chat, files, logs, comments, or pull requests;
- use floating action or reusable-workflow references;
- grant broad write permissions to simplify automation;
- make ordinary pull-request checks deploy or require production secrets;
- bypass repository-native tests with a generic substitute;
- fabricate badges, licences, status, cost, security, reliability, backup, or live claims;
- add empty tests, placeholder documentation, or speculative configuration to satisfy appearance;
- mix implementation, provider writes, deployment, publication, and live verification into one unapproved action;
- hand-edit generated article HTML or metadata;
- write article output directly into `atlas-systems`;
- treat a green advisory workflow as zero findings without inspecting its report;
- retire a component before all dependency and evidence gates are resolved.

## Part 18: agent output contract

Before changing a repository, the agent should report:

- inspected repositories and authoritative files;
- current classification and governance path;
- detected deployment and provider-write boundaries;
- relevant contracts and validators;
- cross-repository dependencies;
- contradictions or stale guidance;
- proposed branch and pull request sequence;
- validation commands discovered from source;
- decisions still requiring owner authority.

After changing a repository, the agent should report:

- exact files changed;
- exact validations observed;
- policy findings remaining;
- pull request state and current head commit;
- whether merge triggers a live action;
- actions deliberately not performed;
- rollout and live-verification steps that remain separate.

## Repository creation checklist

```text
[ ] Part 0 inspection completed
[ ] purpose and non-goals recorded
[ ] lifecycle approved
[ ] scope approved
[ ] provenance approved
[ ] runtime status approved
[ ] public or private governance path selected
[ ] estate authority change identified
[ ] repository name and service identities separated
[ ] data ownership and recovery classification decided
[ ] deployment and provider-write boundary documented
[ ] secrets represented by names and purposes only
[ ] README contract satisfied
[ ] metadata and topic contract satisfied
[ ] label contract satisfied where applicable
[ ] licence claim backed by a real licence file
[ ] ecosystem and lockfile strategy correct
[ ] Dependabot treatment matches lifecycle and policy
[ ] workflows use least privilege
[ ] workflows declare concurrency and bounded timeouts
[ ] all actions and reusable workflows use immutable SHAs
[ ] ordinary PR checks are non-deploying and secret-safe
[ ] runtime contracts added only when runtime authority exists
[ ] Worker, route, binding, storage, and metadata rules satisfied
[ ] reliability state is measured or explicitly reviewed as unmeasured
[ ] backup or no-backup rationale exists for stateful data
[ ] public/private boundary preserved
[ ] repository-native validation passes
[ ] Atlas conformance validation passes with zero findings
[ ] git diff and changed paths inspected
[ ] draft PR explains source, provider, deployment, and rollback impact
[ ] live rollout remains separate and owner-approved
```

## Existing repository change checklist

```text
[ ] current main and open PR state inspected
[ ] current classification verified
[ ] relevant ADRs and policies inspected
[ ] actual merge-to-main behaviour identified
[ ] change scope does not silently alter governance
[ ] generated files changed only through their owner
[ ] public claims remain evidence-backed
[ ] private data and identities remain private
[ ] workflow permissions and pins remain compliant
[ ] README and prose remain compliant
[ ] repository-native tests pass
[ ] Atlas validators pass with zero findings
[ ] rebase completed and validation rerun
[ ] draft PR opened in dependency order
[ ] no provider write, dispatch, deploy, publish, or merge performed without approval
```

## Maintenance rule

Update this document in the same programme of work when a change affects how agents must navigate two or more Atlas Systems authorities.

Do not copy every policy value into this document. Link stable concepts to executable authority so that machine policy remains the source of truth.

A policy or validator change wins immediately when this document is stale. The stale document must then be repaired before agents are expected to rely on it again.
