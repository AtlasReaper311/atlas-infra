# Backup audit: unsafe restore path

Use this runbook when a path is absolute, traverses upward, contains a symlink, escapes the fixture root, targets an existing destination, or carries executable archive mode bits.

## Safe triage

1. Stop the drill; do not bypass the refusal.
2. Inspect only the declared relative path and archive member names.
3. Confirm the policy uses `system-temporary-directory` and does not contain a command or live location.

## Recovery

Replace unsafe fixture paths with simple repository-relative POSIX paths. Regenerate malicious or malformed archives from reviewed synthetic inputs. Never allow existing application, provider, home, or repository directories as restore destinations.

## Escalation and rollback

Escalate suspicious archive content as a security finding. Remove or revert the unsafe fixture; no extraction into live data is permitted.
