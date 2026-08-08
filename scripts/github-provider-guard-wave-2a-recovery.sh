#!/usr/bin/env bash
set -eu

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
GARDENER_RULESET_ID="20576711"
GARDENER_MAIN="319465dcea68a8fefead3e7d90e82b79078cb34d"
INTERFACE_MAIN="21a1a168e3b25e916555ce4edd4229bd7c061ecb"
INTERFACE_PR="14"
INTERFACE_HEAD="1f26360d938b589cf8a562ca308fd6ca3b4a2b3f"
INTERFACE_CONTEXT="Validate interface kit"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-2a-recovery}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'ERROR: required command is unavailable: %s\n' "$1" >&2
    exit 1
  }
}

write_sha256s() {
  local evidence_dir="$1"
  local output_file="$2"
  : >"$output_file"
  if command -v sha256sum >/dev/null 2>&1
  then
    find "$evidence_dir" -type f ! -name SHA256SUMS.txt -print | LC_ALL=C sort | while IFS= read -r path
    do
      sha256sum "$path"
    done >"$output_file"
  elif command -v shasum >/dev/null 2>&1
  then
    find "$evidence_dir" -type f ! -name SHA256SUMS.txt -print | LC_ALL=C sort | while IFS= read -r path
    do
      shasum -a 256 "$path"
    done >"$output_file"
  else
    printf 'ERROR: neither sha256sum nor shasum is available.\n' >&2
    exit 1
  fi
}

verify_gardener_completed_state() {
  local repo_dir="$1"
  mkdir -p "$repo_dir"

  gh api "/repos/${OWNER}/atlas-gardener/rulesets/${GARDENER_RULESET_ID}" >"${repo_dir}/ruleset-readback.json"
  gh api "/repos/${OWNER}/atlas-gardener/rules/branches/main" >"${repo_dir}/active-rules.json"
  gh api "/repos/${OWNER}/atlas-gardener" >"${repo_dir}/repository.json"
  gh api "/repos/${OWNER}/atlas-gardener/commits/main" >"${repo_dir}/main.json"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_MODE" >"${repo_dir}/variable-mode.json"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_WRITE_GATE" >"${repo_dir}/variable-write-gate.json"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_WRITE_TARGETS_JSON" >"${repo_dir}/variable-write-targets.json"

  jq -e --argjson id "$GARDENER_RULESET_ID" --arg name "$RULESET_NAME" --argjson integration_id "$INTEGRATION_ID" '
    .id == $id and .name == $name and .target == "branch" and .enforcement == "active" and
    (.bypass_actors | length) == 0 and .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and
    .conditions.ref_name.exclude == [] and
    ([.rules[].type] | sort) == (["deletion","non_fast_forward","pull_request","required_status_checks"] | sort) and
    ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
    ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false) and
    ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context:"test",integration_id:$integration_id}]) and
    ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)
  ' "${repo_dir}/ruleset-readback.json" >/dev/null

  jq -e --argjson id "$GARDENER_RULESET_ID" '
    ([.[] | select(.ruleset_id == $id) | .type] | sort) ==
    (["deletion","non_fast_forward","pull_request","required_status_checks"] | sort)
  ' "${repo_dir}/active-rules.json" >/dev/null

  jq -e '.allow_auto_merge == false' "${repo_dir}/repository.json" >/dev/null
  jq -e --arg sha "$GARDENER_MAIN" '.sha == $sha' "${repo_dir}/main.json" >/dev/null
  jq -e '.name == "ATLAS_GARDENER_MODE" and .value == "automerge-low-risk"' "${repo_dir}/variable-mode.json" >/dev/null
  jq -e '.name == "ATLAS_GARDENER_WRITE_GATE" and .value == "enabled"' "${repo_dir}/variable-write-gate.json" >/dev/null
  jq -e '.name == "ATLAS_GARDENER_WRITE_TARGETS_JSON" and .value == "[\"AtlasReaper311/atlas-doc-viewer\",\"AtlasReaper311/atlas-quota-watch\",\"AtlasReaper311/site-pulse\",\"AtlasReaper311/specular-sonify\",\"AtlasReaper311/status\"]"' "${repo_dir}/variable-write-targets.json" >/dev/null
}

