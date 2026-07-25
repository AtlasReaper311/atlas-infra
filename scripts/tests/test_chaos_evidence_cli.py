import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "policy" / "chaos-experiments.json"


class ChaosEvidenceCliTests(unittest.TestCase):
    def test_validate_command_accepts_current_policy(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "chaos_evidence.py"),
                "validate",
                "--policy",
                str(POLICY),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated chaos policy 1.1.0", result.stdout)

    def test_stamp_command_rewrites_report_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            markdown = Path(tmp) / "report.md"
            run = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "chaos_harness.py"),
                    "run",
                    "--policy",
                    str(POLICY),
                    "--mode",
                    "simulate",
                    "--experiment",
                    "specular-route-503-v1",
                    "--output",
                    str(report),
                    "--markdown",
                    str(markdown),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(0, run.returncode, run.stderr)

            stamp = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "chaos_evidence.py"),
                    "stamp",
                    "--policy",
                    str(POLICY),
                    "--report",
                    str(report),
                    "--markdown",
                    str(markdown),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(0, stamp.returncode, stamp.stderr)
            document = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("1.1.0", document["policy"]["version"])
            self.assertIn("Policy version: **1.1.0**", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
