# Atlas Systems control-plane expansion plan

Status: Superseded

Original design date: 14 July 2026

Superseded by: [`docs/adrs/public-private-estate-boundary.md`](adrs/public-private-estate-boundary.md)

## Purpose

This document preserves the public architectural direction of the earlier control-plane expansion work without retaining an account-wide repository inventory. The accepted architecture now separates public runtime governance from private source-owned governance, so a public planning document must not enumerate owner-operated private repositories or services.

## Public control-plane model

The public Atlas Systems control plane has four layers:

1. `atlas-infra` owns public contracts, policy, reusable workflows, validation, release planning, runbooks, and evidence conventions.
2. Specialist public repositories own detection and execution for their own domain. Examples include `atlas-dep-audit`, `atlas-journey-watch`, `deploy-watch`, `atlas-quota-watch`, `atlas-api-index`, and `atlas-api-public`.
3. `atlas-gardener` may propose bounded reviewable remediation branches and pull requests, but it cannot merge or deploy.
4. `atlas-api-public` exposes bounded public projections. `atlas-notify` routes operational events. Local AI and Home Assistant integration remain separate consumers rather than becoming control-plane authorities.

The core rule is evidence without implicit authority. A component that can inspect, score, or propose a change does not automatically gain permission to deploy, restore, merge, mutate provider state, or read secrets.

## Public and private governance boundary

The original planning exercise inspected a wider owner-operated estate. That inventory is intentionally not reproduced here.

Current policy:

- the public runtime registry contains only intentionally public repositories and services;
- private repositories own their governance declarations inside their authenticated source repository;
- account membership is not a publication signal;
- unknown Workers and repositories fail closed for public projection;
- private activity may contribute to anonymous aggregate metrics when source governance permits it;
- repository names, service identities, routes, commit messages, deployment records, and topology relationships from private systems do not cross into public surfaces.

See the accepted ADR for the binding decision and consequences.

## Public capability ownership

### Contracts and policy

`atlas-infra` owns versioned schemas and policy documents for public runtime contracts, findings, evidence, release verification, and deterministic fingerprints.

### Runtime discovery

`atlas-api-index` observes Cloudflare Worker inventory but publishes only an explicit public allowlist. Discovery answers what exists; declaration answers what may be published.

### Public API

`atlas-api-public` is the publication membrane. It independently filters registry and topology output, serves bounded reliability and search projections, and exposes sanitized recent-event data.

### Assurance

Public assurance tools produce evidence without gaining deployment authority. Dependency, journey, resource, quota, and change-impact systems remain read-only or proposal-only unless an explicit owner-approved workflow grants a narrower mutation path.

### Remediation

`atlas-gardener` is the bounded remediation proposal layer. It can create reviewable branches or pull requests within policy, but cannot merge, deploy, rewrite protected history, or mutate production providers.

### Release verification

Synthetic journeys and measured service evidence can verify a release. Missing evidence remains unknown rather than being promoted to healthy. Rollback and production mutation remain human-gated.

### Secret assurance

Secret assurance stores policy about secret names and expected controls, never secret values. Provider metadata is read only with approved permissions. Unavailable evidence is reported as unavailable.

### Resource and cost assurance

Cloudflare resource and quota checks remain read-only. Drift and threshold findings are evidence for review; they are not authority to delete or mutate provider resources.

## Public data-flow rules

```text
provider/account observation
          │
          ▼
 internal evidence collection
          │
          ▼
 explicit publication policy
          │
          ▼
 sanitized public projection
          │
          ├── atlas-api-public
          ├── atlas-systems Lab
          ├── status surface
          └── public corpus
```

A public consumer must never depend directly on raw account-wide discovery when an approved projection exists.

## Validation principles

Every public control-plane change should preserve:

- deterministic offline validation where possible;
- explicit top-level GitHub Actions permissions;
- bounded workflow timeouts and concurrency;
- immutable third-party action pins;
- least-privilege provider tokens;
- no production secrets in pull-request validation;
- separate implementation, merge, and live rollout stages;
- honest unknown states when evidence is absent or stale.

Private repositories receive equivalent governance checks inside their own authenticated source repository through the reusable private-governance workflow. Their identities are not copied into this public plan.

## Outcome

The control plane remains one coherent system without requiring one public inventory of everything the owner operates. Public architecture is explicit and auditable; private systems remain governed and valid without becoming portfolio documentation.
