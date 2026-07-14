# Backup audit: malformed export

Use this runbook when policy, metadata, JSON, JSONL, manifest, or archive structure cannot be validated safely.

## Safe triage

1. Run `python3 -m json.tool` only against the declared synthetic JSON fixture.
2. Run the focused unit tests to identify the rejected field or shape.
3. Check record counts, file sizes, timestamps, and schema versions without opening private provider data.

## Recovery

Regenerate the fixture deterministically and update its digest. Do not relax parsing, traversal, symlink, executable, file-count, or size protections to accept malformed input.

## Escalation and rollback

Escalate an incompatible producer format to its owner. Revert the fixture or parser change if compatibility cannot be established.
