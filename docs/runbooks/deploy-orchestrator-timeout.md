# Deploy orchestrator: timeout

## Trigger

A future bounded preflight, deploy workflow, or release-watch operation exceeds
its policy timeout.

## Recover

Mark the state unknown, stop dependants, and inspect the target workflow before
retrying. A timeout does not prove failure or success. Do not start a duplicate
run until the original run is terminal or cancelled by an owner. Create a new
dry-run plan before retrying.

