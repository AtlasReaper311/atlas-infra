# Retirement planner

Wave 3.6 adds a deterministic planner for deprecating and retiring Atlas Systems repositories and services without giving the planner execution authority.

The contract authority remains `contracts/v1/wave3/retirement-evidence.schema.json`. The planner does not create a second lifecycle authority and does not edit lifecycle values by itself.

## Purpose

Retirement is dangerous when one source says a service is obsolete while routes, bindings, manifests, or production work still refer to it. The planner turns those dependencies into an ordered list of blockers before an owner considers any destructive action.

Run a service assessment:

```bash
python3 scripts/retirement_planner.py \
  --kind service \
  --id atlas-api-index \
  --json-out /tmp/retirement-plan.json \
  --markdown-out /tmp/retirement-plan.md
```

Run a repository assessment:

```bash
python3 scripts/retirement_planner.py \
  --kind repository \
  --id AtlasReaper311/atlas-api-public
```

The command is local and provider-free.

## Derived evidence

The planner derives four gates from current Atlas Infra authority:

- `dependencies_clear` from inbound service-contract dependencies;
- `routes_clear` from declared public Cloudflare routes;
- `bindings_clear` from inbound declared Worker service bindings;
- `manifest_clear` from the public runtime registry and repository classification authority.

The explicit public Cloudflare topology also acts as an immediate public-allowlist blocker. If the subject remains there, `worker_allowlist_clear` is `failed`.

Absence from that topology does not prove every downstream registry or copied allowlist has been cleared, so the same gate becomes `unknown` until separately reviewed evidence proves it.

## External evidence

Some retirement gates cannot be proven from the offline control-plane repository:

- current production pull requests and rollout references;
- downstream Worker allowlist copies;
- historical evidence preservation;
- recovery or replacement handling.

Those states remain `unknown` unless an explicit bounded evidence file is supplied:

```json
{
  "schema_version": "atlas-retirement-external-evidence/v1",
  "subject": {
    "kind": "service",
    "service_id": "example-service"
  },
  "worker_allowlist_clear": "verified",
  "production_prs_clear": "verified",
  "historical_evidence_preserved": "verified",
  "recovery_handled": "not-applicable"
}
```

The file can use only the retirement contract evidence states: `verified`, `failed`, `unknown`, `unavailable`, or `not-applicable`.

External evidence cannot override a contradiction in current Atlas authority. For example, it cannot mark the Worker allowlist clear while the subject is still present in the public Cloudflare topology declaration.

## Eligibility

`eligible_for_owner_retirement_review` becomes true only when every retirement gate is either `verified` or `not-applicable`.

That state means the evidence is complete enough for owner review. It is not permission to execute retirement.

The final owner-reviewed retirement record still uses the canonical `atlas-control-plane/retirement-evidence/v1` contract and can be traced through its deterministic `retirement:sha256:` identity.

## Ordered plan

The planner always presents the gates in this order:

1. remove or replace inbound dependencies;
2. remove runtime routes through the owning repository workflow;
3. remove inbound Worker bindings;
4. remove public manifest/classification membership after runtime detach;
5. prove downstream Worker registry/allowlist projections are clear;
6. review production PRs and pending rollout references;
7. preserve historical ADR, incident, release, and retirement evidence;
8. record recovery, replacement, or explicit not-applicable handling.

The order is advisory evidence sequencing. The planner does not perform any step.

## Safety boundary

The planner has no code path for:

- GitHub repository archive or delete;
- Worker or Pages deployment/deletion;
- DNS changes;
- route or binding mutation;
- KV, D1, R2, or Durable Object mutation;
- secret changes;
- workflow dispatch;
- provider API writes.

Any later destructive retirement action remains a separate, explicit owner-approved operation with its own recovery evidence.
