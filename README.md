\# atlas-infra



Container orchestration, CI/CD pipelines, and deployment infrastructure

for the Atlas Systems platform.



\## Structure



```

.github/workflows/   CI/CD pipeline definitions

docker/              Container images and compose configs

scripts/             Dev and ops utilities (cross-platform)

```



\## Services



| Image | Purpose |

|-------|---------|

| `hello-atlas` | HTTP smoke test — confirms container pipeline works |



\## Local development



Prerequisites: Docker ≥ 24.x



```bash

docker build -t hello-atlas ./docker/hello-atlas

docker run -p 8080:8080 hello-atlas

curl http://localhost:8080/health

```



Expected response:

```json

{

&#x20; "status": "ok",

&#x20; "service": "hello-atlas"

}

```



\## CI/CD pattern



`deploy-pages.yml` is the canonical Cloudflare Pages deploy workflow used

across all Atlas Systems static deployments. Copy it into any static repo's

`.github/workflows/` directory and set the following:



\- `CLOUDFLARE\_API\_TOKEN` — repo secret

\- `CLOUDFLARE\_ACCOUNT\_ID` — repo secret

\- `CF\_PROJECT\_NAME` — repo variable (not a secret)



\---



Part of \[Atlas Systems](https://atlas-systems.uk)

