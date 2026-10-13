# Write freeze

The freeze is application-level and reversible. It is not a database lock.

1. Record the planned freeze timestamp and operator.
2. Apply `compose.freeze.yaml` to the canonical control plane.
3. Verify all three application health responses report `write_frozen: true`.
4. Verify mutation routes return HTTP `503` with error `write_frozen`.
5. Verify health, search, index inspection, and dependency checks remain readable.
6. Verify no refresh task, memory reaper, session append, or failure-capture write
   is active before export.
7. If any write path remains active or a health check fails, stop and roll back the
   overlay before touching Chroma data.

The overlay must remain applied through export, import, validation, and cutover.
Removing it is a separate post-acceptance action.
