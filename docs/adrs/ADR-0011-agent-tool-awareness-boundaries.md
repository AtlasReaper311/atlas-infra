+++
id = "ADR-0011"
date = 2026-08-07
status = "accepted"
visibility = "internal"
repositories = ["AtlasReaper311/atlas-infra"]
services = []
contracts = []
policies = []
+++

# ADR-0011: Keep agent tool awareness separate from runtime availability and mutation authority

## Context

Atlas Systems now uses a provider-neutral agent fleet across Claude Code, Codex,
and Cursor, with additional ChatGPT project instructions and connected tools used
for Atlas work. The fleet can inspect, plan, review, validate, and perform bounded
local source work, but operators still have to remember which connectors, plugins,
MCP servers, local CLIs, skills, browser capabilities, and artifact tools may help
with a task.

A static list copied into every agent or provider instruction would create a new
source of drift. A catalog entry can describe a known Atlas capability family, but
it cannot prove that the capability is installed, connected, authenticated, or
usable in the current provider session. Likewise, seeing a usable tool does not
change the task's existing permission boundary.

Without an explicit decision, later work risks conflating four different claims:

- Atlas knows about a capability family;
- a local binary or provider surface is present;
- the current runtime can actually use that capability;
- the current task is authorised to perform the capability's mutation class.

The private repository `AtlasReaper311/atlas-agent-workflows` owns the agent fleet
and will implement the tool-awareness contracts. Private repository identity stays
outside public classification frontmatter and is named here only as an internal
consumer of this decision.

## Decision

Atlas Systems separates agent tool awareness into four independent layers.

First, a provider-neutral capability catalog is a discovery map only. It may
record stable capability identities, purposes, preferred evidence routes,
mutation classes, safe discovery methods, fallback routes, and secret-handling
rules. It must not contain credentials, secret values, account sessions, or
claims that a capability is currently available.

Second, current runtime evidence is the authority for availability. Agents must
verify the current provider session, connected tool surface, or safe local
runtime observation before claiming that a capability can be used. Catalog state,
historical installation state, and project context are not runtime proof.

Third, source-of-truth routing chooses the most authoritative relevant capability
for the question. Agents should prefer current repository and provider evidence
over weaker manual or historical routes, but must not call unrelated tools merely
because they exist.

Fourth, tool availability never grants mutation authority. Existing approval
boundaries for local files, Git, GitHub, workflows, provider settings, secrets,
releases, publication, deployment, runtime changes, communications, purchases,
and live systems remain controlling. An available write-capable tool may be used
only for the mutation classes already authorised by the current task.

Local discovery is read-only and network-free by default. It may record safe
presence facts such as an allow-listed executable or managed capability path, but
must not read credential stores, secret-bearing configuration, browser cookies,
shell history, private keys, or environment variable values. Presence does not
prove authentication.

Provider instruction surfaces must stay concise. Durable instructions should tell
agents to discover relevant tooling, verify availability, prefer authoritative
sources, avoid irrelevant calls, and preserve authority gates. Detailed inventories
belong in the catalog, skills, generated documentation, or ephemeral runtime
evidence rather than duplicated startup prompts.

Provider-specific installation, global instruction changes, MCP configuration,
account changes, and behavior review remain separate actions after source merge.
One provider result must not be promoted across other providers or surfaces.

## Consequences

Atlas can ask for an outcome without remembering every tool name, while agents gain
a deterministic way to discover useful capability families and choose better
evidence routes.

The catalog becomes easier to maintain because it describes stable capability
semantics rather than volatile session state. Runtime disagreement safely wins over
catalog declaration, so stale inventory cannot manufacture availability.

The separation between awareness and authority preserves the existing Atlas safety
model. A connected deployment, communication, or provider-write tool does not turn
a read-only or source-write task into a rollout or account mutation.

The cost is additional contract and validation work in `atlas-agent-workflows`:
catalog schemas, discovery logic, routing tests, generated instruction surfaces,
local inventory safeguards, provider behavior cases, and capability-specific
evidence. Provider and local rollout must also be reviewed independently because
source integration cannot prove provider behavior.
