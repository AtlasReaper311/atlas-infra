from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.final_integration import DEFAULT_POLICY, ROOT, validate, validate_policy, workflow_inventory
from scripts.control_plane_io import load_json


class FinalIntegrationTests(unittest.TestCase):
    def test_policy_valid(self) -> None:
        self.assertEqual(validate_policy(load_json(DEFAULT_POLICY)), [])

    def test_deferred_cutovers_are_explicit_warnings(self) -> None:
        policy = load_json(DEFAULT_POLICY)
        ids = {item["id"] for item in policy["deferred_cutovers"]}
        self.assertIn("phase9-atlas-api-public", ids)
        self.assertIn("home-assistant-live-install", ids)
        self.assertIn("openwebui-tool-assignment", ids)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = load_json(DEFAULT_POLICY)
            policy["required_files"] = ["missing.json"]
            path = root / "policy.json"
            path.write_text(json.dumps(policy))
            result = validate(root, path)
            self.assertEqual(result["status"], "failed")

    def test_unpinned_action_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("permissions:\n  contents: read\nconcurrency: test\njobs:\n  test:\n    timeout-minutes: 5\n    steps:\n      - uses: actions/checkout@v4\n")
            _, findings = workflow_inventory(root, 90)
            self.assertTrue(any(item["id"] == "workflow-unpinned-action" for item in findings))

    def test_deterministic(self) -> None:
        self.assertEqual(validate(ROOT, DEFAULT_POLICY), validate(ROOT, DEFAULT_POLICY))


if __name__ == "__main__":
    unittest.main()
