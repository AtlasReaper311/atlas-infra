# Dependabot auto-merge runbook

## Scope

Use this runbook when an expected patch stays manual, an ineligible update is
approved, the OSV query cannot complete, or GitHub rejects the auto-merge
request. The policy owner is `atlas-infra`; repository-native CI remains owned
by the affected repository.

## Immediate safety action

Disable new automatic decisions for the affected repository without changing
tests, rulesets, or branch protection:

```bash
gh variable set DEPENDABOT_AUTOMERGE_ENABLED \
  --body false \
  --repo AtlasReaper311/atlas-journey-watch
```

An existing auto-merge request must be cancelled through the pull request UI
or GitHub API after confirming the exact pull request. Do not close or merge the
pull request as part of diagnosis.

## Evidence to collect

- Record the pull request URL, head SHA, dependency name, old and new versions,
  dependency type, update type, ecosystem, group name, and maintainer-change
  flag.
- Inspect the `Dependabot review policy` run and record the policy reason.
- Confirm the caller pins a complete `atlas-infra` commit SHA.
- Confirm `DEPENDABOT_AUTOMERGE_ENABLED` is exactly `true` only when intended.
- Inspect active rules for the default branch and confirm at least one
  repository-native required status check.
- Inspect every required check and its logs. A red or pending check is not an
  auto-merge policy defect.
- If the reason begins with `osv-`, query the same package and proposed version
  again. Treat an outage or malformed response as manual.

## Expected fail-closed outcomes

The policy must leave the pull request manual for production, indirect,
grouped, major, minor, `0.x`, Docker, Python, GitHub Actions, maintainer-modified,
non-npm, vulnerable, or unverified updates. A missing opt-in variable, OSV
timeout, OSV error, or invalid metadata also leaves it manual.

## Recovery

Fix the policy source or repository-native CI in a focused pull request. Run
the policy unit suite, parse modified workflow YAML, and keep the caller pinned
to the reviewed policy commit. Re-enable the repository variable only after the
repair pull request is merged and an ineligible test pull request remains
manual.

No recovery step may merge a pull request, relax a required check, bypass a
ruleset, enable a deployment, or add a broad credential.
