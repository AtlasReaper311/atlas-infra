# Repository hygiene governance

Wave 2 turns Atlas Systems repository presentation from convention into an auditable contract without creating a second repository authority.

## Authority

`policy/public-repository-classifications.json` remains the allowlist of intentionally public repositories. Public hygiene and metadata audits consume that projection and never enumerate account membership. A public GitHub repository that is not in the projection is not silently admitted into Atlas portfolio governance.

`policy/repository-hygiene.json` owns README, GitHub metadata, and PR-status-label presentation rules.

Private repository identities remain source-owned. Private repositories call reusable validators from their own authenticated workflows; Atlas Infra does not add those identities to the public classification projection or public audit reports.

## README contract

Standard repository READMEs must preserve the Atlas icon, exact repository H1, repository-specific `ATLAS SYSTEMS //` banner, branded badge treatment, `## How it fits into Atlas Systems`, and the atlas-systems.uk footer. The GitHub profile repository is a deliberate special case with its existing 120-pixel icon and `# Atlas Reaper` heading.

`## How it fits into Atlas Systems` must be the final H2 section and the Atlas Systems footer must be the final non-empty README line. This keeps the checked contract aligned with the canonical README style guide rather than validating only the presence of individual markers.

The contract also rejects the portfolio wording prohibited by the README style guide and rejects em dashes in README prose.

## Public README audit

`.github/workflows/repository-readme-audit.yml` provides a README-only audit for the approved public projection. Manual dispatch supports `advisory` and `enforce` modes.

The workflow reads only repositories already present in `policy/public-repository-classifications.json` and retains a bounded JSON and Markdown report.

## Private README validation

`.github/workflows/validate-private-readme.yml` is reusable from source-owned private repositories. It checks out the caller repository, then checks out the exact Atlas Infra workflow revision identified by `job.workflow_sha` and runs the same README policy against the caller's local `README.md`.

The private validation path has `contents: read` only. It does not enumerate account repositories, publish a private repository list, alter provider state, or upload a cross-estate private inventory.

Repositories intentionally excluded from Atlas portfolio presentation remain outside this rollout through their source-owned governance decision; they are not named in public policy.

## GitHub metadata contract

Every approved public repository must have:

- public visibility;
- `main` as the default branch;
- a non-empty description of at most 160 characters;
- an HTTPS homepage on `atlas-systems.uk` or one of its subdomains;
- the required `atlas-systems` topic;
- between one and eight topics total;
- only topics from the controlled Atlas Systems vocabulary in `policy/repository-hygiene.json`;
- a GitHub archived state consistent with the declared lifecycle.

Descriptions follow the same restrained language rules as README prose: no prohibited portfolio wording and no em dashes.

The policy does not infer a repository's lifecycle from GitHub metadata. Atlas Infra classification remains authoritative and GitHub metadata must conform to it.

## Public metadata audit

`.github/workflows/repository-metadata-audit.yml` is the metadata-only W2.2 proof path. It queries only repositories in the canonical public projection and reports description, homepage, topic, visibility, default-branch, and archive-state drift without mixing in README or PR-label findings.

Manual dispatch supports `advisory` and `enforce` modes. Reports contain only approved public repository identities and are retained for 30 days.

## Private metadata validation

`.github/workflows/validate-private-metadata.yml` provides the equivalent source-local check for governed private repositories.

The workflow reads the caller's `.atlas/governance.json`, requires `visibility=private` and `public_projection=false`, verifies the caller repository identity, and queries only `github.repository`. The caller's lifecycle remains the archive-state authority.

Private metadata evidence remains in the private caller repository. The workflow does not create or upload a cross-estate private repository inventory.

## Pull request status labels

Atlas-specific labels exist only for states GitHub does not already model directly:

- `status:blocked`;
- `status:live-verified`;
- `status:owner-review`;
- `status:rollout-pending`;
- `status:superseded`.

Draft state, CI state, and merge state remain native GitHub facts and are intentionally not duplicated as labels.

## Audit and enforcement

`.github/workflows/repository-hygiene-audit.yml` remains the combined read-only estate audit. It queries only repositories named in the public classification projection, reads README content, GitHub repository metadata, and labels, then emits a sanitized JSON and Markdown report.

The scheduled combined run remains advisory while Wave 2 remediation is in progress because W2.3 label findings are intentionally still open. Metadata can be proven independently through the metadata-only workflow without weakening that separation.

No audit path changes repository descriptions, topics, labels, archive state, branches, READMEs, or provider resources. GitHub metadata writes remain explicit owner actions performed separately from read-only evidence collection.
