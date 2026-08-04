import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import github_conformance_stamp


class GitHubConformanceStampTests(unittest.TestCase):
    SOURCE_COMMIT = "1" * 40
    COLLECTED_AT = "2026-08-04T22:45:00Z"

    def report(self):
        return {
            "schema_version": "atlas-github-conformance-scoreboard/report/v2",
            "authority": "AtlasReaper311/atlas-infra",
            "summary": {"repositories_checked": 33},
            "repositories": [],
        }

    def test_stamp_adds_source_time_and_canonical_fingerprint(self):
        stamped = github_conformance_stamp.stamp_report(
            self.report(),
            source_commit=self.SOURCE_COMMIT,
            collected_at=self.COLLECTED_AT,
        )
        self.assertEqual(self.COLLECTED_AT, stamped["collected_at"])
        self.assertEqual(
            {
                "repository": "AtlasReaper311/atlas-infra",
                "commit": self.SOURCE_COMMIT,
            },
            stamped["source"],
        )
        self.assertEqual(
            github_conformance_stamp.canonical_fingerprint(stamped),
            stamped["fingerprint"],
        )

    def test_fingerprint_changes_when_report_content_changes(self):
        first = github_conformance_stamp.stamp_report(
            self.report(),
            source_commit=self.SOURCE_COMMIT,
            collected_at=self.COLLECTED_AT,
        )
        changed = self.report()
        changed["summary"]["repositories_checked"] = 34
        second = github_conformance_stamp.stamp_report(
            changed,
            source_commit=self.SOURCE_COMMIT,
            collected_at=self.COLLECTED_AT,
        )
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])

    def test_existing_fingerprint_is_replaced(self):
        report = self.report()
        report["fingerprint"] = "sha256:" + "0" * 64
        stamped = github_conformance_stamp.stamp_report(
            report,
            source_commit=self.SOURCE_COMMIT,
            collected_at=self.COLLECTED_AT,
        )
        self.assertNotEqual(report["fingerprint"], stamped["fingerprint"])
        self.assertEqual(
            github_conformance_stamp.canonical_fingerprint(stamped),
            stamped["fingerprint"],
        )

    def test_invalid_source_commit_is_rejected(self):
        with self.assertRaises(github_conformance_stamp.StampError):
            github_conformance_stamp.stamp_report(
                self.report(),
                source_commit="main",
                collected_at=self.COLLECTED_AT,
            )

    def test_non_utc_timestamp_is_rejected(self):
        with self.assertRaises(github_conformance_stamp.StampError):
            github_conformance_stamp.stamp_report(
                self.report(),
                source_commit=self.SOURCE_COMMIT,
                collected_at="2026-08-04T23:45:00+01:00",
            )

    def test_stamp_files_updates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_path = root / "scoreboard.json"
            markdown_path = root / "scoreboard.md"
            json_path.write_text(json.dumps(self.report()), encoding="utf-8")
            markdown_path.write_text(
                "# Atlas Systems GitHub conformance scoreboard\n\n"
                "## Policy conformance\n",
                encoding="utf-8",
            )
            stamped = github_conformance_stamp.stamp_files(
                json_path,
                markdown_path,
                source_commit=self.SOURCE_COMMIT,
                collected_at=self.COLLECTED_AT,
            )
            written = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
        self.assertEqual(stamped, written)
        self.assertIn("## Evidence identity", markdown)
        self.assertIn(self.SOURCE_COMMIT, markdown)
        self.assertIn(stamped["fingerprint"], markdown)
        self.assertLess(
            markdown.index("## Evidence identity"),
            markdown.index("## Policy conformance"),
        )


if __name__ == "__main__":
    unittest.main()
