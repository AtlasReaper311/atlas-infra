#!/usr/bin/env bash
set -eu

# Atlas Systems GitHub provider-guard Wave 1 runner.
# Default mode is read-only inspection. Provider writes require an exact
# confirmation phrase and are intentionally limited to the two repositories
# declared below.

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-1}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

REPOSITORIES='atlas-bootstrap|9|build
atlas-resource-audit|11|Offline resource audit'

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'ERROR: required command is unavailable: %s\n' "$1" >&2
    exit 1
  }
}

write_sha256s() {
  evidence_dir="$1"
  output_file="$2"

  if command -v sha256sum >/dev/null 2>&1
  then
    digest_command="sha256sum"
  elif command -v shasum >/dev/null 2>&1
  then
    digest_command="shasum -a 256"
  else
    printf 'ERROR: neither sha256sum nor shasum is available.\n' >&2
    exit 1
  fi

  : >"$output_file"

  find "$evidence_dir" -type f ! -name SHA256SUMS.txt -print |
    LC_ALL=C sort |
    while IFS= read -r evidence_file
    do
      if [ "$digest_command" = "sha256sum" ]
      then
        sha256sum "$evidence_file"
      else
        shasum -a 256 "$evidence_file"
      fi
    done >"$output_file"
}

verify_required_check() {
  repository="$1"
  pull_number="$2"
  expected_context="$3"
  pull_file="$4"
  checks_file="$5"

  gh api "/repos/${OWNER}/${repository}/pulls/${pull_number}" >"$pull_file"

  jq -e \
    --arg owner "$OWNER" \
    '.state == "open" and .base.ref == "main" and .head.repo.owner.login == $owner' \
    "$pull_file" >/dev/null

  head_sha="$(jq -r '.head.sha' "$pull_file")"

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/commits/${head_sha}/check-runs?per_page=100" \
    >"$checks_file"

  jq -e \
    --arg context "$expected_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '[.check_runs[] | select(
      .name == $context and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "$checks_file" >/dev/null
}

verify_repository_baseline() {
  repository="$1"
  repository_file="$2"
  rulesets_file="$3"
  protection_file="$4"

  gh api "/repos/${OWNER}/${repository}" >"$repository_file"

  jq -e \
    '.full_name == ("AtlasReaper311/" + .name) and
     .default_branch == "main" and
     .visibility == "public" and
     .archived == false and
     .allow_auto_merge == false' \
    "$repository_file" >/dev/null

  gh api "/repos/${OWNER}/${repository}/rulesets?per_page=100" >"$rulesets_file"

  jq -e \
    '[.[] | select(.target == "branch" and .enforcement == "active")] | length == 0' \
    "$rulesets_file" >/dev/null

  if gh api "/repos/${OWNER}/${repository}/branches/main/protection" >"$protection_file" 2>"${protection_file}.error"
  then
    printf 'ERROR: classic branch protection now exists for %s; refusing migration-by-assumption.\n' "$repository" >&2
    exit 1
  fi

  if ! grep -q 'Branch not protected' "${protection_file}.error" && \
     ! grep -q 'HTTP 404' "${protection_file}.error"
  then
    printf 'ERROR: could not prove classic protection absence for %s.\n' "$repository" >&2
    cat "${protection_file}.error" >&2
    exit 1
  fi
}

build_ruleset_payload() {
  expected_context="$1"
  output_file="$2"

  jq -n \
    --arg name "$RULESET_NAME" \
    --arg context "$expected_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '{
      name: $name,
      target: "branch",
      enforcement: "active",
      bypass_actors: [],
      conditions: {
        ref_name: {
          include: ["~DEFAULT_BRANCH"],
          exclude: []
        }
      },
      rules: [
        {type: "deletion"},
        {type: "non_fast_forward"},
        {
          type: "pull_request",
          parameters: {
            dismiss_stale_reviews_on_push: false,
            require_code_owner_review: false,
            require_last_push_approval: false,
            required_approving_review_count: 0,
            required_review_thread_resolution: false
          }
        },
        {
          type: "required_status_checks",
          parameters: {
            do_not_enforce_on_create: false,
            required_status_checks: [
              {
                context: $context,
                integration_id: $integration_id
              }
            ],
            strict_required_status_checks_policy: false
          }
        }
      ]
    }' >"$output_file"
}

