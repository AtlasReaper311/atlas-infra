#!/usr/bin/env bash
set -eu

# Atlas Systems GitHub provider-guard Wave 2A runner.
# Default mode is read-only inspection. Provider writes require an exact
# confirmation phrase and are limited to atlas-gardener and atlas-interface-kit.
# atlas-journey-watch is explicitly excluded from this runner.

MODE="${MODE:-inspect}"
CONFIRMATION="${ATLAS_PROVIDER_WRITE_CONFIRMATION:-}"
OWNER="AtlasReaper311"
RULESET_NAME="Atlas default branch PR guard"
INTEGRATION_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-2a}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

REPOSITORIES='atlas-gardener|22|open|dependabot[bot]|319465dcea68a8fefead3e7d90e82b79078cb34d|5975733c5d4f05d66f957cb50a322905f7751d06|test
atlas-interface-kit|14|merged|AtlasReaper311|21a1a168e3b25e916555ce4edd4229bd7c061ecb|1f26360d938b589cf8a562ca308fd6ca3b4a2b3f|Validate interface kit'

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

verify_main_identity() {
  repository="$1"
  expected_main="$2"
  output_file="$3"

  gh api "/repos/${OWNER}/${repository}/commits/main" >"$output_file"

  jq -e \
    --arg expected_main "$expected_main" \
    '.sha == $expected_main' \
    "$output_file" >/dev/null
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
    --arg name "$RULESET_NAME" \
    '([.[] | select(.target == "branch" and .enforcement == "active")] | length) == 0 and
     ([.[] | select(.name == $name)] | length) == 0' \
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

verify_validation_evidence() {
  repository="$1"
  pull_number="$2"
  expected_state="$3"
  expected_actor="$4"
  expected_main="$5"
  expected_head="$6"
  expected_context="$7"
  pull_file="$8"
  checks_file="$9"

  gh api "/repos/${OWNER}/${repository}/pulls/${pull_number}" >"$pull_file"

  case "$expected_state" in
    open)
      jq -e \
        --arg actor "$expected_actor" \
        --arg expected_main "$expected_main" \
        --arg expected_head "$expected_head" \
        '.state == "open" and
         .merged == false and
         .base.ref == "main" and
         .base.sha == $expected_main and
         .head.sha == $expected_head and
         .user.login == $actor' \
        "$pull_file" >/dev/null
      ;;
    merged)
      jq -e \
        --arg actor "$expected_actor" \
        --arg expected_main "$expected_main" \
        --arg expected_head "$expected_head" \
        '.state == "closed" and
         .merged == true and
         .base.ref == "main" and
         .head.sha == $expected_head and
         .merge_commit_sha == $expected_main and
         .user.login == $actor' \
        "$pull_file" >/dev/null
      ;;
    *)
      printf 'ERROR: unsupported validation PR state: %s\n' "$expected_state" >&2
      exit 1
      ;;
  esac

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/commits/${expected_head}/check-runs?per_page=100" \
    >"$checks_file"

  jq -e \
    --arg context "$expected_context" \
    --arg expected_head "$expected_head" \
    --argjson integration_id "$INTEGRATION_ID" \
    '[.check_runs[] | select(
      .name == $context and
      .head_sha == $expected_head and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "$checks_file" >/dev/null
}

read_variable() {
  repository="$1"
  name="$2"
  output_file="$3"

  gh api "/repos/${OWNER}/${repository}/actions/variables/${name}" >"$output_file"
}

verify_gardener_controller_state() {
  repo_dir="$1"
  mkdir -p "$repo_dir"

  read_variable "atlas-gardener" "ATLAS_GARDENER_MODE" "${repo_dir}/variable-mode.json"
  read_variable "atlas-gardener" "ATLAS_GARDENER_WRITE_GATE" "${repo_dir}/variable-write-gate.json"
  read_variable "atlas-gardener" "ATLAS_GARDENER_WRITE_TARGETS_JSON" "${repo_dir}/variable-write-targets.json"

  jq -e --arg value "$GARDENER_MODE" '.name == "ATLAS_GARDENER_MODE" and .value == $value' \
    "${repo_dir}/variable-mode.json" >/dev/null
  jq -e --arg value "$GARDENER_WRITE_GATE" '.name == "ATLAS_GARDENER_WRITE_GATE" and .value == $value' \
    "${repo_dir}/variable-write-gate.json" >/dev/null
  jq -e --arg value "$GARDENER_WRITE_TARGETS" '.name == "ATLAS_GARDENER_WRITE_TARGETS_JSON" and .value == $value' \
    "${repo_dir}/variable-write-targets.json" >/dev/null
}

