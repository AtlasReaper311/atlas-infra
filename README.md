<div align="center">
  <img src="https://raw.githubusercontent.com/AtlasReaper311/AtlasReaper311/main/atlas-icon-dark-256.png" width="88" alt="Atlas Systems"/>
</div>

# atlas-infra

```
┌─────────────────────────────────────────────┐
│  ATLAS SYSTEMS // atlas-infra               │
│  the deployment backbone:                   │
│  containers, CI/CD, and ops scripts         │
└─────────────────────────────────────────────┘
```

![Docker](https://img.shields.io/badge/docker-f5a623?style=flat-square&labelColor=0a0a0f)
![GitHub Actions](https://img.shields.io/badge/ci-github%20actions-4ade80?style=flat-square&labelColor=0a0a0f)
![Cross-platform](https://img.shields.io/badge/cross--platform-aaa9a0?style=flat-square&labelColor=0a0a0f)
![Cost](https://img.shields.io/badge/cost-%C2%A30-aaa9a0?style=flat-square&labelColor=0a0a0f)

Container patterns, CI/CD definitions, and deployment infrastructure for the Atlas Systems platform. This is where the deployment backbone is proven before it gets reused across the other repos.

## Structure

```
.github/workflows/   CI/CD and estate assurance definitions
docker/              Container images and compose configs
scripts/             Dev, ops, and assurance utilities
templates/           Copyable workflow callers
policy/              Estate conformance rules
contracts/           Versioned cross-estate data contracts and fixtures
docs/                Decisions and operating guidance
```

## Services

| Image | Purpose |
|---|---|
| `hello-atlas` | HTTP smoke test that confirms the container pipeline works |

## Local development

Prerequisites: Docker 24.x or newer.

```bash
docker build -t hello-atlas ./docker/hello-atlas
docker run -p 8081:8080 hello-atlas
curl http://localhost:8081/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "hello-atlas"
}
```

## CI/CD

This repo holds the reusable workflows every other Atlas Systems repo deploys through. The goal is one pipeline shape per kind of repo, defined once here, adopted by copying a short caller file.

### Reusable workflows

- `deploy-worker.yml`: Cloudflare Worker pipeline. Validate, deploy, and report.
- `validate-static.yml`: static-site pipeline. Validate, publish, and report.
- `change-impact.yml`: read-only pull request blast-radius report derived from `estate.manifest.json`.
- `dependabot-review.yml`: fail-closed review and selective auto-merge policy for eligible Dependabot updates.

### Scheduled assurance

- `estate-policy.yml`: weekly repository conformance audit across the declared estate.
- [`atlas-dep-audit`](https://github.com/AtlasReaper311/atlas-dep-audit): weekly SBOM, OSV, action pin, and provenance audit.
- [`atlas-journey-watch`](https://github.com/AtlasReaper311/atlas-journey-watch): six-hourly synthetic user journeys across public estate surfaces.

The implementation and adoption rules live in [`docs/ESTATE-ASSURANCE.md`](docs/ESTATE-ASSURANCE.md).

### Shared control-plane contracts

`contracts/v1/` contains the eight Phase 1 JSON Schema contracts, positive and
negative fixtures, ownership, compatibility, and deterministic fingerprint
rules. Validate them without installing dependencies:

```bash
python3 scripts/validate_control_plane_contracts.py
python3 scripts/validate_release_evidence.py --instance path/to/release-evidence.json
python3 -m unittest discover -s scripts/tests -v
```

The contracts are governance artifacts only. They add no route, runtime,
storage, deployment, or secret.

### Release watch policy

Phase 3 release policy, calling examples, evidence conventions, and recovery
guidance live in [`docs/release-watch.md`](docs/release-watch.md) and the
[`release-watch` runbook](docs/runbooks/release-watch.md). Verification runs in
`atlas-journey-watch`; this repository remains the contract and policy owner.

### Secret-watch policy

[`policy/secret-watch.json`](policy/secret-watch.json) is the names-only
declaration consumed by `atlas-dep-audit`. It records repository and
environment scopes, required/optional/deprecated names, ownership, purpose,
classification, provenance, and owner-attested rotation policy without
containing a secret value. The format, threat model, suppression rules, and
emergency procedure are documented in
[`docs/secret-watch.md`](docs/secret-watch.md).

### Cost-guard policy

[`policy/cost-guard.json`](policy/cost-guard.json) is the versioned,
advisory-only quota and cost-risk policy consumed by `atlas-quota-watch`. It
declares included allowances, warning and critical thresholds, projection and
freshness windows, ownership, classification, and notification/issue valves.
The architecture, offline fixture workflow, limitations, and recovery guidance
are documented in [`docs/cost-guard.md`](docs/cost-guard.md).

### Contract registry

[`policy/estate-registry.json`](policy/estate-registry.json) is the canonical
36-repository catalogue. Runtime records under
[`policy/service-contracts/`](policy/service-contracts/) conform to the shared
ServiceContract v1 schema and declare exact route ownership, explicit unknowns,
dependencies, runbooks, and assurance links. Validate and generate local JSON,
Markdown, dependency graph, and service catalogue outputs without network
access:

```bash
python3 scripts/validate_contract_registry.py \
  --report /tmp/registry-report.json \
  --markdown /tmp/registry-report.md \
  --graph /tmp/service-dependency-graph.json \
  --catalog /tmp/service-catalog.json
```

Architecture, migration, live-read permissions, limitations, and rollback are
documented in [`docs/contract-registry.md`](docs/contract-registry.md).

### Deploy orchestrator

Phase 7 adds a deterministic, dependency-aware deployment planner without a
dispatcher. [`policy/deploy-orchestrator.json`](policy/deploy-orchestrator.json)
declares existing target workflows, approvals, preflights, rollback guidance,
and post-deploy release-watch plans. The executor is a disabled `noop`, and
`--execute` fails closed.

```bash
python3 scripts/deploy_orchestrator.py validate
python3 scripts/deploy_orchestrator.py plan \
  --service atlas-api-public \
  --environment production \
  --output /tmp/deploy-plan.json \
  --markdown /tmp/deploy-plan.md
```

The manual `deploy-orchestrator-dry-run.yml` workflow has read-only repository
permission, no dispatch permission or secret, and retains plan artifacts for
14 days. Architecture, onboarding, approval gates, partial-deployment recovery,
and rollback limitations are documented in
[`docs/deploy-orchestrator.md`](docs/deploy-orchestrator.md).

### Backup audit

Phase 8 adds a standard-library, offline backup-policy validator and disposable
restore-drill engine. The four initial targets are synthetic GitHub artifact,
Cloudflare KV export, incident export, and Chroma/vector-store fixtures. They
exercise assurance mechanics only and do not prove that a live backup exists.

```bash
python3 scripts/backup_audit.py \
  --policy policy/backup-audit.json \
  --fixtures tests/fixtures/backup-audit \
  --report /tmp/backup-audit.json \
  --markdown /tmp/backup-audit.md \
  --now 2026-07-14T12:00:00Z
```

The auditor cross-checks the Phase 6 registry, emits schema-valid
`BackupEvidence` and `Finding` records, and refuses live destinations, provider
access, traversal, symlinks, executable archive entries, overwrites, and
unbounded extraction. Architecture, policy format, safety limits, future
read-only provider permissions, migration, and rollback are documented in
[`docs/backup-audit.md`](docs/backup-audit.md).

### Ramone and Home Assistant read surface

Phase 9 adds a deterministic offline `ControlPlaneSummary` aggregator, exact
ten-sensor and nine-tool policy, repository integration inventory, generated
fixtures, and disabled rollout/rollback guidance. The implementation remains
read-only and performs no live Home Assistant/OpenWebUI change or deployment.

```bash
python3 scripts/control_plane_summary.py \
  --sources tests/fixtures/control-plane-summary/sources \
  --now 2026-07-14T10:30:00Z
python3 -m unittest scripts.tests.test_control_plane_summary \
  scripts.tests.test_ramone_control_plane_policy -v
```

Architecture and owner gates are documented in
[`docs/ramone-home-assistant-integration.md`](docs/ramone-home-assistant-integration.md),
with repository evidence and live unknowns in the companion
[inventory](docs/ramone-home-assistant-integration-inventory.md).

### Signal and reliability evidence

The weekly estate audit now emits a weighted `atlas-estate-conformance-report/v1` document with per-repository rule coverage, raw findings, provenance, and a deterministic fingerprint. `scripts/publish_evidence.py` publishes the verified result to the public API after the workflow has completed.

`policy/chaos-experiments.json` declares bounded fault contracts. Scheduled runs are deterministic simulations; live mode is manual, requires one named experiment, a protected `production-chaos` environment, a short-lived token, an allowlisted target, and rollback in a `finally` path. The public report records injection, detection, notification, and recovery latency separately.

### Adopt a deployment pipeline

Copy the matching template from `templates/` into a repo as `.github/workflows/deploy.yml`, change the name and flags, and forward secrets with `secrets: inherit`. The repo needs the secrets named in `docs/CICD-DECISIONS.md`.

A Worker caller is this short:

```yaml
name: Deploy
on:
  push:
    branches: [main, dev]
jobs:
  deploy:
    uses: AtlasReaper311/atlas-infra/.github/workflows/deploy-worker.yml@main
    with:
      worker_name: my-worker
      run_lint: true
    secrets: inherit
```

### Adopt change impact

Copy `templates/change-impact-caller.yml` into a repository as `.github/workflows/change-impact.yml`. The caller grants only `contents: read`. Reports stay in the workflow summary and artifact; the central workflow never edits the pull request.

## CI/CD pattern

`deploy-pages.yml` is the canonical Cloudflare Pages deploy workflow used across the static Atlas Systems deployments. Copy it into any static repo's `.github/workflows/` directory and set:

- `CLOUDFLARE_API_TOKEN`, a repo secret
- `CLOUDFLARE_ACCOUNT_ID`, a repo secret
- `CF_PROJECT_NAME`, a repo variable

The production site deploys through Cloudflare's native Git integration rather than this workflow. The workflow remains a documented fallback for repos that need Actions-driven deploys.

## Assurance security boundary

Change impact and policy checks read repositories and the canonical manifest. They do not deploy, edit repositories, open issues, or post pull request comments. The optional outbound write is one consolidated event to `atlas-notify`.

`GH_DIGEST_PAT` is reused for cross-repository reads. No new GitHub credential is required.

## How it fits into Atlas Systems

This repo is the foundation the rest of the stack assumes: container conventions, deployment workflows, change-impact analysis, conformance checks, and cross-platform scripts that the Worker repos and kits lean on. It is deliberately the least glamorous repo in the system and the one everything else depends on.

The transferable pattern is making infrastructure copyable: a workflow that lives in one place and drops into any repo is the difference between a pipeline and a habit.

---

Part of [atlas-systems.uk](https://atlas-systems.uk)
