#!/usr/bin/env bash
set -eu

# Atlas Systems GitHub provider-guard Wave 4A create-first runner.
# Default mode is read-only inspection. Provider writes require an exact
# confirmation phrase and are limited to creating one ruleset in each reviewed
# Wave 4A repository. This runner never touches AtlasReaper311/AtlasReaper311.

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-4a}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

REPOSITORIES='.github|dd3818eeae486c95e1a1fc0860786db5c24308fa|NONE
atlas-api-index|96cd81f643429895847a1c2f143084d6e995005c|build
atlas-blackbox|e0c3ac7cdb2438a13a7ec71a02f7ac86aeed4223|Offline Worker validation
atlas-corpus|faa0690f5f1e58fa97c1839d6f320e00512ecdd1|build
atlas-daily-digest|125e4872b90227c4cf72f33f953308e99ddd027b|Worker validation
atlas-notify|9efeb709cd86f4b7bb7e6910d55a6155eb7e79f0|Test (Vitest)
deploy-watch|72513e434a7b68bdba4e8c181b536b92da6f2b17|Worker validation
github-pulse|8f1435e9302cf9006d9ab8a2cc2a9702c460cad6|Worker validation
ramone-edge|3830dd3839847187e0b5ac6c837a5658f5f47341|Worker validation
ramone-memory|7b983cd4df1435ea0962ff3179d8570ec8dc0e71|build
ramone-voice-trigger|6e3273330e531b936553b34243ed5ee6141ba614|build
specular-sentinel|8dfe8c4274fc278855bcd4658cdb4866d3c29d3f|build
specular-telemetry|0a0a930abaa104e6da5c9ad2da57e78eb0fbec80|build'

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
  repository="$1"
  variable_name="$2"
  output="$3"

  if gh api "/repos/${OWNER}/${repository}/actions/variables/${variable_name}" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: %s is now present for %s; refusing baseline drift.\n' "$variable_name" "$repository" >&2
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
  printf 'ERROR: could not prove %s absence for %s.\n' "$variable_name" "$repository" >&2
  cat "${output}.error" >&2
  exit 1
}

verify_classic_absent() {
  repository="$1"
  output="$2"

  if gh api "/repos/${OWNER}/${repository}/branches/main/protection" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: classic branch protection now exists for %s; refusing create-first assumptions.\n' "$repository" >&2
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
  printf 'ERROR: could not prove classic protection absence for %s.\n' "$repository" >&2
  cat "${output}.error" >&2
  exit 1
}

verify_baseline() {
  repository="$1"
  expected_main="$2"
  root="$3"

  mkdir -p "$root"
  gh api "/repos/${OWNER}/${repository}" >"${root}/repository.json"
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${root}/main.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rulesets?per_page=100" >"${root}/rulesets.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rules/branches/main" >"${root}/active-rules.json"
  verify_classic_absent "$repository" "${root}/classic-protection.json"
  verify_variable_absent "$repository" "ATLAS_GARDENER_AUTOMERGE_ENABLED" "${root}/gardener-automerge-variable.json"
  verify_variable_absent "$repository" "DEPENDABOT_AUTOMERGE_ENABLED" "${root}/dependabot-automerge-variable.json"

  jq -e '.full_name == ("AtlasReaper311/" + .name) and .default_branch == "main" and .visibility == "public" and .archived == false and .allow_auto_merge == false' "${root}/repository.json" >/dev/null
  jq -e --arg expected "$expected_main" '.sha == $expected' "${root}/main.json" >/dev/null
  jq -e 'length == 0' "${root}/rulesets.json" >/dev/null
  jq -e 'length == 0' "${root}/active-rules.json" >/dev/null
}

build_ruleset_payload() {
  native_context="$1"
  output="$2"

  if [ "$native_context" = "NONE" ]
  then
    jq -n \
      --arg name "$RULESET_NAME" \
      '{
        name: $name,
        target: "branch",
        enforcement: "active",
        bypass_actors: [],
        conditions: {ref_name: {include: ["~DEFAULT_BRANCH"], exclude: []}},
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
          }
        ]
      }' >"$output"
    return
  fi

  jq -n \
    --arg name "$RULESET_NAME" \
    --arg context "$native_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '{
      name: $name,
      target: "branch",
      enforcement: "active",
      bypass_actors: [],
      conditions: {ref_name: {include: ["~DEFAULT_BRANCH"], exclude: []}},
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
              {context: $context, integration_id: $integration_id}
            ],
            strict_required_status_checks_policy: false
          }
        }
      ]
    }' >"$output"
}

