# GitHub Projects Operating Boards

`atlas-infra` owns the source automation for the private Atlas operating boards
under `AtlasReaper311` GitHub Projects.

## Estate Rollout Board

Tracks active pull-request rollouts across the bounded Atlas repository set.

- `Status` is derived from pull-request state.
- `Stage` is derived from draft state, merge state, and approval-gate markers.
- `Pillar` is derived from the repository map in `policy/estate-rollout-board.json`.
- `Attention` highlights waiting approvals, stale work, or review-ready work.
- `Stale Days` counts days since the pull request was last updated, or since it closed.
- `Evidence` records the repository, pull-request number, and latest update date.

Done items are retained for 3 days and then archived by the scheduled sync.
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

The scheduled workflows use `ATLAS_PROJECTS_TOKEN` and run in dry-run mode before
applying changes. Manual dispatch keeps `apply` false by default.

Expected local validation before changing these boards:

```bash
python3 -m py_compile scripts/estate_rollout_board.py scripts/model_promotion_coverage.py
python3 -m unittest scripts.tests.test_estate_rollout_board scripts.tests.test_model_promotion_coverage -v
```
