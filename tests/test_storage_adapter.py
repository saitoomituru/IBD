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
        self.assertEqual(graph["resolution_mode"], "deterministic")
        self.assertIsNone(graph["bottom_ref"])

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
        # 循環参照はvisited setで決定論的に停止するため、cycle_refsで
        # 明示記録されてもresolution_modeはdeterministicのままである
        # (「鳥卵パラドクス問題」のうち非終端を防ぐ経路と、パフォーマンス
        # 上限を防ぐbounded-most-likely経路は別物)
        self.assertEqual(graph["resolution_mode"], "deterministic")
        self.assertIsNone(graph["bottom_ref"])

    def test_module_graph_max_nodes_truncates_with_bounded_most_likely_and_bottom_ref(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put(
            _document(
                "fam:chain-1",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:chain-2", "revision_policy": {"mode": "latest"}}],
            )
        )
        store.put(
            _document(
                "fam:chain-2",
                "rev-1",
                fold_refs=[{"fam_ref": "fam:chain-3", "revision_policy": {"mode": "latest"}}],
            )
        )
        store.put(_document("fam:chain-3", "rev-1"))

        graph = store.resolve_module_graph(
            "fam:chain-1", "rev-1", max_nodes=1, cycle_limit_oae_ref="oae://test/cycle-limit-approval"
        )
        self.assertEqual(graph["resolution_mode"], "bounded-most-likely")
        # 「決定論的に解決できなかった」を偽らず返す: 到達可能な全nodeを
        # silent successへ丸めず、打ち切り位置をbottom_refへ必ず付帯する
        self.assertIsNotNone(graph["bottom_ref"])
        self.assertEqual(graph["bottom_ref"]["fam_ref"], "fam:chain-2")
        self.assertEqual(graph["bottom_ref"]["reason"], "max-nodes-reached")
        self.assertEqual(graph["cycle_limit_oae_ref"], "oae://test/cycle-limit-approval")
        self.assertEqual(len(graph["nodes"]), 1)

    def test_module_graph_without_max_nodes_never_sets_cycle_limit_oae_ref(self):
        # cycle_limit_oae_refを渡しても、実際に打ち切りが発生しなければ
        # (bottom_refが無ければ)結果へ混入させない。承認を要求していない
        # 操作にOAE参照を紛れ込ませない。
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:solo", "rev-1"))
        graph = store.resolve_module_graph("fam:solo", "rev-1", cycle_limit_oae_ref="oae://test/unused")
        self.assertEqual(graph["resolution_mode"], "deterministic")
        self.assertIsNone(graph["cycle_limit_oae_ref"])

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

    def _evidence(self, observation_id, branches=("branch-1",), freshness="fresh"):
        return {
            "schema_version": "ibd.evidence-observation/0.1.0-draft",
            "observation_id": observation_id,
            "connector_id": "connector:test",
            "source_object": "table:test",
            "query_fingerprint": "fp:test",
            "parameter_hash": "hash:params",
            "result_hash": "hash:result",
            "observed_at": "2026-09-11T00:00:00+00:00",
            "dependent_branches": list(branches),
            "freshness_status": freshness,
        }

    def test_put_evidence_requires_required_fields(self):
        store = STORAGE.FamDocumentStore(self.root)
        incomplete = self._evidence("obs-1")
        del incomplete["result_hash"]
        with self.assertRaises(STORAGE.ContractError):
            store.put_evidence(incomplete)

    def test_put_evidence_rejects_unknown_fields(self):
        store = STORAGE.FamDocumentStore(self.root)
        observation = self._evidence("obs-1")
        observation["verifier_ref"] = "verifier:leaked"
        with self.assertRaises(STORAGE.ContractError):
            store.put_evidence(observation)

    def test_put_evidence_rejects_bad_freshness(self):
        store = STORAGE.FamDocumentStore(self.root)
        observation = self._evidence("obs-1", freshness="definitely-fresh")
        with self.assertRaises(STORAGE.ContractError):
            store.put_evidence(observation)

    def test_evidence_get_and_branch_index(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put_evidence(self._evidence("obs-1", branches=["branch-1", "branch-2"]))
        store.put_evidence(self._evidence("obs-2", branches=["branch-1"]))

        self.assertEqual(store.get_evidence("obs-1")["observation_id"], "obs-1")
        self.assertIsNone(store.get_evidence("obs-missing"))
        self.assertEqual(store.list_evidence_for_branch("branch-1"), ["obs-1", "obs-2"])
        self.assertEqual(store.list_evidence_for_branch("branch-2"), ["obs-1"])
        self.assertEqual(store.list_evidence_for_branch("branch-none"), [])

    def test_record_oae_requires_observer_ref(self):
        store = STORAGE.FamDocumentStore(self.root)
        with self.assertRaises(STORAGE.ContractError):
            store.record_oae("fam:sample3-1@rev-1", "oae:1", {"rule_ref": "rule:x"})

    def test_record_oae_is_immutable(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.record_oae("fam:sample3-1@rev-1", "oae:1", {"observer_ref": "observer:a"})
        with self.assertRaises(STORAGE.ContractError):
            store.record_oae("fam:sample3-1@rev-1", "oae:1", {"observer_ref": "observer:b"})

    def test_record_oae_preserves_conflicting_observer_verdicts(self):
        store = STORAGE.FamDocumentStore(self.root)
        subject = "fam:sample3-1@rev-1"
        store.record_oae(
            subject,
            "oae:observer-a",
            {
                "observer_ref": "observer:a",
                "rule_ref": "rule:x",
                "record_integrity": "satisfied",
                "rule_conformance": "satisfied",
                "observer_verdict": "valid",
            },
        )
        store.record_oae(
            subject,
            "oae:observer-b",
            {
                "observer_ref": "observer:b",
                "rule_ref": "rule:y",
                "record_integrity": "satisfied",
                "rule_conformance": "not-satisfied",
                "observer_verdict": "invalid",
            },
        )

        records = store.list_oae_for_subject(subject)
        self.assertEqual(len(records), 2)
        verdicts = {record["envelope"]["observer_verdict"] for record in records}
        self.assertEqual(verdicts, {"valid", "invalid"})
        self.assertEqual(store.get_oae("oae:observer-a")["envelope"]["observer_ref"], "observer:a")
        self.assertEqual(store.list_oae_for_subject("fam:unrelated@rev-1"), [])

    def test_oae_can_attach_to_evidence_subject(self):
        store = STORAGE.FamDocumentStore(self.root)
        store.put_evidence(self._evidence("obs-1"))
        store.record_oae(
            "evidence:obs-1",
            "oae:verify-1",
            {"observer_ref": "observer:verifier", "verifier_ref": "verifier:manual-review"},
        )
        records = store.list_oae_for_subject("evidence:obs-1")
        self.assertEqual(records[0]["envelope"]["verifier_ref"], "verifier:manual-review")

    def test_oae_mechanism_stores_atlantis_portal_transformer_receipt(self):
        # responsibility-boundary-2026-09.ja.md: IBDはPortalの必要性を判定しないが、
        # 「Portalが実行された」というreceiptはsource改変なしで保存・検索できる。
        # 新しいstorage primitiveは追加せず、既存のrecord_oae汎用機構で満たせることを検証する。
        store = STORAGE.FamDocumentStore(self.root)
        store.put(_document("fam:target", "rev-1"))
        subject = "fam:target@rev-1"

        store.record_oae(
            subject,
            "oae:portal-receipt-1",
            {
                "observer_ref": "observer:atlantis-orchestration",
                "portal_ref": "portal://world-a-to-world-b",
                "transformer_ref": "transformer://access-map-v3",
                "receipt_kind": "portal-transformation",
                "source_mutation": False,
            },
        )

        receipts = store.list_oae_for_subject(subject)
        self.assertEqual(len(receipts), 1)
        envelope = receipts[0]["envelope"]
        self.assertEqual(envelope["portal_ref"], "portal://world-a-to-world-b")
        self.assertEqual(envelope["source_mutation"], False)
        # sourceのl_topologyはPortal receipt記録によって変更されない
        self.assertEqual(store.get("fam:target", "rev-1")["l_topology"], _document("fam:target", "rev-1")["l_topology"])

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
