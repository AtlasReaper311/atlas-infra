#!/usr/bin/env bash
set -eu

OWNER="AtlasReaper311"
GITHUB_ACTIONS_APP_ID="15368"
EVIDENCE_ROOT="${EVIDENCE_ROOT:-reports/github-provider-guard-wave-3-inspection}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${EVIDENCE_ROOT}/${TIMESTAMP}"

REPOSITORIES="atlas-doc-viewer atlas-quota-watch site-pulse specular-sonify status"

expected_main() {
  case "$1" in
    atlas-doc-viewer) printf '%s\n' '2b03d5843588f0415ecc735f6b33ca7527063137' ;;
    atlas-quota-watch) printf '%s\n' '97304b7df2489a881aca422e494063d62f034a55' ;;
    site-pulse) printf '%s\n' 'be661f348ce7bc96b98f868b9d0eb2c01fcc99af' ;;
    specular-sonify) printf '%s\n' '2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53' ;;
    status) printf '%s\n' '4db1438b1a8859008461903105360a2f09376c02' ;;
    *) return 1 ;;
  esac
}

expected_context() {
  case "$1" in
    atlas-doc-viewer) printf '%s\n' 'Static document validation' ;;
    atlas-quota-watch) printf '%s\n' 'validate' ;;
    site-pulse) printf '%s\n' 'Worker validation' ;;
    specular-sonify) printf '%s\n' 'Worker configuration validation' ;;
    status) printf '%s\n' 'Status site validation' ;;
    *) return 1 ;;
  esac
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1
  then
    sha256sum "$1" | awk '{print $1}'
    return
  fi

  shasum -a 256 "$1" | awk '{print $1}'
}

capture_api() {
  output_path="$1"
  shift

  if gh api "$@" >"${output_path}" 2>"${output_path}.error"
  then
    rm -f "${output_path}.error"
    return 0
  fi

  rm -f "${output_path}"
  return 0
}

capture_file() {
  repository="$1"
  path="$2"
  output_path="$3"
  ref="$4"

  gh api \
    -H 'Accept: application/vnd.github.raw+json' \
    "/repos/${OWNER}/${repository}/contents/${path}?ref=${ref}" \
    >"${output_path}"
}

verify_gate_context() {
  repository="$1"
  gate_path="$2"
  expected="$3"

  python3 - "$repository" "$gate_path" "$expected" <<'PY'
import json
import sys
from pathlib import Path

repository = sys.argv[1]
path = Path(sys.argv[2])
expected = sys.argv[3]
text = path.read_text(encoding="utf-8")
needle = f'required_checks_json: \'["{expected}"]\''
if needle not in text:
    raise SystemExit(
        f"ERROR: {repository} Gardener gate no longer pins expected native context {expected!r}."
    )
PY
}

echo "PART 0: Preflight"

for command_name in gh jq python3
 do
  if ! command -v "${command_name}" >/dev/null 2>&1
  then
    echo "ERROR: required command is unavailable: ${command_name}" >&2
    exit 1
  fi
 done

gh auth status >/dev/null

AUTHENTICATED_LOGIN="$(gh api /user --jq '.login')"
if [ "${AUTHENTICATED_LOGIN}" != "${OWNER}" ]
then
  echo "ERROR: gh is authenticated as ${AUTHENTICATED_LOGIN}, expected ${OWNER}." >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "PART 1: Inspect five Wave 3 repositories"

