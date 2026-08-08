from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-1.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-1-plan.md"


class GithubProviderGuardWave1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_exactly_two_repositories(self) -> None:
        match = re.search(r"REPOSITORIES='([^']+)'", self.script, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertEqual(
            match.group(1).splitlines(),
            [
                "atlas-bootstrap|9|build",
                "atlas-resource-audit|11|Offline resource audit",
            ],
        )

    def test_inspect_is_default_and_apply_requires_confirmation(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn(
            'ATLAS_PROVIDER_WRITE_CONFIRMATION:-',
            self.script,
        )
        self.assertIn(
            'APPLY GITHUB PROVIDER GUARD WAVE 1',
            self.script,
        )

    def test_ruleset_has_no_bypass_and_zero_approvals(self) -> None:
        self.assertIn('bypass_actors: []', self.script)
        self.assertIn('required_approving_review_count: 0', self.script)
        self.assertIn('{type: "deletion"}', self.script)
        self.assertIn('{type: "non_fast_forward"}', self.script)
        self.assertIn('type: "pull_request"', self.script)
        self.assertIn('type: "required_status_checks"', self.script)

    def test_runner_requires_auto_merge_disabled(self) -> None:
        self.assertGreaterEqual(self.script.count('.allow_auto_merge == false'), 2)

    def test_runner_is_cross_platform_for_sha256(self) -> None:
        self.assertIn('command -v sha256sum', self.script)
        self.assertIn('command -v shasum', self.script)
        self.assertIn('shasum -a 256', self.script)
        self.assertNotIn('sort -z', self.script)

    def test_plan_preserves_completed_scope_and_later_wave_boundaries(self) -> None:
        wave_1a = self.plan.split('### Wave 1A', 1)[1].split(
            '### Wave 1B',
            1,
        )[0]
        repositories = re.findall(r'`AtlasReaper311/([^`]+)`', wave_1a)
        self.assertEqual(
            repositories,
            [
                'atlas-bootstrap',
                'atlas-resource-audit',
            ],
        )
        self.assertIn('### Wave 2: specialist active non-runtime repositories', self.plan)
        self.assertIn('Every later wave must follow this sequence:', self.plan)
        self.assertIn('obtain separate provider-write approval for an exact repository list', self.plan)
        self.assertIn('repository auto-merge unchanged unless separately authorised', self.plan)


if __name__ == "__main__":
    unittest.main()
