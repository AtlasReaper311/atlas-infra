#!/usr/bin/env bash
set -eu

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
PINNED_DEPENDABOT_AUTHORITY="8e6d08701823b02c4859bfc72af67fc8ace1f4b5"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-2b-inspection}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${STAMP}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: required command is unavailable: $1" >&2
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

  echo "ERROR: neither sha256sum nor shasum is available." >&2
  exit 1
}

fetch_raw_file() {
  repository="$1"
  ref="$2"
  path="$3"
  destination="$4"

  gh api \
    -H 'Accept: application/vnd.github.raw+json' \
    "/repos/${repository}/contents/${path}?ref=${ref}" \
    >"${destination}"
}

echo "PART 0: Preflight"

for command_name in gh jq python3
 do
  require_command "${command_name}"
 done

gh auth status >/dev/null

AUTHENTICATED_LOGIN="$(gh api /user --jq '.login')"

if [ "${AUTHENTICATED_LOGIN}" != "${OWNER}" ]
then
  echo "ERROR: gh is authenticated as ${AUTHENTICATED_LOGIN}, expected ${OWNER}." >&2
  exit 1
fi

mkdir -p "${EVIDENCE_DIR}"

echo "PART 1: Capture current repository and provider state"

gh api "/repos/${FULL_REPOSITORY}" >"${EVIDENCE_DIR}/repository.json"
gh api "/repos/${FULL_REPOSITORY}/commits/main" >"${EVIDENCE_DIR}/main.json"
gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rulesets?per_page=100" >"${EVIDENCE_DIR}/rulesets.json"
gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rulesets/${EXPECTED_RULESET_ID}" >"${EVIDENCE_DIR}/ruleset-19154613.json"
gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/rules/branches/main" >"${EVIDENCE_DIR}/active-rules-main.json"

if gh api "/repos/${FULL_REPOSITORY}/branches/main/protection" >"${EVIDENCE_DIR}/classic-protection.json" 2>"${EVIDENCE_DIR}/classic-protection.json.error"
then
  printf '%s\n' '{"status":"present"}' >"${EVIDENCE_DIR}/classic-protection-summary.json"
else
  if grep -q 'HTTP 404' "${EVIDENCE_DIR}/classic-protection.json.error"
  then
    printf '%s\n' '{"status":"absent"}' >"${EVIDENCE_DIR}/classic-protection-summary.json"
  else
    cat "${EVIDENCE_DIR}/classic-protection.json.error" >&2
    exit 1
  fi
fi

gh api "/repos/${FULL_REPOSITORY}/actions/variables/${EXPECTED_VARIABLE}" >"${EVIDENCE_DIR}/dependabot-automerge-variable.json"

echo "PART 2: Capture genuine Dependabot path"

gh api "/repos/${FULL_REPOSITORY}/pulls/${EXPECTED_PR}" >"${EVIDENCE_DIR}/validation-pr.json"
gh api -H 'Accept: application/vnd.github+json' "/repos/${FULL_REPOSITORY}/commits/${EXPECTED_PR_HEAD}/check-runs?per_page=100" >"${EVIDENCE_DIR}/validation-check-runs.json"

gh pr view "${EXPECTED_PR}" \
  --repo "${FULL_REPOSITORY}" \
  --json number,state,isDraft,mergeable,mergeStateStatus,headRefOid,baseRefOid,author,autoMergeRequest \
  >"${EVIDENCE_DIR}/validation-pr-automerge.json"

echo "PART 3: Capture immutable automation authority"

