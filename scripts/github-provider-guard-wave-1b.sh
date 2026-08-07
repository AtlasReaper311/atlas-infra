#!/usr/bin/env bash
set -eu

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
REPOSITORY="ollama-rag-kit"
EXPECTED_MAIN_SHA="d0060829dd474d8d8a57b11694ca03411927bf9f"
VALIDATION_PR="16"
EXPECTED_VALIDATION_HEAD="c88e6277f1f2b9bebc8f607bbb59a7d37860e92a"
EXPECTED_CONTEXT="Build and smoke-check"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-1b}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"
REPO_DIR="${EVIDENCE_DIR}/${REPOSITORY}"

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

verify_repository_baseline() {
  gh api "/repos/${OWNER}/${REPOSITORY}" >"${REPO_DIR}/repository-before.json"

  jq -e \
    --arg repository "${OWNER}/${REPOSITORY}" \
    --arg main_sha "$EXPECTED_MAIN_SHA" \
    '.full_name == $repository and
     .default_branch == "main" and
     .visibility == "public" and
     .archived == false and
     .allow_auto_merge == false' \
    "${REPO_DIR}/repository-before.json" >/dev/null

  gh api "/repos/${OWNER}/${REPOSITORY}/commits/main" >"${REPO_DIR}/main-before.json"

  jq -e \
    --arg main_sha "$EXPECTED_MAIN_SHA" \
    '.sha == $main_sha' \
    "${REPO_DIR}/main-before.json" >/dev/null

  gh api "/repos/${OWNER}/${REPOSITORY}/rulesets?per_page=100" >"${REPO_DIR}/rulesets-before.json"

  jq -e \
    '[.[] | select(.target == "branch" and .enforcement == "active")] | length == 0' \
    "${REPO_DIR}/rulesets-before.json" >/dev/null

  if gh api "/repos/${OWNER}/${REPOSITORY}/branches/main/protection" >"${REPO_DIR}/classic-protection-before.json" 2>"${REPO_DIR}/classic-protection-before.json.error"
  then
    printf 'ERROR: classic branch protection exists; refusing migration-by-assumption.\n' >&2
    exit 1
  fi

  if ! grep -q 'Branch not protected' "${REPO_DIR}/classic-protection-before.json.error" && \
     ! grep -q 'HTTP 404' "${REPO_DIR}/classic-protection-before.json.error"
  then
    printf 'ERROR: could not prove classic protection absence.\n' >&2
    cat "${REPO_DIR}/classic-protection-before.json.error" >&2
    exit 1
  fi

  if gh api "/repos/${OWNER}/${REPOSITORY}/contents/.github/workflows/deploy.yml?ref=main" >"${REPO_DIR}/deploy-workflow-before.json" 2>"${REPO_DIR}/deploy-workflow-before.json.error"
  then
    printf 'ERROR: a deploy workflow now exists; refusing stale non-runtime assumptions.\n' >&2
    exit 1
  fi

  if ! grep -q 'Not Found' "${REPO_DIR}/deploy-workflow-before.json.error" && \
     ! grep -q 'HTTP 404' "${REPO_DIR}/deploy-workflow-before.json.error"
  then
    printf 'ERROR: could not prove deploy workflow absence.\n' >&2
    cat "${REPO_DIR}/deploy-workflow-before.json.error" >&2
    exit 1
  fi
}

verify_required_check() {
  gh api "/repos/${OWNER}/${REPOSITORY}/pulls/${VALIDATION_PR}" >"${REPO_DIR}/validation-pr.json"

  jq -e \
    --arg owner "$OWNER" \
    --arg main_sha "$EXPECTED_MAIN_SHA" \
    --arg head_sha "$EXPECTED_VALIDATION_HEAD" \
    '.state == "open" and
     .base.ref == "main" and
     .base.sha == $main_sha and
     .head.sha == $head_sha and
     .head.repo.owner.login == $owner' \
    "${REPO_DIR}/validation-pr.json" >/dev/null

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${REPOSITORY}/commits/${EXPECTED_VALIDATION_HEAD}/check-runs?per_page=100" \
    >"${REPO_DIR}/validation-check-runs.json"

  jq -e \
    --arg context "$EXPECTED_CONTEXT" \
    --argjson integration_id "$INTEGRATION_ID" \
    '[.check_runs[] | select(
      .name == $context and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "${REPO_DIR}/validation-check-runs.json" >/dev/null
}

build_ruleset_payload() {
  jq -n \
    --arg name "$RULESET_NAME" \
    --arg context "$EXPECTED_CONTEXT" \
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
    }' >"${REPO_DIR}/ruleset-request.json"
}

verify_ruleset_readback() {
  ruleset_id="$(jq -r '.id' "${REPO_DIR}/ruleset-created.json")"

  jq -e \
    --arg name "$RULESET_NAME" \
    --arg context "$EXPECTED_CONTEXT" \
    --argjson integration_id "$INTEGRATION_ID" \
    '.id != null and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and
     ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}]) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "${REPO_DIR}/ruleset-readback.json" >/dev/null

  jq -e \
    --argjson ruleset_id "$ruleset_id" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) ==
     (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "${REPO_DIR}/active-rules-after.json" >/dev/null

  jq -e '.allow_auto_merge == false' "${REPO_DIR}/repository-after.json" >/dev/null
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

if [ "$MODE" = "apply" ] && [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 1B" ]
then
  printf 'ERROR: provider write refused. Set the exact approved confirmation phrase.\n' >&2
  exit 1
fi

mkdir -p "$REPO_DIR"

printf 'PART 1: Read-only baseline and native-check verification\n'
verify_repository_baseline
verify_required_check
build_ruleset_payload
printf 'Verified %s with required context: %s\n' "$REPOSITORY" "$EXPECTED_CONTEXT"

if [ "$MODE" = "inspect" ]
then
  printf 'PART 2: Inspection complete; no provider write performed.\n'
  write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"
  printf 'Evidence: %s\n' "$EVIDENCE_DIR"
  exit 0
fi

printf 'PART 2: Apply exactly one approved Wave 1B ruleset\n'
gh api \
  --method POST \
  -H 'Accept: application/vnd.github+json' \
  "/repos/${OWNER}/${REPOSITORY}/rulesets" \
  --input "${REPO_DIR}/ruleset-request.json" \
  >"${REPO_DIR}/ruleset-created.json"

ruleset_id="$(jq -r '.id' "${REPO_DIR}/ruleset-created.json")"

gh api \
  -H 'Accept: application/vnd.github+json' \
  "/repos/${OWNER}/${REPOSITORY}/rulesets/${ruleset_id}" \
  >"${REPO_DIR}/ruleset-readback.json"

gh api \
  -H 'Accept: application/vnd.github+json' \
  "/repos/${OWNER}/${REPOSITORY}/rules/branches/main" \
  >"${REPO_DIR}/active-rules-after.json"

gh api "/repos/${OWNER}/${REPOSITORY}" >"${REPO_DIR}/repository-after.json"

verify_ruleset_readback

printf 'Created and verified %s ruleset ID %s\n' "$REPOSITORY" "$ruleset_id"

printf 'PART 3: Final evidence identity\n'
write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"

printf 'Wave 1B provider write complete.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
printf 'Do not merge Dependabot PRs or begin Wave 2.\n'