verify_interface_baseline() {
  local repo_dir="$1"
  mkdir -p "$repo_dir"

  gh api "/repos/${OWNER}/atlas-interface-kit" >"${repo_dir}/repository-before.json"
  gh api "/repos/${OWNER}/atlas-interface-kit/commits/main" >"${repo_dir}/main-before.json"
  gh api "/repos/${OWNER}/atlas-interface-kit/rulesets?per_page=100" >"${repo_dir}/rulesets-before.json"
  gh api "/repos/${OWNER}/atlas-interface-kit/pulls/${INTERFACE_PR}" >"${repo_dir}/validation-pr.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/atlas-interface-kit/commits/${INTERFACE_HEAD}/check-runs?per_page=100" >"${repo_dir}/validation-check-runs.json"

  jq -e '.default_branch == "main" and .visibility == "public" and .archived == false and .allow_auto_merge == false' "${repo_dir}/repository-before.json" >/dev/null
  jq -e --arg sha "$INTERFACE_MAIN" '.sha == $sha' "${repo_dir}/main-before.json" >/dev/null
  jq -e --arg name "$RULESET_NAME" '([.[] | select(.target == "branch" and .enforcement == "active")] | length) == 0 and ([.[] | select(.name == $name)] | length) == 0' "${repo_dir}/rulesets-before.json" >/dev/null
  jq -e --arg head "$INTERFACE_HEAD" --arg main "$INTERFACE_MAIN" '.number == 14 and .state == "closed" and .merged == true and .base.ref == "main" and .head.sha == $head and .merge_commit_sha == $main and .user.login == "AtlasReaper311"' "${repo_dir}/validation-pr.json" >/dev/null
  jq -e --arg head "$INTERFACE_HEAD" --arg context "$INTERFACE_CONTEXT" --argjson integration_id "$INTEGRATION_ID" '[.check_runs[] | select(.name == $context and .head_sha == $head and .status == "completed" and .conclusion == "success" and .app.id == $integration_id)] | length == 1' "${repo_dir}/validation-check-runs.json" >/dev/null

  if gh api "/repos/${OWNER}/atlas-interface-kit/branches/main/protection" >"${repo_dir}/classic-protection-before.json" 2>"${repo_dir}/classic-protection-before.json.error"
  then
    printf 'ERROR: Interface Kit classic protection now exists; refusing recovery write.\n' >&2
    exit 1
  fi

  if ! grep -q 'Branch not protected' "${repo_dir}/classic-protection-before.json.error" && ! grep -q 'HTTP 404' "${repo_dir}/classic-protection-before.json.error"
  then
    printf 'ERROR: could not prove Interface Kit classic-protection absence.\n' >&2
    exit 1
  fi
}

build_interface_payload() {
  local output_file="$1"
  jq -n --arg name "$RULESET_NAME" --arg context "$INTERFACE_CONTEXT" --argjson integration_id "$INTEGRATION_ID" '{
    name:$name,target:"branch",enforcement:"active",bypass_actors:[],
    conditions:{ref_name:{include:["~DEFAULT_BRANCH"],exclude:[]}},
    rules:[
      {type:"deletion"},
      {type:"non_fast_forward"},
      {type:"pull_request",parameters:{dismiss_stale_reviews_on_push:false,require_code_owner_review:false,require_last_push_approval:false,required_approving_review_count:0,required_review_thread_resolution:false}},
      {type:"required_status_checks",parameters:{do_not_enforce_on_create:false,required_status_checks:[{context:$context,integration_id:$integration_id}],strict_required_status_checks_policy:false}}
    ]
  }' >"$output_file"
}

