from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-3-inspect.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-3-plan.md"


class GithubProviderGuardWave3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_exactly_five_wave_3_repositories(self) -> None:
        repositories = (
            "atlas-doc-viewer",
            "atlas-quota-watch",
            "site-pulse",
            "specular-sonify",
            "status",
        )
        for repository in repositories:
            self.assertIn(repository, self.script)
            self.assertIn(repository, self.plan)

        for forbidden in (
            "atlas-gardener` as a Wave 3 target",
            "atlas-interface-kit` as a Wave 3 target",
            "atlas-journey-watch` as a Wave 3 target",
        ):
            self.assertNotIn(forbidden, self.plan)

    def test_current_main_identities_are_pinned(self) -> None:
        for sha in (
            "2b03d5843588f0415ecc735f6b33ca7527063137",
            "97304b7df2489a881aca422e494063d62f034a55",
            "be661f348ce7bc96b98f868b9d0eb2c01fcc99af",
            "2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53",
            "4db1438b1a8859008461903105360a2f09376c02",
        ):
            self.assertIn(sha, self.script)
            self.assertIn(sha, self.plan)

    def test_native_contexts_are_pinned(self) -> None:
        for context in (
            "Static document validation",
            "validate",
            "Worker validation",
            "Worker configuration validation",
            "Status site validation",
        ):
            self.assertIn(context, self.script)
            self.assertIn(context, self.plan)
        self.assertIn('GITHUB_ACTIONS_APP_ID="15368"', self.script)

    def test_classic_protection_and_rulesets_are_read(self) -> None:
        self.assertIn("branches/main/protection", self.script)
        self.assertIn("/rulesets?includes_parents=true", self.script)
        self.assertIn("/rules/branches/main", self.script)
        self.assertIn("classic_protection", self.script)
        self.assertIn("active_rule_types", self.script)

    def test_gardener_and_dependabot_state_are_read(self) -> None:
        self.assertIn("ATLAS_GARDENER_AUTOMERGE_ENABLED", self.script)
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.script)
        self.assertIn("ATLAS_GARDENER_MODE", self.script)
        self.assertIn("ATLAS_GARDENER_WRITE_GATE", self.script)
        self.assertIn("ATLAS_GARDENER_WRITE_TARGETS_JSON", self.script)
        self.assertIn("gardener-remediation-gate.yml", self.script)
        self.assertIn("dependabot-automerge.yml", self.script)

    def test_repository_auto_merge_is_preservation_boundary(self) -> None:
        self.assertIn(".allow_auto_merge", self.script)
        self.assertIn("repository auto-merge", self.plan)
        self.assertIn("currently report repository-level auto-merge enabled", self.plan)

    def test_operator_is_read_only(self) -> None:
        forbidden = (
            "--method POST",
            "--method PUT",
            "--method PATCH",
            "--method DELETE",
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh workflow run",
            "gh pr merge",
            "gh release create",
            "enable_auto_merge",
        )
        for token in forbidden:
            self.assertNotIn(token, self.script)

        self.assertIn('"provider_writes_performed": False', self.script)
        self.assertIn('"variables_written": False', self.script)
        self.assertIn('"secrets_read": False', self.script)

    def test_inspection_fails_closed_on_source_drift(self) -> None:
        self.assertIn("main drifted", self.script)
        self.assertIn("repository auto-merge drifted", self.script)
        self.assertIn("Gardener gate no longer pins expected native context", self.script)
        self.assertIn("must stop before the first write", self.plan)

    def test_expected_target_semantics_match_atlas_guard(self) -> None:
        for value in (
            "~DEFAULT_BRANCH",
            "deletion",
            "non_fast_forward",
            "pull_request",
            "required_status_checks",
            "strict_required_status_checks_policy: false",
        ):
            self.assertIn(value, self.plan)

    def test_provider_write_requires_later_approval(self) -> None:
        self.assertIn("do not authorise provider mutation", self.plan)
        self.assertIn("No provider write should occur before that approval", self.plan)

    def test_wave_4_remains_unstarted(self) -> None:
        self.assertIn("Wave 4 and all later waves remain unstarted.", self.plan)
        self.assertIn('"wave_4_started": False', self.script)

    def test_cross_platform_sha256_support(self) -> None:
        self.assertIn("sha256sum", self.script)
        self.assertIn("shasum -a 256", self.script)


if __name__ == "__main__":
    unittest.main()
