# GitHub provider guard wider rollout: Wave 1 plan

Status: source plan prepared. No wider-rollout provider write has been performed.

## Purpose

Extend the proven `atlas-badges` default-branch guard pattern to a first bounded rollout wave without treating the remaining estate as homogeneous.

This programme begins from the final canary receipt merged in `atlas-infra#124` as `72b85fe4a04598da20a1c10543dd24ed90e796a1`.

The owner-authenticated scoreboard collected on `2026-08-04T23:22:02Z` recorded:

- report fingerprint: `sha256:cfb03af45343602dfa5bcc1c6180d2e054242a14a6295695ffda99d7ae5427bd`;
- repositories checked: 33;
- required checks passed: 234;
- required checks failed: 26;
- required checks unknown: 0.

All 26 required failures are readable `default_branch_guard` findings. This plan does not reinterpret them as source defects.

## Part 0 result

The remaining repositories divide into five operational groups.

### Wave 1A: active non-runtime, current Dependabot proof available

- `AtlasReaper311/atlas-bootstrap`
- `AtlasReaper311/atlas-resource-audit`

### Wave 1B: active non-runtime, fresh owner validation still required

- `AtlasReaper311/ollama-rag-kit`

### Wave 2: specialist active non-runtime repositories

- `AtlasReaper311/atlas-gardener`
- `AtlasReaper311/atlas-interface-kit`
- `AtlasReaper311/atlas-journey-watch`

`atlas-journey-watch` currently has repository auto-merge capability enabled. It is excluded until its automation authority and desired repository setting are reviewed together.

`atlas-gardener` is the dependency-remediation controller and needs a controller-specific protection review rather than being treated as a generic utility.

`atlas-interface-kit` owns immutable interface releases and needs release-path compatibility evidence before protection changes.

### Wave 3: partial classic-protection migrations

- `AtlasReaper311/atlas-doc-viewer`
- `AtlasReaper311/atlas-quota-watch`
- `AtlasReaper311/site-pulse`
- `AtlasReaper311/specular-sonify`
- `AtlasReaper311/status`

These are migrations, not additions. Their existing classic protection must be captured and either preserved or deliberately replaced one repository at a time.

### Wave 4: production runtime repositories without a qualifying guard

- `AtlasReaper311/atlas-api-index`
- `AtlasReaper311/atlas-blackbox`
- `AtlasReaper311/atlas-corpus`
- `AtlasReaper311/atlas-daily-digest`
- `AtlasReaper311/atlas-dora`
- `AtlasReaper311/atlas-notify`
- `AtlasReaper311/deploy-watch`
- `AtlasReaper311/github-pulse`
- `AtlasReaper311/ramone-edge`
- `AtlasReaper311/ramone-memory`
- `AtlasReaper311/ramone-voice-trigger`
- `AtlasReaper311/specular-sentinel`
- `AtlasReaper311/specular-telemetry`

Runtime repositories require deployment and emergency-recovery path inspection before each provider write.

### Wave 5: owner-wide special repositories

- `AtlasReaper311/.github`
- `AtlasReaper311/AtlasReaper311`

These repositories do not currently provide a recent repository-native pull-request gate. They remain last until their special inheritance and profile behaviour is reviewed and a meaningful native check exists.

## Wave 1A selection

Wave 1A contains exactly two repositories.

Both are:

- public;
- lifecycle `active`;
- classified as non-runtime;
- on default branch `main`;
- not archived;
- configured with repository auto-merge disabled;
- reported by the final owner-authenticated scoreboard as having no active qualifying ruleset or classic pull-request guard;
- covered by a current genuine Dependabot pull request with the repository-owned native check passing.

### atlas-bootstrap

Current validation pull request:

- pull request: `atlas-bootstrap#9`;
- state: open and mergeable;
- inspected head: `aea2f6412f711f4b7342a548c398ae94ed890702`;
- required native context: `build`;
- GitHub Actions integration ID: `15368`;
- `Dependabot review policy` run `30681441159`: success;
- `ci` run `30681441407`: success;
- `OpenSSF Scorecard` run `30681441188`: success.

The `build` job performs Bash syntax, JSON validity, and PowerShell AST parsing. CodeQL is not selected because the repository implementation is Bash and PowerShell outside the configured CodeQL language set.

