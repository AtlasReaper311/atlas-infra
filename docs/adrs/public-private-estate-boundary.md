+++
id = "ADR-0003"
date = 2026-07-20
status = "accepted"
slug = "public-private-estate-boundary"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-index", "AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-corpus", "AtlasReaper311/atlas-infra"]
services = ["atlas-api-index", "atlas-api-public", "atlas-corpus"]
contracts = ["atlas-control-plane/service-contract/v1"]
policies = ["policy/estate-registry.json", "policy/public-boundary-projections.json", "policy/public-repository-classifications.json"]
+++

# ADR-0003: Public and private estate boundary

Amended 10 August 2026 to reconcile the original source-boundary wording with later accepted ownership decisions and the executable projection audit.

## Context

Atlas Systems contains public portfolio infrastructure and private owner-operated repositories. The previous control-plane model treated account membership as a publication signal in several places. Public registry material named private repositories, the Worker registry enumerated account-wide Cloudflare scripts, and public consumers could inherit identities that were never intended to be portfolio surfaces.

Repository visibility, repository identity, and estate publication membership are different concerns. A private component can require dependency checks, CI, deployment validation, operational monitoring, aggregate engineering metrics, and an explicit ownership reference without becoming a public repository or entering a public runtime projection.

The original implementation interpreted the boundary as a literal ban on every private repository name in every public source file. Later accepted decisions make that interpretation too broad. ADR-0009 intentionally records private publication-pipeline ownership in public architecture authority. ADR-0010 intentionally names private collaborators in decision text while keeping them outside public classification authority. Public tests can also name a private component solely to assert that it is absent from a published topology, and a repository name can collide with an unrelated public code token.

The security property that must remain fail-closed is therefore publication and projection membership, not lexical absence from all public source bytes.

## Decision

The estate has two governance planes with a one-way publication boundary.

The public plane contains only explicitly approved public repositories, public runtime contracts, public Worker metadata, governed public topology, and sanitized public telemetry. `atlas-infra/policy/estate-registry.json` is the public runtime contract index. It must never contain private repository identities.

Private repositories own `.atlas/governance.json` inside their own source repository. The reusable `validate-private-governance.yml` workflow validates that declaration in authenticated repository context. Private governance remains source-owned and is never projected into the public classification authority.

A textual ownership reference to a private repository is not, by itself, public estate membership. Accepted ADRs, reviewed contracts, tests, and technical documentation may name a private collaborator when the identity is necessary to explain ownership, exclusion, compatibility, or a privacy assertion. Such references do not authorize publication of private source, service identities, provider resources, routes, commit messages, deployment records, credentials, or private topology relationships.

The machine boundary is explicit. `policy/public-boundary-projections.json` lists the public source coordinates whose contents represent repository membership or governed topology. The scheduled boundary audit derives the current private repository identity set only inside authenticated GitHub context and scans those coordinates. A private identity found in any governed projection fails closed. The report contains only public repository/path/line coordinates and a fingerprint derived from those public coordinates. It never writes the protected identity, a hash of the protected identity, or a private repository count.

Account-wide public code search is not publication authority and is not used as the boundary gate. This avoids treating reviewed ADR text, privacy regression tests, historical control-plane explanation, or unrelated lexical collisions as public membership.

Cloudflare Worker discovery is fail-closed for publication. Account-level discovery may observe all scripts internally, but `atlas-api-index` publishes only an explicit allowlist of public Workers. `atlas-api-public` independently filters the registry against the public manifest.

Public event and metric endpoints may include anonymous aggregate contribution from private repositories when the private governance document permits it. They must not expose private repository-level attribution, private service identities, routes, commit messages, deployment records, or topology relationships.

Unknown repositories and Workers are private by default. Public repository or runtime membership requires an explicit public declaration through the accepted classification and projection authorities.

## Consequences

Private applications and operational services continue to run under their existing authentication and deployment controls. Excluding them from public registries does not retire or disable them.

A new private repository gets governance by adding `.atlas/governance.json` and calling the reusable private-governance workflow. A new public runtime requires an explicit public registry and manifest change.

A new machine-readable public projection that can expose repository membership or topology must be added to `policy/public-boundary-projections.json` before it can become part of the governed publication boundary.

Public DORA and activity metrics can represent whole-estate engineering activity only as aggregate numbers. Source-level breakdowns remain limited to public repositories.

The public corpus may index reviewed public ADRs and technical documentation that contain intentional private ownership references. That makes the reference searchable, but it does not make the private repository a member of the public estate and does not permit private source or topology to enter corpus ingestion.

Privacy tests may retain real private identities when their purpose is to prove those identities are absent from a published projection. Unrelated public code tokens are not treated as repository publication solely because their text matches a private repository name.

Historical Git commits are not rewritten. The boundary applies to current and future governed projection state.