capture_specialist_workflows() {
  repository="$1"
  repo_dir="$2"

  case "$repository" in
    atlas-gardener)
      gh api \
        -H 'Accept: application/vnd.github.raw+json' \
        "/repos/${OWNER}/${repository}/contents/.github/workflows/ci.yml?ref=main" \
        >"${repo_dir}/ci.yml"
      gh api \
        -H 'Accept: application/vnd.github.raw+json' \
        "/repos/${OWNER}/${repository}/contents/.github/workflows/controller.yml?ref=main" \
        >"${repo_dir}/controller.yml"
      ;;
    atlas-interface-kit)
      gh api \
        -H 'Accept: application/vnd.github.raw+json' \
        "/repos/${OWNER}/${repository}/contents/.github/workflows/ci.yml?ref=main" \
        >"${repo_dir}/ci.yml"
      gh api \
        -H 'Accept: application/vnd.github.raw+json' \
        "/repos/${OWNER}/${repository}/contents/.github/workflows/release.yml?ref=main" \
        >"${repo_dir}/release.yml"
      ;;
    *)
      printf 'ERROR: unexpected Wave 2A repository: %s\n' "$repository" >&2
      exit 1
      ;;
  esac
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
  expected_main="$2"
  created_file="$3"
  readback_file="$4"
  active_rules_file="$5"
  repository_file="$6"
  main_file="$7"

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
     .conditions.ref_name.exclude == [] and
     ([.rules[].type] | sort) == (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_approving_review_count == 0) and
     ([.rules[] | select(.type == "pull_request")][0].parameters.required_review_thread_resolution == false) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.required_status_checks == [{context: $context, integration_id: $integration_id}]) and
     ([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)' \
    "$readback_file" >/dev/null

  jq -e \
    --argjson ruleset_id "$ruleset_id" \
    '([.[] | select(.ruleset_id == $ruleset_id) | .type] | sort) ==
     (["deletion", "non_fast_forward", "pull_request", "required_status_checks"] | sort)' \
    "$active_rules_file" >/dev/null

  jq -e '.allow_auto_merge == false' "$repository_file" >/dev/null

  jq -e --arg expected_main "$expected_main" '.sha == $expected_main' "$main_file" >/dev/null
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

if [ "$MODE" = "apply" ] && [ "$CONFIRMATION" != "APPLY GITHUB PROVIDER GUARD WAVE 2A" ]
then
  printf 'ERROR: provider write refused. Set the exact approved confirmation phrase.\n' >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"

printf 'PART 1: Read-only Wave 2A baseline verification\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository pull_number expected_state expected_actor expected_main expected_head expected_context
do
  repo_dir="${EVIDENCE_DIR}/${repository}"
  mkdir -p "$repo_dir"

  verify_repository_baseline \
    "$repository" \
    "${repo_dir}/repository-before.json" \
    "${repo_dir}/rulesets-before.json" \
    "${repo_dir}/classic-protection-before.json"

  verify_main_identity \
    "$repository" \
    "$expected_main" \
    "${repo_dir}/main-before.json"

  verify_validation_evidence \
    "$repository" \
    "$pull_number" \
    "$expected_state" \
    "$expected_actor" \
    "$expected_main" \
    "$expected_head" \
    "$expected_context" \
    "${repo_dir}/validation-pr.json" \
    "${repo_dir}/validation-check-runs.json"

  capture_specialist_workflows "$repository" "$repo_dir"

  if [ "$repository" = "atlas-gardener" ]
  then
    verify_gardener_controller_state "$repo_dir"
  fi

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
  printf 'atlas-journey-watch remains excluded from Wave 2A.\n'
  exit 0
fi

printf 'PART 2: Apply exactly two approved Wave 2A rulesets\n'
printf '%s\n' "$REPOSITORIES" | while IFS='|' read -r repository pull_number expected_state expected_actor expected_main expected_head expected_context
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
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${repo_dir}/main-after.json"

  if [ "$repository" = "atlas-gardener" ]
  then
    verify_gardener_controller_state "${repo_dir}/after-controller-state"
  fi

  verify_ruleset_readback \
    "$expected_context" \
    "$expected_main" \
    "${repo_dir}/ruleset-created.json" \
    "${repo_dir}/ruleset-readback.json" \
    "${repo_dir}/active-rules-after.json" \
    "${repo_dir}/repository-after.json" \
    "${repo_dir}/main-after.json"

  printf 'Created and verified %s ruleset ID %s\n' "$repository" "$ruleset_id"
done

printf 'PART 3: Final evidence identity\n'
write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"

printf 'Wave 2A provider write complete.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
printf 'Do not change Gardener controller variables, touch atlas-journey-watch, or begin Wave 3 from this runner.\n'
