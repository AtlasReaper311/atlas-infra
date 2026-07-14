# Ramone and Home Assistant integration inventory

Inventory date: 14 July 2026

Scope: Phase 9 repository evidence under `/Users/atlasreaper/Personal` only.
No live OpenWebUI database, Home Assistant runtime configuration, browser
profile, keychain, SSH material, credential store, secret value, or file
outside the workspace was read.

## Decision

Repository-only implementation can proceed safely in disabled fixture/shadow
mode. Live configuration or local runtime state is not required to add and
test the bounded contracts, fixture aggregator, sensor-only package example,
dashboard example, or fixture-backed read-only tool server. Live enablement is
blocked until the owner completes the later read-only checks listed below.

The existing Ramone identity, prompt, model, memory path, Home Assistant
control, device tools, SPECULAR status, phone/watch tools, wake word, Wyoming
STT/TTS, and spoken behavior remain outside the implementation boundary.

## Evidence inventory

### OpenWebUI and tool-pack source

- `atlas-corpus/docs/atlas-public-service-map.md` names a local Open WebUI
  service and an integrated `atlas-owui-tools` pack whose valves still need
  review.
- No source directory or repository for `atlas-owui-tools` exists under
  `~/Personal`.
- No committed OpenWebUI database, configuration export, external-tool-server
  definition, access assignment, or tool valve file was found.
- The supported OpenAPI connection mode and installed OpenWebUI version are
  unknown.

### Ramone prompt, model, memory, and assignments

- `ramone-memory/README.md`, `docker-compose.yml`, and `app/` define an
  Ollama-compatible memory proxy on port `8091`, with committed defaults for
  the chat and embedding model names. They do not prove the current live model
  or OpenWebUI assignment.
- `atlas-daily-digest/src/index.js` contains a digest-specific Ramone system
  prompt. It is not evidence of the live OpenWebUI system prompt.
- `atlas-infra/docs/decisions.md` records the Home Assistant selection gotcha:
  the Assist pipeline's selected conversation entity determines whether the
  `:8091` memory path is used instead of raw Ollama on `:11434`.
- The live Ramone identity, system prompt, model ID, knowledge attachments,
  tool groups, access assignments, and configuration digest are unknown.

### Home Assistant repository surface

`ramone-memory/integrations/home-assistant/estate-dashboard/` contains the
existing repository-owned examples:

- `atlas_estate_package.yaml`: read-only REST sensors polling public Atlas
  endpoints;
- `atlas_estate_dashboard.yaml`: one YAML Lovelace dashboard;
- `README.md`: manual copy and registration guidance.

The existing package represents these entity IDs:

- `sensor.atlas_estate_health`
- `sensor.atlas_active_incidents`
- `sensor.atlas_services`
- `sensor.atlas_estate_operational`
- `sensor.atlas_infra_overall`
- `sensor.atlas_slo_observations`
- `sensor.atlas_quota_highest_usage`
- `sensor.atlas_recent_events`

These files do not prove which entities are installed, enabled, exposed to
Assist, renamed in the entity registry, or selected by a live dashboard. The
Phase 9 package must therefore remain a disabled example and must not be
installed alongside the legacy package without an owner-reviewed migration
for the overlapping `sensor.atlas_estate_health` identity.

### SPECULAR-CORE status and tools

- `specular-sentinel` documents read-only local observation of Ollama, corpus
  health, corpus search, and WSL address drift, reported to
  `atlas-api-public`.
- `specular-telemetry` documents public-safe hardware/Ollama telemetry through
  `specular-tunnel.atlas-systems.uk` and an edge Worker.
- `atlas-api-public` currently exposes bounded SPECULAR/sentinel state through
  public stats and infra routes.
- The live OpenWebUI SPECULAR tool names, schemas, valves, and assignments are
  unknown and are not present in these repositories.

### Phone and watch tools

Phone/watch preservation is an owner-confirmed compatibility requirement in
`docs/control-plane-expansion-plan.md`. No phone/watch tool implementation,
schema, valve, entity list, or access assignment was found under `~/Personal`.
Their source owner and live configuration remain unknown. Phase 9 must not
claim to have runtime-regression-tested them and must not change any existing
tool group.

### Wyoming, wake word, STT, TTS, and satellites

`atlas-corpus/docs/atlas-public-service-map.md` records repository evidence
for:

- Faster Whisper over Wyoming on port `10300`;
- OpenWakeWord over Wyoming on port `10400`;
- Kokoro TTS on ports `10200` and `8880`;
- Home Assistant voice on port `8123`.

