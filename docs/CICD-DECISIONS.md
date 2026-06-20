# CI/CD decisions

How deployment works across Atlas Systems, and why it is shaped this way.
This file is the reference. New repos copy a caller and inherit a working
pipeline; they do not rediscover this configuration.

## Three pipeline shapes

Every repo uses one of three reusable workflows defined in this repo:

| Shape | Workflow | Used by |
|---|---|---|
| Worker deploy | `.github/workflows/deploy-worker.yml` | github-pulse, site-pulse, deploy-watch, atlas-vault, atlas-notify |
| Static deploy | `.github/workflows/validate-static.yml` | atlas-systems, status, atlas-doc-viewer |
| Python CI | inline `ci.yml` per repo | atlas-kit-python-rag, ollama-rag-kit |

A caller is a short file that names the reusable workflow, passes a label
and a couple of flags, and forwards secrets with `secrets: inherit`. The
pipeline logic lives in one place, so a change to the deploy shape is one
edit, not one per repo.

## Token model

Two Cloudflare deploy tokens, scoped as narrowly as the job allows. These
are GitHub Actions secrets, used by the workflows to publish.

| Secret | Cloudflare scope | Used by |
|---|---|---|
| `CF_WORKERS_DEPLOY_TOKEN` | Workers Scripts: Edit, Workers Routes: Edit | the five Worker repos |
| `CF_PAGES_DEPLOY_TOKEN` | Cloudflare Pages: Edit | the three static-site repos |

`CF_ACCOUNT_ID` accompanies both. There is no account-wide token: a leak of
either is limited to Workers or Pages, not both, and not the whole account.

Runtime secrets are separate from deploy tokens. They are set on the Worker
itself with `npx wrangler secret put NAME`, never in Actions, and each Worker
needs its own:

| Worker | Runtime secrets |
|---|---|
| atlas-notify | `DISCORD_WEBHOOK_URL`, `NOTIFY_TOKEN` |
| github-pulse | `GITHUB_TOKEN`, optionally `NOTIFY_TOKEN` |
| site-pulse | `CLOUDFLARE_API_TOKEN` (Zone Analytics: Read) |
| deploy-watch | `CLOUDFLARE_API_TOKEN` (Account Pages: Read), `DISCORD_DEPLOY_WEBHOOK` |
| atlas-vault | `VAULT_TOKEN`, `DISCORD_WEBHOOK` |

Note that deploy-watch's runtime `CLOUDFLARE_API_TOKEN` is a Pages: Read
token, a different and narrower thing than the Workers deploy token that
ships the code. They are intentionally distinct.

## Discord routing

| Channel | Receives | Secret |
|---|---|---|
| api-deploys | every Worker deploy outcome | `DISCORD_API_DEPLOYS_WEBHOOK` |
| deploy-log | static-site deploy outcomes, plus deploy-watch | `DISCORD_DEPLOY_WEBHOOK` |
| ci-cd | test/CI results (atlas-notify, both Python kits) | `DISCORD_CICD_WEBHOOK` |

## Two rules learned the hard way

**Routes use `zone_id`, never `zone_name`.** A scoped CI token cannot do the
membership lookup that resolves a zone name to an id, so a route written as
`zone_name = "atlas-systems.uk"` fails in Actions with "Could not find zone".
Every route in every `wrangler.toml` uses the literal `zone_id`. atlas-notify
has two routes; both must use `zone_id`.

**Named environments inherit almost nothing.** A `[env.dev]` block does not
inherit `vars`, `kv_namespaces`, `routes`, or `triggers` from the top level.
Each must be redeclared, or the dev Worker deploys with them empty. Across
Atlas Systems, dev environments set `workers_dev = true`, omit `routes` so
dev never claims a production path, omit `triggers` so dev never runs crons,
and point at their own KV namespaces so dev never writes to a production cache.
