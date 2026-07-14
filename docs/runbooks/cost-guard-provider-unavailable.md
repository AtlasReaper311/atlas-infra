# Cost guard: provider unavailable

## Trigger

The snapshot source explicitly reports unavailable or no usable quota data.

## Safe response

1. Distinguish timeout, authentication metadata, rate limit, and invalid response class.
2. Check only token presence/scope names; never print a value.
3. Retain prior evidence as stale if one exists and mark current state unavailable.
4. Retry only an approved idempotent read with the existing bounded timeout.

Do not add broad permissions, a generic HTTP client, or any billing/provider
write capability.
