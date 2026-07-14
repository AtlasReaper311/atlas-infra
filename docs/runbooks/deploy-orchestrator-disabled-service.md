# Deploy orchestrator: disabled service requested

## Trigger

The planner emits `disabled-service-requested` or `service-excluded`.

## Recover

Confirm the request used the intended stable service ID. Keep `simple-proxy`,
deprecated, archived, experimental, and external-derived repositories
excluded. For an intentionally disabled eligible service, review why it was
disabled before changing policy. Enabling requires a focused policy review and
does not enable dispatch execution.

