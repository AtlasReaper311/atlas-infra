<div align="center">
  <img src="https://raw.githubusercontent.com/AtlasReaper311/AtlasReaper311/main/atlas-icon-dark-256.png" width="88" alt="Atlas Systems"/>
</div>

# atlas-infra

```
┌─────────────────────────────────────────────┐
│  ATLAS SYSTEMS // atlas-infra               │
│  shared policy, contracts, and pipelines    │
└─────────────────────────────────────────────┘
```

![Docker](https://img.shields.io/badge/docker-f5a623?style=flat-square&labelColor=0a0a0f)
![GitHub Actions](https://img.shields.io/badge/ci-github%20actions-4ade80?style=flat-square&labelColor=0a0a0f)
![Cross-platform](https://img.shields.io/badge/cross--platform-aaa9a0?style=flat-square&labelColor=0a0a0f)
![Cost](https://img.shields.io/badge/cost-%C2%A30-aaa9a0?style=flat-square&labelColor=0a0a0f)

Shared CI/CD workflows, control-plane contracts, policy, validation, and recovery guidance for Atlas Systems. Public runtime governance lives here; private repository governance is validated in the authenticated source repository and is never listed in this public control plane.

## Structure

```
.github/workflows/   reusable CI/CD and assurance workflows
contracts/           versioned cross-estate contracts and schemas
docker/              container images and compose examples
docs/                ADRs, runbooks, and operating guidance
policy/               public runtime policy and contract indexes
scripts/              validation, planning, and assurance utilities
templates/            copyable workflow callers
```

## Agent repository workflow

Agents and operators creating, adopting, changing, publishing, deploying, deprecating, or retiring a repository should begin with [`docs/AGENT-REPOSITORY-COMPLIANCE.md`](docs/AGENT-REPOSITORY-COMPLIANCE.md).

The document is a navigation and execution contract. Current repository truth, accepted ADRs, machine-readable policy, schemas, executable validators, and reusable workflows remain higher authority.

## CI/CD

The repository owns reusable workflow shapes rather than application deployment state. Service repositories keep their own callers and credentials; shared workflows provide consistent validation and reporting.

### Reusable workflows

- `deploy-worker.yml`: validate, deploy, and report a Cloudflare Worker.
- `validate-static.yml`: validate and publish a static site.
- `change-impact.yml`: read-only pull request impact analysis.
- `dependabot-review.yml`: bounded Dependabot review policy.
- `validate-private-governance.yml`: validate source-owned governance inside a private Atlas Systems repository without publishing its identity here.

Every workflow uses explicit permissions, bounded runner time, and immutable third-party action pins. Production deployment remains separate from ordinary pull request validation.

### Scheduled assurance

- `estate-policy.yml`: public-estate conformance audit.
- [`atlas-dep-audit`](https://github.com/AtlasReaper311/atlas-dep-audit): dependency, SBOM, OSV, action pin, and provenance assurance.
- [`atlas-journey-watch`](https://github.com/AtlasReaper311/atlas-journey-watch): synthetic journeys across public estate surfaces.

The implementation and adoption rules live in [`docs/ESTATE-ASSURANCE.md`](docs/ESTATE-ASSURANCE.md).

## Public runtime contracts

[`policy/estate-registry.json`](policy/estate-registry.json) is the public runtime contract index. It contains only repositories and services intentionally represented by the public Atlas Systems estate. Runtime records under [`policy/service-contracts/`](policy/service-contracts/) conform to ServiceContract v1 and declare route ownership, dependencies, runbooks, metadata expectations, and assurance links.

The public registry is deliberately not a complete list of everything the owner operates. A repository or Worker does not become public merely because it exists in the GitHub or Cloudflare account.

Validate the public runtime contract set without network access:

```bash
python3 scripts/validate_contract_registry.py \
  --report /tmp/registry-report.json \
  --markdown /tmp/registry-report.md \
  --graph /tmp/service-dependency-graph.json \
  --catalog /tmp/service-catalog.json
```

Architecture and boundary decisions are recorded in [`docs/adrs/public-private-estate-boundary.md`](docs/adrs/public-private-estate-boundary.md).

## Private repository governance

Private Atlas Systems repositories own `.atlas/governance.json` in their own authenticated source repository. The declaration records lifecycle, internal estate membership, whether anonymous aggregate metrics are allowed, runtime status, and service IDs while enforcing `public_projection: false`.

The repository calls the reusable validator:

```yaml
jobs:
  validate:
    uses: AtlasReaper311/atlas-infra/.github/workflows/validate-private-governance.yml@<immutable-commit>
```

This preserves estate checks without creating a public central inventory of private repository identities. Unknown repositories and Workers fail closed for publication.

The schema is [`contracts/v1/repository-governance.schema.json`](contracts/v1/repository-governance.schema.json).

## Shared control-plane contracts

`contracts/v1/` contains versioned JSON Schema contracts, compatibility rules, fixtures, and deterministic fingerprint policy used by read-only assurance tooling.

```bash
python3 scripts/validate_control_plane_contracts.py
python3 scripts/validate_release_evidence.py --instance path/to/release-evidence.json
python3 -m unittest discover -s scripts/tests -v
```

The contracts are governance artifacts. They do not create routes, storage, provider mutations, deployment authority, or secrets.

## Release and reliability policy

Release verification is journey-owned and stateless. `atlas-infra` owns contracts, policy, runbooks, and deterministic planning; execution remains in the repository that owns the actual journey or deployment path.

Relevant guidance includes:

- [`docs/release-watch.md`](docs/release-watch.md)
- [`docs/runbooks/release-watch.md`](docs/runbooks/release-watch.md)
- [`docs/deploy-orchestrator.md`](docs/deploy-orchestrator.md)

The deployment orchestrator is a deterministic planner. Its executor remains a disabled `noop`; `--execute` fails closed.

## Secret assurance

[`policy/secret-watch.json`](policy/secret-watch.json) stores names and policy only. Secret values are never committed or requested by the control plane. Provider metadata that cannot be read with approved permissions is reported as unavailable rather than healthy.

Emergency and operating guidance is documented in [`docs/secret-watch.md`](docs/secret-watch.md).

## Cost and resource assurance

[`policy/cost-guard.json`](policy/cost-guard.json) defines advisory quota thresholds and freshness rules. Resource reconciliation remains read-only and cannot delete or mutate Cloudflare state.

The standing rule is separation of evidence from authority: an audit may report drift, but it does not receive deployment or provider-write permissions merely to fix what it found.

## Local development

Prerequisite: Docker 24.x or newer.

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

## Assurance security boundary

Public control-plane validation reads committed public policy and contracts. Private governance validation runs inside the private repository that owns the declaration. Neither path requires secret values, and neither turns repository visibility into a publication signal.

Provider writes, workflow dispatches, deployments, corpus refreshes, and other live changes remain separate owner-approved actions.

## How it fits into Atlas Systems

`atlas-infra` is the policy and workflow layer beneath the public site, API, observability services, and reusable repository library. It defines the contracts that let those components agree on ownership and evidence while keeping public architecture distinct from private owner-operated systems.

The transferable pattern is to separate governance from publication: every component can be checked without requiring every component to be advertised.

---

Part of [atlas-systems.uk](https://atlas-systems.uk)
