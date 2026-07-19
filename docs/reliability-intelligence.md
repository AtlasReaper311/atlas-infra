# Reliability intelligence

The reliability layer turns the estate's existing probe counters into derived verdicts: error budgets, day-granular burn rates, coverage, freshness, and explicit failure states. The full design, ownership map and merge order live in `atlas-reliability-intelligence-plan.md`; this document is the operating reference.

## Ownership

- Canonical objectives: `policy/reliability/objectives/<service_id>.json`, one per measured service, validated by the `reliability-objective` v1 contract. Targets migrate unchanged from the previously approved `status/slo.json` values (see ADR-0002).
- Evaluator constants: `policy/reliability/evaluator-config.json`.
- Reference evaluator: `scripts/reliability_evaluator.py`, pure stdlib, offline.
- Runtime consumer: `atlas-api-public` vendors the same mathematics in `src/lib/reliability.js` and serves `/v1/reliability*`.
- Shared vectors: `tests/fixtures/reliability/vectors/`, pinned inputs and byte-exact expected outputs that both implementations must reproduce. The vectors, not prose, are the compatibility contract; change them only with a deliberate, reviewed reason.

## Commands

```bash
python3 scripts/reliability_policy.py validate
python3 scripts/reliability_policy.py emit-policy-document --output reports/reliability-policy.json
python3 scripts/reliability_policy.py emit-status-slo --output reports/status-slo-projection.json
python3 scripts/reliability_evaluator.py evaluate \
  --policy reports/reliability-policy.json \
  --uptime tests/fixtures/reliability/vectors/healthy/input.json \
  --now 2026-07-19T12:00:00Z
python3 scripts/incident_evidence_pack.py --help
python3 -m unittest scripts.tests.test_reliability_policy scripts.tests.test_reliability_evaluator scripts.tests.test_incident_evidence_pack
```

The evaluate example above expects a counters document; vector `input.json` files embed one under `uptime` together with the policy, so real invocations pass the two files separately.

## States

| State | Produced when | Never produced when |
|---|---|---|
| `objective_met` | Fresh, sufficient samples with budget above every risk threshold | Any evidence is missing |
| `budget_at_risk` | Fast burn at or above 2.0, slow burn at or above 1.5, or remaining budget at or below 25 percent | Samples are below minima |
| `budget_exhausted` | Remaining budget at or below zero over the window | The window lacks minimum samples |
| `insufficient_evidence` | Fewer than 288 window samples | |
| `stale_evidence` | Counters confirmed longer ago than the freshness bound, or the newest bucket is older than one day | |
| `unavailable_source` | Counters, component, or published policy missing | |
| `malformed_evidence` | Structural violations in day buckets | |
| `unmeasured` | The service has no approved objective | |

Precedence runs top to bottom of the failure conditions: malformed beats unavailable beats stale beats insufficient beats exhausted beats at risk. A missing measurement can never become a success.

## Publish path

The `reliability-policy.yml` workflow validates everything, renders the policy document, and publishes it to `POST /v1/reliability/objectives/report` with `EVIDENCE_REPORT_KEY`. Publishing is idempotent: `generated_at` derives from objective approvals, so an unchanged policy re-publishes as `changed: false`. The Worker treats policy older than eight days as gone and degrades every result to `unavailable_source`, keeping last-known values visible only as labelled stale history.

## Runbooks

- `docs/runbooks/reliability-budget-exhausted.md`
- `docs/runbooks/reliability-evidence-stale.md`
- `docs/runbooks/reliability-source-unavailable.md`