fetch_raw_file "${FULL_REPOSITORY}" "${EXPECTED_MAIN_SHA}" ".github/workflows/ci.yml" "${EVIDENCE_DIR}/ci.yml"
fetch_raw_file "${FULL_REPOSITORY}" "${EXPECTED_MAIN_SHA}" ".github/workflows/dependabot-automerge.yml" "${EVIDENCE_DIR}/dependabot-automerge.yml"
fetch_raw_file "${FULL_REPOSITORY}" "${EXPECTED_MAIN_SHA}" ".github/workflows/release-watch.yml" "${EVIDENCE_DIR}/release-watch.yml"
fetch_raw_file "AtlasReaper311/atlas-infra" "${PINNED_DEPENDABOT_AUTHORITY}" ".github/workflows/dependabot-review.yml" "${EVIDENCE_DIR}/pinned-dependabot-review.yml"
fetch_raw_file "AtlasReaper311/atlas-infra" "${PINNED_DEPENDABOT_AUTHORITY}" "scripts/dependabot_automerge_policy.py" "${EVIDENCE_DIR}/pinned-dependabot-automerge-policy.py"

echo "PART 4: Verify pinned identity and normalize reconciliation evidence"

python3 - "${EVIDENCE_DIR}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

def read_json(name):
    return json.loads((root / name).read_text(encoding="utf-8"))

repository = read_json("repository.json")
main = read_json("main.json")
rulesets = read_json("rulesets.json")
ruleset = read_json("ruleset-19154613.json")
active_rules = read_json("active-rules-main.json")
classic = read_json("classic-protection-summary.json")
variable = read_json("dependabot-automerge-variable.json")
pr = read_json("validation-pr.json")
checks = read_json("validation-check-runs.json")
automerge = read_json("validation-pr-automerge.json")

expected_main = "a124d23ba4444522c206ae3c169165b4e0ef8019"
expected_head = "acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022"
expected_context = "Offline journey validation"
expected_integration = 15368
expected_ruleset_id = 19154613

if repository.get("full_name") != "AtlasReaper311/atlas-journey-watch":
    raise SystemExit("ERROR: repository identity drifted.")
if repository.get("default_branch") != "main":
    raise SystemExit("ERROR: default branch drifted.")
if repository.get("visibility") != "public" or repository.get("archived") is not False:
    raise SystemExit("ERROR: repository visibility/lifecycle drifted.")
if repository.get("allow_auto_merge") is not True:
    raise SystemExit("ERROR: repository auto-merge is no longer enabled.")
if main.get("sha") != expected_main:
    raise SystemExit("ERROR: main moved from the reviewed Part 0 identity.")

active_branch_rulesets = [
    item for item in rulesets
    if item.get("target") == "branch" and item.get("enforcement") == "active"
]
if len(active_branch_rulesets) != 1 or active_branch_rulesets[0].get("id") != expected_ruleset_id:
    raise SystemExit("ERROR: active branch ruleset set drifted from the reviewed hold state.")

if ruleset.get("id") != expected_ruleset_id:
    raise SystemExit("ERROR: ruleset 19154613 could not be read back exactly.")
if ruleset.get("name") != "Require native pull request validation":
    raise SystemExit("ERROR: held ruleset name drifted.")
if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
    raise SystemExit("ERROR: held ruleset target/enforcement drifted.")

if variable.get("name") != "DEPENDABOT_AUTOMERGE_ENABLED" or variable.get("value") != "true":
    raise SystemExit("ERROR: selective Dependabot auto-merge opt-in drifted.")

if pr.get("number") != 12 or pr.get("state") != "open":
    raise SystemExit("ERROR: validation PR #12 is no longer open.")
if pr.get("base", {}).get("sha") != expected_main:
    raise SystemExit("ERROR: validation PR base drifted.")
if pr.get("head", {}).get("sha") != expected_head:
    raise SystemExit("ERROR: validation PR head drifted.")
if pr.get("mergeable") is not True:
    raise SystemExit("ERROR: validation PR #12 is not currently mergeable.")

matching_checks = [
    check for check in checks.get("check_runs", [])
    if check.get("name") == expected_context
    and check.get("head_sha") == expected_head
    and check.get("status") == "completed"
    and check.get("conclusion") == "success"
    and check.get("app", {}).get("id") == expected_integration
]
if len(matching_checks) != 1:
    raise SystemExit("ERROR: native required check is not uniquely successful.")

if automerge.get("number") != 12 or automerge.get("headRefOid") != expected_head:
    raise SystemExit("ERROR: gh PR auto-merge projection does not match PR #12 head.")

