+++
id = "ADR-0001"
date = 2026-07-02
status = "accepted"
+++

# ADR-0001: Worker-to-Worker calls use service bindings, not public hostnames

## Context

Workers in the estate need to call one another: a runtime alert travels from a Worker to atlas-notify, the API index fans out to the Workers it documents, and so on. The first shape for these calls was the obvious one, a `fetch()` to the callee's public hostname on the same zone. It failed intermittently with 522 at the Cloudflare edge. In this estate, that same-zone public-hostname path left the Worker runtime and re-entered through the public edge, where it produced intermittent 522 responses. The observed failure was in the route taken to the callee, not evidence that the callee itself was unavailable.

## Decision

Worker-to-Worker calls use Cloudflare Service Bindings, declared in `wrangler.toml`, and never the callee's public hostname. A binding is an internal reference the runtime resolves without a network hop, so `env.ATLAS_NOTIFY.fetch(...)` reaches atlas-notify without a public request. The alert envelope `{source, level, title, message, fields}` travels this way. Service bindings solve routing; any application-layer authorization, such as `NOTIFY_TOKEN`, remains an explicit and separate callee policy. This is the estate default for calls that stay inside the account.

## Consequences

The 522 failure class disappears because there is no public round trip to refuse, and internal traffic stops competing with the public rate limits and CORS rules that guard the front door. The cost is explicit wiring: every caller declares its bindings, and because named environments inherit nothing, each `[env.dev]` block redeclares the bindings it needs. A binding also couples deploy order loosely, since the referenced service must exist in the account for the binding to resolve, which is a fact worth stating in a runbook rather than discovering at deploy time.
