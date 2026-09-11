# Gardener remediation coverage replay, 10 September 2026

This record is the evidence basis for the authority change proposed after the first ADR-0015 live remediation run. It is not deployment evidence and does not authorise a rollout by itself.

## Exact execution evidence

The replay is bound to these exact runs and source revisions:

- Atlas Dep Audit run `34533375894`, `workflow_dispatch`, source `786a3aca2449b587386140366416fc1fd90a2aa4`;
- Finding bundle digest `sha256:7205d506c8e75e33788b45dbeeb5a8338c9ca4bf5a9fad1537881d48c77791ac`;
- Atlas Gardener run `34533553511`, `workflow_dispatch`, source `b1908fe15f556223a3b25b9fa63f7677644f2104`;
- accepted authority `11e7a727590aa5376e766416b1e6a83fb6fd98ef`.

The audit produced 17 Gardener Findings over the 20 covered public runtime repositories. The controller produced two draft container-digest remediation pull requests, fifteen observations, and zero refusals. The two draft pull requests were `AtlasReaper311/atlas-corpus#43` and `AtlasReaper311/ramone-memory#29`. Neither dependency/container proposal was authorised for automatic merge.

## Producer defect discovered by replay

The same audit artifact contains 52 raw vulnerability rows. Every row was emitted with `severity=unknown` and `fixed_version=null`.

That output is not reliable evidence that all 52 advisories lack fixes. At source revision `786a3aca2449b587386140366416fc1fd90a2aa4`, `audit.py` submitted versioned package URLs to OSV `/v1/querybatch` and passed the returned shallow vulnerability entries directly into severity and fixed-version extraction. OSV batch results identify vulnerabilities but do not provide the complete affected-range and severity objects required by those extractors.

The producer must therefore hydrate each unique vulnerability ID to its full OSV record before remediation eligibility is decided. Full-record hydration, pagination handling, component-specific affected-range selection, and `last_affected` handling are being corrected separately in `AtlasReaper311/atlas-dep-audit#18`. This authority proposal must not be used to waive that producer correctness gate.

## Exact 17-Finding replay

| # | Repository | Source | Vulnerable dependency set in the audited source | ADR-0015 result | Correct next-stage disposition |
|---:|---|---|---|---|---|
| 1 | `atlas-quota-watch` | `package-lock.json` | `sharp 0.35.2` | observation | graph remediation candidate only after exact Wrangler regeneration proves `sharp 0.35.2` is absent |
| 2 | `deploy-watch` | `package-lock.json` | `sharp 0.35.2` | observation | graph remediation candidate only after exact Wrangler regeneration proves `sharp 0.35.2` is absent |
| 3 | `atlas-api-public` | `package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both, but only if exact regeneration proves both advisory sets absent |
| 4 | `atlas-blackbox` | `package-lock.json` | `brace-expansion 5.0.7` | observation | bounded transitive lock remediation to a patched accepted version after exact regeneration proof |
| 5 | `atlas-dora` | `package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |
| 6 | `atlas-api-index` | `package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |
| 7 | `ramone-edge` | `package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |
| 8 | `ramone-memory` | `Dockerfile:1` | `python:3.12-slim` tag | draft PR | remediation available under existing `container-digest-pin` authority |
| 9 | `atlas-corpus` | `requirements.txt` | `chromadb 0.5.23` | observation | `awaiting-upstream-fix` while current stable ChromaDB releases remain in the affected ranges |
| 10 | `github-pulse` | `package-lock.json` | `sharp 0.35.2` | observation | graph remediation candidate only after exact Wrangler regeneration proves `sharp 0.35.2` is absent |
| 11 | `atlas-corpus` | `Dockerfile:1` | `python:3.12-slim` tag | draft PR | remediation available under existing `container-digest-pin` authority |
| 12 | `ramone-memory` | `requirements.txt` | `chromadb 0.5.23` | observation | `awaiting-upstream-fix` while current stable ChromaDB releases remain in the affected ranges |
| 13 | `site-pulse` | `package-lock.json` | `sharp 0.35.2` | observation | graph remediation candidate only after exact Wrangler regeneration proves `sharp 0.35.2` is absent |
| 14 | `specular-telemetry` | `worker/package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |
| 15 | `ramone-voice-trigger` | `worker/package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |
| 16 | `atlas-notify` | `package-lock.json` | `sharp 0.35.2` | observation | graph remediation candidate only after exact Wrangler regeneration proves `sharp 0.35.2` is absent |
| 17 | `atlas-daily-digest` | `package-lock.json` | `brace-expansion 5.0.7`, `sharp 0.35.2` | observation | one bounded npm graph remediation candidate may address both after exact regeneration proof |