rule_types = sorted(rule.get("type") for rule in ruleset.get("rules", []))
pull_request_rule = next((rule for rule in ruleset.get("rules", []) if rule.get("type") == "pull_request"), None)
status_rule = next((rule for rule in ruleset.get("rules", []) if rule.get("type") == "required_status_checks"), None)

pull_parameters = (pull_request_rule or {}).get("parameters", {})
status_parameters = (status_rule or {}).get("parameters", {})

standard_required_checks = [{"context": expected_context, "integration_id": expected_integration}]

standard_semantics = {
    "default_branch_only": ruleset.get("conditions", {}).get("ref_name", {}).get("include") == ["~DEFAULT_BRANCH"]
    and ruleset.get("conditions", {}).get("ref_name", {}).get("exclude") == [],
    "no_bypass_actors": ruleset.get("bypass_actors", []) == [],
    "deletion_blocked": "deletion" in rule_types,
    "non_fast_forward_blocked": "non_fast_forward" in rule_types,
    "pull_request_required": pull_request_rule is not None,
    "zero_required_approvals": pull_parameters.get("required_approving_review_count") == 0,
    "review_thread_resolution_not_required": pull_parameters.get("required_review_thread_resolution") is False,
    "native_required_check_exact": status_parameters.get("required_status_checks") == standard_required_checks,
    "strict_required_status_policy_disabled": status_parameters.get("strict_required_status_checks_policy") is False,
}

summary = {
    "schema": "atlas-github-provider-guard-wave-2b/inspection-summary/v1",
    "repository": "AtlasReaper311/atlas-journey-watch",
    "main": expected_main,
    "repository_auto_merge": True,
    "dependabot_automerge_enabled": True,
    "ruleset": {
        "id": expected_ruleset_id,
        "name": ruleset.get("name"),
        "target": ruleset.get("target"),
        "enforcement": ruleset.get("enforcement"),
        "rule_types": rule_types,
        "conditions": ruleset.get("conditions"),
        "bypass_actors": ruleset.get("bypass_actors", []),
        "pull_request_parameters": pull_parameters,
        "required_status_parameters": status_parameters,
        "effective_rule_types_on_main": sorted(
            rule.get("type") for rule in active_rules if rule.get("ruleset_id") == expected_ruleset_id
        ),
        "standard_semantics": standard_semantics,
        "qualifies_standard_guard_semantics": all(standard_semantics.values()),
    },
    "classic_protection": classic,
    "genuine_dependabot_pr": {
        "number": 12,
        "head": expected_head,
        "native_required_context": expected_context,
        "native_required_context_success": True,
        "auto_merge_request": automerge.get("autoMergeRequest"),
        "merge_state_status": automerge.get("mergeStateStatus"),
    },
    "provider_writes_performed": False,
    "variables_written": False,
    "secrets_read": False,
    "wave_3_started": False,
}

(root / "wave-2b-inspection-summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

print("Wave 2B provider state captured and normalized.")
print("Existing ruleset qualifies standard semantics:", summary["ruleset"]["qualifies_standard_guard_semantics"])
print("Dependabot PR #12 auto-merge request present:", summary["genuine_dependabot_pr"]["auto_merge_request"] is not None)
print("Provider writes performed: 0")
PY

echo "PART 5: Build SHA-256 evidence manifest"

(
  cd "${EVIDENCE_DIR}"
  : >SHA256SUMS.txt
  for path in $(find . -type f ! -name SHA256SUMS.txt | LC_ALL=C sort)
  do
    digest="$(sha256_file "${path}")"
    printf '%s  %s\n' "${digest}" "${path#./}" >>SHA256SUMS.txt
  done
)

echo
echo "WAVE 2B READ-ONLY INSPECTION COMPLETE"
echo "Evidence: ${EVIDENCE_DIR}"
echo "Provider writes performed: none."
echo "Variables written: none."
echo "Secrets read: none."
echo "Wave 3 started: no."
