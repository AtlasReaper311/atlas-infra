# Secret watch

## Architecture and ownership

`atlas-infra` owns `policy/secret-watch.json`, its JSON Schema, this operating
guide, and the response runbooks. `atlas-dep-audit` owns enforcement through
the existing weekly assurance path. No new service, endpoint, database, or
paid dependency is introduced.

The declaration is names-only. It must never contain a credential value, a
value-derived hash, an authorization header, a cookie, a private key, or a
token-bearing URL. Findings conform to
`contracts/v1/finding.schema.json` and use fingerprints derived from stable
location and rule fields, never from suspected credential material.

## Threat model and no-values rule

Secret watch is designed to detect declaration drift and likely plaintext
credentials without becoming a secret reader.

- The GitHub adapter calls only metadata list endpoints for Actions secret
  names. It never calls a create, update, delete, or public-key endpoint and
  cannot retrieve plaintext values because GitHub does not return them.
- Credential-bearing environment variables are never enumerated or printed.
  The optional token is read by its fixed variable name and used only as an
  HTTP authorization header.
- The plaintext scanner reads tracked local text files, discards every matched
  substring immediately, and records only the repository, relative path, line,
  rule ID, redacted summary, and stable Finding fingerprint.
- API errors are reduced to bounded status/reason codes. Response bodies and
  headers are not copied into reports.
- Metadata absence, timeout, authentication failure, or insufficient
  permission is `unavailable`; it is never interpreted as compliant.
- Secret watch has no mutation code path. Rotation, revocation, replacement,
  and deletion are human procedures performed outside the audit.

Out of scope: proving a secret has the right value or provider permissions,
proving that an upstream credential was actually rotated, scanning Git
history, scanning untracked files, and replacing a dedicated secret scanner
with full history/entropy analysis.

## Declaration format

`policy/secret-watch.json` has four policy layers:

1. `github_metadata` states whether live names-only comparison is optional or
   required and records the GitHub secret *name* that carries the reader token.
2. `plaintext_scan` sets the tracked-file byte limit, approved fixture globs,
   inline suppression marker, and centrally reviewed suppressions.
3. `secret_definitions` records owner, purpose, lifecycle, provenance,
   replacement guidance, and rotation metadata once per secret name.
4. `repositories` binds those names to a full repository, classification,
   global repository scope (`environment: null`) or a named environment, and
   the required, optional, or deprecated set.

Supported stores are `github-actions`, `cloudflare-worker`, and
`external-provider`. Live mode compares only `github-actions` scopes. Other
stores remain declaration and rotation-policy inputs; the GitHub result must
not imply that provider metadata was checked.

Classification axes are independent: lifecycle, public/internal scope, and
original/external-derived provenance. Archived, deprecated, and
external-derived repositories must be explicitly excluded unless the owner
documents an exceptional assurance need. `simple-proxy` is fixed as
deprecated, internal, external-derived, and excluded from active assurance.

The initial attested names cover `atlas-infra` and `atlas-dep-audit`. The local
plaintext scan still covers every checked-out repository except explicit
exclusions. Other repositories must be added to names-only comparison only
after their owners classify required, optional, provider-runtime, and
deprecated names; committed references alone are observations, not authority
to invent desired policy.

## Add a secret name safely

1. Add the uppercase name to `secret_definitions`; add no value or example
   value.
2. Declare a named owner, one-sentence purpose, provenance, lifecycle, and
   rotation policy. A required rotation policy needs a positive
   `max_age_days`; `last_rotated_at` is optional owner-attested evidence.
3. Reference the name from exactly one required or optional list for the
   repository/store/environment scope.
4. Run the policy and fixture validation in `atlas-dep-audit` before making any
   provider-side change.
5. Have the owner create or rotate the provider secret through its protected
   interactive interface. Do not paste the value into Git, chat, a command
   line, a workflow input, or a report.

## Deprecate a secret name

1. Change the definition lifecycle to `deprecated`.
2. Add non-sensitive `replacement` guidance naming the successor or removal
   procedure.
3. Move the name from required/optional to `deprecated_secret_names` in every
   applicable scope.
