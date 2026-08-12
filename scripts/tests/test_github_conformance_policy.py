import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import github_conformance_policy


class GitHubConformancePolicyTests(unittest.TestCase):
    def load_requirements(self):
        return github_conformance_policy.load_requirements(
            ROOT / "policy/github-conformance-requirements.json"
        )

    def projection(self):
        requirements = self.load_requirements()
        repositories = [
            {
                "repository": repository,
                "lifecycle": "active",
                "scope": "public",
                "runtime_service": False,
            }
            for repository in requirements["repositories"]
        ]
        repositories.append(
            {
                "repository": "AtlasReaper311/example",
                "lifecycle": "active",
                "scope": "public",
                "runtime_service": False,
            }
        )
        return {"repositories": repositories}

    def raw_report(self):
        return {
            "schema_version": "atlas-github-conformance-scoreboard/report/v1",
            "source_fingerprint": "sha256:" + "0" * 64,
            "summary": {
                "repositories_checked": 2,
                "checks_total": 4,
                "checks_passed": 1,
                "checks_failed": 3,
                "checks_unknown": 0,
            },
            "repositories": [
                {
                    "repository": "AtlasReaper311/atlas-dep-audit",
                    "lifecycle": "active",
                    "scope": "public",
                    "score": 0,
                    "summary": {
                        "passed": 0,
                        "failed": 2,
                        "unknown": 0,
                        "known": 2,
                        "total": 2,
                    },
                    "checks": [
                        {
                            "id": "dependabot",
                            "label": "Dependabot config",
                            "status": "failed",
                            "message": "missing",
                        },
                        {
                            "id": "release_history",
                            "label": "Release or tag exists",
                            "status": "failed",
                            "message": "missing",
                        },
                    ],
                },
                {
                    "repository": "AtlasReaper311/atlas-interface-kit",
                    "lifecycle": "active",
                    "scope": "public",
                    "score": 50,
                    "summary": {
                        "passed": 1,
                        "failed": 1,
                        "unknown": 0,
                        "known": 2,
                        "total": 2,
                    },
                    "checks": [
                        {
                            "id": "release_workflow",
                            "label": "Release workflow",
                            "status": "passed",
                            "message": "present",
                        },
                        {
                            "id": "release_history",
                            "label": "Release or tag exists",
                            "status": "failed",
                            "message": "missing",
                        },
                    ],
                },
            ],
        }

    def test_requirements_cover_supported_checks(self):
        requirements = self.load_requirements()
        self.assertEqual(
            set(github_conformance_policy.CHECK_IDS), set(requirements["defaults"])
        )

    def test_policy_preserves_raw_evidence_and_adds_outcomes(self):
        raw = self.raw_report()
        report = github_conformance_policy.apply_policy(
            raw, self.load_requirements(), self.projection()
        )
        dep_audit = report["repositories"][0]
        interface_kit = report["repositories"][1]
        self.assertEqual("failed", dep_audit["checks"][0]["status"])
        self.assertEqual("exception", dep_audit["checks"][0]["outcome"])
        self.assertEqual("not_applicable", dep_audit["checks"][1]["outcome"])
        self.assertEqual("passed", interface_kit["checks"][0]["outcome"])
        self.assertEqual("failed", interface_kit["checks"][1]["outcome"])
        self.assertEqual(50, interface_kit["policy_score"])
        self.assertEqual(1, report["summary"]["checks_exception"])
        self.assertEqual(0, report["summary"]["checks_deferred"])
        self.assertEqual(1, report["summary"]["policy_checks_failed"])

    def test_passed_evidence_satisfies_deferred_rule(self):
        raw = self.raw_report()
        raw["repositories"][1]["repository"] = "AtlasReaper311/worker-meta-kit"
        raw["repositories"][1]["checks"][1]["status"] = "failed"
        report = github_conformance_policy.apply_policy(
            raw, self.load_requirements(), self.projection()
        )
        self.assertEqual("deferred", report["repositories"][1]["checks"][1]["outcome"])
        raw["repositories"][1]["checks"][1]["status"] = "passed"
        report = github_conformance_policy.apply_policy(
            raw, self.load_requirements(), self.projection()
        )
        self.assertEqual("passed", report["repositories"][1]["checks"][1]["outcome"])

    def test_unknown_requirement_repository_is_rejected(self):
        requirements = copy.deepcopy(self.load_requirements())
        requirements["repositories"]["AtlasReaper311/not-in-projection"] = {
            "codeql": {
                "disposition": "exception",
                "reason": "test",
            }
        }
        with self.assertRaises(github_conformance_policy.PolicyError):
            github_conformance_policy.validate_requirement_repositories(
                self.projection(), requirements
            )

    def test_markdown_separates_policy_and_evidence(self):
        report = github_conformance_policy.apply_policy(
            self.raw_report(), self.load_requirements(), self.projection()
        )
        markdown = github_conformance_policy.render_markdown(report)
        self.assertIn("Policy conformance", markdown)
        self.assertIn("Raw evidence inventory", markdown)
        self.assertIn("Exceptions", markdown)
        self.assertIn("Deferred", markdown)


if __name__ == "__main__":
    unittest.main()
