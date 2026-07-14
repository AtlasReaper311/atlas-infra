# Deploy orchestrator: release-watch mismatch

## Trigger

Release watch reports a repository, commit, service, or environment mismatch.

## Recover

Stop dependent deployments. Compare the immutable plan and target workflow run
with the public metadata response and ReleaseEvidence. Treat short SHAs,
display versions, and missing identity as insufficient. The owner chooses a
forward fix or repository-owned rollback; the orchestrator does neither.

