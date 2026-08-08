#!/usr/bin/env bash
set -eu

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
GARDENER_BARRIER="Gardener native auto-merge barrier"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-3-apply}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

REPOSITORIES='atlas-doc-viewer|2b03d5843588f0415ecc735f6b33ca7527063137|Static document validation|true
atlas-quota-watch|97304b7df2489a881aca422e494063d62f034a55|validate|true
site-pulse|be661f348ce7bc96b98f868b9d0eb2c01fcc99af|Worker validation|true
specular-sonify|2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53|Worker configuration validation|false
status|4db1438b1a8859008461903105360a2f09376c02|Status site validation|true'

GARDENER_MODE="automerge-low-risk"
GARDENER_WRITE_GATE="enabled"
GARDENER_WRITE_TARGETS='["AtlasReaper311/atlas-doc-viewer","AtlasReaper311/atlas-quota-watch","AtlasReaper311/site-pulse","AtlasReaper311/specular-sonify","AtlasReaper311/status"]'

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'ERROR: required command is unavailable: %s\n' "$1" >&2
    exit 1
  }
}

write_sha256s() {
  root="$1"
  output="$2"
  if command -v sha256sum >/dev/null 2>&1
  then
    digest_command="sha256sum"
  elif command -v shasum >/dev/null 2>&1
  then
    digest_command="shasum -a 256"
  else
    printf 'ERROR: no SHA-256 utility is available.\n' >&2
    exit 1
  fi
  : >"$output"
  find "$root" -type f ! -name SHA256SUMS.txt -print | LC_ALL=C sort |
    while IFS= read -r path
    do
      if [ "$digest_command" = "sha256sum" ]
      then
        sha256sum "$path"
      else
        shasum -a 256 "$path"
      fi
    done >"$output"
}

verify_dependabot_variable_absent() {
  repository="$1"
  output="$2"
  if gh api "/repos/${OWNER}/${repository}/actions/variables/DEPENDABOT_AUTOMERGE_ENABLED" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: DEPENDABOT_AUTOMERGE_ENABLED is now present for %s; refusing baseline drift.\n' "$repository" >&2
    exit 1
  fi
  if ! grep -q 'HTTP 404' "${output}.error" && ! grep -q 'Not Found' "${output}.error"
  then
    printf 'ERROR: could not prove Dependabot variable absence for %s.\n' "$repository" >&2
    cat "${output}.error" >&2
    exit 1
  fi
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

verify_classic_protection() {
  repository="$1"
  native_context="$2"
  strict_value="$3"
  output="$4"

  gh api "/repos/${OWNER}/${repository}/branches/main/protection" >"$output"

  jq -e \
    --arg native "$native_context" \
    --arg barrier "$GARDENER_BARRIER" \
    --argjson integration_id "$INTEGRATION_ID" \
    --argjson strict "$strict_value" \
    '.required_status_checks.strict == $strict and
     ([.required_status_checks.checks[] | {context: .context, app_id: .app_id}] | sort_by(.context)) ==
       ([{context: $native, app_id: $integration_id}, {context: $barrier, app_id: $integration_id}] | sort_by(.context)) and
     .required_signatures.enabled == false and
     .enforce_admins.enabled == false and
     .required_linear_history.enabled == false and
     .allow_force_pushes.enabled == false and
     .allow_deletions.enabled == false and
     .block_creations.enabled == false and
     .required_conversation_resolution.enabled == false and
     .lock_branch.enabled == false and
     .allow_fork_syncing.enabled == false' \
    "$output" >/dev/null
}

verify_baseline() {
  repository="$1"
  expected_main="$2"
  native_context="$3"
  strict_value="$4"
  root="$5"

  mkdir -p "$root"
  gh api "/repos/${OWNER}/${repository}" >"${root}/repository.json"
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${root}/main.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rulesets?per_page=100" >"${root}/rulesets.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rules/branches/main" >"${root}/active-rules.json"
  gh api "/repos/${OWNER}/${repository}/actions/variables/ATLAS_GARDENER_AUTOMERGE_ENABLED" >"${root}/gardener-automerge-variable.json"
  verify_dependabot_variable_absent "$repository" "${root}/dependabot-automerge-variable.json"
  verify_classic_protection "$repository" "$native_context" "$strict_value" "${root}/classic-protection.json"

  jq -e '.full_name == ("AtlasReaper311/" + .name) and .default_branch == "main" and .visibility == "public" and .archived == false and .allow_auto_merge == true' "${root}/repository.json" >/dev/null
  jq -e --arg expected "$expected_main" '.sha == $expected' "${root}/main.json" >/dev/null
  jq -e 'length == 0' "${root}/rulesets.json" >/dev/null
  jq -e 'length == 0' "${root}/active-rules.json" >/dev/null
  jq -e '.name == "ATLAS_GARDENER_AUTOMERGE_ENABLED" and .value == "true"' "${root}/gardener-automerge-variable.json" >/dev/null
}

build_ruleset_payload() {
  native_context="$1"
  strict_value="$2"
  output="$3"

  jq -n \
    --arg name "$RULESET_NAME" \
    --arg native "$native_context" \
    --arg barrier "$GARDENER_BARRIER" \
    --argjson integration_id "$INTEGRATION_ID" \
    --argjson strict "$strict_value" \
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
              {context: $native, integration_id: $integration_id},
              {context: $barrier, integration_id: $integration_id}
            ],
            strict_required_status_checks_policy: $strict
          }
        }
      ]
    }' >"$output"
}

