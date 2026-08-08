#!/usr/bin/env bash
set -eu

# Atlas Systems GitHub provider-guard Wave 2B reconciliation runner.
# Default mode is read-only inspection. Provider mutation requires an exact
# confirmation phrase and is limited to updating existing ruleset 19154613
# in place. This runner never creates or deletes a ruleset and never changes
# repository auto-merge or Actions variables.

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"

OWNER="AtlasReaper311"
REPOSITORY="atlas-journey-watch"
FULL_REPOSITORY="${OWNER}/${REPOSITORY}"

EXPECTED_MAIN_SHA="a124d23ba4444522c206ae3c169165b4e0ef8019"
EXPECTED_RULESET_ID="19154613"
EXPECTED_RULESET_NAME="Require native pull request validation"
EXPECTED_PR="12"
EXPECTED_PR_HEAD="acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022"
EXPECTED_CONTEXT="Offline journey validation"
EXPECTED_INTEGRATION_ID="15368"
EXPECTED_VARIABLE="DEPENDABOT_AUTOMERGE_ENABLED"
EXPECTED_VARIABLE_VALUE="true"

EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-2b-reconcile}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'ERROR: required command is unavailable: %s\n' "$1" >&2
    exit 1
  }
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1
  then
    sha256sum "$1" | awk '{print $1}'
    return
  fi

  if command -v shasum >/dev/null 2>&1
  then
    shasum -a 256 "$1" | awk '{print $1}'
    return
  fi

  printf 'ERROR: neither sha256sum nor shasum is available.\n' >&2
  exit 1
}

capture_pr_automerge() {
  destination="$1"

  gh pr view "${EXPECTED_PR}" \
    --repo "${FULL_REPOSITORY}" \
    --json number,state,isDraft,mergeable,mergeStateStatus,headRefOid,baseRefOid,author,autoMergeRequest \
    >"${destination}"
}

