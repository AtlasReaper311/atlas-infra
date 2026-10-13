# Ramone and RAG deployment control plane

This directory is the proposed source-of-truth for the private Ramone memory,
atlas-corpus, ollama-rag-kit, and Qdrant deployment. It is source configuration
only. It does not change the currently running Compose projects.

The intended runtime directories are:

- `U:\runtime-deployments\rag-estate` for checked-out, reviewed deployment files.
- `U:\runtime-secrets\rag-estate` for local-only environment files and TLS material.

Neither directory is created by this change. The first directory must be owned
by the deployment owner. The second must be owner-only and must never be added
to Git, printed, or copied into chat.

The steady-state file publishes only the application ports on loopback. Qdrant
has no host port and lives on an internal Docker network. Each application must
receive an immutable image reference, a Qdrant API key, a CA path, and its
existing application secret through the protected local environment files. The
Compose definition maps the protected `QDRANT__SERVICE__API_KEY` input to the
applications' required `QDRANT_API_KEY` name at runtime. This keeps one key in
the protected source and avoids placing or duplicating its value in source
control.

When invoking Compose, pass the protected Qdrant environment file as an
interpolation input as well as the `RAG_SECRET_ROOT` runtime configuration, for
example with `--env-file U:\runtime-secrets\rag-estate\qdrant.env`. Use
`docker compose config --quiet` for validation so the resolved environment is
never rendered into logs or diagnostics.

`compose.freeze.yaml` is an explicit maintenance overlay. When applied, all
three applications receive `WRITE_FREEZE=true`. Health, dependency checks, and
read-only inspection remain available; memory, corpus, session, refresh, and
failure-capture writes fail with `503` and `write_frozen`.

Migration tooling is not part of this Compose project and is disabled by
default. Existing Chroma volumes remain outside this control plane and are
retained for rollback until a separately approved acceptance decision.

The U: TLS directory is the protected source of certificate material. Because
the runtime uses non-root containers, the approved installation step must copy
the three TLS files into the Docker-managed `rag-estate_qdrant-tls` volume and
set readable-but-not-writable permissions before Compose starts. The Compose
file mounts that volume read-only and never binds Windows TLS files directly.

The current Qdrant candidate digest is recorded as evaluation evidence, not as
proof of a current registry publication. Preflight must re-verify the image
reference and all application image digests before any runtime action.