verify_ruleset() {
  repository="$1"
  native_context="$2"
  strict_value="$3"
  ruleset_id="$4"
  root="$5"

  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rulesets/${ruleset_id}" >"${root}/ruleset-readback.json"
  gh api -H 'Accept: application/vnd.github+json' "/repos/${OWNER}/${repository}/rules/branches/main" >"${root}/active-rules.json"

  jq -e \
    --arg name "$RULESET_NAME" \
    --arg native "$native_context" \
    --arg barrier "$GARDENER_BARRIER" \
    --argjson integration_id "$INTEGRATION_ID" \
    --argjson strict "$strict_value" \
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
     (([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks | sort_by(.context)) ==
       ([{context: $native, integration_id: $integration_id}, {context: $barrier, integration_id: $integration_id}] | sort_by(.context))) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == $strict)' \
    "${root}/ruleset-readback.json" >/dev/null

  jq -e \
    --argjson ruleset_id "$ruleset_id" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "${root}/active-rules.json" >/dev/null
}

verify_classic_absent() {
  repository="$1"
  output="$2"
  if gh api "/repos/${OWNER}/${repository}/branches/main/protection" >"$output" 2>"${output}.error"
  then
    printf 'ERROR: classic protection still exists for %s after migration.\n' "$repository" >&2
    exit 1
  fi
  if ! grep -q 'HTTP 404' "${output}.error" && ! grep -q 'Branch not protected' "${output}.error" && ! grep -q 'Not Found' "${output}.error"
  then
    printf 'ERROR: could not prove classic protection absence for %s.\n' "$repository" >&2
    cat "${output}.error" >&2
    exit 1
  fi
}

verify_final_preservation() {
  repository="$1"
  expected_main="$2"
  root="$3"
  gh api "/repos/${OWNER}/${repository}" >"${root}/repository-final.json"
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${root}/main-final.json"
  gh api "/repos/${OWNER}/${repository}/actions/variables/ATLAS_GARDENER_AUTOMERGE_ENABLED" >"${root}/gardener-automerge-variable-final.json"
  verify_dependabot_variable_absent "$repository" "${root}/dependabot-automerge-variable-final.json"
  jq -e '.allow_auto_merge == true' "${root}/repository-final.json" >/dev/null
  jq -e --arg expected "$expected_main" '.sha == $expected' "${root}/main-final.json" >/dev/null
  jq -e '.name == "ATLAS_GARDENER_AUTOMERGE_ENABLED" and .value == "true"' "${root}/gardener-automerge-variable-final.json" >/dev/null
}

for command_name in gh jq python3
 do
  require_command "$command_name"
 done

mkdir -p "$EVIDENCE_DIR"

echo "PART 0: Preflight all five repositories before any provider write"
verify_gardener_controller "${EVIDENCE_DIR}/gardener-controller-before"

printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context strict_value
 do
  verify_baseline "$repository" "$expected_main" "$native_context" "$strict_value" "${EVIDENCE_DIR}/${repository}/before"
  printf 'Verified baseline: %s\n' "$repository"
 done

if [ "$MODE" = "inspect" ]
then
  python3 - "$EVIDENCE_DIR" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