for repository in ${REPOSITORIES}
 do
  repo_dir="${OUTPUT_DIR}/${repository}"
  mkdir -p "${repo_dir}"

  expected_sha="$(expected_main "${repository}")"
  native_context="$(expected_context "${repository}")"

  gh api "/repos/${OWNER}/${repository}" >"${repo_dir}/repository.json"
  gh api "/repos/${OWNER}/${repository}/commits/main" >"${repo_dir}/main.json"

  actual_sha="$(jq -r '.sha' "${repo_dir}/main.json")"
  if [ "${actual_sha}" != "${expected_sha}" ]
  then
    echo "ERROR: ${repository} main drifted: expected ${expected_sha}, got ${actual_sha}." >&2
    exit 1
  fi

  if [ "$(jq -r '.default_branch' "${repo_dir}/repository.json")" != "main" ]
  then
    echo "ERROR: ${repository} default branch is no longer main." >&2
    exit 1
  fi

  if [ "$(jq -r '.archived' "${repo_dir}/repository.json")" != "false" ]
  then
    echo "ERROR: ${repository} is archived." >&2
    exit 1
  fi

  if [ "$(jq -r '.allow_auto_merge' "${repo_dir}/repository.json")" != "true" ]
  then
    echo "ERROR: ${repository} repository auto-merge drifted from the reviewed source baseline." >&2
    exit 1
  fi

  capture_api "${repo_dir}/classic-protection.json" \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/branches/main/protection"

  capture_api "${repo_dir}/rulesets.json" \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rulesets?includes_parents=true"

  capture_api "${repo_dir}/active-rules-main.json" \
    -H 'Accept: application/vnd.github+json' \
    "/repos/${OWNER}/${repository}/rules/branches/main"

  capture_api "${repo_dir}/gardener-automerge-variable.json" \
    "/repos/${OWNER}/${repository}/actions/variables/ATLAS_GARDENER_AUTOMERGE_ENABLED"

  capture_api "${repo_dir}/dependabot-automerge-variable.json" \
    "/repos/${OWNER}/${repository}/actions/variables/DEPENDABOT_AUTOMERGE_ENABLED"

  gh pr list \
    --repo "${OWNER}/${repository}" \
    --state open \
    --limit 100 \
    --json number,title,state,headRefName,headRefOid,baseRefName,author \
    >"${repo_dir}/open-prs.json"

  gh pr list \
    --repo "${OWNER}/${repository}" \
    --state merged \
    --limit 1 \
    --json number,title,state,headRefName,headRefOid,baseRefName,author,mergedAt \
    >"${repo_dir}/latest-merged-pr-list.json"

  latest_head="$(jq -r 'if length == 0 then "" else .[0].headRefOid end' "${repo_dir}/latest-merged-pr-list.json")"
  if [ -n "${latest_head}" ]
  then
    gh api \
      -H 'Accept: application/vnd.github+json' \
      "/repos/${OWNER}/${repository}/commits/${latest_head}/check-runs?per_page=100" \
      >"${repo_dir}/latest-merged-pr-check-runs.json"
  else
    printf '%s\n' '{"total_count":0,"check_runs":[]}' >"${repo_dir}/latest-merged-pr-check-runs.json"
  fi

  capture_file \
    "${repository}" \
    '.github/workflows/gardener-remediation-gate.yml' \
    "${repo_dir}/gardener-remediation-gate.yml" \
    "${expected_sha}"

  capture_file \
    "${repository}" \
    '.github/workflows/dependabot-automerge.yml' \
    "${repo_dir}/dependabot-automerge.yml" \
    "${expected_sha}"

  verify_gate_context "${repository}" "${repo_dir}/gardener-remediation-gate.yml" "${native_context}"

done

echo "PART 2: Inspect Gardener controller authority"

mkdir -p "${OUTPUT_DIR}/atlas-gardener-controller"
for variable_name in \
  ATLAS_GARDENER_MODE \
  ATLAS_GARDENER_WRITE_GATE \
  ATLAS_GARDENER_WRITE_TARGETS_JSON
 do
  capture_api \
    "${OUTPUT_DIR}/atlas-gardener-controller/${variable_name}.json" \
    "/repos/${OWNER}/atlas-gardener/actions/variables/${variable_name}"
 done

echo "PART 3: Normalize read-only inspection"

