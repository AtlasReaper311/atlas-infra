# Cost guard: malformed snapshot

## Trigger

A local snapshot fails the versioned structural or semantic checks.

## Safe response

1. Run `--validate-snapshots` against the same local input.
2. Correct the producer mapping, UTC timestamp, classification, or numeric field.
3. Confirm malformed content was not copied into findings or logs.
4. Re-run twice and compare the generated reports byte-for-byte.

Do not weaken the schema or mark the record healthy. The malformed record is
excluded from burn calculations.
