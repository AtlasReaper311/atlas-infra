# Reliability intelligence

The reliability layer turns the estate's existing probe counters into derived verdicts: error budgets, day-granular burn rates, coverage, freshness, and explicit failure states. The full design, ownership map and merge order live in `atlas-reliability-intelligence-plan.md`; this document is the operating reference.

## Ownership

- Canonical objectives: `policy/reliability/objectives/<service_id>.json`, one per measured service, validated by the `reliability-objective` v1 contract. Targets migrate unchanged from previously approved values or carry explicit owner approval in their provenance.
- Explicit unmeasured reasons: `policy/reliability/unmeasured.json`, one reviewed reason for every active runtime service without an objective.
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
| `unmeasured` | The service has no approved objective and carries an owner-reviewed reason | |

Precedence runs top to bottom of the failure conditions: malformed beats unavailable beats stale beats insufficient beats exhausted beats at risk. A missing measurement can never become a success.

## Unmeasured runtime review

The reliability policy intentionally separates observation from objective approval. A component having a ten-minute counter does not automatically grant it an SLO target.

The current eight active runtime services without objectives are explicitly reviewed:

| Service | Reason for remaining unmeasured |
|---|---|
| `atlas-api-public` | The evaluator runs inside the service; self-probing would not provide independent availability evidence. |
| `atlas-blackbox` | A ten-minute health counter exists, but no availability target has been owner-approved. The counter remains observational evidence. |
| `atlas-daily-digest` | Worker liveness would not prove successful scheduled digest delivery; no end-to-end delivery objective or journey is approved. |
| `atlas-dora` | A health route exists, but it is not in the current estate probe set and DORA correctness must not be inferred from liveness. |
| `atlas-quota-watch` | Its probe mixes reachability with quota-threshold policy, so the counter is not a pure availability indicator. |
| `ramone-edge` | Reachability is probed and sleeping local AI is intentionally healthy, but no edge availability target has been owner-approved. |
| `specular-sentinel` | Sentinel silence contributes to the machine verdict, but there is no independent sentinel probe; a direct objective would reuse derived evidence. |
| `specular-sonify` | No dedicated uptime probe or approved availability target exists. |

The policy validator requires this list to match the active runtime services without objective files exactly. A new runtime service cannot silently become generically unmeasured, and a measured service cannot remain in both sets.

The estate probe also records workflow-health components for `atlas-badges`, `atlas-dep-audit`, and `atlas-journey-watch`. Those are assurance signals rather than runtime ServiceContracts, so they do not enter the runtime reliability objective or unmeasured sets.

Adding an objective remains a separate owner decision. It requires an honest indicator, approved target, measurement-source mapping, objective file, `slo_refs` update, tests, regenerated projections, and a separate reliability-policy publish after merge.

## Pull-request validation

Changes under `policy/reliability/**`, the reliability policy schemas, `scripts/reliability_policy.py`, or reliability tests trigger the read-only Contract Registry CI workflow. That workflow compiles policy tooling and runs the control-plane unit suite without publishing anything.

The scheduled or manually dispatched `reliability-policy.yml` workflow is the only path that publishes the rendered policy to `atlas-api-public`. A source merge therefore does not prove that the live reliability policy has changed.

## Publish path

The `reliability-policy.yml` workflow validates everything, renders the policy document, and publishes it to `POST /v1/reliability/objectives/report` with `EVIDENCE_REPORT_KEY`. Publishing is idempotent: an unchanged canonical policy re-publishes as `changed: false`. The Worker treats policy older than eight days as gone and degrades every result to `unavailable_source`, keeping last-known values visible only as labelled stale history.

`generated_at` remains derived from objective approval timestamps rather than wall time. Changes to reviewed unmeasured reasons still change the canonical policy fingerprint, so a later approved publish updates the live explanation without inventing a new objective approval timestamp.

## Runbooks

- `docs/runbooks/reliability-budget-exhausted.md`
- `docs/runbooks/reliability-evidence-stale.md`
- `docs/runbooks/reliability-source-unavailable.md`
