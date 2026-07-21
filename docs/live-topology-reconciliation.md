# Live topology reconciliation

Wave 3.3 extends Atlas Systems from storage-only reconciliation to a declared-versus-observed view of the public Cloudflare topology.

## Authority

`policy/public-cloudflare-topology.json` is the public desired-state allowlist for Cloudflare Workers, routes, service bindings, metadata endpoints, and Pages projects.

`policy/public-cloudflare-resources.json` remains the separate storage ownership authority for KV, D1, and R2. The topology policy references those resource identities rather than creating a second storage registry.

Service ownership and metadata expectations remain in `policy/service-contracts/`. The topology validator cross-checks the topology declaration against those current contracts.

## Privacy boundary

The topology policy is not an account inventory.

Cloudflare may return Workers, routes, Pages projects, bindings, or storage resources that are not in the public Atlas declaration. Those objects are private by default. A provider read cannot make an identity public.

The later observed-state collector must therefore keep raw provider responses temporary and private. Retained reports may contain:

- declared public identities and their reconciliation state;
- findings about declared public topology;
- aggregate counts for undeclared provider objects;
- explicit redacted state.

They must not contain undeclared Worker names, route patterns, Pages project names, service-binding targets, provider binding payloads, or inferred owners.

Worker settings responses require additional care because provider payloads can include bindings that represent secrets. The collector must reduce settings immediately to the bounded binding types needed for reconciliation and must never retain or emit secret binding text.

## Declared topology

The v1 policy currently covers the fourteen explicitly approved public Worker script identities used by the public Worker registry and three public Cloudflare Pages projects.

Each Worker declaration contains:

- Worker script and service identity;
- source repository and source configuration reference;
- expected public routes;
- expected metadata URL;
- expected Worker-to-Worker service bindings;
- storage bindings that are either linked to the storage authority or, for a Durable Object, bounded to the public binding and class name.

Each Pages declaration contains the project name, repository, deployment-workflow source reference, and public surface.

## Offline validation

Run:

```bash
python3 scripts/public_cloudflare_topology.py --root .
```

Validation fails closed on:

- malformed contract data;
- secret-bearing keys;
- duplicate public Worker identities;
- duplicate exact route ownership;
- a Worker whose repository/runtime kind disagrees with its service contract;
- a metadata URL that disagrees with a known service-contract metadata endpoint;
- an unknown service-binding target;
- a KV, D1, or R2 binding absent from the storage authority;
- a storage binding where the Worker is neither declared owner nor declared consumer;
- a Pages project without a Cloudflare Pages service contract.

The validator performs no network calls.

## Observed-state rollout

`atlas-resource-audit` owns the read-only provider observer and reconciler. Source implementation and live collection are separate gates.

A future live collection needs only read access sufficient for the provider objects being observed. No write, deploy, route mutation, DNS mutation, storage write, or delete permission belongs in the topology auditor.

Changing the existing Cloudflare audit token permissions is a separate provider action and is not performed by this policy change.

## Failure semantics

Expected public topology that is missing or inconsistent is a finding. Unknown provider topology is not automatically an error and is never automatically public.

The reconciler may distinguish states such as `failed`, `warning`, `unknown`, `unavailable`, and informational redacted observations. It must never convert missing or unavailable evidence into healthy evidence.

No remediation path exists in Wave 3.3.
