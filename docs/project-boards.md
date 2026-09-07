# GitHub Projects Operating Boards

`atlas-infra` owns the source automation for the private Atlas operating boards
under `AtlasReaper311` GitHub Projects.

## Estate Rollout Board

Tracks active pull-request rollouts across the bounded Atlas repository set.

- `Status` is derived from pull-request state. Merged pull requests remain `Done` as a workflow completion status, not as live proof.
- `Stage` is derived from draft state, merge state, and approval-gate markers. A merged pull request maps to `Merged` (ADR-0013 source integration only) and must not be labelled `Live / Verified` from merge evidence. Closed-unmerged pull requests remain `Closed - Not Merged`.
- `Pillar` is derived from the repository map in `policy/estate-rollout-board.json`.
- `Attention` highlights waiting approvals, stale work, or review-ready work.
- `Stale Days` counts days since the pull request was last updated, or since it closed.
- `Evidence` records the repository, pull-request number, and latest update date.

Done items are retained for 3 days. Scheduled syncs report proposed archival but do not mutate Project state; archival occurs only on a separately authorised manual apply run.
Dependabot and dependency-noise pull requests are intentionally excluded.

## Model Promotion and Eval Coverage

Tracks whether Atlas model-using capabilities have live-model evidence,
eval coverage, and promotion records.

- `Coverage Status` is computed from source evidence.
- `Action Needed` is computed from the coverage state.
- `Attention` highlights critical gaps, live/promoted mismatches, stale actions, and healthy rows.
- `Stale Days` counts how long the same open action has remained unchanged.
- `Evidence` records the source paths used to compute the row.

Repository config defaults are not the same as deployed runtime proof. Rows that
depend on documented defaults should keep that limitation visible until runtime
evidence is added.

## Maintenance

The Estate Rollout Board schedule is dry-run only. It validates the tooling and
publishes the proposed Project changes without applying them.

Project mutation requires an explicitly authorised manual `workflow_dispatch`
with `apply: true`. Manual dispatch keeps `apply` false by default. A scheduled
run must never apply Project changes merely because the schedule fired.

The workflow uses `ATLAS_PROJECTS_TOKEN`. Do not expose, print, or copy that
secret value.

Expected local validation before changing these boards:

```bash
python3 -m py_compile scripts/estate_rollout_board.py scripts/model_promotion_coverage.py
python3 -m unittest scripts.tests.test_estate_rollout_board scripts.tests.test_model_promotion_coverage -v
```
