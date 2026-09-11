# Gardener ADR-0016 remediation closeout, 11 September 2026

This record closes the ADR-0016 implementation and the 11 September 2026 public-runtime remediation wave at the source, GitHub, and GitHub Actions evidence layers. It does not claim independent Cloudflare provider state or endpoint health beyond successful repository deployment workflows.

## Authority and implementation

- accepted Atlas Infra authority: `eb634e5b19725ecc87902543058a4dd2a2e089c7`;
- accepted decision: `ADR-0016`;
- final Atlas Gardener source revision used for reconciliation: `ec20d2a099634e8cddbc3ea73552b29bf646e648`;
- final source correction: `AtlasReaper311/atlas-gardener#36`, preserving Gardener idempotence across Finding-bundle expiry renewal without widening mutation or merge authority;
- controller mode observed in final evidence: `automerge-low-risk`;
- dependency and container proposals remain review-required and are not automatically mergeable under ADR-0016.

## Completed remediation set

Six reviewed `npm-lock-security-remediation` pull requests were merged after owner review. Each patch was limited to the reviewed npm lockfile change and removed the affected `brace-expansion 5.0.7` state in favour of `5.0.9`.

| Repository | Pull request | Merge commit | Deployment workflow evidence |
|---|---:|---|---|
| `AtlasReaper311/atlas-api-public` | `#76` | `8ff638f92cfc3a3ec5e2243ecb6464c964bd8e65` | `Deploy` run `34608255020`, success |
| `AtlasReaper311/atlas-api-index` | `#28` | `b290cd7c2f803343642373d1d89b6ddfae7212fb` | `Deploy` run `34614634815`, success |
| `AtlasReaper311/atlas-dora` | `#47` | `5f5b163fe2d7a10c24618f722a5c1c6949cf641d` | `Deploy` run `34614656316`, success |
| `AtlasReaper311/atlas-daily-digest` | `#23` | `d9ac29928df94f717b549ee07c3656634c964d1b` | `Deploy` run `34614675761`, success |
| `AtlasReaper311/ramone-voice-trigger` | `#30` | `7f99171ca894b110f2aa7a6261667fdea79588cf` | `Deploy` run `34614699699`, success |
| `AtlasReaper311/specular-telemetry` | `#34` | `a7198278712a9009a189811b9218c814541d3744` | `Deploy` run `34614722339`, success |

A successful GitHub Actions deployment workflow is deployment-execution evidence only. This record does not reinterpret it as independent provider or live endpoint verification.

## Fresh post-remediation audit

The post-remediation Atlas Dep Audit evidence is bound to:

- workflow run: `AtlasReaper311/atlas-dep-audit` run `34602507343`, attempt `2`;
- source revision: `269032064cf3ded1303f66b9eacb5fbd3a28f056`;
- generated at: `2026-09-11T15:16:30Z`;
- authority commit: `eb634e5b19725ecc87902543058a4dd2a2e089c7`;
- Finding bundle digest: `sha256:e6b37c4d210edacafa10dd411badd11f482151d3082b5052405234080e5304dd`.

Audit generation and Finding-bundle attestation/publication completed successfully. The workflow retained a failing blocking result because four real vulnerability Findings remain. That red result is expected evidence, not a failed remediation closeout.

The six remediated `brace-expansion` Findings are absent from the fresh bundle. The remaining bundle contains exactly four non-actionable Findings:

| Repository | Source | Disposition | Reason |
|---|---|---|---|
| `AtlasReaper311/atlas-corpus` | `requirements.txt` | `awaiting-upstream-fix` | no released non-affected version is present in current advisory evidence |
| `AtlasReaper311/ramone-memory` | `requirements.txt` | `awaiting-upstream-fix` | no released non-affected version is present in current advisory evidence |
| `AtlasReaper311/ramone-edge` | `package-lock.json` | `unsupported-remediation` | post-regeneration proof still reports `GHSA-rgj7-g3m4-5g8c` |
| `AtlasReaper311/atlas-notify` | `package-lock.json` | `unsupported-remediation` | post-regeneration proof still reports `GHSA-rgj7-g3m4-5g8c` |

These Findings remain visible and blocking until new authoritative upstream or repository evidence changes their disposition. They must not be suppressed to make the audit green.

## Final current-head reconciliation

The final controller reconciliation is:

- repository: `AtlasReaper311/atlas-gardener`;
- workflow: `.github/workflows/controller.yml`;
- run: `34616330050`;
- event: `workflow_dispatch`;
- head: `ec20d2a099634e8cddbc3ea73552b29bf646e648`;
- conclusion: `success`;
- evidence artifact: `atlas-gardener-controller-34616330050-1`;
- artifact digest: `sha256:7a674cadde583e7b05635bd0a872ddc04a16e1a3e93dd51616154263fa275878`.

The bounded `controller.json` evidence records:

- `attestation_verified: true`;
- authority commit `eb634e5b19725ecc87902543058a4dd2a2e089c7`;
- Finding bundle digest `sha256:e6b37c4d210edacafa10dd411badd11f482151d3082b5052405234080e5304dd`;
- four Finding fingerprints;
- four `findings_observed` records;
- zero remediation plans;
- zero proposals;
- zero pull requests;
- zero refusals;
- zero merge outcomes.

This is the required idempotent no-op proof after the six reviewed remediations. Gardener consumed the fresh attested bundle, accounted for every remaining Finding, and created no duplicate or unsupported work.

## Closeout decision

ADR-0016 implementation and this remediation wave are complete at the reviewed source, GitHub merge, GitHub Actions deployment-workflow, post-remediation audit, attestation, and final-controller reconciliation layers.

This does not mean the estate is vulnerability-free. Four Findings remain intentionally open and non-actionable under current evidence. It also does not claim independent provider or live endpoint verification beyond the successful deployment workflows listed above.

No change is required to `policy/gardener-automation.json`, `policy/gardener-github-app-coverage.json`, `policy/gardener-target-readiness.json`, estate classification, or topology as part of this closeout. Those authorities already describe the active boundaries. Future remediation begins only from a fresh attested Finding bundle and the authority in force at that time.
