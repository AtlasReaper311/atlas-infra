from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-1b.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-1b-plan.md"


class GithubProviderGuardWave1BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_exactly_ollama_rag_kit(self) -> None:
        self.assertIn('REPOSITORY="ollama-rag-kit"', self.script)
        self.assertNotIn('atlas-bootstrap|', self.script)
        self.assertNotIn('atlas-resource-audit|', self.script)
        self.assertIn('Wave 1B was limited to exactly one repository', self.plan)

    def test_runner_pins_current_main_and_validation_head(self) -> None:
        self.assertIn(
            'EXPECTED_MAIN_SHA="d0060829dd474d8d8a57b11694ca03411927bf9f"',
            self.script,
        )
        self.assertIn('VALIDATION_PR="16"', self.script)
        self.assertIn(
            'EXPECTED_VALIDATION_HEAD="c88e6277f1f2b9bebc8f607bbb59a7d37860e92a"',
            self.script,
        )
        self.assertIn('EXPECTED_CONTEXT="Build and smoke-check"', self.script)

    def test_inspect_is_default_and_apply_requires_wave_1b_confirmation(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn('ATLAS_PROVIDER_WRITE_CONFIRMATION:-', self.script)
        self.assertIn('APPLY GITHUB PROVIDER GUARD WAVE 1B', self.script)
        self.assertNotIn('APPLY GITHUB PROVIDER GUARD WAVE 1"', self.script)

    def test_ruleset_has_exact_controls(self) -> None:
        self.assertIn('bypass_actors: []', self.script)
        self.assertIn('required_approving_review_count: 0', self.script)
        self.assertIn('required_review_thread_resolution: false', self.script)
        self.assertIn('{type: "deletion"}', self.script)
        self.assertIn('{type: "non_fast_forward"}', self.script)
        self.assertIn('type: "pull_request"', self.script)
        self.assertIn('type: "required_status_checks"', self.script)
        self.assertIn('strict_required_status_checks_policy: false', self.script)

    def test_runner_refuses_runtime_and_provider_drift(self) -> None:
        self.assertIn('.allow_auto_merge == false', self.script)
        self.assertIn('rulesets?per_page=100', self.script)
        self.assertIn('branches/main/protection', self.script)
        self.assertIn('contents/.github/workflows/deploy.yml?ref=main', self.script)
        self.assertIn('refusing stale non-runtime assumptions', self.script)

    def test_runner_is_cross_platform_for_sha256(self) -> None:
        self.assertIn('command -v sha256sum', self.script)
        self.assertIn('command -v shasum', self.script)
        self.assertIn('shasum -a 256', self.script)
        self.assertNotIn('sort -z', self.script)

    def test_plan_preserves_closeout_and_later_wave_boundary(self) -> None:
        self.assertIn('Status: completed and evidenced.', self.plan)
        self.assertIn('Wave 2 and all later waves remain unstarted.', self.plan)
        self.assertIn('Provider apply required the exact confirmation phrase:', self.plan)
        self.assertIn('APPLY GITHUB PROVIDER GUARD WAVE 1B', self.plan)
        self.assertIn('Wave 2 did not begin implicitly from Wave 1B completion.', self.plan)
        self.assertIn('Wave 2 is a separate optional stage', self.plan)


if __name__ == "__main__":
    unittest.main()
