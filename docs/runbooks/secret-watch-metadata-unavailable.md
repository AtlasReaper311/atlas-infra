# Runbook: GitHub metadata unavailable

1. Confirm whether live mode is disabled, optional, or required. Disabled is
   not healthy; it means no comparison was attempted.
2. For 401/403, verify only the token's presence and selected-repository
   `Metadata: read` and `Secrets: read` scopes. Never echo the token.
3. For timeout/rate limit/server failure, retry the read-only job after the
   provider recovers. Do not change policy to hide the unavailable state.
4. Continue declaration and plaintext scanning offline. If metadata is
   required, keep the assurance result blocking until a complete list is read.

Rollback: disable optional live mode and retain explicit `disabled/unknown`
status. Do not widen token scope to force a green result.