verify_interface_readback() {
  local repo_dir="$1"
  local ruleset_id
  ruleset_id="$(jq -r '.id' "${repo_dir}/ruleset-created.json")"

  jq -e --arg name "$RULESET_NAME" --arg context "$INTERFACE_CONTEXT" --argjson integration_id "$INTEGRATION_ID" '
    .id != null and .name == $name and .target == "branch" and .enforcement == "active" and
    (.bypass_actors | length) == 0 and .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and .conditions.ref_name.exclude == [] and
    ([.rules[].type] | sort) == (["deletion","non_fast_forward","pull_request","required_status_checks"] | sort) and
    ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
    ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false) and
    ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context:$context,integration_id:$integration_id}]) and
    ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)
  ' "${repo_dir}/ruleset-readback.json" >/dev/null

  jq -e --argjson id "$ruleset_id" '([.[] | select(.ruleset_id == $id) | .type] | sort) == (["deletion","non_fast_forward","pull_request","required_status_checks"] | sort)' "${repo_dir}/active-rules-after.json" >/dev/null
  jq -e '.allow_auto_merge == false' "${repo_dir}/repository-after.json" >/dev/null
  jq -e --arg sha "$INTERFACE_MAIN" '.sha == $sha' "${repo_dir}/main-after.json" >/dev/null
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
  inspect|apply-interface-kit)
    ;;
  *)
    printf 'ERROR: MODE must be inspect or apply-interface-kit.\n' >&2
    exit 1
    ;;
esac

if [ "$MODE" = "apply-interface-kit" ] && [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 2A INTERFACE KIT RECOVERY" ]
then
  printf 'ERROR: recovery provider write refused.\n' >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"

printf 'PART 1: Verify completed Gardener provider state\n'
verify_gardener_completed_state "${EVIDENCE_DIR}/atlas-gardener"

printf 'PART 2: Verify untouched Interface Kit baseline\n'
verify_interface_baseline "${EVIDENCE_DIR}/atlas-interface-kit"
build_interface_payload "${EVIDENCE_DIR}/atlas-interface-kit/ruleset-request.json"

if [ "$MODE" = "inspect" ]
then
  write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"
  printf 'Recovery inspection complete; no provider write performed.\n'
  exit 0
fi

printf 'PART 3: Apply remaining approved Interface Kit ruleset\n'
gh api --method POST -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/atlas-interface-kit/rulesets" --input "${EVIDENCE_DIR}/atlas-interface-kit/ruleset-request.json" >"${EVIDENCE_DIR}/atlas-interface-kit/ruleset-created.json"
RULESET_ID="$(jq -r '.id' "${EVIDENCE_DIR}/atlas-interface-kit/ruleset-created.json")"
gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/atlas-interface-kit/rulesets/${RULESET_ID}" >"${EVIDENCE_DIR}/atlas-interface-kit/ruleset-readback.json"
gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/atlas-interface-kit/rules/branches/main" >"${EVIDENCE_DIR}/atlas-interface-kit/active-rules-after.json"
gh api "/repos/${OWNER}/atlas-interface-kit" >"${EVIDENCE_DIR}/atlas-interface-kit/repository-after.json"
gh api "/repos/${OWNER}/atlas-interface-kit/commits/main" >"${EVIDENCE_DIR}/atlas-interface-kit/main-after.json"
verify_interface_readback "${EVIDENCE_DIR}/atlas-interface-kit"

printf 'PART 4: Re-verify Gardener remained unchanged\n'
verify_gardener_completed_state "${EVIDENCE_DIR}/atlas-gardener-after-interface-write"

write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"
printf 'Wave 2A recovery write complete. Interface Kit ruleset ID %s created and verified.\n' "$RULESET_ID"
printf 'atlas-journey-watch was not touched. Wave 3 was not started.\n'