verify_baseline() {
  evidence_dir="$1"

  gh api "/repos/${FULL_REPOSITORY}" >"${evidence_dir}/repository-before.json"
  gh api "/repos/${FULL_REPOSITORY}/commits/main" >"${evidence_dir}/main-before.json"
  gh api -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/rulesets?per_page=100" \
    >"${evidence_dir}/rulesets-before.json"
  gh api -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" \
    >"${evidence_dir}/ruleset-before.json"
  gh api -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/rules/branches/main" \
    >"${evidence_dir}/active-rules-before.json"

  if gh api "/repos/${FULL_REPOSITORY}/branches/main/protection" \
    >"${evidence_dir}/classic-protection-before.json" \
    2>"${evidence_dir}/classic-protection-before.json.error"
  then
    printf 'ERROR: classic branch protection appeared; refusing in-place reconciliation.\n' >&2
    exit 1
  fi

  if ! grep -q 'HTTP 404' "${evidence_dir}/classic-protection-before.json.error" && \
     ! grep -q 'Branch not protected' "${evidence_dir}/classic-protection-before.json.error"
  then
    printf 'ERROR: could not prove classic protection absence.\n' >&2
    cat "${evidence_dir}/classic-protection-before.json.error" >&2
    exit 1
  fi

  gh api \
    "/repos/${FULL_REPOSITORY}/actions/variables/${EXPECTED_VARIABLE}" \
    >"${evidence_dir}/dependabot-automerge-variable-before.json"

  gh api \
    "/repos/${FULL_REPOSITORY}/pulls/${EXPECTED_PR}" \
    >"${evidence_dir}/validation-pr-before.json"

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/commits/${EXPECTED_PR_HEAD}/check-runs?per_page=100" \
    >"${evidence_dir}/validation-check-runs-before.json"

  capture_pr_automerge "${evidence_dir}/validation-pr-automerge-before.json"

  jq -e \
    --arg full_repository "${FULL_REPOSITORY}" \
    '.full_name == $full_repository and
     .default_branch == "main" and
     .visibility == "public" and
     .archived == false and
     .allow_auto_merge == true' \
    "${evidence_dir}/repository-before.json" >/dev/null

  jq -e \
    --arg expected_main "${EXPECTED_MAIN_SHA}" \
    '.sha == $expected_main' \
    "${evidence_dir}/main-before.json" >/dev/null

  jq -e \
    --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
    '([.[] | select(.target == "branch" and .enforcement == "active")] | length) == 1 and
     ([.[] | select(.id == $ruleset_id and .target == "branch" and .enforcement == "active")] | length) == 1' \
    "${evidence_dir}/rulesets-before.json" >/dev/null

  jq -e \
    --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
    --arg name "${EXPECTED_RULESET_NAME}" \
    --arg context "${EXPECTED_CONTEXT}" \
    --argjson integration_id "${EXPECTED_INTEGRATION_ID}" \
    '.id == $ruleset_id and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["refs/heads/main"] and
     .conditions.ref_name.exclude == [] and
     ([.rules[].type] | sort) == ["required_status_checks"] and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.do_not_enforce_on_create == false) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}]) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == true)' \
    "${evidence_dir}/ruleset-before.json" >/dev/null

  jq -e \
    --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == ["required_status_checks"]' \
    "${evidence_dir}/active-rules-before.json" >/dev/null

  jq -e \
    --arg name "${EXPECTED_VARIABLE}" \
    --arg value "${EXPECTED_VARIABLE_VALUE}" \
    '.name == $name and .value == $value' \
    "${evidence_dir}/dependabot-automerge-variable-before.json" >/dev/null

  jq -e \
    --arg expected_main "${EXPECTED_MAIN_SHA}" \
    --arg expected_head "${EXPECTED_PR_HEAD}" \
    '.number == 12 and
     .state == "open" and
     .merged == false and
     .base.ref == "main" and
     .base.sha == $expected_main and
     .head.sha == $expected_head and
     .user.login == "dependabot[bot]" and
     .mergeable == true' \
    "${evidence_dir}/validation-pr-before.json" >/dev/null

  jq -e \
    --arg context "${EXPECTED_CONTEXT}" \
    --arg expected_head "${EXPECTED_PR_HEAD}" \
    --argjson integration_id "${EXPECTED_INTEGRATION_ID}" \
    '[.check_runs[] | select(
      .name == $context and
      .head_sha == $expected_head and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "${evidence_dir}/validation-check-runs-before.json" >/dev/null

  jq -e \
    --arg expected_head "${EXPECTED_PR_HEAD}" \
    '.number == 12 and
     .state == "OPEN" and
     .headRefOid == $expected_head and
     .mergeable == "MERGEABLE" and
     .autoMergeRequest == null' \
    "${evidence_dir}/validation-pr-automerge-before.json" >/dev/null
}

build_reconciled_payload() {
  output_file="$1"

  jq -n \
    --arg name "${EXPECTED_RULESET_NAME}" \
    --arg context "${EXPECTED_CONTEXT}" \
    --argjson integration_id "${EXPECTED_INTEGRATION_ID}" \
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
    }' >"${output_file}"
}

verify_reconciled_state() {
  evidence_dir="$1"

  gh api -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" \
    >"${evidence_dir}/ruleset-after.json"
  gh api -H 'Accept: application/vnd.github+json' \
    "/repos/${FULL_REPOSITORY}/rules/branches/main" \
    >"${evidence_dir}/active-rules-after.json"
  gh api "/repos/${FULL_REPOSITORY}" >"${evidence_dir}/repository-after.json"
  gh api "/repos/${FULL_REPOSITORY}/commits/main" >"${evidence_dir}/main-after.json"
  gh api \
    "/repos/${FULL_REPOSITORY}/actions/variables/${EXPECTED_VARIABLE}" \
    >"${evidence_dir}/dependabot-automerge-variable-after.json"
  capture_pr_automerge "${evidence_dir}/validation-pr-automerge-after.json"

  jq -e \
    --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
    --arg name "${EXPECTED_RULESET_NAME}" \
    --arg context "${EXPECTED_CONTEXT}" \
    --argjson integration_id "${EXPECTED_INTEGRATION_ID}" \
    '.id == $ruleset_id and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and
     .conditions.ref_name.exclude == [] and
     ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.do_not_enforce_on_create == false) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}]) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "${evidence_dir}/ruleset-after.json" >/dev/null

  jq -e \
    --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) ==
     (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "${evidence_dir}/active-rules-after.json" >/dev/null

  jq -e '.allow_auto_merge == true' \
    "${evidence_dir}/repository-after.json" >/dev/null

  jq -e \
    --arg expected_main "${EXPECTED_MAIN_SHA}" \
    '.sha == $expected_main' \
    "${evidence_dir}/main-after.json" >/dev/null

  jq -e \
    --arg name "${EXPECTED_VARIABLE}" \
    --arg value "${EXPECTED_VARIABLE_VALUE}" \
    '.name == $name and .value == $value' \
    "${evidence_dir}/dependabot-automerge-variable-after.json" >/dev/null

  jq -e \
    --arg expected_head "${EXPECTED_PR_HEAD}" \
    '.number == 12 and
     .state == "OPEN" and
     .headRefOid == $expected_head and
     .mergeable == "MERGEABLE" and
     .autoMergeRequest == null' \
    "${evidence_dir}/validation-pr-automerge-after.json" >/dev/null
}

