from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import atlas_trace
import control_plane_contracts as contracts


class AtlasTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.trace_root = ROOT / "contracts" / "v1" / "atlas-trace"
        cls.schemas, cls.rules = atlas_trace.load_trace_contracts(ROOT)

    def fixture(self, relative: str) -> dict:
        return contracts.load_json(self.trace_root / "fixtures" / relative)

    def test_complete_trace_contract_set_passes(self) -> None:
        report = atlas_trace.validate_trace_repository(ROOT)
        self.assertEqual([], report["errors"])
        self.assertEqual(3, report["schemas_checked"])
        self.assertEqual(3, report["positive_fixtures"])
        self.assertEqual(3, report["negative_fixtures"])

    def test_node_identity_is_independent_of_evidence_order(self) -> None:
        node = self.fixture("valid/evidence-node.json")
        second_reference = copy.deepcopy(node["evidence"][0])
        second_reference["digest"] = "sha256:" + ("4" * 64)
        node["evidence"].append(second_reference)

        first = atlas_trace.calculate_trace_fingerprint(
            "evidence-node",
            node,
            self.rules,
        )
        node["evidence"].reverse()
        second = atlas_trace.calculate_trace_fingerprint(
            "evidence-node",
            node,
            self.rules,
        )
        self.assertEqual(first, second)

    def test_correlation_requires_explicit_correlation_basis(self) -> None:
        edge = self.fixture("valid/evidence-edge.json")
        edge["relation"] = "CORRELATED_WITH"
        edge["edge_id"] = atlas_trace.calculate_trace_fingerprint(
            "evidence-edge",
            edge,
            self.rules,
        )
        errors = atlas_trace.validate_trace_instance(
            "evidence-edge.schema.json",
            edge,
            self.schemas,
            self.rules,
        )
        self.assertTrue(any("CORRELATED_WITH requires" in item for item in errors))

    def test_dangling_edge_is_rejected(self) -> None:
        graph = self.fixture("valid/evidence-graph.json")
        graph["edges"][0]["to_node"] = "node:sha256:" + ("f" * 64)
        graph["edges"][0]["edge_id"] = atlas_trace.calculate_trace_fingerprint(
            "evidence-edge",
            graph["edges"][0],
            self.rules,
        )
        graph["fingerprint"] = atlas_trace.calculate_trace_fingerprint(
            "evidence-graph",
            graph,
            self.rules,
        )
        errors = atlas_trace.validate_trace_instance(
            "evidence-graph.schema.json",
            graph,
            self.schemas,
            self.rules,
        )
        self.assertTrue(any("referenced node is absent" in item for item in errors))

    def test_public_graph_rejects_internal_node(self) -> None:
        graph = self.fixture("valid/evidence-graph.json")
        graph["nodes"][0]["visibility"] = "internal"
        graph["nodes"][0]["evidence"][0]["visibility"] = "internal"
        graph["fingerprint"] = atlas_trace.calculate_trace_fingerprint(
            "evidence-graph",
            graph,
            self.rules,
        )
        errors = atlas_trace.validate_trace_instance(
            "evidence-graph.schema.json",
            graph,
            self.schemas,
            self.rules,
        )
        self.assertTrue(any("exceeds graph visibility" in item for item in errors))

    def test_assembly_is_byte_idempotent_and_input_order_independent(self) -> None:
        graph = self.fixture("valid/evidence-graph.json")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_a = root / "a"
            input_b = root / "b"
            for input_dir in (input_a, input_b):
                (input_dir / "nodes").mkdir(parents=True)
                (input_dir / "edges").mkdir(parents=True)

            nodes = list(graph["nodes"])
            (input_a / "nodes" / "01.json").write_text(
                json.dumps(nodes[0], indent=2),
                encoding="utf-8",
            )
            (input_a / "nodes" / "02.json").write_text(
                json.dumps(nodes[1], indent=2),
                encoding="utf-8",
            )
            (input_b / "nodes" / "01.json").write_text(
                json.dumps(nodes[1], indent=2),
                encoding="utf-8",
            )
            (input_b / "nodes" / "02.json").write_text(
                json.dumps(nodes[0], indent=2),
                encoding="utf-8",
            )
            for input_dir in (input_a, input_b):
                (input_dir / "edges" / "01.json").write_text(
                    json.dumps(graph["edges"][0], indent=2),
                    encoding="utf-8",
                )

            output_a = root / "graph-a.json"
            output_b = root / "graph-b.json"

            for input_dir, output in ((input_a, output_a), (input_b, output_b)):
                subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPTS / "atlas_trace.py"),
                        "--root",
                        str(ROOT),
                        "assemble",
                        "--input-dir",
                        str(input_dir),
                        "--output",
                        str(output),
                        "--visibility",
                        "internal",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            self.assertEqual(output_a.read_bytes(), output_b.read_bytes())
            first = output_a.read_bytes()

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "atlas_trace.py"),
                    "--root",
                    str(ROOT),
                    "assemble",
                    "--input-dir",
                    str(input_a),
                    "--output",
                    str(output_a),
                    "--visibility",
                    "internal",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first, output_a.read_bytes())

    def test_canonical_graph_checker_rejects_pretty_printed_bytes(self) -> None:
        graph = self.fixture("valid/evidence-graph.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(atlas_trace.TraceError, "not canonical"):
                atlas_trace.check_graph(ROOT, path)

    def test_offline_assembler_refuses_public_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_dir = Path(directory)
            (input_dir / "nodes").mkdir()
            (input_dir / "edges").mkdir()
            with self.assertRaisesRegex(atlas_trace.TraceError, "public graph assembly"):
                atlas_trace.assemble_graph(ROOT, input_dir, "public")


if __name__ == "__main__":
    unittest.main()
