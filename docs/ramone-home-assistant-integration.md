# Ramone and Home Assistant control-plane integration

Status: Phase 9 repository implementation, disabled by default and not
deployed.

## Architecture and ownership

The integration is additive and has three owners:

- `atlas-infra` owns the `ControlPlaneSummary` contract, deterministic local
  aggregator, exact sensor/tool policy, generated fixtures, inventory,
  rollout gates, and rollback guidance.
- `ramone-memory` owns a separate sensor-only Home Assistant package and
  dashboard example. It does not change the existing memory proxy, legacy
  dashboard, Assist exposure, or any device control.
- `atlas-api-public` owns a fixture/KV-backed external HTTPS OpenAPI read
  surface. It performs no provider call and adds no writer, schedule,
  deployment, or automatic OpenWebUI assignment.

OpenWebUI remains the owner-controlled Ramone interface. Existing identity,
prompt, model, memory, Home Assistant/light control, device tools, SPECULAR
status/tools, phone/watch tools, wake word, Wyoming STT/TTS, and spoken
behavior remain on their prior paths.

```text
committed local reports/fixtures/policies
                  |
                  v
      deterministic ControlPlaneSummary
             /                    \
            v                      v
  Home Assistant package      atlas-api-public
  10 read-only sensors        9 bearer-protected GET tools
            |                      |
       dashboard only       disabled OpenWebUI connection later
```

No model receives GitHub, Cloudflare, Home Assistant, SSH, backup, provider,
deployment, or secret credentials.

## ControlPlaneSummary aggregation

`scripts/control_plane_summary.py` reads only these allowlisted local JSON
filenames from the directory supplied with `--sources`:

- `health.json`
- `journeys.json`
- `release.json`
- `contract-registry.json`
- `quota.json`
- `findings.json`
- `gardener-proposals.json`
- `secret-watch.json`
- `backups.json`
- `runbooks.json`
- `evidence.json`

It performs no discovery or network call. The caller supplies `--now`, and the
request ID is derived from canonical input, so repeated runs are byte
identical. A missing source becomes `unknown`, malformed input becomes
`unavailable`, and expired input becomes `stale`. Aggregate precedence is
`failed`, `unavailable`, `stale`, `warning`, `unknown`, `healthy`.

```bash
python3 scripts/control_plane_summary.py \
  --sources tests/fixtures/control-plane-summary/sources \
  --now 2026-07-14T10:30:00Z \
  --output /tmp/control-plane-summary.json
```

Phase 9 adds optional `journeys`, `contract_registry`, and
`gardener_proposals.open_pull_requests` projections within v1. Earlier v1
summaries remain valid; missing optional projections remain unknown.

## Home Assistant sensor design

The disabled package example makes one five-minute public summary request and
fans it out to exactly these sensors:

- `sensor.atlas_estate_health`
- `sensor.atlas_failed_journeys`
- `sensor.atlas_release_state`
- `sensor.atlas_contract_drift`
- `sensor.atlas_quota_level`
- `sensor.atlas_quota_projection`
- `sensor.atlas_open_gardener_prs`
- `sensor.atlas_secret_hygiene`
- `sensor.atlas_backup_freshness`
- `sensor.atlas_latest_evidence`

The package contains no service call, REST command, script, automation,
button, switch, light, device control, or credential. Entity exposure to
Assist is never automatic. The dashboard is an example using standard cards
that stack on mobile and remain readable on desktop.

The existing package already represents `sensor.atlas_estate_health`.
Therefore the Phase 9 package must not be loaded beside it until the owner
reviews the live entity registry and chooses a collision-free migration.
Repository fixture rendering does not create that collision.

## Atlas tool group

The dedicated OpenAPI document contains exactly nine GET operations:

- `GetEstateSummary`
- `GetServiceStatus`
- `GetReleaseStatus`
- `ListActiveFindings`
- `GetQuotaProjection`
- `GetBackupStatus`
- `ListGardenerProposals`
- `FindRunbook`
- `SearchEvidence`

Inputs are allowlisted and bounded. There is no generic URL/method/body,
shell, command field, provider proxy, Home Assistant service call, GitHub or
Cloudflare mutation, deployment, merge, remediation, secret read, backup
restore, raw evidence dereference, or write method. Runbook search returns safe
summaries and references, not executable diagnostic commands. Evidence search
returns metadata and stable references only.

The API reads the injected local test fixture or the future bounded KV key
`control-plane:read-model:v1`. Phase 9 creates no producer or KV write. Invalid
or secret/private-bearing data fails closed with `503`. The API applies
positive response-field and public-reference allowlists and reclassifies an
expired KV read model as stale at read time.

## Authentication names

- `RAMONE_CONTROL_PLANE_READ_TOKEN`: future dedicated bearer for only the
  nine tool GET operations and their OpenAPI document; no provider scope.
- `WEBUI_SECRET_KEY`: existing OpenWebUI encryption key whose presence and
  stability must be verified before it stores an external-tool credential.

No value is created, read, printed, copied, committed, or passed to the model
in this phase. Home Assistant's public summary sensors need no credential.

## Non-goals and blocked actions

- no deployment, restart, reload, merge, or production mutation;
- no live Home Assistant/OpenWebUI edit or automatic tool assignment;
- no prompt, model, memory, Assist pipeline, entity exposure, voice, wake,
  STT, TTS, phone/watch, SPECULAR, light, or device-tool change;
