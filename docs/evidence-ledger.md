# Evidence ledger

The evidence ledger stores searchable metadata and source digests in a local SQLite database. It does not store raw evidence blobs, credentials, authorization headers, cookies, request bodies, private keys, or secret values.

Record IDs are deterministic. Re-ingesting the same source metadata is idempotent. Records expire according to the committed retention policy, initially 90 days.

The database location is an owner decision. Do not commit the SQLite file. Back it up only after a separate data-handling and retention review.