verify_ruleset_readback() {
  expected_context="$1"
  created_file="$2"
  readback_file="$3"
  active_rules_file="$4"
  repository_file="$5"

  ruleset_id="$(jq -r '.id' "$created_file")"

  jq -e \
    --arg name "$RULESET_NAME" \
    --arg context "$expected_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '.id != null and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and
     ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}])' \
    "$readback_file" >/dev/null

  jq -e \
    --argjson ruleset_id "$ruleset_id" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) ==
     (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "$active_rules_file" >/dev/null

  jq -e '.allow_auto_merge == false' "$repository_file" >/dev/null
}

printf 'PART 0: Preflight\n'
require_command gh
require_command jq

gh auth status >/dev/null
AUTHENTICATED_LOGIN="$(gh api /user --jq '.login')"

if [ "$AUTHENTICATED_LOGIN" != "$OWNER" ]
then
  printf 'ERROR: gh is authenticated as %s, expected %s.\n' "$AUTHENTICATED_LOGIN" "$OWNER" >&2
  exit 1
fi

case "$MODE" in
  inspect|apply)
    ;;
  *)
    printf 'ERROR: MODE must be inspect or apply.\n' >&2
    exit 1
    ;;
esac

if [ "$MODE" = "apply" ] && [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 1" ]
then
  printf 'ERROR: provider write refused. Set the exact approved confirmation phrase.\n' >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"

printf 'PART 1: Read-only baseline and native-check verification\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository pull_number expected_context
 do
  repo_dir="${EVIDENCE_DIR}/${repository}"
  mkdir -p "$repo_dir"

  verify_repository_baseline \
    "$repository" \
    "${repo_dir}/repository-before.json" \
    "${repo_dir}/rulesets-before.json" \
    "${repo_dir}/classic-protection-before.json"

  verify_required_check \
    "$repository" \
    "$pull_number" \
    "$expected_context" \
    "${repo_dir}/validation-pr.json" \
    "${repo_dir}/validation-check-runs.json"

  build_ruleset_payload \
    "$expected_context" \
    "${repo_dir}/ruleset-request.json"

  printf 'Verified %s with required context: %s\n' "$repository" "$expected_context"
 done

if [ "$MODE" = "inspect" ]
then
  printf 'PART 2: Inspection complete; no provider write performed.\n'
  write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"
  printf 'Evidence: %s\n' "$EVIDENCE_DIR"
  exit 0
fi

printf 'PART 2: Apply exactly two approved rulesets\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository pull_number expected_context
 do
  repo_dir="${EVIDENCE_DIR}/${repository}"

  gh api \
    --method POST \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rulesets" \
    --input "${repo_dir}/ruleset-request.json" \
    >"${repo_dir}/ruleset-created.json"

  ruleset_id="$(jq -r '.id' "${repo_dir}/ruleset-created.json")"

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rulesets/${ruleset_id}" \
    >"${repo_dir}/ruleset-readback.json"

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rules/branches/main" \
    >"${repo_dir}/active-rules-after.json"

  gh api "/repos/${OWNER}/${repository}" >"${repo_dir}/repository-after.json"

  verify_ruleset_readback \
    "$expected_context" \
    "${repo_dir}/ruleset-created.json" \
    "${repo_dir}/ruleset-readback.json" \
    "${repo_dir}/active-rules-after.json" \
    "${repo_dir}/repository-after.json"

  printf 'Created and verified %s ruleset ID %s\n' "$repository" "$ruleset_id"
 done

printf 'PART 3: Final evidence identity\n'
write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"

printf 'Wave 1 provider write complete.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
printf 'Do not merge validation PRs or begin another wave until this evidence and a new stamped scoreboard are reviewed.\n'
