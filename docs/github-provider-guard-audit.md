# GitHub provider guard audit

## Status

Phase III is active as a read-only provider-state audit.

Phase II closed the public-repository source-conformance work with zero required source failures. This phase resolves the 27 remaining `default_branch_guard` outcomes that the scheduled scoreboard could not read.

No ruleset, branch-protection, token, repository, release, tag, workflow, deployment, or secret change is authorised by this document.

## Part 0 inspection

The closing scoreboard run was GitHub Actions run [`30535544793`](https://github.com/AtlasReaper311/atlas-infra/actions/runs/30535544793). It checked the authoritative 33-repository public projection and recorded:

- 233 required passes;
- 0 required failures;
- 27 required unknown outcomes;
- 68 not-applicable outcomes;
- 1 approved exception;
- 1 deferred outcome.

All 27 unknown outcomes are `default_branch_guard`. The report message is `GitHub ruleset or branch-protection evidence was unavailable.` This is an evidence-access result. It does not prove that a guard is present or absent.

The existing scoreboard implementation already uses the correct read-only provider paths:

- `GET /repos/{owner}/{repo}/rulesets`;
- the returned ruleset detail endpoint when the list response omits conditions or rules;
- `GET /repos/{owner}/{repo}/branches/{default_branch}/protection` as the classic-protection fallback.

The accepted pass conditions are:

- an active branch ruleset that targets the default branch and contains `pull_request`, `deletion`, and `non_fast_forward`; or
- classic branch protection with pull-request review protection.

The scheduled workflow uses the repository-scoped `GITHUB_TOKEN`. It can read normal repository contents but could not establish provider-state evidence for these 27 repositories. The connected ChatGPT GitHub application also exposes repository administration metadata but does not expose a ruleset or branch-protection read action. The initial audit therefore requires an owner-authenticated local read using the existing Atlas Infra tooling.

GitHub documents repository-ruleset listing as a Metadata read and classic branch-protection retrieval as an Administration read. The local credential must have sufficient read access to the repositories, but its value must never be copied into chat, written into a report, or committed.

## Authoritative audit scope

The scope is the 27 repositories that were unknown in the 30 July report:

1. `AtlasReaper311/.github`
2. `AtlasReaper311/atlas-api-index`
3. `AtlasReaper311/atlas-badges`
4. `AtlasReaper311/atlas-blackbox`
5. `AtlasReaper311/atlas-bootstrap`
6. `AtlasReaper311/atlas-corpus`
7. `AtlasReaper311/atlas-daily-digest`
8. `AtlasReaper311/atlas-doc-viewer`
9. `AtlasReaper311/atlas-dora`
10. `AtlasReaper311/atlas-gardener`
11. `AtlasReaper311/atlas-interface-kit`
12. `AtlasReaper311/atlas-journey-watch`
13. `AtlasReaper311/atlas-notify`
14. `AtlasReaper311/atlas-quota-watch`
15. `AtlasReaper311/atlas-resource-audit`
16. `AtlasReaper311/AtlasReaper311`
17. `AtlasReaper311/deploy-watch`
18. `AtlasReaper311/github-pulse`
19. `AtlasReaper311/ollama-rag-kit`
20. `AtlasReaper311/ramone-edge`
21. `AtlasReaper311/ramone-memory`
22. `AtlasReaper311/ramone-voice-trigger`
23. `AtlasReaper311/site-pulse`
24. `AtlasReaper311/specular-sentinel`
25. `AtlasReaper311/specular-sonify`
26. `AtlasReaper311/specular-telemetry`
27. `AtlasReaper311/status`

The authoritative projection remains `policy/public-repository-classifications.json`. Do not enumerate unrelated private repositories or widen the scope through account discovery.

## Read-only evidence collection

Run from a current clean checkout of `atlas-infra` using an already authenticated GitHub CLI session. The command obtains the token internally and does not print it.

```bash
git switch main
git pull --ff-only
mkdir -p reports
GITHUB_TOKEN="$(gh auth token)" python3 scripts/github_conformance_policy.py \
  --json-out reports/github-provider-guard-audit.json \
  --markdown-out reports/github-provider-guard-audit.md
```

Validate the resulting report before sharing it:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("reports/github-provider-guard-audit.json")
report = json.loads(path.read_text(encoding="utf-8"))
checks = []
for repository in report["repositories"]:
    for check in repository["checks"]:
        if check["id"] == "default_branch_guard":
            checks.append((repository["repository"], check["outcome"], check["message"]))

assert len(checks) == 33, len(checks)
for row in checks:
    print("\t".join(row))
PY
```

The generated JSON and Markdown reports may be uploaded to the audit conversation. The GitHub credential must not be uploaded or pasted.

## Evidence classification

Each repository will be assigned exactly one provider result:

- `proved_ruleset`: an active default-branch ruleset satisfies the accepted rule set;
- `proved_classic`: classic protection requires pull-request reviews;
- `readable_insufficient`: provider state is readable but does not satisfy the accepted guard;
- `unreadable`: the owner-authenticated audit still lacks sufficient evidence;
- `scope_changed`: the repository no longer matches the authoritative public projection and requires a separate ADR-0004 policy review.

The report must retain the repository, default branch, evidence type, rule or protection identity, observed required rules, source commit, run time, and report fingerprint.

## Decision gates after evidence

1. If all 27 repositories are proved, update the scoreboard evidence path and close Phase III without provider changes.
2. If any repository is readable but insufficient, return the exact gap and a proposed canary repository. Do not create or edit a ruleset yet.
3. Any canary provider write requires Atlas approval and must be limited to one low-risk public repository.
4. After a canary, prove pull-request flow, required checks, Dependabot compatibility, administrator behavior, rollback, and scoreboard visibility before proposing a wider wave.
5. Provider rollout waves must be lifecycle-aware, with production runtime repositories handled only after the canary evidence is accepted.

## Separate release boundary

The first owner-approved `worker-meta-kit` release remains independent from this provider audit. Do not create a tag, GitHub Release, or release artifact as part of Phase III.

## Completion criteria

Phase III can close only when:

- every one of the 27 unknown repositories has current provider evidence;
- every result is classified without converting unknown into pass or failure by assumption;
- any required provider corrections have separately approved rollout and rollback evidence;
- a fresh policy-aware scoreboard run records the resulting state;
- the final evidence and residual boundaries are committed to Atlas Infra.
