# Reliability: source unavailable or malformed

Use this runbook when a service's reliability state is `unavailable_source` or `malformed_evidence`: the counters or the published policy are missing, unreadable, or structurally invalid, so no verdict can honestly be derived.

## Safe triage

1. Read the reasons array on the service entry at `/v1/reliability/services/<service_id>`. It names the exact condition: a missing component, a missing counters document, a missing policy, or the specific malformed day bucket.
2. For a missing policy: confirm the last `reliability-policy.yml` workflow run in atlas-infra succeeded and that atlas-api-public accepted the publish (the run log records changed or unchanged plus the fingerprint; the fingerprint is safe to read).
3. For a missing component: the objective's `measurement_source.component` must match a component name that the atlas-api-public estate pass actually probes. A rename on either side without the other is the usual cause.
4. For malformed counters: the evaluator names the day and the violation. Counters are only written by the probe cron, so corruption usually means a partial KV write or a manual edit; the malformed day ages out of the window on its own.

## Recovery

Fix the named condition at its owner: policy problems in atlas-infra, probe and counter problems in atlas-api-public. Nothing should fabricate a bridge value; `unavailable` is the correct public answer until the source is genuinely back.

## Escalation and rollback

Reverting the most recent change to whichever side broke the pairing (objective component name, or probe component list) restores the previous working state. Both sides are in Git; neither requires touching live KV.
