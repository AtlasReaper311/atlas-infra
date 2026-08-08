#!/usr/bin/env bash
set -eu

OWNER="AtlasReaper311"
INTEGRATION_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-2}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_STAMP}"

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

read_classic_protection() {
  repository="$1"
  repo_dir="$2"

  if gh api "/repos/${OWNER}/${repository}/branches/main/protection" >"${repo_dir}/classic-protection.json" 2>"${repo_dir}/classic-protection.error"
  then
    jq -n \
      --arg status "present" \
      --slurpfile protection "${repo_dir}/classic-protection.json" \
      '{status: $status, protection: $protection[0]}' \
      >"${repo_dir}/classic-protection-summary.json"
    return 0
  fi

  if grep -q 'Branch not protected' "${repo_dir}/classic-protection.error"
  then
    jq -n '{status: "absent", protection: null}' >"${repo_dir}/classic-protection-summary.json"
    return 0
  fi

  if grep -q 'HTTP 404' "${repo_dir}/classic-protection.error"
  then
    jq -n '{status: "absent", protection: null}' >"${repo_dir}/classic-protection-summary.json"
    return 0
  fi

  printf 'ERROR: could not inspect classic protection for %s.\n' "$repository" >&2
  cat "${repo_dir}/classic-protection.error" >&2
  exit 1
}

read_action_variable() {
  repository="$1"
  variable_name="$2"
  output_file="$3"
  error_file="$4"

  if gh api "/repos/${OWNER}/${repository}/actions/variables/${variable_name}" >"${output_file}.raw" 2>"$error_file"
  then
    jq \
      '{name: .name, present: true, value: .value, created_at: .created_at, updated_at: .updated_at}' \
      "${output_file}.raw" \
      >"$output_file"
    rm "${output_file}.raw"
    return 0
  fi

  if grep -q 'Not Found' "$error_file"
  then
    jq -n \
      --arg name "$variable_name" \
      '{name: $name, present: false, value: null, created_at: null, updated_at: null}' \
      >"$output_file"
    return 0
  fi

  if grep -q 'HTTP 404' "$error_file"
  then
    jq -n \
      --arg name "$variable_name" \
      '{name: $name, present: false, value: null, created_at: null, updated_at: null}' \
      >"$output_file"
    return 0
  fi

  printf 'ERROR: could not inspect Actions variable %s in %s.\n' "$variable_name" "$repository" >&2
  cat "$error_file" >&2
  exit 1
}

fetch_raw_file() {
  repository="$1"
  path="$2"
  output_file="$3"

  gh api \
    -H 'Accept: application/vnd.github.raw+json' \
    "/repos/${OWNER}/${repository}/contents/${path}?ref=main" \
    >"$output_file"
}

verify_repository() {
  repository="$1"
  expected_main="$2"
  expected_auto_merge="$3"
  repo_dir="$4"

  gh api "/repos/${OWNER}/${repository}" >"${repo_dir}/repository.json"

  jq -e \
    --arg full_name "${OWNER}/${repository}" \
    --argjson expected_auto_merge "$expected_auto_merge" \
    '.full_name == $full_name and
     .default_branch == "main" and
     .visibility == "public" and
     .archived == false and
     .allow_auto_merge == $expected_auto_merge' \
    "${repo_dir}/repository.json" \
    >/dev/null

  gh api "/repos/${OWNER}/${repository}/commits/main" >"${repo_dir}/main.json"

  jq -e \
    --arg expected_main "$expected_main" \
    '.sha == $expected_main' \
    "${repo_dir}/main.json" \
    >/dev/null

  gh api "/repos/${OWNER}/${repository}/rulesets?per_page=100" >"${repo_dir}/rulesets.json"

  read_classic_protection "$repository" "$repo_dir"
}

