# Cost guard

## Architecture and ownership

`atlas-infra` owns the versioned policy, thresholds, classification decisions,
examples, and response runbooks. `atlas-quota-watch` owns snapshot validation,
quota calculations, burn-rate and projection logic, Finding production,
evidence production, and the offline CLI. `atlas-dep-audit` is not changed by
Phase 5.

The Phase 5 implementation is deliberately read-only and advisory-only. It
reads local policy and snapshot JSON, produces local JSON/Markdown reports,
and describes notification eligibility in dry-run records. It has no provider
write client, billing mutation, deployment path, service-shutdown action,
issue-creation client, secret access, or generic HTTP fetcher.

## Policy format

The canonical declaration is [`../policy/cost-guard.json`](../policy/cost-guard.json)
and its JSON Schema is
[`../policy/cost-guard.schema.json`](../policy/cost-guard.schema.json). Each
service/quota entry declares:

- stable service and repository IDs, provider, quota type, unit, and whether
  the measurement is a cumulative counter or point-in-time gauge;
- the included `free_tier_limit` used as the no-marginal-cost allowance;
- warning and critical percentages, projection horizon, cooldown, maximum data
  age, and acceleration threshold;
- owner plus route/worker references when applicable;
- independent lifecycle, scope, and provenance classifications;
- whether assurance and notification are enabled, whether issue creation is
  allowed, and the mandatory advisory-only valve.

The field name `free_tier_limit` is retained as the policy contract requested
for Phase 5. For the current Workers Paid account it records the included
allowance before marginal overage, not a claim that the account is on a free
plan. Pricing and allowances remain owner-reviewed configuration.

All canonical entries are `advisory_only: true` and
`issue_creation_allowed: false`. Notifications are policy-eligible only for
active meters; Phase 5 reports them as dry-run decisions and does not send.

`simple-proxy` remains declared only to make the exclusion auditable. It is
deprecated, internal, external-derived, excluded from active assurance, and
cannot notify or create an issue.

## Snapshot and state model

`atlas-quota-watch` accepts versioned snapshots containing current usage,
optional observed quota limit, UTC evidence timestamp, period boundaries,
availability, source metadata, classification, and confidence. The policy
limit is used only when the snapshot does not supply one. Producers may also
supply a previous-period usage value and at most ten redacted contributors;
the report calculates the comparison and displays the five largest contributors
in stable usage/ID order. Missing optional comparison data remains unavailable.

The current state vocabulary is the Phase 1 shared set:

| State | Cost-guard meaning |
|---|---|
| `healthy` | Fresh, valid, sufficiently evidenced data is below all risk conditions. |
| `warning` | A warning threshold, projected exhaustion, or material acceleration is proven. |
| `failed` | A critical threshold, malformed snapshot, or classification conflict is proven. |
| `stale` | The last valid evidence is older than the policy freshness window. |
| `unavailable` | The source explicitly reports no usable quota data. |
| `unknown` | History, ownership, service identity, or quota limit is insufficient. |

Missing, stale, unavailable, or malformed input is never converted to
`healthy`. Aggregate precedence is `failed`, `unavailable`, `stale`,
`warning`, `unknown`, then `healthy`. Explicitly excluded policy entries do not
degrade the active aggregate. Every state includes bounded recommended next
steps, but those recommendations cannot execute an action.

## Burn rate and projection

For cumulative counters, fixed-window burn is current usage divided by elapsed
days since the declared period start. Rolling-window burn is the non-negative
usage change between the oldest and newest valid snapshots divided by their
UTC time separation. Rolling burn is selected when at least two samples exist;
otherwise the fixed calculation is displayed but the history status and meter
state are `insufficient-history`/`unknown`.

Projected exhaustion is `remaining allowance / selected daily burn`, added to
the latest evidence timestamp. A finding is emitted only when that date is
inside the configured horizon. Point-in-time gauges report current percentage
but are not projected as cumulative burn.

Acceleration compares the latest interval burn with the immediately preceding
interval when at least three samples exist. It is a deterministic comparison,
not a statistical anomaly model. Zero/negative deltas are clamped to zero;
missing intervals or a zero prior rate are reported explicitly without an
invented percentage. No confidence interval or causal claim is made.

## Findings, evidence, cooldown, and deduplication

Every finding uses `contracts/v1/finding.schema.json`. Its fingerprint follows
the canonical Phase 1 selected-field rule and is independent of timestamps and
JSON object order. Output is sorted by service/provider/quota and fingerprint.

The JSON report contains an inline `EvidenceEnvelope` whose SHA-256 digest is
calculated over its canonical payload and validated against the Phase 1
evidence contract when the sibling `atlas-infra` checkout is available.

Notification candidates are inert records. One candidate consolidates all
Finding fingerprints for one meter/state transition, and its deduplication key
is a SHA-256 of that stable state key and state. A previous report suppresses
the same meter/state inside the policy cooldown; a changed state or expired
cooldown becomes eligible again. Every candidate records `dry_run: true`,
`network_send: false`, and `issue_creation: false`.

## Offline fixture mode

From `atlas-quota-watch`:

```bash
node scripts/cost-guard.js \
  --policy ../atlas-infra/policy/cost-guard.json \
  --fixture test/fixtures/cost/healthy.json \
  --report /tmp/cost-report.json \
  --markdown /tmp/cost-report.md
```

Policy and snapshot-only validation are also available:

```bash
node scripts/cost-guard.js --policy ../atlas-infra/policy/cost-guard.json --validate-policy
node scripts/cost-guard.js --policy ../atlas-infra/policy/cost-guard.json --fixture test/fixtures/cost/healthy.json --validate-snapshots
```

Fixture files carry an explicit evaluation timestamp so repeated runs are
byte-for-byte deterministic. Directory mode reads local `*.json` snapshots in
lexical order. No command performs a network request.

## Future live-provider integration

Phase 5 does not add live reads or storage. A future approved integration may
adapt the existing read-only Cloudflare analytics result into the snapshot
contract and supply bounded historical snapshots from an already approved
low-cost store. That work must retain Account Analytics Read only, add no
billing or provider write permission, prove bounded retention, and keep the
offline evaluator as the acceptance oracle. It must not add a generic URL
fetcher.

Until that adapter is approved, the existing `/quota` Worker continues reading
its limits from `wrangler.toml`, while the offline cost guard reads the canonical
policy from `atlas-infra`. The values currently agree, but automatic drift
reconciliation is not part of Phase 5 and neither file may silently overwrite
the other.

Live notification wiring is also deferred. If approved later, it must consume
only dry-run candidates after cooldown/deduplication, use the existing
`atlas-notify` path, redact source metadata, and have a network-free test mode.
Issue creation remains a separate human-approved gate.

## Failure modes and rollback

Malformed or missing policy is a validation failure. Malformed snapshots emit
Finding-compatible failure evidence without echoing raw content. Stale or
unavailable sources remain explicit. Insufficient history remains unknown.

Rollback is source-only: revert the `atlas-quota-watch` Phase 5 files and the
`atlas-infra` policy/docs branch. No provider state, quota, billing setting,
secret, route, deployment, notification destination, or issue tracker state is
created by this phase. The existing `/quota` analytics endpoint remains in
place; its only Phase 5 runtime change is correcting healthy meters that were
previously labelled `warning`.

See the focused runbooks in `docs/runbooks/cost-guard-*.md`.