The 13 npm source Findings represent 20 dependency groups: twelve `sharp` groups and eight `brace-expansion` groups. Seven repositories contain both vulnerable dependencies in the same lockfile. Treating each source file as one generic observation therefore hides materially different remediation states.

## Current upstream evidence

The audited npm manifests show that all twelve repositories containing `sharp 0.35.2` directly declare Wrangler. The vulnerable `sharp` node is transitive through the Wrangler/Miniflare toolchain rather than a direct Atlas dependency.

Cloudflare merged `workers-sdk#15580`, which updates Miniflare's exact `sharp` dependency from `0.35.2` to `0.35.4` specifically to resolve `GHSA-rgj7-g3m4-5g8c`. Cloudflare has also published `wrangler@4.131.0`, whose release includes `miniflare@5.20260910.0-alpha` carrying that update. This is evidence for a possible direct-parent remediation path, not permission to blindly bump Wrangler. Atlas Dep Audit must reproduce the target lock graph from the exact repository snapshot and prove that the affected `sharp` version and advisory are gone before it emits a candidate.

The audited `brace-expansion 5.0.7` nodes are transitive. Current advisory data provides patched 5.x releases, with `5.0.9` required to clear the two vulnerability IDs present in the audit. A lockfile-only remediation is acceptable only when every constraining parent range in the exact lock graph admits the chosen target and a pinned, lifecycle-script-disabled regeneration produces a bounded output whose post-state clears the vulnerability IDs.

The ChromaDB findings are different. Current OSV records include affected ranges ending with `last_affected=1.5.9`, and PyPI currently lists `1.5.9` as the latest stable `chromadb` release. No target version may be invented. Those two source Findings must be reported as `awaiting-upstream-fix` until authoritative package/advisory evidence provides a non-affected released target.

## Corrected coverage target

The controller is not required to manufacture one pull request per Finding. It is required to account for every Finding with a precise evidence-backed disposition.

For the exact 17-Finding replay, the next-stage target is:

- 2 existing container Findings: `remediation-available`, already proven to produce bounded draft pull requests;
- 13 npm Findings: eligible for a single bounded graph-remediation proposal per source only when producer regeneration proves the resulting manifest/lock graph clears every vulnerability ID claimed by that proposal;
- 2 ChromaDB Findings: `awaiting-upstream-fix` until a released non-affected version exists.

The maximum expected draft-PR coverage from the current evidence is therefore 15 of 17 source Findings, not 17 of 17. The required accounting coverage is 17 of 17. A future audit may change that ratio as upstream releases and repository snapshots change.

## Safety invariants for the next authority

The next authority must preserve all ADR-0015 separation-of-authority controls and add these constraints:

1. Fix OSV full-record enrichment before using dependency fixed-version data for live remediation.
2. Emit distinct dependency dispositions instead of collapsing unrelated dependency states into one generic source-level observation.
3. Permit npm graph remediation only for exact `package.json` plus `package-lock.json` snapshots.
4. Permit only released patch/minor direct-parent targets within the existing major version.
5. Permit transitive target updates only when every parent constraint in the exact lock graph admits the selected target.
6. Regenerate npm lock state in a disposable checkout with lifecycle scripts disabled and a pinned toolchain.
7. Require package-manifest changes to match the structured direct-update list exactly.
8. Require all claimed vulnerability IDs to be absent from a post-regeneration vulnerability scan before candidate emission and again before proposal publication.
9. Bind the candidate to exact target manifest/lock digests so producer and controller regeneration disagree closed.
10. Keep npm graph remediation review-required and draft-PR-only. It must never inherit housekeeping automatic-merge authority.
11. Never use npm `overrides` merely to force a transitive package around its parent dependency declaration.
12. Never invent a target version for an advisory represented only by `last_affected` or another open-ended affected range.

## Rollout boundary

This document does not authorise a workflow dispatch, target mutation, merge, provider change, package release, deployment, or live rollout. Any implementation must first bind to an accepted exact Atlas Infra authority commit, pass repository-native validation, and stop at its own merge and rollout gates.