from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from validate_release_evidence import validate_release_evidence


class ReleaseEvidenceValidationTests(unittest.TestCase):
    def fixture(self) -> dict:
        path = (
            ROOT
            / "contracts"
            / "v1"
            / "fixtures"
            / "valid"
            / "release-evidence.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_valid_release_evidence_passes(self) -> None:
        instance = (
            ROOT
            / "contracts"
            / "v1"
            / "fixtures"
            / "valid"
            / "release-evidence.json"
        )
        report = validate_release_evidence(ROOT, instance)
        self.assertTrue(report["valid"])
        self.assertEqual([], report["errors"])

    def test_missing_release_identity_is_rejected(self) -> None:
        release = self.fixture()
        release.pop("commit")
        with tempfile.TemporaryDirectory() as directory:
            instance = Path(directory) / "release-evidence.json"
            instance.write_text(json.dumps(release), encoding="utf-8")
            report = validate_release_evidence(ROOT, instance)
        self.assertFalse(report["valid"])
        self.assertTrue(any("commit" in error for error in report["errors"]))

    def test_cli_report_is_byte_idempotent(self) -> None:
        instance = (
            ROOT
            / "contracts"
            / "v1"
            / "fixtures"
            / "valid"
            / "release-evidence.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            command = [
                sys.executable,
                str(SCRIPTS / "validate_release_evidence.py"),
                "--instance",
                str(instance),
                "--report",
                str(report_path),
                "--quiet",
            ]
            subprocess.run(command, check=True)
            first = report_path.read_bytes()
            subprocess.run(command, check=True)
            self.assertEqual(first, report_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
