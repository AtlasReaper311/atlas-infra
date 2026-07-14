# Deploy orchestrator: post-deploy journey failure

## Trigger

Release identity matches but a targeted `atlas-journey-watch` journey fails or
is unavailable.

## Recover

Stop the dependency chain and retain the Playwright report, trace, screenshot,
workflow URL, and ReleaseEvidence reference. Distinguish an explicit failure
from an unavailable local dependency. The service owner decides rollback or a
forward fix. Re-run release watch only after the underlying condition changes.