(root / "wave-3-migration-summary.json").write_text(json.dumps({
    "schema": "atlas-github-provider-guard-wave-3/migration-summary/v1",
    "mode": "inspect",
    "provider_writes_performed": False,
    "classic_protection_removed": False,
    "variables_written": False,
    "wave_4_started": False,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"
  echo "Wave 3 inspection-only migration preflight complete."
  exit 0
fi

if [ "$MODE" != "apply" ]
then
  printf 'ERROR: unsupported MODE: %s\n' "$MODE" >&2
  exit 1
fi

if [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 3" ]
then
  printf 'ERROR: exact Wave 3 provider confirmation is required.\n' >&2
  exit 1
fi

echo "PART 1: Create all five replacement rulesets while classic protection remains"
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context strict_value
 do
  repo_root="${EVIDENCE_DIR}/${repository}"
  mkdir -p "${repo_root}/ruleset-create"
  build_ruleset_payload "$native_context" "$strict_value" "${repo_root}/ruleset-create/ruleset-request.json"
  gh api \
    --method POST \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rulesets" \
    --input "${repo_root}/ruleset-create/ruleset-request.json" \
    >"${repo_root}/ruleset-create/ruleset-created.json"
  ruleset_id="$(jq -r '.id' "${repo_root}/ruleset-create/ruleset-created.json")"
  case "$ruleset_id" in
    ''|null|*[!0-9]*)
      printf 'ERROR: invalid ruleset ID returned for %s.\n' "$repository" >&2
      exit 1
      ;;
  esac
  verify_ruleset "$repository" "$native_context" "$strict_value" "$ruleset_id" "${repo_root}/ruleset-create"
  verify_classic_protection "$repository" "$native_context" "$strict_value" "${repo_root}/ruleset-create/classic-protection-still-present.json"
  printf 'Created and verified ruleset %s for %s; classic protection still present.\n' "$ruleset_id" "$repository"
 done

echo "PART 2: Re-verify every replacement before removing any classic protection"
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context strict_value
 do
  repo_root="${EVIDENCE_DIR}/${repository}"
  ruleset_id="$(jq -r '.id' "${repo_root}/ruleset-create/ruleset-created.json")"
  mkdir -p "${repo_root}/pre-classic-delete"
  verify_ruleset "$repository" "$native_context" "$strict_value" "$ruleset_id" "${repo_root}/pre-classic-delete"
  verify_classic_protection "$repository" "$native_context" "$strict_value" "${repo_root}/pre-classic-delete/classic-protection.json"
 done

echo "PART 3: Remove only the superseded classic protections"
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context strict_value
 do
  repo_root="${EVIDENCE_DIR}/${repository}"
  mkdir -p "${repo_root}/classic-delete"
  gh api \
    --method DELETE \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/branches/main/protection" \
    >"${repo_root}/classic-delete/delete-response.txt"
  verify_classic_absent "$repository" "${repo_root}/classic-delete/classic-protection-after.json"
  printf 'Removed superseded classic protection: %s\n' "$repository"
 done

echo "PART 4: Final provider and automation preservation verification"
verify_gardener_controller "${EVIDENCE_DIR}/gardener-controller-after"

printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository expected_main native_context strict_value
 do
  repo_root="${EVIDENCE_DIR}/${repository}"
  ruleset_id="$(jq -r '.id' "${repo_root}/ruleset-create/ruleset-created.json")"
  mkdir -p "${repo_root}/final"
  verify_ruleset "$repository" "$native_context" "$strict_value" "$ruleset_id" "${repo_root}/final"
  verify_classic_absent "$repository" "${repo_root}/final/classic-protection.json"
  verify_final_preservation "$repository" "$expected_main" "${repo_root}/final"
 done

python3 - "$EVIDENCE_DIR" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
repos = [
    "atlas-doc-viewer",
    "atlas-quota-watch",
    "site-pulse",
    "specular-sonify",
    "status",
]
created = {}
for repo in repos:
    payload = json.loads((root / repo / "ruleset-create" / "ruleset-created.json").read_text(encoding="utf-8"))
    created[repo] = payload["id"]
summary = {
    "schema": "atlas-github-provider-guard-wave-3/migration-summary/v1",
    "mode": "apply",
    "provider_writes_performed": True,
    "rulesets_created": created,
    "classic_protection_removed": True,
    "repository_auto_merge_preserved": True,
    "gardener_automerge_enabled_preserved": True,
    "dependabot_automerge_variable_remained_absent": True,
    "gardener_controller_preserved": True,
    "existing_pull_requests_merged_by_operator": False,
    "variables_written": False,
    "secrets_read": False,
    "workflow_dispatches": False,
    "wave_4_started": False,
}
(root / "wave-3-migration-summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"

echo
echo "WAVE 3 BATCH MIGRATION COMPLETE"
echo "Five replacement rulesets created and verified."
echo "Five superseded classic protections removed only after all replacements were verified."
echo "Repository auto-merge remains enabled on all five."
echo "Gardener auto-merge remains enabled on all five."
echo "Dependabot auto-merge variable remains absent on all five."
echo "No existing pull request was merged by this operator."
echo "Wave 4 was not started."
