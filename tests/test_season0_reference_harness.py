import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "experiments" / "season0" / "reference_harness.py"
SPEC = importlib.util.spec_from_file_location("season0_reference_harness", HARNESS_PATH)
HARNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)


class Season0ReferenceHarnessTest(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = ROOT / "experiments" / "season0" / "fixtures"
        self.query_path = ROOT / "examples" / "season-0" / "query-fam.json"

    def load(self, name):
        with (self.fixture_dir / name).open("r", encoding="utf-8") as stream:
            return json.load(stream)

    def resolve(self, query=None):
        if query is None:
            with self.query_path.open("r", encoding="utf-8") as stream:
                query = json.load(stream)
        return HARNESS.resolve(
            query=query,
            registries=self.load("registries.json"),
            databases=self.load("databases.json"),
            clusters=self.load("clusters.json"),
            previous_observations=self.load("observations-previous.json"),
            current_observations=self.load("observations-current.json"),
            last_orders=self.load("last-orders.json"),
            ontology_assertions=self.load("ontology-assertions.json"),
        )

    def test_q_scopes_isolate_unrequested_database(self):
        result = self.resolve()
        databases = {item["database_ref"] for item in result["source_clusters"]}
        self.assertEqual(databases, {"ibd://agent", "ibd://finance"})
        self.assertNotIn("ibd://system", databases)

    def test_cross_database_mix_requires_mapping_fam(self):
        with self.query_path.open("r", encoding="utf-8") as stream:
            query = json.load(stream)
        query["Q"]["composition"]["mapping_fam_refs"] = []
        with self.assertRaises(HARNESS.ContractError):
            self.resolve(query)

    def test_composition_does_not_mutate_sources(self):
        clusters = self.load("clusters.json")
        before = HARNESS.canonical_hash(clusters)
        result = HARNESS.resolve(
            query=json.loads(self.query_path.read_text(encoding="utf-8")),
            registries=self.load("registries.json"),
            databases=self.load("databases.json"),
            clusters=clusters,
            previous_observations=self.load("observations-previous.json"),
            current_observations=self.load("observations-current.json"),
            last_orders=self.load("last-orders.json"),
            ontology_assertions=self.load("ontology-assertions.json"),
        )
        self.assertFalse(result["source_mutation"])
        self.assertEqual(before, HARNESS.canonical_hash(clusters))
        self.assertEqual(
            result["provenance"]["source_fixture_hash_before"],
            result["provenance"]["source_fixture_hash_after"],
        )

    def test_evidence_growth_marks_only_dependent_branch_stale(self):
        result = self.resolve()
        self.assertEqual(len(result["freshness_changes"]), 1)
        self.assertEqual(
            result["freshness_changes"][0]["dependent_branches"],
            ["fam:branch:quantity-audit"],
        )

    def test_last_order_is_returned_for_selected_database(self):
        result = self.resolve()
        self.assertEqual(
            [item["last_order_id"] for item in result["last_orders"]],
            ["ibd:last-order:archived-quantity"],
        )

    def test_upstream_ontology_confirmation_is_not_downgraded(self):
        query_path = ROOT / "examples" / "season-0" / "ontology-query-fam.json"
        query = json.loads(query_path.read_text(encoding="utf-8"))
        result = self.resolve(query)
        self.assertEqual(len(result["ontology_assertions"]), 1)
        assertion = result["ontology_assertions"][0]
        self.assertEqual(assertion["existence_status"], "confirmed")
        self.assertEqual(assertion["fact_scope"]["world_ref"], "world:mmo-a")
        self.assertEqual(assertion["fact_scope"]["scope_kind"], "world_internal_fact")

    def test_selfhood_entities_remain_distinct(self):
        context = self.load("selfhood-context.json")
        identifiers = {
            context["subject"]["subject_id"],
            context["actor"]["actor_id"],
            context["agent_instance"]["instance_id"],
            context["runtime"]["runtime_id"],
        }
        self.assertEqual(len(identifiers), 4)
        self.assertEqual(context, copy.deepcopy(context))


if __name__ == "__main__":
    unittest.main()