### atlas-resource-audit

Current validation pull request:

- pull request: `atlas-resource-audit#11`;
- state: open and mergeable;
- inspected head: `67dcd75194fc9ffd5c3002d722013626a4315872`;
- required native context: `Offline resource audit`;
- GitHub Actions integration ID: `15368`;
- `Dependabot review policy` run `30681524898`: success;
- `Pull request CI` run `30681524897`: success;
- `CodeQL` run `30681524902`: success;
- `OpenSSF Scorecard` run `30681524901`: success.

The `Offline resource audit` job compiles and tests the deterministic audit engine without accessing Cloudflare provider state.

## Proposed ruleset state

Each Wave 1A repository receives one repository ruleset with the same structural pattern proven on `atlas-badges` and its own exact native check context.

Common state:

- name: `Atlas default branch PR guard`;
- target: branch;
- condition: `~DEFAULT_BRANCH`;
- enforcement: active;
- require changes through a pull request;
- required approving reviews: 0;
- required review thread resolution: false;
- block deletion;
- block non-fast-forward updates;
- no bypass actors;
- strict required-status branch update policy: false;
- repository auto-merge remains disabled.

Required status checks:

| Repository | Context | Integration ID |
| --- | --- | ---: |
| `atlas-bootstrap` | `build` | `15368` |
| `atlas-resource-audit` | `Offline resource audit` | `15368` |

## Fail-closed runner

`scripts/github-provider-guard-wave-1.sh` owns the proposed operator path.

It defaults to `MODE=inspect` and performs only read operations. Inspection requires:

- the authenticated GitHub user is `AtlasReaper311`;
- each repository is public, unarchived, on `main`, and has auto-merge disabled;
- no active branch ruleset is present;
- classic branch protection is absent;
- the named validation pull request remains open against `main`;
- the required native check is completed successfully under GitHub Actions integration `15368`.

Provider writes require both:

```text
MODE=apply
ATLAS_PROVIDER_WRITE_CONFIRMATION=APPLY GITHUB PROVIDER GUARD WAVE 1
```

The apply path is limited to the two declared repositories. It stores the request, create response, provider read-back, active-rule projection, repository settings, validation pull request, check runs, and SHA-256 file list under the ignored `reports/` directory.

The runner refuses to continue when provider state has drifted. It does not edit an existing ruleset or migrate classic protection by assumption.

## Validation sequence

After source review and a separate provider-write approval:

1. run the script in inspection mode from a clean checkout of the approved Atlas Infra merge commit;
2. review the generated pre-write evidence and digests;
3. run the script in apply mode with the exact confirmation phrase;
4. verify each ruleset create response and provider read-back are equivalent in meaning;
5. verify the four active rules apply to `main`;
6. confirm repository auto-merge remains disabled;
7. re-read the two existing Dependabot pull requests and their required checks;
8. open one harmless owner validation pull request in each repository;
9. merge each owner validation pull request only after the required context passes;
10. rerun the stamped owner-authenticated scoreboard from the exact Atlas Infra source commit;
11. expect movement from 234 passed and 26 failed to 236 passed and 24 failed only when no unrelated estate drift occurred;
12. commit the actual report identity and provider evidence through a separate Atlas Infra closeout pull request.

Expected counts are planning arithmetic, not evidence. The closeout must record the actual stamped result.

## Rollback

If either repository blocks an intended owner or Dependabot path:

1. stop the wave immediately;
2. do not touch the other repository if its write has not occurred;
3. identify only the ruleset ID created for the affected repository from the evidence directory;
4. obtain separate rollback approval;
5. disable or delete only that ruleset;
6. verify repository auto-merge and all unrelated settings remain unchanged;
7. rerun the owner-authenticated scoreboard;
8. record the failure and do not begin Wave 1B.

Rollback is a provider write and is not pre-approved by this source plan.

## Boundaries

This source plan does not:

- create, update, disable, or delete a ruleset;
- edit classic branch protection;
- change auto-merge capability;
- merge a Dependabot pull request;
- dispatch a workflow;
- create a release or tag;
- deploy anything;
- change a secret or token;
- begin Wave 1B or any later wave.

The shared work-allocation document is not changed because unrelated Phase 15 coordination remains active in `atlas-infra#122`.
