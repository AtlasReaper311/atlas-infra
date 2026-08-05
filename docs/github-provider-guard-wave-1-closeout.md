# GitHub provider guard Wave 1A closeout

Status: complete.

## Scope

Wave 1A extended the proven `atlas-badges` default-branch guard pattern to exactly two active, public, non-runtime repositories:

- `AtlasReaper311/atlas-bootstrap`;
- `AtlasReaper311/atlas-resource-audit`.

No Wave 1B or later repository was changed.

Source authority:

- repository: `AtlasReaper311/atlas-infra`;
- merge commit: `c84c4f4822ced17da79cba552def0eb9ada215a6`;
- source PR: `atlas-infra#125`.

## Provider result

| Repository | Ruleset | Required context | Integration |
| --- | ---: | --- | ---: |
| `atlas-bootstrap` | `20443224` | `build` | `15368` |
| `atlas-resource-audit` | `20443225` | `Offline resource audit` | `15368` |

Both rulesets are active, target `~DEFAULT_BRANCH`, and contain:

- `pull_request`;
- `required_status_checks`;
- `deletion`;
- `non_fast_forward`.

Both rulesets have:

- zero required approving reviews;
- no bypass actors;
- strict required-status branch update policy disabled;
- repository auto-merge disabled before and after the provider write.

The provider create responses and provider read-backs were equivalent in meaning. The active-rules endpoint independently returned the four expected controls for each ruleset.

Provider evidence archive:

- SHA-256: `ccbcf57ac3bc0df833b93657fc2ec9c0d76b43e26fe822a0c4fd21ef6e01decf`;
- receipt schema: `atlas-github-provider-guard-wave-1/receipt/v1`;
- provider verification timestamp: `2026-08-05T08:44:25.577356Z`.

## Dependabot compatibility

The pre-write inspection used genuine open Dependabot pull requests:

- `atlas-bootstrap#9` at `aea2f6412f711f4b7342a548c398ae94ed890702`;
- `atlas-resource-audit#11` at `67dcd75194fc9ffd5c3002d722013626a4315872`.

Each pull request was open against `main`, mergeable, and had its repository-owned required context passing under GitHub Actions integration `15368`. Repository auto-merge remained disabled.

No Dependabot pull request was merged as part of Wave 1A.

## Protected owner-path validation

### atlas-bootstrap

- validation PR: `atlas-bootstrap#10`;
- reviewed head: `1bb61ab660fd987625bee83b57ed71caefd0da1f`;
- required workflow run: `30990627184`;
- required context: `build`;
- result: success;
- unresolved review threads: zero;
- protected squash merge: `c4da05eb850ec9dffa8cf84e98d33f0b8d4aaa22`.

### atlas-resource-audit

- validation PR: `atlas-resource-audit#13`;
- reviewed head: `9d44d8b4ef417fa92ef29d5e7481bdb0990ea839`;
- required workflow run: `30990644705`;
- required context: `Offline resource audit`;
- CodeQL run: `30990644964`;
- result: success;
- unresolved review threads: zero;
- protected squash merge: `76ec572239a35c7f8a00111801e1aaebd1dc1b27`.

These merges prove that the normal owner pull-request path remains available under both active rulesets.

## Final owner-authenticated scoreboard

The final read-only scoreboard was collected at `2026-08-05T08:56:34Z` from exact Atlas Infra source commit `c84c4f4822ced17da79cba552def0eb9ada215a6`.

Evidence identity:

- schema: `atlas-github-conformance-scoreboard/report/v2`;
- report fingerprint: `sha256:6838a900dbae4b2c1b4e218b2a5d02e9922649c5ea17e9740a402a145eb1c485`;
- repositories checked: 33;
- required checks passed: 236;
- required checks failed: 24;
- required checks unknown: 0.

Observed movement from the canary-closeout baseline:

- required passes: 234 to 236;
- required failures: 26 to 24;
- required unknowns: remained 0.

Both Wave 1A repositories passed `default_branch_guard` with the message `An active default-branch ruleset was observed.`

Final evidence file digests:

| File | SHA-256 |
| --- | --- |
| `github-conformance-scoreboard.json` | `ab2a801dcf56d5b2e950a6cc53f318663d942b531d391900183e631a63943664` |
| `github-conformance-scoreboard.md` | `8b51baa43523ec9a3970730570be5fe782327c13e4e2ccebff798df6412bd361` |
| `github-provider-guard-wave-1-final-receipt.json` | `48ee9c179b0e4e4438aa8d56681d6d56bcb4355d70ddea2d757e55e1118fb24a` |
| `atlas-bootstrap-owner-validation-pr.json` | `a202b1dfcafb6718715bab28a8da2e20d20224fd7de023120672797eca3ae3df` |
| `atlas-resource-audit-owner-validation-pr.json` | `50689961ee5bc336a52281abbb8df0c0ee7283d19fd8409e07baf4efaa61a9a9` |

Final evidence archive SHA-256:

- `7987a2274be9bef3242a227739ddaaa5b2975591d7644376b63c8eacbed309f1`.

The generated scoreboard outputs remain external evidence because `reports/` is intentionally ignored. Their identity is preserved through the embedded report fingerprint, file digests, archive digest, and committed machine-readable receipt.

## Residual boundaries

Wave 1A did not:

- attempt direct pushes to protected `main`;
- attempt destructive force pushes or branch deletion;
- enable repository auto-merge;
- merge either Dependabot pull request;
- deploy, publish, release, dispatch a workflow, or change a secret;
- begin Wave 1B or any later wave.

Provider read-back proves the deletion and non-fast-forward controls are active. No destructive test is required for Wave 1A closure.

## Closure decision

Wave 1A is complete and requires no further work.

The wider programme remains open with 24 required `default_branch_guard` failures. Wave 1B is a separate stage for `AtlasReaper311/ollama-rag-kit` and requires:

1. a fresh Part 0 inspection;
2. a fresh owner validation pull request;
3. repository-native required-check discovery;
4. separate provider-write approval;
5. a new stamped scoreboard and closeout receipt.
