from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-2b-reconcile.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-2b-plan.md"


class GithubProviderGuardWave2BReconcileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_exactly_journey_watch(self) -> None:
        self.assertIn('REPOSITORY="atlas-journey-watch"', self.script)
        self.assertNotIn('REPOSITORY="atlas-gardener"', self.script)
        self.assertNotIn('REPOSITORY="atlas-interface-kit"', self.script)

    def test_existing_ruleset_is_updated_in_place(self) -> None:
        self.assertIn('EXPECTED_RULESET_ID="19154613"', self.script)
        self.assertIn('/rulesets/${EXPECTED_RULESET_ID}', self.script)
        self.assertEqual(self.script.count("--method PUT"), 1)
        self.assertNotIn("--method POST", self.script)
        self.assertNotIn("--method PATCH", self.script)
        self.assertNotIn("--method DELETE", self.script)

    def test_baseline_is_pinned_to_reviewed_inspection(self) -> None:
        for value in (
            "a124d23ba4444522c206ae3c169165b4e0ef8019",
            "Require native pull request validation",
            "acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022",
            "Offline journey validation",
            "15368",
            "DEPENDABOT_AUTOMERGE_ENABLED",
        ):
            self.assertIn(value, self.script)
            self.assertIn(value, self.plan)

        self.assertIn('["refs/heads/main"]', self.script)
        self.assertIn("strict_required_status_checks_policy == true", self.script)
        self.assertIn("rule types: `required_status_checks`", self.plan)

    def test_reconciled_guard_shape_matches_atlas_pattern(self) -> None:
        self.assertIn('include: ["~DEFAULT_BRANCH"]', self.script)
        self.assertIn('{type: "deletion"}', self.script)
        self.assertIn('{type: "non_fast_forward"}', self.script)
        self.assertIn('type: "pull_request"', self.script)
        self.assertIn("required_approving_review_count: 0", self.script)
        self.assertIn("required_review_thread_resolution: false", self.script)
        self.assertIn('type: "required_status_checks"', self.script)
        self.assertIn("strict_required_status_checks_policy: false", self.script)

    def test_selective_automerge_is_preserved_not_mutated(self) -> None:
        self.assertIn('.allow_auto_merge == true', self.script)
        self.assertIn('EXPECTED_VARIABLE_VALUE="true"', self.script)
        self.assertIn(".autoMergeRequest == null", self.script)
        self.assertNotIn("gh variable set", self.script)
        self.assertNotIn("gh variable delete", self.script)
        self.assertNotIn("enable_auto_merge", self.script)
        self.assertNotIn("gh pr merge", self.script)
        self.assertIn("Repository auto-merge remains enabled", self.plan)
        self.assertIn("`DEPENDABOT_AUTOMERGE_ENABLED=true` remains unchanged", self.plan)

    def test_apply_requires_exact_confirmation(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn("APPLY GITHUB PROVIDER GUARD WAVE 2B", self.script)
        self.assertIn("Any provider mutation requires a new explicit approval", self.plan)

    def test_genuine_dependabot_path_stays_open(self) -> None:
        self.assertIn('.user.login == "dependabot[bot]"', self.script)
        self.assertIn('.state == "open"', self.script)
        self.assertIn('.mergeable == true', self.script)
        self.assertIn('.autoMergeRequest == null', self.script)
        self.assertIn("PR `#12` remains a genuine ineligible Dependabot specimen", self.plan)

    def test_no_unrelated_mutation_surface(self) -> None:
        forbidden = (
            "gh secret",
            "gh workflow run",
            "gh release create",
            '/actions/variables/${EXPECTED_VARIABLE}" --method',
            'rulesets" --method POST',
        )
        for token in forbidden:
            self.assertNotIn(token, self.script)

    def test_plan_records_reviewed_inspection_receipt(self) -> None:
        self.assertIn(
            "abf7f135257a5b842188ea8ffae6cc9e2be28b0a0e60bbcba06d46c83bef0141",
            self.plan,
        )
        self.assertIn("18 manifest entries", self.plan)
        self.assertIn("digest mismatches: zero", self.plan)
        self.assertIn("qualifies_standard_guard_semantics: false", self.plan)

    def test_wave_3_remains_unstarted(self) -> None:
        self.assertIn("Wave 3 and all later waves remain unstarted.", self.plan)
        self.assertIn("Wave 3 remains unstarted.", self.script)

    def test_cross_platform_sha256_support(self) -> None:
        self.assertIn("sha256sum", self.script)
        self.assertIn("shasum -a 256", self.script)


if __name__ == "__main__":
    unittest.main()
