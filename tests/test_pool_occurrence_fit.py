import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments" / "season0" / "fixtures" / "fquery-live-candidates"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FIT = _load_module("season0_pool_occurrence_fit", ROOT / "experiments" / "season0" / "pool_occurrence_fit.py")


class PoolOccurrenceFitGraphTest(unittest.TestCase):
    """docs/architecture/pool-occurrence-driver.ja.md §2の
    「FAM Ψ ↔ Graph Node、FAM ∇φ ↔ Graph Relationship Type」を、
    実candidate(2026-09-11 Issue #42 live run由来)で検証する。
    """

    def setUp(self):
        with (FIXTURES / "candidate-a.claude.fam.json").open("r", encoding="utf-8") as stream:
            self.candidate_a = json.load(stream)
        with (FIXTURES / "candidate-b.gemini.fam.json").open("r", encoding="utf-8") as stream:
            self.candidate_b = json.load(stream)

    def test_candidate_a_has_no_sub_splitters_and_three_gradient_edges(self):
        graph = FIT.build_fit_occurrence_graph(self.candidate_a)
        self.assertEqual(graph["occurrence"], "FIT")
        self.assertEqual(graph["root_ref"], self.candidate_a["fam_id"])
        # root + unit-1/2/3
        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(
            sorted(edge["relationship_type"] for edge in graph["gradient_edges"]),
            ["data_center_expansion", "energy_agreement", "investment_commitment"],
        )
        for edge in graph["gradient_edges"]:
            self.assertEqual(edge["from_node_ref"], self.candidate_a["fam_id"])
        self.assertEqual(graph["copy_edges"], [])
        self.assertEqual(graph["unclassified_node_refs"], [])

    def test_candidate_b_translation_witness_sub_splitters_become_copy_edges_not_gradient_edges(self):
        graph = FIT.build_fit_occurrence_graph(self.candidate_b)
        # root + unit-1/2/3 + 3 translation-witness copies
        self.assertEqual(len(graph["nodes"]), 7)
        self.assertEqual(
            sorted(edge["relationship_type"] for edge in graph["gradient_edges"]),
            ["agreement_details", "infrastructure_scope", "investment_amount"],
        )
        self.assertEqual(len(graph["copy_edges"]), 3)
        for edge in graph["copy_edges"]:
            self.assertEqual(edge["copy_role"], "translation-witness")
            # copyのfrom_node_refは合成node_refではなく、元のunit_refそのもの
            self.assertIn(edge["from_node_ref"], {"unit-1", "unit-2", "unit-3"})
        self.assertEqual(graph["unclassified_node_refs"], [])

    def test_gradient_and_copy_edges_stay_in_separate_namespaces(self):
        graph = FIT.build_fit_occurrence_graph(self.candidate_b)
        gradient_targets = {edge["to_node_ref"] for edge in graph["gradient_edges"]}
        copy_targets = {edge["to_node_ref"] for edge in graph["copy_edges"]}
        self.assertEqual(gradient_targets.intersection(copy_targets), set())

    def test_rejects_non_decomposition_kind(self):
        with self.assertRaises(FIT.ContractError):
            FIT.build_fit_occurrence_graph({"kind": "access-map", "fam_id": "x", "ψ": {}, "λ": {}})

    def test_rejects_unit_without_unit_ref_or_source_node_ref(self):
        fam = {
            "kind": "decomposition",
            "fam_id": "fam:x",
            "ψ": {"source_text": "t"},
            "λ": {"output_units": [{"ψ": {}, "∇φ": [], "λ": {}, "Q": {}}]},
        }
        with self.assertRaises(FIT.ContractError):
            FIT.build_fit_occurrence_graph(fam)

    def test_rejects_gradient_without_gradient_type(self):
        fam = {
            "kind": "decomposition",
            "fam_id": "fam:x",
            "ψ": {"source_text": "t"},
            "λ": {"output_units": [{"ψ": {}, "∇φ": [{"source_expression": "x"}], "λ": {}, "Q": {"unit_ref": "u1"}}]},
        }
        with self.assertRaises(FIT.ContractError):
            FIT.build_fit_occurrence_graph(fam)


if __name__ == "__main__":
    unittest.main()