- no provider API, generic network client, SSH, shell, backup content, restore,
  deployment, remediation, merge, or write tool;
- no secret creation, value access, or credential reuse;
- no Phase 10 runbook matcher or Phase 11 evidence ledger. Phase 9 exposes
  fixture-backed read projections only.

## Owner-gated rollout

Repository completion is not permission to run these steps.

1. Review and merge the three focused repository pull requests separately.
2. Complete the redacted read-only live inventory in
   `ramone-home-assistant-integration-inventory.md`: resolve OpenWebUI `3000`
   versus `8080`, locate the tool-pack source, inventory current tool schemas
   and assignments, identify the selected Assist conversation entity, and
   capture redacted configuration digests/rollback exports outside Git.
3. Implement and review a bounded producer for
   `control-plane:read-model:v1`. Prove schema, freshness, redaction, and
   source ownership. Do not add provider calls to the read route.
4. Create `RAMONE_CONTROL_PLANE_READ_TOKEN` through the approved secret
   mechanism and give it no provider permission. Confirm `WEBUI_SECRET_KEY`
   stability without reading or copying either value.
5. Deploy `atlas-api-public` only through its normal separately approved
   workflow. Verify the public summary, `401` failures, exact nine-operation
   spec, read-model outage, bounds, and no-write tests.
6. Run the Home Assistant fixture renderer. Inspect whether the legacy
   package/entity is live, choose the overlap migration, copy the Phase 9
   package/dashboard to owner-approved paths, and run Home Assistant's
   configuration check. Keep Assist exposure disabled.
7. Add the external HTTPS OpenAPI server to OpenWebUI in a disabled state.
   Store the bearer only in the administrator-owned connection. Verify the
   model never sees request headers or the token.
8. Confirm discovery of exactly the nine operation IDs and no other tool.
   Compare protected configuration digests before assigning anything.
9. After separate owner approval, expose exactly the ten sensors and assign
   only the new Atlas group to the existing Ramone identity. Do not remove,
   rename, wrap, or broaden an existing group.
10. Validate text first, then the existing voice path, all six states,
    credential/write refusals, outage behavior, mobile/desktop dashboard, and
    request bounds. Observe before removing any legacy example.

## Regression gates

Before live enablement, evidence must show:

- Ramone identity, prompt digest, model, knowledge/memory attachments, and
  spoken style are unchanged except for any separately reviewed additive
  guidance;
- `ramone-memory` routes, compose stack, model defaults, and stored memory
  behavior are unchanged;
- existing Home Assistant control/lights and Assist conversation selection
  are unchanged;
- existing SPECULAR, phone, and watch tool names/schemas/valves/assignments
  are unchanged;
- wake word, Faster Whisper/Wyoming STT, Wyoming/TTS target, satellites, and
  response media player are unchanged;
- disabling Atlas alone restores the prior behavior;
- local outages never halt cloud assurance or become healthy observations.

Repository tests snapshot the protected `ramone-memory` files. Live-only
capabilities cannot be claimed as tested until the owner supplies the redacted
inventory and runs harmless regression checks.

## Rollback

1. Disable the Atlas external tool-server assignment in OpenWebUI, then remove
   only that connection if needed.
2. Remove or disable only the Atlas Home Assistant sensor package and
   dashboard. Run Home Assistant's configuration check before any later
   owner-approved reload or restart.
3. Leave every existing Ramone tool, identity, prompt, model, memory path,
   Home Assistant control, SPECULAR tool, phone/watch tool, wake word, Wyoming
   component, and TTS target untouched.
4. Stop or remove the bounded read-model producer if it was enabled; do not
   delete source evidence.
5. Revert the three focused repository pull requests independently if needed.

The focused rollback runbook repeats the shortest safe sequence.

## Manual owner checklist

- [ ] All live unknowns in the inventory are resolved read-only.
- [ ] Protected configuration export and digests exist outside Git.
- [ ] Port, tool-pack source, Assist entity, Wyoming stages, and TTS target are
      confirmed.
- [ ] The bearer exists only in the gateway and encrypted OpenWebUI
      connection; the model sees no credential.
- [ ] Public/internal leak review and nine-operation allowlist pass.
- [ ] Home Assistant configuration check passes with no duplicate unique ID.
- [ ] Ten sensors only; no services/actions; Assist exposure remains explicit.
- [ ] Existing identity, prompt, model, memory, controls, device tools,
      SPECULAR, phone/watch, wake, STT, TTS, and spoken behavior pass.
- [ ] Atlas-only disablement and repository reverts have been rehearsed.
- [ ] Deployment, restart, reload, tool assignment, and secret creation each
      have separate explicit approval.

## Known limitations

- Repository evidence does not establish the live OpenWebUI port/version,
  current Ramone configuration, Assist selection, phone/watch/SPECULAR tool
  source, Wyoming configuration, TTS target, or tunnel ingress.
- Phase 9 has no deployed read-model producer, so a deployed route would
  honestly return unavailable until later approved work provides one.
- Fixture-backed runbook and evidence search are bounded API behavior, not the
  Phase 10 deterministic matcher or Phase 11 evidence ledger.
- Home Assistant Core validation against a pinned runtime and end-to-end
  voice/text regression require the owner-controlled live environment and are
  not run in this repository-only phase.