verify_ruleset() {
  repository="$1"
  native_context="$2"
  ruleset_id="$3"
  root="$4"

  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rulesets/${ruleset_id}" >"${root}/ruleset-readback.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rules/branches/main" >"${root}/active-rules.json"

  if [ "$native_context" = "NONE" ]
  then
    jq -e \
      --arg name "$RULESET_NAME" \
      --argjson ruleset_id "$ruleset_id" \
      '.id == $ruleset_id and
       .name == $name and
       .target == "branch" and
       .enforcement == "active" and
       (.bypass_actors | length) == 0 and
       .conditions.ref_name.include == ["~DEFAULT_BRANCH"] and
       .conditions.ref_name.exclude == [] and
       ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request"] | sort) and
       ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
       ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false)' \
      "${root}/ruleset-readback.json" >/dev/null

    jq -e \
      --argjson ruleset_id "$ruleset_id" \
      '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == (["deletion", "non_fast_forward", "pull_request"] | sort)' \
      "${root}/active-rules.json" >/dev/null
    return
  fi

  jq -e \
    --arg name "$RULESET_NAME" \
    --arg context "$native_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    --argjson ruleset_id "$ruleset_id" \
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
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}]) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "${root}/ruleset-readback.json" >/dev/null

  jq -e \
    --argjson ruleset_id "$ruleset_id" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "${root}/active-rules.json" >/dev/null
}

verify_preservation() {
  repository="$1"
  expected_main="$2"
  root="$3"

  gh api "/repos/${OWNER}/${repository}" >"${root}/repository-after.json"
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${root}/main-after.json"
  verify_variable_absent "$repository" "ATLAS_GARDENER_AUTOMERGE_ENABLED" "${root}/gardener-automerge-variable-after.json"
  verify_variable_absent "$repository" "DEPENDABOT_AUTOMERGE_ENABLED" "${root}/dependabot-automerge-variable-after.json"

  jq -e '.allow_auto_merge == false' "${root}/repository-after.json" >/dev/null
  jq -e --arg expected "$expected_main" '.sha == $expected' "${root}/main-after.json" >/dev/null
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
  if [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 4A" ]
  then
    printf 'ERROR: exact Wave 4A provider confirmation is required.\n' >&2
    exit 1
  fi
fi

mkdir -p "$EVIDENCE_DIR"

printf 'PART 0: Preflight all 13 Wave 4A repositories before any provider write\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context
 do
  verify_baseline "$repository" "$expected_main" "${EVIDENCE_DIR}/${repository}/before"
  build_ruleset_payload "$native_context" "${EVIDENCE_DIR}/${repository}/ruleset-request.json"
  printf 'Verified baseline: %s\n' "$repository"
 done

if [ "$MODE" = "inspect" ]
then
  printf '%s\n' '{"schema":"atlas-github-provider-guard-wave-4a/run-summary/v1","mode":"inspect","provider_writes_performed":false,"variables_written":false,"profile_repository_modified":false}' >"${EVIDENCE_DIR}/wave-4a-summary.json"
  write_sha256s "$EVIDENCE_DIR"
  printf 'Wave 4A inspection-only preflight complete.\n'
  printf 'Evidence: %s\n' "$EVIDENCE_DIR"
  exit 0
fi

printf 'PART 1: Create and verify one additive ruleset per Wave 4A repository\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context
 do
  root="${EVIDENCE_DIR}/${repository}"
  gh api \
    --method POST \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rulesets" \
    --input "${root}/ruleset-request.json" \
    >"${root}/ruleset-created.json"

  ruleset_id="$(jq -r '.id' "${root}/ruleset-created.json")"
  case "$ruleset_id" in
    ''|null|*[!0-9]*)
      printf 'ERROR: invalid ruleset ID returned for %s.\n' "$repository" >&2
      exit 1
      ;;
  esac

  verify_ruleset "$repository" "$native_context" "$ruleset_id" "$root"
  verify_classic_absent "$repository" "${root}/classic-protection-after.json"
  verify_preservation "$repository" "$expected_main" "$root"
  printf 'Created and verified ruleset %s for %s.\n' "$ruleset_id" "$repository"
 done

printf '%s\n' '{"schema":"atlas-github-provider-guard-wave-4a/run-summary/v1","mode":"apply","provider_writes_performed":true,"provider_write_type":"ruleset-create-only","variables_written":false,"profile_repository_modified":false}' >"${EVIDENCE_DIR}/wave-4a-summary.json"
write_sha256s "$EVIDENCE_DIR"
printf 'Wave 4A provider creation complete.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
