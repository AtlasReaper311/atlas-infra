# Atlas Systems technical decisions log

This file is a historical summary of public Atlas Systems architecture decisions. Accepted architecture is recorded in `docs/adrs/`; current repository and deployment state must be verified from source and live evidence.

Private owner-operated repositories and services are intentionally omitted. Their governance remains source-owned and does not form part of the public estate inventory.

## Infrastructure

### Hosting

- Cloudflare Pages hosts the public static surfaces.
- Cloudflare Workers host bounded public API, observability, telemetry, and edge projections.
- The accepted Workers Plus subscription is the only standing exception to the otherwise free-tier-first infrastructure policy.

### CI/CD

- GitHub Actions is the controlled deployment path for public Atlas Systems repositories.
- Reusable workflows in `atlas-infra` standardise validation and deployment behavior.
- Worker validation performs a Wrangler dry run before deployment.
- Static surfaces validate HTML and links before deployment.
- Production rollout remains distinct from repository merge state.

### Public and private boundary

- The public control plane contains only explicitly approved public repositories and runtime contracts.
- Private repository governance is stored and validated inside the authenticated source repository.
- Account membership is never a publication signal.
- Unknown repositories and Workers fail closed for public projection.
- Anonymous aggregate activity may include private work when source governance permits it, but public output never exposes private repository identities, routes, commit messages, deployment records, or topology relationships.

### Token model

- Deploy-time and runtime credentials remain separate.
- Read-only introspection services receive read-only provider permissions.
- GitHub and Cloudflare tokens are scoped to the smallest practical permission set.
- Secrets are entered only through approved interactive prompts and are never committed to source.

### Worker metadata

- Public Workers may expose the shared `/_meta` contract.
- The public registry is fail-closed and contains only explicitly approved public Workers.
- Account-wide Cloudflare discovery is observation, not publication.
- Same-zone Worker-to-Worker calls use service bindings rather than public-hostname round trips.

### Event routing

- Runtime events use the fixed Atlas event envelope through the central event router.
- CI and deployment workflows can report directly to their configured notification channel.
- The public recent-event surface is a sanitized projection. Internal event evidence may remain richer for authenticated operational consumers.

### Public activity metrics

- Public repository details can be displayed directly.
- Whole-estate commit activity can contribute to anonymous totals and heatmaps.
- Repository names, commit messages, workflow details, and per-repository breakdowns are public-only.

### DORA metrics

- DORA calculations are downstream, read-only consumers of existing deployment and reliability evidence.
- Public DORA responses expose aggregate delivery metrics.
- Repository-level deployment breakdowns are not part of the public contract.
- Release correlation is reported as correlation evidence, not causal proof.

## Local AI and knowledge

### Public corpus

- The corpus is a projection of public repository source, published site content, and explicitly approved public documentation.
- Chunk IDs are deterministic so refreshes converge instead of duplicating content.
- Public search endpoints carry their own query bounds, rate limiting, and CORS policy.
- Private repository source is never an ingestion source.

### Ramone

- The public edge remains a bounded gateway to local AI services.
- Local inference and memory services remain on owner-controlled hardware.
- Public architecture documents only the intentionally published boundary.

### Telemetry

- Public telemetry is a bounded edge projection rather than direct workstation access.
- Hot data uses the Cache API; KV is reserved for bounded last-known-good state and conditional writes.
- Telemetry and service health must fail honestly rather than report stale success as current state.

## Reliability and assurance

### Release verification

- Synthetic browser journeys verify public surfaces.
- Release evidence is stateless and does not create automatic rollback authority.
- Missing release identity or evidence remains unknown rather than being promoted to healthy.

### Secret assurance

- Policy declares secret names and expected controls, never values.
- Scanners inspect names and tracked-file plaintext without requesting secret material.
- Missing or under-permissioned provider metadata is unavailable, not healthy.

### Resource audit

- Cloudflare resource reconciliation is read-only.
- Declared and observed state are compared without deletion or provider mutation authority.

### Dependency assurance

- Dependency and supply-chain checks remain evidence producers rather than deployment authorities.
- Public dependency findings can be surfaced when they concern public repositories.
- Private repository findings remain inside authenticated repository workflows.

## Operational principles

### Provider truth versus source truth

Merged code does not prove deployment. Deployment state is verified through provider evidence or live endpoints.

### Public declaration versus discovery

Discovery answers what exists in an account. Declaration answers what Atlas Systems intentionally publishes. Public surfaces consume the declaration boundary, never raw account inventory.

### Fail closed

A new or unknown runtime does not become public because it was deployed. Publication requires an explicit public contract and registry change.

### Conditional writes

Edge caches and polling systems write durable state only when the value changes or bounded staleness requires refresh.

### Browser-context validation

A healthy API can still fail in a browser because of CSP or CORS. Public-facing features are tested from the browser context, not only with command-line probes.

### PowerShell secret handling

Native PowerShell API calls involving secrets or JSON use `Invoke-RestMethod`, a header hashtable, and `ConvertTo-Json`. Secret-bearing inline command strings are avoided.

### WSL2 operational checks

Windows host health and WSL2 bridge health are separate failure domains. GPU, networking, and portproxy diagnostics verify the actual boundary in use before changing application code.

## Current public repository roles

The current public estate includes:

- `atlas-systems` for the primary portfolio and Lab surface.
- `status` for public availability reporting.
- `atlas-doc-viewer` for the public document viewer.
- `atlas-api-public` for the versioned public API.
- `atlas-api-index` for the approved public Worker registry.
- `atlas-notify` for operational event routing and the sanitized public event projection.
- `github-pulse` for public repository detail and anonymous activity aggregates.
- `site-pulse` for bounded public site analytics.
- `deploy-watch` for public Pages deployment outcomes.
- `atlas-blackbox` for incident evidence.
- `atlas-dora` for aggregate delivery metrics.
- `specular-telemetry`, `specular-sentinel`, and `specular-sonify` for bounded telemetry and observability.
- `atlas-corpus` for semantic search over public estate material.
- `ramone-edge`, `ramone-memory`, and `ramone-voice-trigger` for the documented public and local AI architecture.
- `atlas-infra`, `atlas-bootstrap`, `atlas-journey-watch`, `atlas-dep-audit`, `atlas-resource-audit`, `atlas-gardener`, `atlas-badges`, `worker-meta-kit`, `atlas-kit-python-rag`, and `ollama-rag-kit` for public infrastructure, assurance, and reusable engineering patterns.

The machine-readable public estate definition lives in `atlas-api-public/data/estate.manifest.json`. The public runtime contract index lives in `atlas-infra/policy/estate-registry.json`.