verify_open_validation_pr() {
  repository="$1"
  pull_number="$2"
  expected_main="$3"
  expected_head="$4"
  expected_context="$5"
  repo_dir="$6"

  gh api "/repos/${OWNER}/${repository}/pulls/${pull_number}" >"${repo_dir}/validation-pr.json"

  jq -e \
    --arg expected_main "$expected_main" \
    --arg expected_head "$expected_head" \
    '.state == "open" and
     .base.ref == "main" and
     .base.sha == $expected_main and
     .head.sha == $expected_head' \
    "${repo_dir}/validation-pr.json" \
    >/dev/null

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/commits/${expected_head}/check-runs?per_page=100" \
    >"${repo_dir}/validation-check-runs.json"

  jq -e \
    --arg context "$expected_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '[.check_runs[] | select(
      .name == $context and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "${repo_dir}/validation-check-runs.json" \
    >/dev/null
}

verify_merged_validation_pr() {
  repository="$1"
  pull_number="$2"
  expected_head="$3"
  expected_merge="$4"
  expected_context="$5"
  repo_dir="$6"

  gh api "/repos/${OWNER}/${repository}/pulls/${pull_number}" >"${repo_dir}/validation-pr.json"

  jq -e \
    --arg expected_head "$expected_head" \
    --arg expected_merge "$expected_merge" \
    '.state == "closed" and
     .merged == true and
     .base.ref == "main" and
     .head.sha == $expected_head and
     .merge_commit_sha == $expected_merge' \
    "${repo_dir}/validation-pr.json" \
    >/dev/null

  gh api \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/commits/${expected_head}/check-runs?per_page=100" \
    >"${repo_dir}/validation-check-runs.json"

  jq -e \
    --arg context "$expected_context" \
    --argjson integration_id "$INTEGRATION_ID" \
    '[.check_runs[] | select(
      .name == $context and
      .status == "completed" and
      .conclusion == "success" and
      .app.id == $integration_id
    )] | length == 1' \
    "${repo_dir}/validation-check-runs.json" \
    >/dev/null
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

mkdir -p "$EVIDENCE_DIR"

printf 'PART 1: Inspect atlas-gardener\n'
GARDENER_DIR="${EVIDENCE_DIR}/atlas-gardener"
mkdir -p "$GARDENER_DIR"
verify_repository \
  "atlas-gardener" \
  "319465dcea68a8fefead3e7d90e82b79078cb34d" \
  "false" \
  "$GARDENER_DIR"
verify_open_validation_pr \
  "atlas-gardener" \
  "22" \
  "319465dcea68a8fefead3e7d90e82b79078cb34d" \
  "5975733c5d4f05d66f957cb50a322905f7751d06" \
  "test" \
  "$GARDENER_DIR"
fetch_raw_file \
  "atlas-gardener" \
  ".github/workflows/ci.yml" \
  "${GARDENER_DIR}/ci.yml"
fetch_raw_file \
  "atlas-gardener" \
  ".github/workflows/controller.yml" \
  "${GARDENER_DIR}/controller.yml"
read_action_variable \
  "atlas-gardener" \
  "ATLAS_GARDENER_MODE" \
  "${GARDENER_DIR}/variable-mode.json" \
  "${GARDENER_DIR}/variable-mode.error"
read_action_variable \
  "atlas-gardener" \
  "ATLAS_GARDENER_WRITE_GATE" \
  "${GARDENER_DIR}/variable-write-gate.json" \
  "${GARDENER_DIR}/variable-write-gate.error"
read_action_variable \
  "atlas-gardener" \
  "ATLAS_GARDENER_WRITE_TARGETS_JSON" \
  "${GARDENER_DIR}/variable-write-targets.json" \
  "${GARDENER_DIR}/variable-write-targets.error"

printf 'PART 2: Inspect atlas-interface-kit\n'
INTERFACE_DIR="${EVIDENCE_DIR}/atlas-interface-kit"
mkdir -p "$INTERFACE_DIR"
verify_repository \
  "atlas-interface-kit" \
  "21a1a168e3b25e916555ce4edd4229bd7c061ecb" \
  "false" \
  "$INTERFACE_DIR"
verify_merged_validation_pr \
  "atlas-interface-kit" \
  "14" \
  "1f26360d938b589cf8a562ca308fd6ca3b4a2b3f" \
  "21a1a168e3b25e916555ce4edd4229bd7c061ecb" \
  "Validate interface kit" \
  "$INTERFACE_DIR"
fetch_raw_file \
  "atlas-interface-kit" \
  ".github/workflows/ci.yml" \
  "${INTERFACE_DIR}/ci.yml"
