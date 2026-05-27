# atlas-infra

Container orchestration, CI/CD pipelines, and deployment infrastructure
for the Atlas Systems platform.

## Structure

```
.github/workflows/   CI/CD pipeline definitions
docker/              Container images and compose configs
scripts/             Dev and ops utilities (cross-platform)
```

## Services

| Image | Purpose |
|-------|---------|
| `hello-atlas` | HTTP smoke test — confirms container pipeline works |

## Local development

Prerequisites: Docker ≥ 24.x

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

`deploy-pages.yml` is the canonical Cloudflare Pages deploy workflow used
across all Atlas Systems static deployments. Copy it into any static repo's
`.github/workflows/` directory and set the following:

- `CLOUDFLARE_API_TOKEN` — repo secret
- `CLOUDFLARE_ACCOUNT_ID` — repo secret
- `CF_PROJECT_NAME` — repo variable (not a secret)

---

Part of [Atlas Systems](https://www.atlas-systems.uk)
