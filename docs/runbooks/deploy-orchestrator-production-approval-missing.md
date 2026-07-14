# Deploy orchestrator: production approval missing

## Trigger

A production dispatch is requested without a separately recorded human gate.

## Recover

Return to dry-run. Prefer protected-environment reviewers. If that feature is
unavailable, follow the approved documentation-only fallback: one owner reviews
and records the immutable plan, then a second owner separately dispatches the
target workflow. Do not emulate approval with a boolean input or bypass an
environment.

