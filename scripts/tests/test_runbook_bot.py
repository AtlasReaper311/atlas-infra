from __future__ import annotations

import json
import unittest

from scripts.runbook_bot import ROOT, match, markdown, validate_index


class RunbookBotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = json.loads((ROOT / "policy/runbook-index.json").read_text(encoding="utf-8"))
        self.routing = json.loads((ROOT / "policy/runbook-routing.json").read_text(encoding="utf-8"))

    def test_index_is_valid(self) -> None:
        self.assertEqual(validate_index(self.index, self.routing), [])

    def test_entries_use_strict_contract_shape(self) -> None:
        for entry in self.index["entries"]:
            self.assertEqual(entry["schema_version"], "atlas-control-plane/runbook-index-entry/v1")
            self.assertIn("diagnostic_commands", entry)
            self.assertNotIn("blocked_actions", entry)
            self.assertNotIn("triggers", entry)

    def test_release_mismatch_matches(self) -> None:
        event = json.loads((ROOT / "tests/fixtures/runbook-bot/release-mismatch.json").read_text())
        result = match(self.index, self.routing, event, None, 5)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["matches"][0]["runbook_id"], "release-mismatch")
        self.assertFalse(result["safety"]["commands_executed"])

    def test_unknown_event_is_no_match(self) -> None:
        event = json.loads((ROOT / "tests/fixtures/runbook-bot/unknown.json").read_text())
        result = match(self.index, self.routing, event, None, 5)
        self.assertEqual(result["status"], "no-match")
        self.assertEqual(result["matches"], [])

    def test_deterministic(self) -> None:
        event = json.loads((ROOT / "tests/fixtures/runbook-bot/release-mismatch.json").read_text())
        self.assertEqual(
            match(self.index, self.routing, event, None, 5),
            match(self.index, self.routing, event, None, 5),
        )

    def test_query_can_match(self) -> None:
        result = match(self.index, self.routing, {}, "quota projected exhaustion", 5)
        self.assertEqual(result["matches"][0]["runbook_id"], "quota-critical")

    def test_duplicate_ids_fail(self) -> None:
        broken = json.loads(json.dumps(self.index))
        broken["entries"].append(dict(broken["entries"][0]))
        self.assertTrue(any("duplicate" in error for error in validate_index(broken, self.routing)))

    def test_unknown_route_fails(self) -> None:
        broken = json.loads(json.dumps(self.routing))
        broken["routes"]["unknown-entry"] = dict(next(iter(broken["routes"].values())))
        self.assertTrue(any("unknown entry_id" in error for error in validate_index(self.index, broken)))

    def test_markdown_contains_blocked_actions(self) -> None:
        event = json.loads((ROOT / "tests/fixtures/runbook-bot/release-mismatch.json").read_text())
        rendered = markdown(match(self.index, self.routing, event, None, 5))
        self.assertIn("Blocked actions", rendered)
        self.assertIn("automatic rollback", rendered)
        self.assertIn("manual-owner-reviewed-only", rendered)


if __name__ == "__main__":
    unittest.main()
