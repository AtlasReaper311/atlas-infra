# Public Cloudflare resource registry

## Purpose

`policy/public-cloudflare-resources.json` is the declared public resource set for
Cloudflare storage that Atlas Systems intentionally exposes to read-only
assurance. It is not an account inventory and it must never become one.

The registry exists so `atlas-resource-audit` can answer one bounded question:

> Are the Cloudflare KV, D1, and R2 resources declared by the public Atlas
> Systems runtime still present in the provider account under the expected
> ownership model?

`atlas-infra` owns the declaration. Provider observation remains read-only and
belongs to `atlas-resource-audit`.

## Privacy boundary

Cloudflare account observation can see more than the public Atlas Systems
estate. Private and undeclared resources therefore follow the accepted
public/private boundary:

- declared public resources may appear in assurance findings by their already
  public provider ID, display label, owner, and source reference;
- undeclared provider resources may contribute only aggregate counts by resource
  kind;
- undeclared provider IDs, names, metadata, and ownership guesses must not be
  written to public logs, reports, workflow summaries, or artifacts;
- absence from this registry does not mean orphaned because a resource may be
  intentionally private.

The raw provider observation is transient runner data and is never an artifact.

## Resource identity

The registry matches resources by provider identity, not by a binding label or
provider display name. Each record declares:

- resource kind: `kv-namespace`, `d1-database`, or `r2-bucket`;
- immutable or provider-stable resource ID;
- a portfolio-facing display label taken from the owning source configuration;
- exactly one owning public service and repository;
- zero or more explicitly declared consumers;
- the repository and configuration path that proves the binding declaration.

This avoids treating two services that bind the same resource as two owners.
For example, `TELEMETRY_KV` is owned by `specular-edge` and consumed read-only by
`specular-sonify`.

## Current scope

Version one contains nine public KV namespaces. No public D1 database or R2
bucket is currently declared by the public runtime set.

SQLite-backed Durable Object storage such as `atlas-blackbox` is intentionally
outside this v1 collector because the current resource auditor supports KV, D1,
and R2 only. Backup and recovery classification for that state remains governed
by `policy/backup-audit.json`.

## Validation

`scripts/validate_public_cloudflare_resources.py` validates the document against
`policy/public-cloudflare-resources.schema.json` and checks it against
`policy/estate-registry.json`.

Validation fails when:

- the document violates its schema;
- a provider identity is declared more than once;
- an owner or consumer service is absent from the public runtime registry;
- a repository disagrees with the authoritative service owner;
- consumers are duplicated or unsorted;
- the owning service is repeated as its own consumer;
- resource records are not sorted by owner service ID.

The weekly estate-policy workflow runs this validator offline. Live Cloudflare
observation is deliberately separate and is performed by `atlas-resource-audit`
with its own read-only credential.

## Change procedure

A public resource change is source-first:

1. change the owning repository configuration on a reviewed branch;
2. update this registry with the new provider identity and ownership evidence;
3. run the Atlas Infra validators and repository tests;
4. merge the source changes through normal review;
5. allow the scheduled resource audit to verify the declared state against the
   provider account.

A provider resource appearing in account observation never adds itself to this
registry. Publication always requires an explicit reviewed source change.
