# Public and private estate boundary

Status: Accepted

Date: 2026-07-20

## Context

Atlas Systems contains public portfolio infrastructure and private owner-operated repositories. The previous control-plane model treated account membership as a publication signal in several places. Public repository files named private repositories, the Worker registry enumerated account-wide Cloudflare scripts, and public consumers could inherit identities that were never intended to be portfolio surfaces.

Repository visibility and estate membership are different concerns. A private component can still require dependency checks, CI, deployment validation, operational monitoring, and aggregate engineering metrics without becoming public documentation.

## Decision

The estate has two governance planes with a one-way publication boundary.

The public plane contains only explicitly approved public repositories, public runtime contracts, public Worker metadata, and sanitized public telemetry. `atlas-infra/policy/estate-registry.json` is the public runtime contract index. It must never contain private repository identities.

Private repositories own `.atlas/governance.json` inside their own source repository. The reusable `validate-private-governance.yml` workflow validates that declaration in the authenticated repository context. No central public file lists those repositories.

Cloudflare Worker discovery is fail-closed for publication. Account-level discovery may observe all scripts internally, but `atlas-api-index` publishes only an explicit allowlist of public Workers. `atlas-api-public` independently filters the registry against the public manifest.

Public event and metric endpoints may include anonymous aggregate contribution from private repositories when the private governance document permits it. They must not expose private repository names, service identities, routes, commit messages, deployment records, or topology relationships.

Unknown repositories and Workers are private by default. Publication requires an explicit public declaration.

## Consequences

Private applications and operational services continue to run under their existing authentication and deployment controls. Removing them from public registries does not retire or disable them.

A new private repository gets governance by adding `.atlas/governance.json` and calling the reusable private-governance workflow. A new public runtime requires an explicit public registry and manifest change.

Public DORA and activity metrics can represent whole-estate engineering activity only as aggregate numbers. Source-level breakdowns remain limited to public repositories.

The public corpus ingests public source and published site material only. Public documentation must not name private repository identities because the corpus can make any public source reference searchable.

Historical Git commits are not rewritten. The boundary applies to current and future public state.
