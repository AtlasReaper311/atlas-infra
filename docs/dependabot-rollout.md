# Dependabot rollout

## Ownership and boundary

`atlas-infra` owns estate reconciliation, ecosystem detection, policy decisions,
configuration generation, and the immutable review plan. It does not write to
other repositories. `atlas-gardener` remains the only approved automated
cross-repository write boundary.

Dependabot supplies version-currency pull requests. `atlas-dep-audit` continues
to supply SBOM and OSV vulnerability evidence. The rollout changes no
`atlas-dep-audit` scanner, policy, workflow, or credential. The repository
itself is excluded from this rollout; no Dependabot configuration or
auto-merge workflow is proposed for it.

`simple-proxy` remains `deprecated`, `internal`, and `external-derived`. It gets
vulnerability alerts only. It never gets a version-update configuration,
automated security fixes, an auto-merge workflow, or a dependency-version pull
request. Archived repositories get no change.

## Credentials

Use a new fine-grained token in the local `ATLAS_DEPENDABOT_READ_TOKEN`
environment variable. Select only the repositories owned by `AtlasReaper311`
and grant `Metadata: read` and `Contents: read`. Read access to repository
administration may be needed to prove required status checks. Do not commit the
token, add it as a repository secret, print it, or reuse `GH_DIGEST_PAT`.

The planning scripts use Python's standard-library `urllib` client. This keeps
the same command path on Windows, WSL2, and Ubuntu and adds no package install.

## Reconcile the estate

Run reconciliation before generating a plan:

```bash
python3 scripts/estate_repo_diff.py
```

The command reads authenticated `/user/repos` results so private owner
repositories are included. It writes `estate-repo-diff.md` for review and
`estate-repo-diff.json` for exact machine input in the operating system's
temporary directory. On WSL2 and Ubuntu this is normally `/tmp`; on Windows it
uses the directory reported by Python's `tempfile.gettempdir()`. It changes no
GitHub or registry state. Authentication or API failure returns a nonzero exit
because an incomplete private-repository list is not a safe rollout basis.

The first mismatch section lists live repositories that need classification.
Do not add them automatically. The second lists possible renames, deletions, or
token-access problems. Only the confirmed intersection is eligible for the
plan.

## Generate the dry-run plan

```bash
python3 scripts/dependabot_rollout.py
```

The default output is `dependabot-rollout-plan` below the same operating system
temporary directory. Review `summary.md`, `plan.json`, and every proposed file
below its repository directory. The plan records registry and reconciliation
digests. Existing Dependabot files that do not match are blockers and are never
overwritten silently.

Production and runtime-service repositories run weekly at 04:00 Europe/London
on Monday. Active non-runtime repositories run monthly at 04:00 on the first
calendar day, which is GitHub's documented monthly behavior. The `day` option
is valid only for weekly schedules.

Minor and patch updates are grouped per ecosystem. Major updates stay
individual and the common workflow adds `dependabot-major`. Each repository
caller pins the central `atlas-infra` reusable policy to a complete commit SHA.
The reusable workflow uses the `pull_request` event and verifies both the event
actor and pull request author before it reads metadata. It checks out only the
same immutable `atlas-infra` policy commit, never pull request code.

The common workflow keeps workflow-level permissions read-only. Its guarded
review job alone receives repository-scoped contents and pull-request write
permissions. This permits the opt-in label, approval, and auto-merge steps
without granting write access to unrelated jobs.

Auto-merge is off by default. The common workflow considers it only when the
repository variable `DEPENDABOT_AUTOMERGE_ENABLED` is exactly `true`. The
initial policy accepts only one ungrouped npm patch update to a stable direct
development dependency. Production, indirect, grouped, major, minor, `0.x`,
Docker, Python, GitHub Actions, and maintainer-modified updates remain manual.

An eligible candidate is queried against OSV at its proposed version. An active
advisory, malformed response, timeout, or OSV outage makes the update manual.
This query is an extra merge guard and does not replace `atlas-dep-audit`.

Do not set the opt-in variable until the default branch has an active ruleset or
branch protection rule requiring at least one repository-native passing check,
repository auto-merge is enabled, and the repository has no deployment on a
merge to its default branch. GitHub then holds the squash merge until all
required checks and reviews pass.

GitHub Free includes repository auto-merge for public repositories, not private
repositories. To preserve the free-tier rule, keep
`DEPENDABOT_AUTOMERGE_ENABLED` unset in every private repository and merge its
dependency pull requests manually. Do not upgrade a GitHub plan for this
rollout.

Pilot one public, active, non-runtime repository first. Keep every production
or deploy-on-default-branch repository manual. Expand the allowlist only after
the pilot records an eligible patch, an ineligible update, a failing required
check, and an OSV failure path without an unintended merge.

Failure diagnosis and the immediate opt-out command are in the
[`Dependabot auto-merge runbook`](runbooks/dependabot-automerge-ineligible.md).

## Apply after review

`dependabot_rollout.py --apply` refuses. This is an intentional enforcement of
the existing `atlas-gardener` ownership boundary. A separately reviewed
gardener execution phase must consume the exact plan digest, regenerate and
verify each patch, request confirmation for each repository, create a unique
branch, and open a draft pull request. It must use a selected-repository GitHub
App installation token and must not merge, deploy, force-push, or alter branch
protection.

Before that execution phase, create the `dependencies`, ecosystem, and
`dependabot-major` labels named in the plan. For a deprecated repository, enable
only native vulnerability alerts through repository settings. Do not enable
automated security fixes for `simple-proxy`.

## Onboard a repository later

1. Run `estate_repo_diff.py` and review both mismatch sections.
2. Classify the repository on lifecycle, scope, and provenance axes through the
   normal registry review. An archived repository stays read-only.
3. Merge the approved registry change and rerun registry validation.
4. Run `dependabot_rollout.py` and review the new reconciliation and plan
   digests.
5. Confirm detected manifest directories, default branch, labels, required
   checks, schedule, and collision status.
6. Submit only that reviewed repository proposal through the approved gardener
   execution phase.

## Refusal and recovery

Stop when GitHub and registry state differ, ecosystem detection returns none,
required state cannot be read, or an existing configuration collides. Resolve
the source-of-truth issue and produce a new plan. A stale plan is never an
authority to write.

The generated pull requests remain draft and repository-owned. Close a rejected
pull request and delete its feature branch through normal GitHub review. No
default branch, branch protection rule, deployment, secret, or provider state is
changed by the planning tools.
