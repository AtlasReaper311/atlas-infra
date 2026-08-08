#!/usr/bin/env bash
set -eu

# Atlas Systems GitHub provider-guard Wave 4B DORA reconciliation runner.
# Default mode is read-only inspection. Provider mutation requires an exact
# confirmation phrase and is limited to updating existing ruleset 19581236 in
# place. This runner never creates or deletes a ruleset.

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
REPOSITORY="atlas-dora"
FULL_REPOSITORY="${OWNER}/${REPOSITORY}"
EXPECTED_MAIN_SHA="fff7c2c5453240dafd693e8a4de645beab523031"
EXPECTED_RULESET_ID="19581236"
EXPECTED_RULESET_NAME="Atlas Gardener native auto-merge barrier"
EXPECTED_NATIVE_CONTEXT="check"
EXPECTED_BARRIER_CONTEXT="Gardener native auto-merge barrier"
EXPECTED_GARDENER_VARIABLE_VALUE="false"
GARDENER_MODE="automerge-low-risk"
GARDENER_WRITE_GATE="enabled"
GARDENER_WRITE_TARGETS='["AtlasReaper311/atlas-doc-viewer","AtlasReaper311/atlas-quota-watch","AtlasReaper311/site-pulse","AtlasReaper311/specular-sonify","AtlasReaper311/status"]'
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-4b}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

require_command() {
  if command -v "$1" >/dev/null 2>&1
  then
    return
  fi
  printf 'ERROR: required command is unavailable: %s\n' "$1" >&2
  exit 1
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

write_sha256s() {
  root="$1"
  (
    cd "$root"
    : >SHA256SUMS.txt
    find . -type f ! -name SHA256SUMS.txt -print | LC_ALL=C sort | while IFS= read -r path
    do
      digest="$(sha256_file "$path")"
      printf '%s  %s\n' "$digest" "${path#./}" >>SHA256SUMS.txt
    done
  )
}

verify_variable_absent() {
  variable_name="$1"
  output="$2"

  if gh api "/repos/${FULL_REPOSITORY}/actions/variables/${variable_name}" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: %s is now present for %s; refusing baseline drift.\n' "$variable_name" "$FULL_REPOSITORY" >&2
    exit 1
  fi

  if grep -q 'HTTP 404' "${output}.error"
  then
    return
  fi
  if grep -q 'Not Found' "${output}.error"
  then
    return
  fi
  printf 'ERROR: could not prove %s absence.\n' "$variable_name" >&2
  cat "${output}.error" >&2
  exit 1
}

verify_classic_absent() {
  output="$1"

  if gh api "/repos/${FULL_REPOSITORY}/branches/main/protection" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: classic branch protection appeared; refusing in-place reconciliation.\n' >&2
    exit 1
  fi

  if grep -q 'HTTP 404' "${output}.error"
  then
    return
  fi
  if grep -q 'Branch not protected' "${output}.error"
  then
    return
  fi
  if grep -q 'Not Found' "${output}.error"
  then
    return
  fi
  printf 'ERROR: could not prove classic protection absence.\n' >&2
  cat "${output}.error" >&2
  exit 1
}

verify_gardener_controller() {
  root="$1"
  mkdir -p "$root"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_MODE" >"${root}/mode.json"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_WRITE_GATE" >"${root}/write-gate.json"
  gh api "/repos/${OWNER}/atlas-gardener/actions/variables/ATLAS_GARDENER_WRITE_TARGETS_JSON" >"${root}/write-targets.json"
  jq -e --arg value "$GARDENER_MODE" '.name == "ATLAS_GARDENER_MODE" and .value == $value' "${root}/mode.json" >/dev/null
  jq -e --arg value "$GARDENER_WRITE_GATE" '.name == "ATLAS_GARDENER_WRITE_GATE" and .value == $value' "${root}/write-gate.json" >/dev/null
  jq -e --arg value "$GARDENER_WRITE_TARGETS" '.name == "ATLAS_GARDENER_WRITE_TARGETS_JSON" and .value == $value' "${root}/write-targets.json" >/dev/null
}

verify_baseline() {
  root="$1"
  mkdir -p "$root"

  gh api "/repos/${FULL_REPOSITORY}" >"${root}/repository.json"
  gh api "/repos/${FULL_REPOSITORY}/commits/main" >"${root}/main.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rulesets?per_page=100" >"${root}/rulesets.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" >"${root}/ruleset.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rules/branches/main" >"${root}/active-rules.json"
  gh api "/repos/${FULL_REPOSITORY}/actions/variables/ATLAS_GARDENER_AUTOMERGE_ENABLED" >"${root}/gardener-automerge-variable.json"
  verify_variable_absent "DEPENDABOT_AUTOMERGE_ENABLED" "${root}/dependabot-automerge-variable.json"
  verify_classic_absent "${root}/classic-protection.json"

  jq -e '.full_name == "AtlasReaper311/atlas-dora" and .default_branch == "main" and .visibility == "public" and .archived == false and .allow_auto_merge == false' "${root}/repository.json" >/dev/null
  jq -e --arg expected "$EXPECTED_MAIN_SHA" '.sha == $expected' "${root}/main.json" >/dev/null
  jq -e --argjson ruleset_id "$EXPECTED_RULESET_ID" '([.[] | select(.target == "branch" and .enforcement == "active")] | length) == 1 and ([.[] | select(.id == $ruleset_id)] | length) == 1' "${root}/rulesets.json" >/dev/null
  jq -e \
    --argjson ruleset_id "$EXPECTED_RULESET_ID" \
    --arg name "$EXPECTED_RULESET_NAME" \
    --arg native "$EXPECTED_NATIVE_CONTEXT" \
    --arg barrier "$EXPECTED_BARRIER_CONTEXT" \
    '.id == $ruleset_id and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["refs/heads/main"] and
     .conditions.ref_name.exclude == [] and
     ([.rules[].type] | sort) == ["required_status_checks"] and
     (([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks | map(.context) | sort) == ([$native, $barrier] | sort)) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "${root}/ruleset.json" >/dev/null
  jq -e --argjson ruleset_id "$EXPECTED_RULESET_ID" '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == ["required_status_checks"]' "${root}/active-rules.json" >/dev/null
  jq -e --arg value "$EXPECTED_GARDENER_VARIABLE_VALUE" '.name == "ATLAS_GARDENER_AUTOMERGE_ENABLED" and .value == $value' "${root}/gardener-automerge-variable.json" >/dev/null
}

build_reconciled_payload() {
  output="$1"
  jq -n \
    --arg name "$EXPECTED_RULESET_NAME" \
    --arg native "$EXPECTED_NATIVE_CONTEXT" \
    --arg barrier "$EXPECTED_BARRIER_CONTEXT" \
    '{
      name: $name,
      target: "branch",
      enforcement: "active",
      bypass_actors: [],
      conditions: {ref_name: {include: ["refs/heads/main"], exclude: []}},
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
              {context: $native},
              {context: $barrier}
            ],
            strict_required_status_checks_policy: false
          }
        }
      ]
    }' >"$output"
}

