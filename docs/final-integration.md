# Final control-plane integration

Phase 12 is the final build-phase gate. It checks that all control-plane components are present, their policies parse, the runbook index and evidence policy are valid, workflows remain hardened, and deferred live cutovers remain explicit warnings.

A warning result is expected while the Phase 9 API PR is draft-only, Home Assistant sensors are not installed, OpenWebUI tools are not assigned, and backup coverage includes explicit undeclared gaps.

The gate performs no deployment, provider mutation, secret creation, Home Assistant change, OpenWebUI change, or workflow dispatch.
