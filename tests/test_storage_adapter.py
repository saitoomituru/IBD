import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "season0" / "storage_adapter.py"
SPEC = importlib.util.spec_from_file_location("season0_storage_adapter", MODULE_PATH)
STORAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STORAGE
SPEC.loader.exec_module(STORAGE)


def _document(fam_ref, revision_ref, fold_refs=None):
    return {
        "fam_ref": fam_ref,
        "revision_ref": revision_ref,
        "l_topology": {"parent": None, "children": [], "siblings": [], "prev": None, "next": None},
        "fold_refs": fold_refs or [],
        "q_refs": {"registry_refs": [], "fact_scope": "test"},
        "provenance": {"source": "test-fixture"},
    }


class FamDocumentStoreTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_put_get_has_list_revisions(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))
        store.put(_document("fam:sample3-1", "rev-2"))

        self.assertTrue(store.has("fam:sample3-1", "rev-1"))
        self.assertFalse(store.has("fam:sample3-1", "rev-3"))
        self.assertEqual(store.list_revisions("fam:sample3-1"), ["rev-1", "rev-2"])
        self.assertEqual(store.get("fam:sample3-1", "rev-1")["fam_ref"], "fam:sample3-1")
        self.assertIsNone(store.get("fam:sample3-1", "rev-3"))

    def test_resolve_pinned_default_not_latest(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))
        store.put(_document("fam:sample3-1", "rev-2"))

        pinned = store.resolve("fam:sample3-1", {"mode": "pinned", "revision_ref": "rev-1"})
        self.assertEqual(pinned["status"], "resolved")
        self.assertEqual(pinned["revision_ref"], "rev-1")

        latest = store.resolve("fam:sample3-1", {"mode": "latest"})
        self.assertEqual(latest["revision_ref"], "rev-2")

    def test_resolve_unknown_revision_returns_last_order(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))

        result = store.resolve("fam:sample3-1", {"mode": "pinned", "revision_ref": "rev-999"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["last_order"]["schema_version"], "ibd.last-order/0.1.0-draft")
        self.assertEqual(result["last_order"]["reason"]["code"], "REVISION-NOT-FOUND")

    def test_resolve_unknown_fam_ref_returns_last_order(self):
        store = STORAGE.FamDocumentStore(self.root)
        result = store.resolve("fam:does-not-exist", {"mode": "latest"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["last_order"]["reason"]["code"], "FAM-REF-NOT-FOUND")

    def test_resolve_requires_explicit_mode(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))
        with self.assertRaises(STORAGE.ContractError):
            store.resolve("fam:sample3-1", {})

    def test_axis_separation_rejects_ml_keys_in_l_topology(self):
        store = STORAGE.FamDocumentStore(self.root)
        document = _document("fam:sample3-1", "rev-1")
        document["l_topology"]["before"] = "fam:leaked"
        with self.assertRaises(STORAGE.ContractError):
            store.put(document)

    def test_axis_separation_rejects_l_keys_in_ml_route(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))
        with self.assertRaises(STORAGE.ContractError):
            store.append_ml_trace(
                "fam:sample3-1",
                "run-1",
                "rev-1",
                [{"before": "開発部", "after": "製造", "next": "leaked"}],
            )

    def test_ml_trace_does_not_overwrite_l_topology(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:sample3-1", "rev-1"))
        store.append_ml_trace(
            "fam:sample3-1",
            "run-1",
            "rev-1",
            [{"before": "製造", "after": "法務部"}, {"before": "法務部", "after": "QA"}],
        )
        store.append_ml_trace(
            "fam:sample3-1",
            "run-2",
            "rev-1",
            [{"before": "製造", "after": "QA"}],
        )

        document = store.get("fam:sample3-1", "rev-1")
        self.assertEqual(document["l_topology"], _document("fam:sample3-1", "rev-1")["l_topology"])

        run1_trace = store.get_ml_trace("fam:sample3-1", run_ref="run-1")
        self.assertEqual(len(run1_trace), 1)
        self.assertEqual(run1_trace[0]["route"][0]["before"], "製造")

        all_trace = store.get_ml_trace("fam:sample3-1")
        self.assertEqual(len(all_trace), 2)

    def test_module_graph_cross_fam_no_inline_expansion(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(
            _document(
                "fam:sample3-1",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:sample3-2", "revision_policy": {"mode": "latest"}}],
            )
        )
        store.put(_document("fam:sample3-2", "rev-1"))

        graph = store.resolve_module_graph("fam:sample3-1", "rev-1")
        self.assertEqual(graph["inline_expansion"], False)
        self.assertEqual({node["fam_ref"] for node in graph["nodes"]}, {"fam:sample3-1", "fam:sample3-2"})
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual(graph["cycle_refs"], [])

    def test_module_graph_cycle_does_not_infinite_expand(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(
            _document(
                "fam:a",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:b", "revision_policy": {"mode": "latest"}}],
            )
        )
        store.put(
            _document(
                "fam:b",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}}],
            )
        )

        graph = store.resolve_module_graph("fam:a", "rev-1")
        self.assertEqual(graph["inline_expansion"], False)
        self.assertTrue(len(graph["cycle_refs"]) >= 1)
        fam_refs_in_nodes = [node["fam_ref"] for node in graph["nodes"]]
        self.assertEqual(fam_refs_in_nodes.count("fam:a"), 1)
        self.assertEqual(fam_refs_in_nodes.count("fam:b"), 1)

    def test_shared_child_referenced_from_multiple_parents(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:child", "rev-1"))
        store.put(
            _document(
                "fam:parent-1",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:child", "revision_policy": {"mode": "pinned", "revision_ref": "rev-1"}}],
            )
        )
        store.put(
            _document(
                "fam:parent-2",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:child", "revision_policy": {"mode": "pinned", "revision_ref": "rev-1"}}],
            )
        )

        graph_1 = store.resolve_module_graph("fam:parent-1", "rev-1")
        graph_2 = store.resolve_module_graph("fam:parent-2", "rev-1")
        child_1 = next(node for node in graph_1["nodes"] if node["fam_ref"] == "fam:child")
        child_2 = next(node for node in graph_2["nodes"] if node["fam_ref"] == "fam:child")
        self.assertEqual(child_1, child_2)

    def test_rehydrate_after_restart(self):
        store_a = STORAGE.FamDocumentStore(self.root)
        store_a.put(_document("fam:sample3-1", "rev-1"))
        store_a.append_ml_trace(
            "fam:sample3-1", "run-1", "rev-1", [{"before": "製造", "after": "QA"}]
        )

        store_b = STORAGE.FamDocumentStore(self.root)
        self.assertTrue(store_b.has("fam:sample3-1", "rev-1"))
        self.assertEqual(store_b.list_revisions("fam:sample3-1"), ["rev-1"])
        self.assertEqual(len(store_b.get_ml_trace("fam:sample3-1")), 1)
        resolved = store_b.resolve("fam:sample3-1", {"mode": "pinned", "revision_ref": "rev-1"})
        self.assertEqual(resolved["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
