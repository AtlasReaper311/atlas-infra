+++
id = "ADR-0007"
date = 2026-07-23
status = "accepted"
visibility = "public"
repositories = ["AtlasReaper311/atlas-api-public", "AtlasReaper311/atlas-doc-viewer", "AtlasReaper311/atlas-infra", "AtlasReaper311/atlas-systems", "AtlasReaper311/ramone-edge", "AtlasReaper311/status"]
services = []
contracts = ["atlas-control-plane/public-interface-surface/v1"]
policies = ["policy/atlas-owned-domains.json", "policy/browser-icons-v1.json", "policy/public-interface-contract.json"]
+++

# ADR-0007: Public interface contract

## Context

Atlas Systems has several public browser-facing surfaces owned by independent repositories and deployment models. The estate already shares a visual language, but navigation, search, status presentation, browser icons, metadata, mobile wayfinding, link targets, and accessibility behaviour have drifted between the main site, Status, CV, Ramone, public API documentation, specialist Lab tools, and generated articles.

A remote shared stylesheet or script would reduce copied code but would also make independent surfaces depend on another deployment at runtime. It would require cross-origin coupling, complicate Content Security Policy, and create a common failure mode. A single universal page template would remove useful product identity and would not fit Worker-rendered interfaces or generated articles.

The estate also has protected operational, privacy, publishing, audio, and accessibility contracts. Interface work must be testable without changing machine APIs, telemetry meaning, publication ownership, inference behaviour, audio behaviour, or the public and private boundary.

## Decision

Atlas Systems adopts a versioned public interface contract owned by `atlas-infra`.

The contract defines common behaviour rather than one universal layout. Every public human-facing HTML surface must provide:

- the Atlas Systems wordmark and global routes for Work, Writing, Lab, About, and estate search;
- a compact status link on non-home surfaces, derived from the bounded aggregate fields in `https://api.atlas-systems.uk/v1/stats`;
- same-tab navigation between explicitly approved Atlas-owned domains;
- safe new-tab behaviour for genuinely external destinations;
- repository-local browser icons and complete page metadata;
- WCAG 2.2 AA interaction and readability baselines;
- predictable mobile navigation and visible focus;
- a purpose-specific product identity and footer where appropriate.

The homepage keeps its existing operational treatment and must not receive a duplicate status indicator. The Lab keeps Ramone as the first major experience after the global header. Contextual navigation augments global navigation and never replaces it.

Implementation assets remain local to each repository. Synchronised assets use deterministic manifests and checksums. Source repositories may express the contract with different markup and CSS where their product purpose requires it, but repository-native tests and the shared validator must prove the same behavioural outcomes.

Generated article shell changes originate in `atlas-article-gen`, pass through `atlas-scheduler`, and reach `atlas-systems` only through the established publication path. Those private authoring repositories remain outside the public repository projection and are named here only to document the protected pipeline boundary. Machine-facing endpoints remain outside the visual interface contract.

## Consequences

Public surfaces remain independently deployable and continue to function when another presentation surface is unavailable. Content Security Policy does not need to be weakened to load a remote shell.

A change to a shared behaviour now requires a contract revision, local implementation updates, and validation in each affected repository. This is more deliberate than copying markup, but it prevents silent drift and preserves product-specific layouts.

The contract does not create deployment authority. Draft pull requests, previews, merges, and production rollouts remain separate evidence stages. Preview deployments use non-production branches and cannot be treated as publication or live deployment proof.