4. Keep the declaration until names-only metadata proves the old name is gone
   everywhere it was declared. Removal of the old provider secret is a
   separate, human-approved action.

## Rotation metadata

`rotation.required` determines whether a manually declared maximum age is
mandatory. `max_age_days` is policy, not evidence that a rotation occurred.
`last_rotated_at` is an optional UTC owner attestation. When both are present,
secret watch reports overdue rotation after the declared interval. GitHub's
`updated_at` metadata is not substituted for upstream rotation evidence.

## Live GitHub metadata mode

Live mode is optional by default and tests never use GitHub. The selected
repository token needs only:

- repository `Metadata: read`;
- repository `Secrets: read`;
- access restricted to the repositories being checked.

No write scope is required or permitted. The configured secret name is
`SECRET_WATCH_GITHUB_TOKEN`; no token is created by this phase. A missing token
sets metadata to `disabled`. HTTP 401/403, timeout, rate limit, or an incomplete
response sets it to `unavailable`. When `metadata_required` is true for a
repository, unavailable metadata is blocking; otherwise the offline scan and
declaration checks continue and the result remains explicitly unknown.

## Plaintext scanning and suppression

Only paths returned by `git ls-files` are considered. Files containing NUL
bytes and files over the configured byte limit are skipped. Approved fixture
globs are skipped before reading. Findings never include the matched text or a
hash of it.

A false positive may be suppressed in one of two reviewable ways:

- add `secret-watch: ignore <rule-id>` on the same line; or
- add an exact repository/path/line/rule entry under
  `plaintext_scan.suppressions`, including owner and reason.

Suppress the narrowest line and rule possible. Do not suppress a whole
repository, generated directory, or broad extension. Moving a suppressed line
intentionally invalidates the central suppression so it receives review again.

## Emergency rotation procedure

1. Treat any suspected disclosure as compromised; do not inspect or repeat the
   value to decide whether it is real.
2. Identify the secret by declaration name, repository, environment/store, and
   owner only.
3. Revoke or rotate through the provider's protected interactive interface.
4. Update dependent systems, then verify the previous credential is rejected
   without printing either value.
5. Record `last_rotated_at` and any name migration in this policy without
   recording a value-derived artifact.
6. Run secret watch in offline mode and, when available, names-only metadata
   mode. Attach only redacted Finding fingerprints to incident evidence.

## False-positive procedure

Confirm the rule, path, and line without copying the match. Prefer changing a
fixture to an obviously constructed test value or moving it under the approved
fixture path. If the text is necessary, add a line-specific suppression with a
reason and owner, run the scanner twice to prove deterministic output, and
review the suppression in the pull request.

## Rollback

Revert the `atlas-dep-audit` integration first; the existing dependency,
provenance, OSV, and contract checks continue unchanged. The declaration then
remains inert version-controlled policy. Revert the policy/docs branch only if
the format itself is being withdrawn. Rollback never deletes or changes a
provider secret.

## Migration order

1. Review and merge the `atlas-infra` policy/schema/runbook branch first.
2. Rebase the `atlas-dep-audit` enforcement branch on current `main`; its CI
   intentionally fails closed if the canonical policy is not yet on
   `atlas-infra/main`.
3. Run fixture mode and the offline local audit before enabling optional live
   metadata.
4. If names-only comparison is wanted, create a selected-repository reader
   token outside this phase and store it under `SECRET_WATCH_GITHUB_TOKEN`.
5. Add further repository/environment declarations in small owner-attested
   policy changes; do not infer required state from a workflow reference alone.

## Runbooks

- [Missing required secret](runbooks/secret-watch-missing-required.md)
- [Deprecated secret still present](runbooks/secret-watch-deprecated-present.md)
- [Plaintext credential pattern](runbooks/secret-watch-plaintext-pattern.md)
- [Metadata unavailable](runbooks/secret-watch-metadata-unavailable.md)
- [Malformed declaration](runbooks/secret-watch-malformed-declaration.md)
- [Overdue rotation](runbooks/secret-watch-overdue-rotation.md)
