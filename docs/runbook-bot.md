# Runbook bot

The runbook bot is a deterministic, read-only matcher. It accepts a local structured event and returns ranked runbook metadata, bounded diagnostic guidance, manual commands, and blocked actions.

It never executes commands, contacts providers, reads secrets, deploys, rolls back, or mutates infrastructure. Every command returned by the bot is labelled `manual-owner-reviewed-only`.

The canonical contract objects live in `policy/runbook-index.json`. Every entry validates against `contracts/v1/runbook-index-entry.schema.json` without adding properties to that strict contract. Matching aliases and blocked-action guidance live separately in `policy/runbook-routing.json`, keyed by the contract's `entry_id`.

Additions require a pull request, a repository-relative runbook path, a valid escalation owner, and deterministic tests. `doctor` fails if a contract, route, or referenced runbook is missing.
