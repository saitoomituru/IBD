import importlib.util
import json
import sys
import tempfile
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


STORAGE = _load_module("season0_storage_adapter", ROOT / "experiments" / "season0" / "storage_adapter.py")
ADAPTER = _load_module("season0_fquery_fam_adapter", ROOT / "experiments" / "season0" / "fquery_fam_adapter.py")


class FQueryFamAdapterRoundTripTest(unittest.TestCase):
    """2026-09-11、FQuery #42のlive run(commit c0d5873)で生成された実candidateを
    IBD storage_adapter.FamDocumentStoreへ実際にput/resolveし、Data Driver
    round-tripがlosslessに成立することを検証する。合成fixtureではなく、
    実際にFQuery main branchへcommit済みのFAM JSONをそのまま入力にする。
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = STORAGE.FamDocumentStore(Path(self.tempdir.name))
        with (FIXTURES / "candidate-a.claude.fam.json").open("r", encoding="utf-8") as stream:
            self.candidate_a = json.load(stream)
        with (FIXTURES / "candidate-b.gemini.fam.json").open("r", encoding="utf-8") as stream:
            self.candidate_b = json.load(stream)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_candidate_a_round_trips_losslessly_with_fold_ref_and_children(self):
        document = ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_a)
        self.store.put(document)

        resolved = self.store.resolve(self.candidate_a["fam_id"], {"mode": "pinned", "revision_ref": self.candidate_a["revision_id"]})
        self.assertEqual(resolved["status"], "resolved")
        stored = resolved["document"]

        self.assertEqual(stored["l_topology"]["children"], ["unit-1", "unit-2", "unit-3"])
        self.assertEqual(stored["l_topology"]["parent"], None)
        self.assertEqual(len(stored["fold_refs"]), 1)
        self.assertEqual(
            stored["fold_refs"][0]["fam_ref"],
            "fam://anthropic/claude-code/google-finland-investment/candidate-a/energy-agreement-fortum-loviisa",
        )
        # losslessness: 元のFQuery FAM全体がbyte-for-byteで復元できる
        self.assertEqual(stored["source_document"], self.candidate_a)

    def test_candidate_b_round_trips_with_no_fold_refs(self):
        document = ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_b)
        self.store.put(document)

        resolved = self.store.resolve(self.candidate_b["fam_id"], {"mode": "latest"})
        self.assertEqual(resolved["status"], "resolved")
        stored = resolved["document"]

        self.assertEqual(len(stored["l_topology"]["children"]), 3)
        self.assertEqual(stored["fold_refs"], [])
        self.assertEqual(stored["source_document"], self.candidate_b)

    def test_both_candidates_coexist_as_independent_fam_refs(self):
        self.store.put(ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_a))
        self.store.put(ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_b))

        self.assertTrue(self.store.has(self.candidate_a["fam_id"], self.candidate_a["revision_id"]))
        self.assertTrue(self.store.has(self.candidate_b["fam_id"], self.candidate_b["revision_id"]))
        self.assertNotEqual(self.candidate_a["fam_id"], self.candidate_b["fam_id"])

    def test_rehydrate_after_restart_preserves_fquery_round_trip(self):
        store_a = STORAGE.FamDocumentStore(Path(self.tempdir.name) / "rehydrate")
        store_a.put(ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_a))

        store_b = STORAGE.FamDocumentStore(Path(self.tempdir.name) / "rehydrate")
        resolved = store_b.resolve(self.candidate_a["fam_id"], {"mode": "pinned", "revision_ref": self.candidate_a["revision_id"]})
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(resolved["document"]["source_document"]["title"], self.candidate_a["title"])

    def test_persists_real_nonlinear_observer_oae_pair_as_non_destructive_oae_records(self):
        # experiments/season0/fixtures/fquery-live-candidates/nonlinear-observer-comparison.json は
        # FQuery main(commit c0d5873)へ実際にcommitされた2-candidate gestalt比較fixtureそのもの。
        with (FIXTURES / "nonlinear-observer-comparison.json").open("r", encoding="utf-8") as stream:
            replay_fixture = json.load(stream)

        self.store.put(ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_a))
        self.store.put(ADAPTER.fquery_decomposition_fam_to_storage_document(self.candidate_b))
        recorded = ADAPTER.persist_fquery_nonlinear_observations(self.store, replay_fixture)
        self.assertEqual(len(recorded), 2)

        subject_a = f"{self.candidate_a['fam_id']}@{self.candidate_a['revision_id']}"
        subject_b = f"{self.candidate_b['fam_id']}@{self.candidate_b['revision_id']}"
        oae_a = self.store.list_oae_for_subject(subject_a)
        oae_b = self.store.list_oae_for_subject(subject_b)
        self.assertEqual(len(oae_a), 1)
        self.assertEqual(len(oae_b), 1)
        self.assertEqual(oae_a[0]["envelope"]["observerRef"], "observer://anthropic/claude-code/current-session")
        self.assertEqual(oae_b[0]["envelope"]["observerRef"], "observer://google/gemini-3.5-flash/live-api")
        # 相反しうるverdictも上書きせず、それぞれ別subjectへ非破壊で並存する
        self.assertNotEqual(oae_a[0]["envelope"]["observerVerdict"], oae_b[0]["envelope"]["observerVerdict"])

        # 再record(同じoaeRef)は不変性違反としてContractError
        with self.assertRaises(STORAGE.ContractError):
            ADAPTER.persist_fquery_nonlinear_observations(self.store, replay_fixture)

    def test_rejects_non_decomposition_kind(self):
        with self.assertRaises(ADAPTER.ContractError):
            ADAPTER.fquery_decomposition_fam_to_storage_document({"kind": "access-map", "fam_id": "x", "revision_id": "1", "λ": {}})

    def test_rejects_missing_output_units_array(self):
        with self.assertRaises(ADAPTER.ContractError):
            ADAPTER.fquery_decomposition_fam_to_storage_document({"kind": "decomposition", "fam_id": "x", "revision_id": "1", "λ": {}})


if __name__ == "__main__":
    unittest.main()
