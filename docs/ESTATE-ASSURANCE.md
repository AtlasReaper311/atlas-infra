# Estate assurance

Atlas Systems now carries two central assurance workflows in `atlas-infra`.

## Change impact

`.github/workflows/change-impact.yml` is a reusable workflow. A caller passes the repository and pull request base and head commits. The workflow reads `estate.manifest.json`, maps the changed repository to declared components, follows reverse dependency edges, classifies the changed paths, and writes a Markdown blast-radius report to the workflow summary and an artifact.

Copy `templates/change-impact-caller.yml` into a repository as `.github/workflows/change-impact.yml`. The caller needs only `contents: read`.

The report does not comment on the pull request. This keeps the reusable workflow read-only and avoids granting pull request write permission across the estate.

## Estate policy

`.github/workflows/estate-policy.yml` runs every Monday and on demand. It enumerates the repository list from the canonical manifest and checks repository structure, npm lockfiles, workflow permissions, workflow timeouts, concurrency, immutable action pins, Worker metadata adoption, and portfolio-facing copy rules.

Errors fail the workflow. Warnings remain visible during adoption so existing repositories can be corrected deliberately rather than all at once. The full JSON and Markdown reports are retained for 90 days. One consolidated event is sent through `atlas-notify` when findings exist.

The workflow reuses `GH_DIGEST_PAT`, the existing read-only cross-repository token. It does not require a new GitHub credential.

## Security boundary

Both workflows read repository and manifest data. Neither deploys, edits a repository, opens an issue, posts a pull request comment, or changes estate state. The only outbound write is the optional consolidated assurance event to `atlas-notify`.
