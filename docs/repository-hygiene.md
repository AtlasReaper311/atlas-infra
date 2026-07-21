# Repository hygiene governance

Wave 2 turns Atlas Systems repository presentation from convention into an auditable contract without creating a second repository authority.

## Authority

`policy/public-repository-classifications.json` remains the allowlist of intentionally public repositories. The hygiene auditor consumes that projection and never enumerates account membership. A public GitHub repository that is not in the projection is not silently admitted into Atlas portfolio governance.

`policy/repository-hygiene.json` owns presentation rules for the repositories already approved by that projection.

## README contract

Standard repository READMEs must preserve the Atlas icon, exact repository H1, repository-specific `ATLAS SYSTEMS //` banner, branded badge treatment, `## How it fits into Atlas Systems`, and the atlas-systems.uk footer. The GitHub profile repository is a deliberate special case with its existing 120-pixel icon and `# Atlas Reaper` heading.

The contract also rejects the portfolio wording prohibited by the README style guide and rejects em dashes in README prose.

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
