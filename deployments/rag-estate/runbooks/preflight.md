# Preflight

1. Confirm the deployment owner and the checked-out revision of this directory.
2. Confirm the current live Compose projects, Chroma volumes, and backup hashes.
3. Confirm the protected secret directory exists and is not inside a Git worktree.
4. Confirm the three application env files and `qdrant.env` exist. Report names
   only; never print values.
5. Confirm the TLS directory contains the approved CA, certificate, and private
   key with owner-only permissions. Do not create or rotate them in this run.
6. Confirm every image reference is `name@sha256:<64 hex characters>` and matches
   fresh publication evidence.
7. Run `docker compose config --quiet` with the runtime env file and verify that
   Qdrant has no host port and the private network is internal.
8. Keep the existing Chroma volumes stopped or isolated only under a separately
   approved cutover procedure. Do not delete them.

Failure of any step stops the rollout before a write freeze or data export.
