from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from scripts.evidence_ledger import DEFAULT_POLICY, ROOT, connect, doctor, ingest, normalize, prune, search
from scripts.control_plane_io import load_json


class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "ledger.sqlite3"
        self.policy = load_json(DEFAULT_POLICY)
        self.now = datetime(2026, 7, 14, 13, 0, tzinfo=timezone.utc)
        self.fixtures = ROOT / "tests/fixtures/evidence-ledger"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_ingest_is_idempotent(self) -> None:
        first = ingest(self.database, self.fixtures, ROOT, DEFAULT_POLICY, self.now)
        second = ingest(self.database, self.fixtures, ROOT, DEFAULT_POLICY, self.now)
        self.assertEqual(first["inserted"], 2)
        self.assertEqual(second["duplicates"], 2)
        self.assertFalse(first["raw_payloads_stored"])

    def test_search(self) -> None:
        ingest(self.database, self.fixtures, ROOT, DEFAULT_POLICY, self.now)
        args = argparse.Namespace(kind="release-evidence", service=None, repository=None, state=None, query=None, limit=100)
        result = search(self.database, args)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["records"][0]["state"], "live")

    def test_forbidden_field_rejected(self) -> None:
        path = Path(self.temp.name) / "bad.json"
        path.write_text(json.dumps({"type": "incident", "token_value": "not-stored"}))
        with self.assertRaises(ValueError):
            normalize(json.loads(path.read_text()), path, Path(self.temp.name), self.policy, self.now)

    def test_raw_secret_pattern_rejected(self) -> None:
        path = Path(self.temp.name) / "bad.json"
        payload = {"type": "incident", "summary": "Bearer abcdefghijklmnopqrstuvwxyz"}
        path.write_text(json.dumps(payload))
        with self.assertRaises(ValueError):
            normalize(payload, path, Path(self.temp.name), self.policy, self.now)

    def test_prune(self) -> None:
        ingest(self.database, self.fixtures, ROOT, DEFAULT_POLICY, self.now)
        deleted = prune(self.database, datetime(2027, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(deleted, 2)

    def test_doctor(self) -> None:
        with connect(self.database):
            pass
        self.assertEqual(doctor(self.database, DEFAULT_POLICY)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