`atlas-daily-digest` separately documents a narrow Home Assistant webhook
handoff to the existing `tts.openai` and `media_player.specular_core` path.
No live Wyoming service/add-on configuration, satellite inventory, wake-word
selection, Assist pipeline, or current response media player is committed.

### OpenWebUI port discrepancy

- `atlas-corpus/docs/atlas-public-service-map.md` records Open WebUI on port
  `3000`.
- `atlas-systems/writing/ramone-local-ai-system/index.html` records the older
  container surface on port `8080`.

Repository evidence cannot determine the live port. No endpoint or connection
configuration may be applied until the owner resolves this drift read-only.

### Tunnel ingress and authentication

Repository documentation names these ingress surfaces:

- `ramone-tunnel.atlas-systems.uk` for the public Ramone retrieval upstream;
- `specular-tunnel.atlas-systems.uk` for public-safe SPECULAR telemetry;
- `corpus.atlas-systems.uk` for the estate corpus;
- `ollama-tunnel.atlas-systems.uk` for the Access-gated daily-digest path.

The repositories describe Cloudflare Access service-token headers for the
Ollama digest path, an origin secret for the Ramone public gateway, and bearer
keys for selected report routes. The live tunnel ID/name, ingress order,
origin targets, Access application/policy names, current scopes, and bindings
are unknown. Phase 9 does not read or change them.

### Configuration and secret names

Names observed in committed Phase 9-relevant files, without values:

- future tool connection: `RAMONE_CONTROL_PLANE_READ_TOKEN`,
  `WEBUI_SECRET_KEY`;
- `atlas-api-public`: `INFRA_REPORT_KEY`, `RAG_REPORT_KEY`, `NOTIFY_TOKEN`,
  `CF_WORKERS_DEPLOY_TOKEN`, `CF_ACCOUNT_ID`;
- `ramone-memory` configuration: `OLLAMA_HOST`, `CHAT_MODEL`, `EMBED_MODEL`,
  `CHROMA_HOST`, `CHROMA_PORT`, `COLLECTION_NAME`, `TOP_K`,
  `MAX_INJECTED_CHARS`, `SESSION_IDLE_SECONDS`, `REAPER_INTERVAL_SECONDS`,
  `RAW_TURNS_KEPT`, `SYSTEM_PROMPT`, `NUM_CTX`, `TEMPERATURE`, `LOG_LEVEL`;
- existing voice trigger: `TRIGGER_SECRET`, `GITHUB_TOKEN`, `NOTIFY_TOKEN`,
  `ramone_trigger_secret`;
- existing daily digest: `CF_ACCESS_CLIENT_ID`,
  `CF_ACCESS_CLIENT_SECRET`, `HA_DIGEST_WEBHOOK_URL`, `DIGEST_RUN_TOKEN`,
  `DIGEST_WEBHOOK_URL`, `NOTIFY_TOKEN`.

The names above do not prove presence, correctness, age, value, or live scope.
No existing credential is reused by the Phase 9 tool group.

## Unknowns requiring owner inspection before live enablement

The owner must provide or approve a redacted, read-only inventory of:

1. OpenWebUI version, connection mode, live port, enabled tool groups, access
   assignments, and supported external OpenAPI authentication handling.
2. Ramone model ID, system-prompt digest, knowledge/memory attachments, and
   tool names/descriptions/parameter schemas/valve names.
3. The source and owner of `atlas-owui-tools`, including the existing Home
   Assistant, SPECULAR, phone, watch, and light/device capabilities.
4. Home Assistant Assist pipeline IDs, selected conversation entity, exposed
   entity/script set, installed dashboard/package state, and entity-registry
   collision risk.
5. Wyoming STT/TTS/wake integrations, satellites, selected wake word, and
   response media player.
6. Tunnel hostnames, ingress targets, Access application/policy names, and
   authentication names/scopes only.

No values, transcripts, private device state, token material, or backup
contents are needed. The exact paths/commands depend on the owner's actual
OpenWebUI and Home Assistant installation method, which the repositories do
not establish; they must be supplied and approved before use.

## Phase 9 repository implementation boundary

Safe to implement now:

- deterministic local `ControlPlaneSummary` fixture aggregation;
- optional minor-compatible summary projections required by the ten sensors;
- a disabled sensor-only Home Assistant package and dashboard example;
- fixture rendering and structural tests;
- a fixture/KV-backed, GET-only external OpenAPI surface with exactly nine
  operations and a dedicated future bearer name;
- policy, contracts, tests, rollout, rollback, and owner checklists.

Blocked in this phase:

- deployment, restart, live configuration edit, entity exposure, Assist
  reassignment, OpenWebUI tool assignment, prompt/model/tool mutation, tunnel
  mutation, credential creation, provider access, write tools, and any Home
  Assistant service call.
