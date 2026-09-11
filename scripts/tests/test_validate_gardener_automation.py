import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_contracts
import validate_gardener_automation


class GardenerAutomationAuthorityTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def policy(self) -> dict:
        return self.load("policy/gardener-automation.json")

    def coverage(self) -> dict:
        return self.load("policy/gardener-github-app-coverage.json")

    def graph_candidate(self) -> dict:
        return {
            "kind": "npm-lock-security-remediation",
            "manifest_file": "package.json",
            "lockfile_file": "package-lock.json",
            "npm_version": "10.9.3",
            "direct_updates": [
                {
                    "dependency": "wrangler",
                    "section": "devDependencies",
                    "current_version": "4.127.0",
                    "target_version": "4.131.0",
                    "current_spec": "^4.127.0",
                    "target_spec": "^4.131.0",
                    "vulnerability_ids": ["GHSA-rgj7-g3m4-5g8c"],
                }
            ],
            "transitive_updates": [
                {
                    "dependency": "brace-expansion",
                    "package_path": "node_modules/brace-expansion",
                    "current_version": "5.0.7",
                    "target_version": "5.0.9",
                    "parents": [
                        {
                            "package_path": "node_modules/minimatch",
                            "specifier": "^5.0.0",
                        }
                    ],
                    "vulnerability_ids": ["GHSA-rgw5-rvv9-x895"],
                }
            ],
            "vulnerability_ids": [
                "GHSA-rgj7-g3m4-5g8c",
                "GHSA-rgw5-rvv9-x895",
            ],
            "target_manifest_sha256": "sha256:" + "a" * 64,
            "target_lockfile_sha256": "sha256:" + "b" * 64,
        }

    def test_committed_policy_is_valid_and_disabled(self):
        report = validate_gardener_automation.validate_policy(
            self.policy(), self.coverage()
        )
        self.assertEqual("valid", report["status"])
        self.assertEqual("disabled", report["default_mode"])
        self.assertEqual(20, report["coverage_count"])
        self.assertEqual(
            ["macos-metadata-ignore", "python-cache-ignore"],
            report["automatic_fixers"],
        )
        self.assertEqual(
            [
                "action-pin-plan",
                "container-digest-pin",
                "npm-lock-security-remediation",
                "npm-security-update",
                "python-security-pin",
                "workflow-permissions",
                "workflow-timeout",
            ],
            report["review_only_fixers"],
        )
        self.assertEqual(0, report["provider_mutations"])

    def test_unknown_mode_fails_closed(self):
        policy = self.policy()
        policy["allowed_modes"].append("unsafe")
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "exact ordered v1 mode set"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_default_write_mode_fails_closed(self):
        policy = self.policy()
        policy["default_mode"] = "automerge-low-risk"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "default source mode"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_dependency_fixer_cannot_gain_automatic_merge(self):
        policy = self.policy()
        policy["fixers"]["npm-security-update"]["automatic_merge"] = True
        policy["fixers"]["npm-security-update"]["risk_class"] = "low"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "must remain review-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_graph_fixer_cannot_gain_automatic_merge(self):
        policy = self.policy()
        policy["fixers"]["npm-lock-security-remediation"]["automatic_merge"] = True
        policy["fixers"]["npm-lock-security-remediation"]["risk_class"] = "low"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "must remain review-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_container_fixer_cannot_gain_automatic_merge(self):
        policy = self.policy()
        policy["fixers"]["container-digest-pin"]["automatic_merge"] = True
        policy["fixers"]["container-digest-pin"]["risk_class"] = "low"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "must remain review-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_housekeeping_fixer_is_gitignore_only(self):
        policy = self.policy()
        policy["fixers"]["python-cache-ignore"]["automatic_merge_paths"] = [
            ".gitignore",
            "src/cache.py",
        ]
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "gitignore-only"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_fixer_path_boundary_cannot_expand(self):
        policy = self.policy()
        policy["fixers"]["python-security-pin"]["allowed_path_patterns"] = [r".*"]
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "allowed path boundary changed"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_graph_fixer_path_boundary_cannot_expand(self):
        policy = self.policy()
        policy["fixers"]["npm-lock-security-remediation"]["allowed_path_patterns"] = [
            r".*"
        ]
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "allowed path boundary changed"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_new_review_paths_are_not_globally_forbidden(self):
        policy = self.policy()
        policy["forbidden_exact_paths"].append("requirements.txt")
        policy["forbidden_exact_paths"].sort()
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError,
            "review-only remediation paths remain globally forbidden",
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_unverified_coverage_fails_closed(self):
        coverage = self.coverage()
        coverage["batches"][0]["status"] = "planned"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "not verified"
        ):
            validate_gardener_automation.validate_policy(self.policy(), coverage)

    def test_permission_expansion_fails_closed(self):
        coverage = self.coverage()
        coverage["permissions"]["actions"] = "read"
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "permission boundary changed"
        ):
            validate_gardener_automation.validate_policy(self.policy(), coverage)

    def test_long_approval_expiry_fails_closed(self):
        policy = self.policy()
        policy["approval_ttl_hours"] = 25
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "longer than 24 hours"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_missing_source_path_refusal_fails_closed(self):
        policy = self.policy()
        policy["forbidden_path_prefixes"].remove("src/")
        with self.assertRaisesRegex(
            validate_gardener_automation.PolicyError, "required forbidden prefix"
        ):
            validate_gardener_automation.validate_policy(policy, self.coverage())

    def test_schedule_schema_alignment_is_weekly(self):
        policy = self.policy()
        self.assertEqual("15 10 * * 1", policy["scheduling"]["controller_cron"])
        self.assertFalse(policy["scheduling"]["daily_reconciliation"])

    def test_policy_digest_is_deterministic(self):
        policy = self.policy()
        reordered = copy.deepcopy(policy)
        reordered = dict(reversed(list(reordered.items())))
        self.assertEqual(
            validate_gardener_automation.digest_json(policy),
            validate_gardener_automation.digest_json(reordered),
        )

    def test_finding_schema_accepts_graph_candidate_and_disposition(self):
        schema = self.load("contracts/v1/finding.schema.json")
        finding = self.load("contracts/v1/fixtures/valid/finding.json")
        finding["remediation"] = {
            "eligible": True,
            "reason": "Bounded npm graph regeneration proved the advisory set absent.",
            "disposition": "remediation-available",
            "candidate": self.graph_candidate(),
        }
        self.assertEqual(
            [], control_plane_contracts.validate_instance(finding, schema)
        )
        fingerprint_rules = self.load("contracts/v1/fingerprint-rules.json")
        self.assertEqual(
            [],
            control_plane_contracts.semantic_errors(
                "finding.schema.json", finding, fingerprint_rules
            ),
        )

    def test_graph_candidate_requires_at_least_one_operation(self):
        schema = self.load("contracts/v1/finding.schema.json")
        finding = self.load("contracts/v1/fixtures/valid/finding.json")
        candidate = self.graph_candidate()
        candidate["direct_updates"] = []
        candidate["transitive_updates"] = []
        finding["remediation"] = {
            "eligible": True,
            "reason": "Invalid empty graph candidate.",
            "disposition": "remediation-available",
            "candidate": candidate,
        }
        errors = control_plane_contracts.validate_instance(finding, schema)
        self.assertTrue(any("anyOf" in error for error in errors), errors)

    def test_unknown_disposition_is_rejected(self):
        schema = self.load("contracts/v1/finding.schema.json")
        finding = self.load("contracts/v1/fixtures/valid/finding.json")
        finding["remediation"]["disposition"] = "pretend-fixed"
        errors = control_plane_contracts.validate_instance(finding, schema)
        self.assertTrue(any("must be one of" in error for error in errors), errors)

    def test_proposal_schema_accepts_graph_remediation_input(self):
        schema = self.load("contracts/v1/remediation-proposal.schema.json")
        proposal = self.load("contracts/v1/fixtures/valid/remediation-proposal.json")
        proposal["remediation_input"] = self.graph_candidate()
        self.assertEqual(
            [], control_plane_contracts.validate_instance(proposal, schema)
        )
        fingerprint_rules = self.load("contracts/v1/fingerprint-rules.json")
        self.assertEqual(
            [],
            control_plane_contracts.semantic_errors(
                "remediation-proposal.schema.json", proposal, fingerprint_rules
            ),
        )


if __name__ == "__main__":
    unittest.main()