python3 - "${OUTPUT_DIR}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
repositories = {
    "atlas-doc-viewer": {
        "main": "2b03d5843588f0415ecc735f6b33ca7527063137",
        "native_context": "Static document validation",
    },
    "atlas-quota-watch": {
        "main": "97304b7df2489a881aca422e494063d62f034a55",
        "native_context": "validate",
    },
    "site-pulse": {
        "main": "be661f348ce7bc96b98f868b9d0eb2c01fcc99af",
        "native_context": "Worker validation",
    },
    "specular-sonify": {
        "main": "2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53",
        "native_context": "Worker configuration validation",
    },
    "status": {
        "main": "4db1438b1a8859008461903105360a2f09376c02",
        "native_context": "Status site validation",
    },
}


def read_json(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def api_status(path: Path):
    if path.is_file():
        return "present"
    error = Path(str(path) + ".error")
    if error.is_file():
        return "absent-or-unavailable"
    return "missing-evidence"

summary_repositories = {}
for repository, expected in repositories.items():
    repo_dir = root / repository
    repo = read_json(repo_dir / "repository.json")
    rulesets = read_json(repo_dir / "rulesets.json")
    active_rules = read_json(repo_dir / "active-rules-main.json")
    gardener_variable = read_json(repo_dir / "gardener-automerge-variable.json")
    dependabot_variable = read_json(repo_dir / "dependabot-automerge-variable.json")
    latest_list = read_json(repo_dir / "latest-merged-pr-list.json") or []
    checks = read_json(repo_dir / "latest-merged-pr-check-runs.json") or {"check_runs": []}

    native_matches = [
        item
        for item in checks.get("check_runs", [])
        if item.get("name") == expected["native_context"]
        and item.get("status") == "completed"
        and item.get("conclusion") == "success"
        and item.get("app", {}).get("id") == 15368
    ]

    summary_repositories[repository] = {
        "main": expected["main"],
        "repository_auto_merge": repo.get("allow_auto_merge") if repo else None,
        "classic_protection": api_status(repo_dir / "classic-protection.json"),
        "rulesets_status": api_status(repo_dir / "rulesets.json"),
        "ruleset_count": len(rulesets) if isinstance(rulesets, list) else None,
        "active_rules_status": api_status(repo_dir / "active-rules-main.json"),
        "active_rule_types": sorted(
            item.get("type") for item in (active_rules or []) if isinstance(item, dict) and item.get("type")
        ),
        "gardener_automerge_variable": gardener_variable,
        "dependabot_automerge_variable": dependabot_variable,
        "native_context": expected["native_context"],
        "latest_merged_pr": latest_list[0] if latest_list else None,
        "latest_merged_pr_native_context_success": len(native_matches) == 1,
    }

controller = {}
for name in (
    "ATLAS_GARDENER_MODE",
    "ATLAS_GARDENER_WRITE_GATE",
    "ATLAS_GARDENER_WRITE_TARGETS_JSON",
):
    path = root / "atlas-gardener-controller" / f"{name}.json"
    controller[name] = read_json(path)

summary = {
    "schema": "atlas-github-provider-guard-wave-3/inspection-summary/v1",
    "github_actions_integration_id": 15368,
    "repositories": summary_repositories,
    "gardener_controller": controller,
    "provider_writes_performed": False,
    "variables_written": False,
    "secrets_read": False,
    "wave_4_started": False,
}

(root / "wave-3-inspection-summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

echo "PART 4: Build evidence digests"

(
  cd "${OUTPUT_DIR}"
  : > SHA256SUMS.txt
  find . -type f ! -name SHA256SUMS.txt -print | LC_ALL=C sort | while IFS= read -r path
  do
    clean_path="${path#./}"
    digest="$(sha256_file "${clean_path}")"
    printf '%s  %s\n' "${digest}" "${clean_path}" >> SHA256SUMS.txt
  done
)

echo
echo "WAVE 3 READ-ONLY INSPECTION COMPLETE"
echo "Provider writes performed: 0"
echo "Variables written: 0"
echo "Secrets read: 0"
echo "Wave 4 started: false"
echo "Evidence directory: ${OUTPUT_DIR}"