write_sha256s() {
  evidence_dir="$1"

  (
    cd "${evidence_dir}"
    : >SHA256SUMS.txt
    for path in $(find . -type f ! -name SHA256SUMS.txt | LC_ALL=C sort)
    do
      digest="$(sha256_file "${path}")"
      printf '%s  %s\n' "${digest}" "${path#./}" >>SHA256SUMS.txt
    done
  )
}

printf 'PART 0: Preflight\n'
require_command gh
require_command jq

gh auth status >/dev/null
AUTHENTICATED_LOGIN="$(gh api /user --jq '.login')"

if [ "${AUTHENTICATED_LOGIN}" != "${OWNER}" ]
then
  printf 'ERROR: gh is authenticated as %s, expected %s.\n' "${AUTHENTICATED_LOGIN}" "${OWNER}" >&2
  exit 1
fi

case "${MODE}" in
  inspect|apply)
    ;;
  *)
    printf 'ERROR: MODE must be inspect or apply.\n' >&2
    exit 1
    ;;
esac

if [ "${MODE}" = "apply" ] && \
   [ "${CONFIRMATION}" != "APPLY GITHUB PROVIDER GUARD WAVE 2B" ]
then
  printf 'ERROR: provider write refused. Set the exact approved confirmation phrase.\n' >&2
  exit 1
fi

mkdir -p "${EVIDENCE_DIR}"

printf 'PART 1: Verify exact pre-reconciliation provider state\n'
verify_baseline "${EVIDENCE_DIR}"
build_reconciled_payload "${EVIDENCE_DIR}/ruleset-request.json"

if [ "${MODE}" = "inspect" ]
then
  printf 'PART 2: Inspection complete; no provider write performed.\n'
  write_sha256s "${EVIDENCE_DIR}"
  printf 'Evidence: %s\n' "${EVIDENCE_DIR}"
  printf 'Ruleset 19154613 remains unchanged.\n'
  printf 'Repository auto-merge and DEPENDABOT_AUTOMERGE_ENABLED remain unchanged.\n'
  printf 'Wave 3 remains unstarted.\n'
  exit 0
fi

printf 'PART 2: Reconcile existing ruleset 19154613 in place\n'

gh api \
  --method PUT \
  -H 'Accept: application/vnd.github+json' \
  "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" \
  --input "${EVIDENCE_DIR}/ruleset-request.json" \
  >"${EVIDENCE_DIR}/ruleset-update-response.json"

jq -e \
  --argjson ruleset_id "${EXPECTED_RULESET_ID}" \
  '.id == $ruleset_id' \
  "${EVIDENCE_DIR}/ruleset-update-response.json" >/dev/null

printf 'PART 3: Verify reconciled provider state\n'
verify_reconciled_state "${EVIDENCE_DIR}"

printf 'PART 4: Final evidence identity\n'
write_sha256s "${EVIDENCE_DIR}"

printf 'Wave 2B provider reconciliation complete.\n'
printf 'Ruleset 19154613 was updated in place; no second ruleset was created.\n'
printf 'Repository auto-merge remains enabled.\n'
printf 'DEPENDABOT_AUTOMERGE_ENABLED remains true.\n'
printf 'Dependabot PR #12 remains open and was not merged.\n'
printf 'Wave 3 remains unstarted.\n'
printf 'Evidence: %s\n' "${EVIDENCE_DIR}"
