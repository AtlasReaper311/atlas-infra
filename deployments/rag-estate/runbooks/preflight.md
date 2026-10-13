# Preflight

1. Confirm the deployment owner and the checked-out revision of this directory.
2. Confirm the current live Compose projects, Chroma volumes, and backup hashes.
3. Confirm the protected secret directory exists and is not inside a Git worktree.
4. Confirm the three application env files and `qdrant.env` exist. Report names
   only; never print values.
5. Confirm `U:\runtime-secrets\rag-estate\tls` contains the approved CA,
   certificate, and private key with restricted permissions. Confirm the
   Docker-managed `rag-estate_qdrant-tls` volume is populated from that source
   and contains only the expected filenames with non-root-readable,
   non-writable permissions. Do not create or rotate credentials in this run.
6. Confirm every image reference is `name@sha256:<64 hex characters>` and matches
   fresh publication evidence.
7. Pass the protected `qdrant.env` file as a Compose interpolation input. This
   provides the server key once; `compose.yaml` maps its
   `QDRANT__SERVICE__API_KEY` name to the applications' required
   `QDRANT_API_KEY` variable without adding a second secret file or a value to
   source control. Run `docker compose config --quiet` with the runtime env
   file and protected Qdrant env file, and verify that Qdrant has no host port
   and the private network is internal. Never use rendered `docker compose
   config` output in logs or diagnostics.
8. Keep the existing Chroma volumes stopped or isolated only under a separately
   approved cutover procedure. Do not delete them.

Failure of any step stops the rollout before a write freeze or data export.
