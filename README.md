<div align="center">
  <img src="https://raw.githubusercontent.com/AtlasReaper311/AtlasReaper311/main/atlas-icon-dark-256.png" width="88" alt="Atlas Systems"/>
</div>

# atlas-infra

```
┌─────────────────────────────────────────────┐
│  ATLAS SYSTEMS // atlas-infra               │
│  the deployment backbone:                   │
│  containers, CI/CD, and ops scripts          │
└─────────────────────────────────────────────┘
```

![Docker](https://img.shields.io/badge/docker-f5a623?style=flat-square&labelColor=0a0a0f)
![GitHub Actions](https://img.shields.io/badge/ci-github%20actions-4ade80?style=flat-square&labelColor=0a0a0f)
![Cross-platform](https://img.shields.io/badge/cross--platform-aaa9a0?style=flat-square&labelColor=0a0a0f)
![Cost](https://img.shields.io/badge/cost-%C2%A30-aaa9a0?style=flat-square&labelColor=0a0a0f)

Container patterns, CI/CD definitions, and deployment infrastructure for the Atlas Systems platform. This is where the deployment backbone is proven before it gets reused across the other repos.

## Structure

```
.github/workflows/   CI/CD pipeline definitions
docker/              Container images and compose configs
scripts/             Dev and ops utilities (cross-platform)
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

## CI/CD pattern

`deploy-pages.yml` is the canonical Cloudflare Pages deploy workflow used across the static Atlas Systems deployments. Copy it into any static repo's `.github/workflows/` directory and set:

- `CLOUDFLARE_API_TOKEN`, a repo secret
- `CLOUDFLARE_ACCOUNT_ID`, a repo secret
- `CF_PROJECT_NAME`, a repo variable (not a secret)

The production site deploys through Cloudflare's native Git integration rather than this workflow; the workflow is kept as a documented, reusable fallback for repos that need Actions-driven deploys. Keeping the pattern here means a new repo inherits a working pipeline by copying one file rather than rediscovering the config.

## How it fits into Atlas Systems

This repo is the foundation the rest of the stack assumes: the container conventions, the deploy workflow, and the cross-platform scripts that the Worker repos and kits lean on. It is deliberately the least glamorous repo in the system and the one everything else depends on.

The transferable pattern is making infrastructure copyable: a deploy workflow that lives in one place and drops into any repo is the difference between a pipeline and a habit.

---

Part of [atlas-systems.uk](https://atlas-systems.uk)
