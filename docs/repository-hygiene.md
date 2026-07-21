# Repository hygiene governance

Wave 2 turns Atlas Systems repository presentation from convention into an auditable contract without creating a second repository authority.

## Authority

`policy/public-repository-classifications.json` remains the allowlist of intentionally public repositories. The hygiene auditor consumes that projection and never enumerates account membership. A public GitHub repository that is not in the projection is not silently admitted into Atlas portfolio governance.

`policy/repository-hygiene.json` owns the presentation rules used by the public audit and by source-local private README validation.

Private repository identities remain source-owned. A private repository calls the reusable README validator from its own authenticated workflow; Atlas Infra does not add those identities to the public classification projection or public audit report.

## README contract

Standard repository READMEs must preserve the Atlas icon, exact repository H1, repository-specific `ATLAS SYSTEMS //` banner, branded badge treatment, `## How it fits into Atlas Systems`, and the atlas-systems.uk footer. The GitHub profile repository is a deliberate special case with its existing 120-pixel icon and `# Atlas Reaper` heading.

`## How it fits into Atlas Systems` must be the final H2 section and the Atlas Systems footer must be the final non-empty README line. This keeps the checked contract aligned with the canonical README style guide rather than validating only the presence of individual markers.

The contract also rejects the portfolio wording prohibited by the README style guide and rejects em dashes in README prose.

## Public README audit

`.github/workflows/repository-readme-audit.yml` provides a README-only audit for the approved public projection. It is useful during W2.1 because metadata and label findings do not obscure README completion. Manual dispatch supports `advisory` and `enforce` modes.

The workflow reads only repositories already present in `policy/public-repository-classifications.json` and retains a bounded JSON and Markdown report.

## Private README validation

`.github/workflows/validate-private-readme.yml` is reusable from source-owned private repositories. It checks out the caller repository, then checks out the exact Atlas Infra workflow revision identified by `job.workflow_sha` and runs the same README policy against the caller's local `README.md`.

The private validation path has `contents: read` only. It does not enumerate account repositories, publish a private repository list, alter provider state, or upload a cross-estate private inventory.

Repositories that are intentionally excluded from Atlas portfolio presentation remain outside this README rollout through their source-owned governance decision; they are not named in public policy.

## GitHub metadata contract

Every approved public repository must have:

- public visibility;
- `main` as the default branch;
- a non-empty bounded description;
- an HTTPS homepage on `atlas-systems.uk` or one of its subdomains;
- the `atlas-systems` topic;
- a GitHub archived state consistent with the declared lifecycle.

The policy does not infer a repository's lifecycle from GitHub metadata. Atlas Infra classification remains authoritative and GitHub metadata must conform to it.

## Pull request status labels

Atlas-specific labels exist only for states GitHub does not already model directly:

- `status:blocked`;
- `status:live-verified`;
- `status:owner-review`;
- `status:rollout-pending`;
- `status:superseded`.

Draft state, CI state, and merge state remain native GitHub facts and are intentionally not duplicated as labels.

## Audit and enforcement

`.github/workflows/repository-hygiene-audit.yml` is read-only. It queries only repositories named in the public classification projection, reads README content, public repository metadata, and labels, then emits a sanitized JSON and Markdown report.

The scheduled run is advisory while Wave 2 remediation is in progress. Manual dispatch supports `advisory` and `enforce` modes. Once the estate is clean, the workflow can be switched to scheduled enforcement in a separate reviewed change.

No audit path changes repository descriptions, topics, labels, archive state, branches, READMEs, or provider resources.