fetch_raw_file \
  "atlas-interface-kit" \
  ".github/workflows/release.yml" \
  "${INTERFACE_DIR}/release.yml"

printf 'PART 3: Inspect atlas-journey-watch\n'
JOURNEY_DIR="${EVIDENCE_DIR}/atlas-journey-watch"
mkdir -p "$JOURNEY_DIR"
verify_repository \
  "atlas-journey-watch" \
  "a124d23ba4444522c206ae3c169165b4e0ef8019" \
  "true" \
  "$JOURNEY_DIR"
verify_open_validation_pr \
  "atlas-journey-watch" \
  "12" \
  "a124d23ba4444522c206ae3c169165b4e0ef8019" \
  "acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022" \
  "Offline journey validation" \
  "$JOURNEY_DIR"
fetch_raw_file \
  "atlas-journey-watch" \
  ".github/workflows/ci.yml" \
  "${JOURNEY_DIR}/ci.yml"
fetch_raw_file \
  "atlas-journey-watch" \
  ".github/workflows/dependabot-automerge.yml" \
  "${JOURNEY_DIR}/dependabot-automerge.yml"
fetch_raw_file \
  "atlas-journey-watch" \
  ".github/workflows/release-watch.yml" \
  "${JOURNEY_DIR}/release-watch.yml"
read_action_variable \
  "atlas-journey-watch" \
  "DEPENDABOT_AUTOMERGE_ENABLED" \
  "${JOURNEY_DIR}/variable-dependabot-automerge.json" \
  "${JOURNEY_DIR}/variable-dependabot-automerge.error"

printf 'PART 4: Render bounded provider baseline summary\n'
jq -n \
  --slurpfile gardener_repo "${GARDENER_DIR}/repository.json" \
  --slurpfile gardener_rulesets "${GARDENER_DIR}/rulesets.json" \
  --slurpfile gardener_classic "${GARDENER_DIR}/classic-protection-summary.json" \
  --slurpfile gardener_mode "${GARDENER_DIR}/variable-mode.json" \
  --slurpfile gardener_gate "${GARDENER_DIR}/variable-write-gate.json" \
  --slurpfile gardener_targets "${GARDENER_DIR}/variable-write-targets.json" \
  --slurpfile interface_repo "${INTERFACE_DIR}/repository.json" \
  --slurpfile interface_rulesets "${INTERFACE_DIR}/rulesets.json" \
  --slurpfile interface_classic "${INTERFACE_DIR}/classic-protection-summary.json" \
  --slurpfile journey_repo "${JOURNEY_DIR}/repository.json" \
  --slurpfile journey_rulesets "${JOURNEY_DIR}/rulesets.json" \
  --slurpfile journey_classic "${JOURNEY_DIR}/classic-protection-summary.json" \
  --slurpfile journey_automerge "${JOURNEY_DIR}/variable-dependabot-automerge.json" \
  '{
    schema: "atlas-github-provider-guard-wave-2/inspection-summary/v1",
    provider_writes_performed: false,
    repositories: {
      "atlas-gardener": {
        auto_merge: $gardener_repo[0].allow_auto_merge,
        rulesets: $gardener_rulesets[0],
        classic_protection: $gardener_classic[0],
        controller_variables: [
          $gardener_mode[0],
          $gardener_gate[0],
          $gardener_targets[0]
        ]
      },
      "atlas-interface-kit": {
        auto_merge: $interface_repo[0].allow_auto_merge,
        rulesets: $interface_rulesets[0],
        classic_protection: $interface_classic[0]
      },
      "atlas-journey-watch": {
        auto_merge: $journey_repo[0].allow_auto_merge,
        rulesets: $journey_rulesets[0],
        classic_protection: $journey_classic[0],
        dependabot_automerge_variable: $journey_automerge[0]
      }
    }
  }' \
  >"${EVIDENCE_DIR}/provider-baseline-summary.json"

printf 'PART 5: Evidence identity\n'
write_sha256s "$EVIDENCE_DIR" "${EVIDENCE_DIR}/SHA256SUMS.txt"

printf 'Wave 2 inspection complete.\n'
printf 'Provider writes performed: none.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
printf 'Do not create a ruleset or change auto-merge from this script.\n'
