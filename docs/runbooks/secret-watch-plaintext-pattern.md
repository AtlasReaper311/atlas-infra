# Runbook: plaintext credential pattern

1. Do not print, copy, quote, hash, or paste the matched text. Use only the
   reported repository, path, line, rule ID, and fingerprint.
2. Treat a plausible match as compromised and notify the declared owner using
   names-only context.
3. Rotate/revoke through the provider's protected interface, remove the
   plaintext from the tracked file, and review Git history exposure separately.
4. If it is a false positive, follow the documented narrow suppression
   procedure and record owner/reason.
5. Re-run the scanner and verify the report contains no suspected value.

Rollback: revert only the code/config cleanup if it breaks behavior; never
restore an exposed credential value to the repository.
