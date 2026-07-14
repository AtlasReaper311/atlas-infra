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
python3 -m unittest discover -s scripts/tests -v
```

The contracts are governance artifacts only. They add no route, runtime,
storage, deployment, or secret.

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