verify_reconciled_state() {
  root="$1"

  gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" >"${root}/ruleset-after.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rules/branches/main" >"${root}/active-rules-after.json"
  gh api "/repos/${FULL_REPOSITORY}" >"${root}/repository-after.json"
  gh api "/repos/${FULL_REPOSITORY}/commits/main" >"${root}/main-after.json"
  gh api "/repos/${FULL_REPOSITORY}/actions/variables/ATLAS_GARDENER_AUTOMERGE_ENABLED" >"${root}/gardener-automerge-variable-after.json"
  verify_variable_absent "DEPENDABOT_AUTOMERGE_ENABLED" "${root}/dependabot-automerge-variable-after.json"
  verify_classic_absent "${root}/classic-protection-after.json"

  jq -e \
    --argjson ruleset_id "$EXPECTED_RULESET_ID" \
    --arg name "$EXPECTED_RULESET_NAME" \
    --arg native "$EXPECTED_NATIVE_CONTEXT" \
    --arg barrier "$EXPECTED_BARRIER_CONTEXT" \
    '.id == $ruleset_id and
     .name == $name and
     .target == "branch" and
     .enforcement == "active" and
     (.bypass_actors | length) == 0 and
     .conditions.ref_name.include == ["refs/heads/main"] and
     .conditions.ref_name.exclude == [] and
     ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false) and
     (([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks | map(.context) | sort) == ([$native, $barrier] | sort)) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "${root}/ruleset-after.json" >/dev/null
  jq -e --argjson ruleset_id "$EXPECTED_RULESET_ID" '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' "${root}/active-rules-after.json" >/dev/null
  jq -e '.allow_auto_merge == false' "${root}/repository-after.json" >/dev/null
  jq -e --arg expected "$EXPECTED_MAIN_SHA" '.sha == $expected' "${root}/main-after.json" >/dev/null
  jq -e --arg value "$EXPECTED_GARDENER_VARIABLE_VALUE" '.name == "ATLAS_GARDENER_AUTOMERGE_ENABLED" and .value == $value' "${root}/gardener-automerge-variable-after.json" >/dev/null
}

for command_name in gh jq
 do
  require_command "$command_name"
 done

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

if [ "$MODE" = "apply" ]
then
  if [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 4B" ]
  then
    printf 'ERROR: exact Wave 4B provider confirmation is required.\n' >&2
    exit 1
  fi
fi

mkdir -p "$EVIDENCE_DIR"
printf 'PART 0: Verify exact DORA provider and Gardener baseline\n'
verify_baseline "${EVIDENCE_DIR}/before"
verify_gardener_controller "${EVIDENCE_DIR}/gardener-controller-before"
build_reconciled_payload "${EVIDENCE_DIR}/ruleset-request.json"

if [ "$MODE" = "inspect" ]
then
  printf '%s\n' '{"schema":"atlas-github-provider-guard-wave-4b/run-summary/v1","mode":"inspect","provider_writes_performed":false,"ruleset_id":19581236,"variables_written":false,"profile_repository_modified":false}' >"${EVIDENCE_DIR}/wave-4b-summary.json"
  write_sha256s "$EVIDENCE_DIR"
  printf 'Wave 4B inspection-only preflight complete.\n'
  printf 'Evidence: %s\n' "$EVIDENCE_DIR"
  exit 0
fi

printf 'PART 1: Update existing DORA ruleset 19581236 in place\n'
gh api \
  --method PUT \
  -H 'Accept: application/vnd.github+json' \
  "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" \
  --input "${EVIDENCE_DIR}/ruleset-request.json" \
  >"${EVIDENCE_DIR}/ruleset-updated.json"

printf 'PART 2: Verify DORA ruleset and preserved automation state\n'
verify_reconciled_state "${EVIDENCE_DIR}"
verify_gardener_controller "${EVIDENCE_DIR}/gardener-controller-after"
printf '%s\n' '{"schema":"atlas-github-provider-guard-wave-4b/run-summary/v1","mode":"apply","provider_writes_performed":true,"provider_write_type":"existing-ruleset-update-only","ruleset_id":19581236,"variables_written":false,"profile_repository_modified":false}' >"${EVIDENCE_DIR}/wave-4b-summary.json"
write_sha256s "$EVIDENCE_DIR"
printf 'Wave 4B DORA reconciliation complete.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
