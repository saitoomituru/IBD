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
            temporal_source=self.load("temporal-source.json"),
            audit_events=self.load("audit-events.json"),
            clock_profiles=self.load("clock-profiles.json"),
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
            temporal_source=self.load("temporal-source.json"),
            audit_events=self.load("audit-events.json"),
            clock_profiles=self.load("clock-profiles.json"),
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
        assertion = next(
            item
            for item in result["ontology_assertions"]
            if item["ontology_assertion_id"] == "ibd:ontology-assertion:mmo-god"
        )
        self.assertEqual(assertion["existence_status"], "confirmed")
        self.assertEqual(assertion["fact_scope"]["world_ref"], "world:mmo-a")
        self.assertEqual(assertion["fact_scope"]["scope_kind"], "world_internal_fact")

    def test_ontology_assertions_follow_registry_and_scope_without_fact_arbitration(self):
        query_path = ROOT / "examples" / "season-0" / "ontology-query-fam.json"
        query = json.loads(query_path.read_text(encoding="utf-8"))
        query["Q"]["registry_refs"] = [
            "mmo-a.ontology.v3",
            "strategy-wiki.ontology.v1",
            "science-a.ontology.v1",
        ]
        query["Q"]["ontology_scopes"] = [
            {"world_ref": "world:mmo-a", "fact_scope": "world_internal_fact"},
            {"world_ref": "context:strategy-wiki", "fact_scope": "published_content_fact"},
            {"world_ref": None, "fact_scope": "empirical_observation"},
        ]
        result = self.resolve(query)
        demon_lord_assertions = {
            item["registry_ref"]: item["existence_status"]
            for item in result["ontology_assertions"]
            if item["subject_ref"] == "ibd:entity:demon-lord-01"
        }
        self.assertEqual(
            demon_lord_assertions,
            {
                "mmo-a.ontology.v3": "confirmed",
                "strategy-wiki.ontology.v1": "confirmed",
                "science-a.ontology.v1": "unknown",
            },
        )

    def test_ontology_scope_match_does_not_bypass_registry_q(self):
        query_path = ROOT / "examples" / "season-0" / "ontology-query-fam.json"
        query = json.loads(query_path.read_text(encoding="utf-8"))
        query["Q"]["registry_refs"] = ["science-a.ontology.v1"]
        result = self.resolve(query)
        self.assertEqual(result["ontology_assertions"], [])

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

    def test_import_and_export_do_not_replace_upstream_dates(self):
        result = self.resolve()["temporal_result"]
        upstream = {item["role"]: item["time"] for item in result["upstream_domain"]}
        meta_events = {item["event_type"]: item for item in result["ibd_meta"]}
        self.assertEqual(
            upstream["source_created_at"]["normalized_value"],
            "2020-04-01T09:00:00+09:00",
        )
        self.assertEqual(
            upstream["source_modified_at"]["normalized_value"],
            "2021-02-03T12:30:00+09:00",
        )
        self.assertEqual(
            meta_events["imported"]["occurred_at"]["normalized_value"],
            "2026-07-18T10:30:00+09:00",
        )
        self.assertEqual(meta_events["exported"]["operation"], "export_record")

    def test_future_schedule_is_preserved_as_upstream_time(self):
        result = self.resolve()["temporal_result"]
        scheduled = next(
            item for item in result["upstream_domain"] if item["role"] == "scheduled_for"
        )
        self.assertEqual(scheduled["time"]["normalized_value"], "2027-05-01T10:00:00+09:00")
        self.assertEqual(scheduled["timeline_kind"], "upstream_domain")

    def test_game_day_is_not_converted_to_real_time(self):
        result = self.resolve()["temporal_result"]
        world_time = next(
            item for item in result["upstream_domain"] if item["role"] == "world_position"
        )
        self.assertEqual(world_time["time"]["coordinate_system"], "mmo-a.calendar.v2")
        self.assertEqual(world_time["time"]["raw_value"], "第12年403日")
        self.assertEqual(world_time["time"]["real_time_mapping_status"], "not_mapped")
        self.assertIsNone(world_time["time"]["mapping_fam_ref"])

    def test_unknown_timezone_is_not_filled_from_execution_environment(self):
        result = self.resolve()["temporal_result"]
        legacy = next(
            item for item in result["upstream_domain"] if item["role"] == "legacy_local_time"
        )
        self.assertEqual(legacy["time"]["timezone_status"], "unknown")
        self.assertIsNone(legacy["time"]["normalized_value"])
        self.assertIsNone(legacy["time"]["zone_id"])
        self.assertIsNone(legacy["time"]["utc_offset"])

    def test_meta_clock_is_namespaced_with_operation_and_target(self):
        result = self.resolve()["temporal_result"]
        self.assertEqual(result["source_payload_hash_before"], result["source_payload_hash_after"])
        for event in result["ibd_meta"]:
            self.assertEqual(event["timeline_kind"], "ibd_meta")
            self.assertTrue(event["operation"])
            self.assertTrue(event["target_ref"])

    def test_uninitialized_epoch_clock_keeps_monotonic_ordering_metadata(self):
        result = self.resolve()["temporal_result"]
        epoch_event = next(
            item for item in result["ibd_meta"] if item["event_id"] == "ibd:audit-event:boot-unsynchronized"
        )
        self.assertEqual(epoch_event["occurred_at"]["normalized_value"], "1970-01-01T00:00:00+00:00")
        self.assertEqual(epoch_event["occurred_at"]["clock_state"], "uninitialized")
        self.assertEqual(epoch_event["occurred_at"]["clock_reading_status"], "placeholder")
        self.assertFalse(epoch_event["occurred_at"]["calibrated"])
        self.assertEqual(epoch_event["boot_id"], "boot:edge-01:1")
        self.assertEqual(epoch_event["monotonic_ns"], 1824000)

    def test_clock_synchronization_is_an_append_only_anchor_event(self):
        result = self.resolve()["temporal_result"]
        event_ids = [item["event_id"] for item in result["ibd_meta"]]
        self.assertIn("ibd:audit-event:boot-unsynchronized", event_ids)
        self.assertIn("ibd:audit-event:clock-synchronized", event_ids)
        synchronized = next(
            item for item in result["ibd_meta"] if item["event_id"] == "ibd:audit-event:clock-synchronized"
        )
        self.assertEqual(synchronized["clock_authority"], "gps")
        self.assertEqual(synchronized["occurred_at"]["clock_state"], "synchronized")
        self.assertTrue(synchronized["occurred_at"]["calibrated"])
        self.assertEqual(
            synchronized["occurred_at"]["calibration_evidence_status"], "verified"
        )
        self.assertEqual(synchronized["anchor"]["uncertainty_ms"], 25)

    def test_plausible_vendor_date_is_uncalibrated_without_sync_evidence(self):
        result = self.resolve()["temporal_result"]
        vendor_event = next(
            item
            for item in result["ibd_meta"]
            if item["event_id"] == "ibd:audit-event:vendor-date-unsynchronized"
        )
        self.assertEqual(
            vendor_event["occurred_at"]["normalized_value"],
            "2024-09-01T00:00:00+00:00",
        )
        self.assertFalse(vendor_event["occurred_at"]["calibrated"])
        self.assertEqual(
            vendor_event["occurred_at"]["calibration_evidence_status"], "unavailable"
        )
        self.assertEqual(
            vendor_event["occurred_at"]["clock_initialization_basis"],
            "vendor_shipped_at",
        )
        self.assertEqual(vendor_event["occurred_at"]["clock_reading_status"], "placeholder")

    def test_clock_sources_are_preserved_for_upper_system_granularity_decision(self):
        result = self.resolve()["temporal_result"]
        edge_profile = next(
            item
            for item in result["clock_profiles"]
            if item["profile_id"] == "ibd:clock-profile:edge-01"
        )
        source_kinds = {item["source_kind"] for item in edge_profile["sources"]}
        self.assertEqual(
            source_kinds,
            {
                "ntp_server",
                "gps_receiver",
                "carrier_network_time",
                "radio_controlled_clock",
                "fm_time_signal",
                "rtc_module",
            },
        )
        ntp = next(item for item in edge_profile["sources"] if item["source_kind"] == "ntp_server")
        gps = next(item for item in edge_profile["sources"] if item["source_kind"] == "gps_receiver")
        self.assertEqual(ntp["server_name"], "ntp.internal.example")
        self.assertIsNone(ntp["last_success_at"])
        self.assertEqual(gps["last_received_at"], "2026-07-18T10:00:00+09:00")
        self.assertEqual(result["clock_metadata_decision_owner"], "upper_system_query_q")

    def test_uncalibrated_clock_does_not_change_upstream_record_truth(self):
        result = self.resolve()["temporal_result"]
        self.assertEqual(result["source_payload_hash_before"], result["source_payload_hash_after"])
        source_created = next(
            item for item in result["upstream_domain"] if item["role"] == "source_created_at"
        )
        self.assertEqual(
            source_created["time"]["normalized_value"], "2020-04-01T09:00:00+09:00"
        )


if __name__ == "__main__":
    unittest.main()
