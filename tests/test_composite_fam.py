import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSITE_FAM_SCHEMA = json.loads((ROOT / "schemas" / "draft" / "composite-fam.schema.json").read_text(encoding="utf-8"))

STORAGE_PATH = ROOT / "experiments" / "season0" / "storage_adapter.py"
STORAGE_SPEC = importlib.util.spec_from_file_location("season0_storage_adapter", STORAGE_PATH)
STORAGE = importlib.util.module_from_spec(STORAGE_SPEC)
sys.modules[STORAGE_SPEC.name] = STORAGE
STORAGE_SPEC.loader.exec_module(STORAGE)

COMPOSITE_PATH = ROOT / "experiments" / "season0" / "composite_fam.py"
COMPOSITE_SPEC = importlib.util.spec_from_file_location("season0_composite_fam", COMPOSITE_PATH)
COMPOSITE = importlib.util.module_from_spec(COMPOSITE_SPEC)
sys.modules[COMPOSITE_SPEC.name] = COMPOSITE
COMPOSITE_SPEC.loader.exec_module(COMPOSITE)


def _document(fam_ref, revision_ref, fold_refs=None):
    return {
        "fam_ref": fam_ref,
        "revision_ref": revision_ref,
        "l_topology": {"parent": None, "children": [], "siblings": [], "prev": None, "next": None},
        "fold_refs": fold_refs or [],
        "q_refs": {},
        "provenance": {"source": "test-fixture"},
    }


class ComposeFamTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = STORAGE.FamDocumentStore(Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_compose_requires_mapping(self):
        with self.assertRaises(COMPOSITE.ContractError):
            COMPOSITE.compose(self.store, "query:1", [])

    def test_compose_requires_explicit_role(self):
        self.store.put(_document("fam:a", "rev-1"))
        with self.assertRaises(COMPOSITE.ContractError):
            COMPOSITE.compose(
                self.store,
                "query:1",
                [{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "unknown-role"}],
            )

    def test_compose_resolves_fam_and_reffam_without_merging(self):
        self.store.put(_document("fam:fact-1", "rev-1"))
        self.store.put(_document("fam:method-1", "rev-1"))

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [
                {"fam_ref": "fam:fact-1", "revision_policy": {"mode": "latest"}, "role": "fam"},
                {"fam_ref": "fam:method-1", "revision_policy": {"mode": "latest"}, "role": "refFAM"},
            ],
        )
        roles = {module["fam_ref"]: module["role"] for module in result["∇φ"]["modules"]}
        self.assertEqual(roles, {"fam:fact-1": "fam", "fam:method-1": "refFAM"})
        self.assertEqual(result["provenance"]["source_mutation"], False)
        self.assertEqual(result["unresolved_slots"], [])

    def test_compose_does_not_silently_drop_unresolved(self):
        self.store.put(_document("fam:a", "rev-1"))

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [
                {"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"},
                {"fam_ref": "fam:missing", "revision_policy": {"mode": "latest"}, "role": "fam"},
            ],
        )
        self.assertEqual(len(result["∇φ"]["modules"]), 1)
        self.assertEqual(len(result["unresolved_slots"]), 1)
        self.assertEqual(result["unresolved_slots"][0]["fam_ref"], "fam:missing")
        self.assertEqual(len(result["last_orders"]), 1)

    def test_compose_does_not_implicitly_expand_beyond_mapping(self):
        # fam:a -> fam:b(未request)。bはmappingに無いのでassembly_graphへ現れない。
        self.store.put(
            _document("fam:a", "rev-1", fold_refs=[{"fam_ref": "fam:b", "revision_policy": {"mode": "latest"}}])
        )
        self.store.put(_document("fam:b", "rev-1"))

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"}],
        )
        self.assertEqual(len(result["∇φ"]["modules"]), 1)
        self.assertEqual(result["∇φ"]["assembly_graph"], [])

    def test_compose_includes_assembly_graph_edge_when_both_sides_requested(self):
        self.store.put(
            _document("fam:a", "rev-1", fold_refs=[{"fam_ref": "fam:b", "revision_policy": {"mode": "latest"}}])
        )
        self.store.put(_document("fam:b", "rev-1"))

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [
                {"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"},
                {"fam_ref": "fam:b", "revision_policy": {"mode": "latest"}, "role": "fam"},
            ],
        )
        self.assertEqual(
            result["∇φ"]["assembly_graph"], [{"from_fam_ref": "fam:a", "to_fam_ref": "fam:b"}]
        )

    def test_compose_surfaces_conflicting_oae_verdicts_without_arbitration(self):
        self.store.put(_document("fam:a", "rev-1"))
        subject = "fam:a@rev-1"
        self.store.record_oae(subject, "oae:1", {"observer_ref": "observer:a", "observer_verdict": "valid"})
        self.store.record_oae(subject, "oae:2", {"observer_ref": "observer:b", "observer_verdict": "invalid"})

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"}],
        )
        self.assertEqual(set(result["oae_refs"]), {"oae:1", "oae:2"})

    def test_compose_binds_explicit_evidence_refs(self):
        self.store.put(_document("fam:a", "rev-1"))
        self.store.put_evidence(
            {
                "schema_version": "ibd.evidence-observation/0.1.0-draft",
                "observation_id": "obs-1",
                "connector_id": "connector:test",
                "source_object": "table:test",
                "query_fingerprint": "fp:test",
                "parameter_hash": "hash:params",
                "result_hash": "hash:result",
                "observed_at": "2026-09-11T00:00:00+00:00",
                "dependent_branches": [],
            }
        )

        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [
                {
                    "fam_ref": "fam:a",
                    "revision_policy": {"mode": "latest"},
                    "role": "fam",
                    "evidence_refs": ["obs-1", "obs-missing"],
                }
            ],
        )
        self.assertEqual(result["evidence_bindings"], ["obs-1"])
        self.assertIn({"evidence_ref": "obs-missing", "reason": "EVIDENCE-NOT-FOUND"}, result["unresolved_slots"])

    def test_compose_conforms_to_composite_fam_schema_top_level_shape(self):
        # jsonschemaライブラリへ依存せず、schemaのrequired/additionalProperties:falseを
        # 手動で再現して構造適合を検証する(他のschema draftも同じ手動検証styleに合わせる)。
        self.store.put(_document("fam:a", "rev-1"))
        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"}],
        )

        self.assertEqual(result["schema_version"], COMPOSITE_FAM_SCHEMA["properties"]["schema_version"]["const"])
        required = set(COMPOSITE_FAM_SCHEMA["required"])
        allowed = set(COMPOSITE_FAM_SCHEMA["properties"].keys())
        self.assertTrue(required.issubset(result.keys()), f"missing required keys: {required - result.keys()}")
        self.assertTrue(set(result.keys()).issubset(allowed), f"unknown keys: {set(result.keys()) - allowed}")

        nabla_phi_schema = COMPOSITE_FAM_SCHEMA["properties"]["∇φ"]
        self.assertTrue(set(nabla_phi_schema["required"]).issubset(result["∇φ"].keys()))

    def test_compose_leaves_unimplemented_match_retrieval_empty_not_fabricated(self):
        self.store.put(_document("fam:a", "rev-1"))
        result = COMPOSITE.compose(
            self.store,
            "query:1",
            [{"fam_ref": "fam:a", "revision_policy": {"mode": "latest"}, "role": "fam"}],
        )
        self.assertEqual(result["local_retrieval_runs"], [])


if __name__ == "__main__":
    unittest.main()
