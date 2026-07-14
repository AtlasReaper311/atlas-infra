# Control-plane contract validation runbook

Owner: `AtlasReaper311/atlas-infra`

Assurance consumer: `AtlasReaper311/atlas-dep-audit`

## Trigger

Use this runbook when the local validator, estate-policy workflow, or dependency
audit reports a control-plane schema, fixture, fingerprint, compatibility, or
idempotency failure.

## First diagnostics

```bash
python3 scripts/validate_control_plane_contracts.py
python3 -m unittest discover -s scripts/tests -v
git diff -- contracts scripts/control_plane_contracts.py scripts/validate_control_plane_contracts.py
```

Commands in `RunbookIndexEntry` and `RemediationProposal` are inert text. No
consumer may execute them without a separate allowlist and approval boundary.

## Failure modes

- **Schema inventory mismatch:** restore the missing v1 schema or move a
  breaking replacement into a new major path.
- **Positive fixture fails:** update the producer-shaped fixture or schema; do
  not weaken a required field merely to turn the check green.
- **Negative fixture passes:** restore the rejected constraint or add a semantic
  validator rule with a targeted failure test.
- **Fingerprint mismatch:** calculate from `fingerprint-rules.json`; do not edit
  the digest by intuition or add timestamps to identity inputs.
- **Idempotency failure:** remove timestamps, absolute paths, unordered input,
  or nondeterministic serialization from the validation report.
- **Assurance adapter failure:** confirm `atlas-infra` is the allowlisted source,
  the canonical validator exists, and no credential variable is passed to the
  subprocess.

## Rollback

Before merge, discard or close the unmerged feature branch after review. After
both changes merge, revert the `atlas-dep-audit` consumer commit first, then
revert the focused contract commit in `atlas-infra`. That order prevents the
fail-closed adapter from observing a missing canonical contract directory. Keep
both prior v1 readers and writers in place until the revert is complete. No
deployment rollback is required because Phase 1 creates no runtime or route.
