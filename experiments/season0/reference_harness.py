#!/usr/bin/env python3
"""外部依存なしのSeason 0契約検証ハーネス。

本番Resolverではない。人工fixtureを使い、文書化したDatabase隔離、非破壊結合、
Evidence鮮度、Last Order、存在論scopeの規則を実行して検査する。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ContractError(ValueError):
    """Query FAMがSeason 0草案契約に違反した場合のエラー。"""


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _index(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items}


def _freshness_changes(
    previous: list[dict[str, Any]], current: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    previous_by_source = _index(previous, "source_key")
    changes: list[dict[str, Any]] = []
    for observation in current:
        old = previous_by_source.get(observation["source_key"])
        if old is None:
            continue
        changed_fields = [
            field
            for field in ("schema_fingerprint", "result_hash", "row_count", "source_cursor")
            if old.get(field) != observation.get(field)
        ]
        if changed_fields:
            changes.append(
                {
                    "source_key": observation["source_key"],
                    "freshness_status": "stale",
                    "changed_fields": changed_fields,
                    "dependent_branches": observation.get("dependent_branches", []),
                    "previous_observation_ref": old["observation_id"],
                    "current_observation_ref": observation["observation_id"],
                }
            )
    return changes


def _validate_time_point(time_point: dict[str, Any]) -> None:
    status = time_point["timezone_status"]
    normalized = time_point.get("normalized_value")
    zone_id = time_point.get("zone_id")
    utc_offset = time_point.get("utc_offset")
    if status == "unknown":
        if normalized is not None or zone_id is not None or utc_offset is not None:
            raise ContractError("timezone不明値へ正規化時刻・zone・offsetを補えません")
        return
    if normalized is None:
        raise ContractError("timezone既知の時刻にはnormalized_valueが必要です")
    parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ContractError("normalized_valueにはUTC offsetが必要です")
    parsed_offset = parsed.strftime("%z")
    parsed_offset = parsed_offset[:3] + ":" + parsed_offset[3:]
    if utc_offset != parsed_offset:
        raise ContractError("normalized_valueとutc_offsetが一致しません")
    if zone_id:
        try:
            zone = ZoneInfo(zone_id)
        except ZoneInfoNotFoundError as error:
            raise ContractError(f"未登録のIANA timezoneです: {zone_id}") from error
        if parsed.astimezone(zone).utcoffset() != parsed.utcoffset():
            raise ContractError("normalized_valueとIANA timezoneのoffsetが一致しません")


def build_temporal_envelope(
    temporal_source: dict[str, Any],
    audit_events: list[dict[str, Any]],
    clock_profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    """IBDメタ時計と上位時系列を混ぜずに返却する。"""

    source_copy = copy.deepcopy(temporal_source)
    events_copy = copy.deepcopy(audit_events)
    profiles_copy = copy.deepcopy(clock_profiles)
    source_hash_before = canonical_hash(temporal_source)
    profile_by_ref = {profile["profile_id"]: profile for profile in profiles_copy}
    if len(profile_by_ref) != len(profiles_copy):
        raise ContractError("clock profile IDは一意でなければなりません")

    for event in events_copy:
        if event.get("timeline_kind") != "ibd_meta":
            raise ContractError("IBD監査eventにはtimeline_kind: ibd_metaが必要です")
        if not event.get("operation") or not event.get("target_ref"):
            raise ContractError("IBD監査eventにはoperationとtarget_refが必要です")
        _validate_time_point(event["occurred_at"])
        clock_state = event["occurred_at"].get("clock_state")
        if clock_state is None:
            raise ContractError("IBD監査eventにはclock_stateが必要です")
        calibrated = event["occurred_at"].get("calibrated")
        evidence_status = event["occurred_at"].get("calibration_evidence_status")
        if calibrated is None or evidence_status is None:
            raise ContractError("IBD監査eventには時計校正flagと証跡状態が必要です")
        if calibrated:
            if evidence_status != "verified":
                raise ContractError("校正済み時計にはverified校正証跡が必要です")
            if not event["occurred_at"].get("calibration_authority_ref"):
                raise ContractError("校正済み時計にはcalibration authorityが必要です")
        if not calibrated:
            if not event.get("boot_id") or event.get("monotonic_ns") is None:
                raise ContractError("未校正時計eventにはboot_idとmonotonic_nsが必要です")
        profile_ref = event.get("clock_profile_ref")
        if profile_ref not in profile_by_ref:
            raise ContractError("IBD監査eventには登録済みclock profileが必要です")
        if profile_by_ref[profile_ref]["runtime_ref"] != event["runtime_ref"]:
            raise ContractError("clock profileと監査eventのruntimeが一致しません")

    for entry in source_copy["upstream_timeline"]:
        if entry.get("timeline_kind") != "upstream_domain":
            raise ContractError("上位時系列にはtimeline_kind: upstream_domainが必要です")
        time_value = entry["time"]
        if "coordinate_system" in time_value:
            if (
                time_value.get("real_time_mapping_status") == "not_mapped"
                and time_value.get("mapping_fam_ref") is not None
            ):
                raise ContractError("未対応の論理時間へMapping FAMを設定できません")
        else:
            _validate_time_point(time_value)

    return {
        "record_ref": source_copy["record_ref"],
        "upstream_domain": source_copy["upstream_timeline"],
        "ibd_meta": events_copy,
        "clock_profiles": profiles_copy,
        "clock_metadata_decision_owner": "upper_system_query_q",
        "source_payload_hash_before": source_hash_before,
        "source_payload_hash_after": canonical_hash(temporal_source),
    }


def resolve(
    query: dict[str, Any],
    registries: list[dict[str, Any]],
    databases: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    previous_observations: list[dict[str, Any]],
    current_observations: list[dict[str, Any]],
    last_orders: list[dict[str, Any]],
    ontology_assertions: list[dict[str, Any]],
    temporal_source: dict[str, Any] | None = None,
    audit_events: list[dict[str, Any]] | None = None,
    clock_profiles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """source fixtureを変更せず、人工Query FAMを解決する。"""

    source_hash = canonical_hash(
        {
            "registries": registries,
            "databases": databases,
            "clusters": clusters,
            "previous_observations": previous_observations,
            "current_observations": current_observations,
            "last_orders": last_orders,
            "ontology_assertions": ontology_assertions,
        }
    )
    query_copy = copy.deepcopy(query)
    q = query_copy["Q"]
    registry_ids = {item["registry_id"] for item in registries}
    database_ids = {item["database_id"] for item in databases}

    missing_registries = sorted(set(q["registry_refs"]) - registry_ids)
    if missing_registries:
        raise ContractError(f"未登録のRegistry参照です: {missing_registries}")

    scopes = list(q["database_scopes"])
    missing_databases = sorted(set(scopes) - database_ids)
    if missing_databases:
        raise ContractError(f"未登録のDatabase scopeです: {missing_databases}")

    composition = q.get("composition", {"enabled": False})
    if composition.get("enabled") and len(scopes) > 1:
        if composition.get("mode") != "non_destructive":
            raise ContractError("Database横断結合はnon_destructiveでなければなりません")
        if not composition.get("mapping_fam_refs"):
            raise ContractError("Database横断結合にはMapping FAMが必要です")
        if composition.get("write_back") is not False:
            raise ContractError("Season 0結合はsource Databaseへ書き戻せません")

    selected_clusters = sorted(
        (copy.deepcopy(item) for item in clusters if item["database_ref"] in scopes),
        key=lambda item: (-item["vector_score"], item["cluster_id"]),
    )
    freshness = _freshness_changes(previous_observations, current_observations)
    selected_branch_ids = {item["branch_id"] for item in selected_clusters}
    relevant_freshness = [
        item
        for item in freshness
        if selected_branch_ids.intersection(item["dependent_branches"])
    ]
    relevant_last_orders = [
        copy.deepcopy(item) for item in last_orders if item["database_ref"] in scopes
    ]

    ontology_scope_pairs = {
        (item.get("world_ref"), item.get("fact_scope"))
        for item in q.get("ontology_scopes", [])
    }
    selected_assertions = []
    if ontology_scope_pairs:
        for assertion in ontology_assertions:
            fact_scope = assertion["fact_scope"]
            pair = (fact_scope.get("world_ref"), fact_scope["scope_kind"])
            if assertion["registry_ref"] in q["registry_refs"] and pair in ontology_scope_pairs:
                selected_assertions.append(copy.deepcopy(assertion))

    result = {
        "schema_version": "ibd.reference-harness-result/0.1.0-draft",
        "query_ref": query_copy["query_fam_id"],
        "selected_database_scopes": scopes,
        "source_clusters": [
            {
                "cluster_ref": item["cluster_id"],
                "database_ref": item["database_ref"],
                "branch_ref": item["branch_id"],
                "content_hash": item["content_hash"],
                "vector_score": item["vector_score"],
            }
            for item in selected_clusters
        ],
        "mapping_fam_refs": composition.get("mapping_fam_refs", []),
        "source_mutation": False,
        "freshness_changes": relevant_freshness,
        "last_orders": relevant_last_orders,
        "ontology_assertions": selected_assertions,
        "temporal_result": (
            build_temporal_envelope(temporal_source, audit_events, clock_profiles)
            if temporal_source is not None
            and audit_events is not None
            and clock_profiles is not None
            else None
        ),
        "provenance": {
            "resolver": "season0-reference-harness",
            "source_fixture_hash_before": source_hash,
            "source_fixture_hash_after": canonical_hash(
                {
                    "registries": registries,
                    "databases": databases,
                    "clusters": clusters,
                    "previous_observations": previous_observations,
                    "current_observations": current_observations,
                    "last_orders": last_orders,
                    "ontology_assertions": ontology_assertions,
                }
            ),
        },
    }
    return result


def run_fixture(fixture_dir: Path, query_path: Path) -> dict[str, Any]:
    return resolve(
        query=load_json(query_path),
        registries=load_json(fixture_dir / "registries.json"),
        databases=load_json(fixture_dir / "databases.json"),
        clusters=load_json(fixture_dir / "clusters.json"),
        previous_observations=load_json(fixture_dir / "observations-previous.json"),
        current_observations=load_json(fixture_dir / "observations-current.json"),
        last_orders=load_json(fixture_dir / "last-orders.json"),
        ontology_assertions=load_json(fixture_dir / "ontology-assertions.json"),
        temporal_source=load_json(fixture_dir / "temporal-source.json"),
        audit_events=load_json(fixture_dir / "audit-events.json"),
        clock_profiles=load_json(fixture_dir / "clock-profiles.json"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        add_help=False,
        usage="%(prog)s [-h] [--fixture-dir DIR] [--query FILE]",
    )
    parser._optionals.title = "オプション"
    parser.add_argument("-h", "--help", action="help", help="このヘルプを表示して終了")
    default_dir = Path(__file__).resolve().parent / "fixtures"
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=default_dir,
        metavar="DIR",
        help="人工fixtureの配置ディレクトリ",
    )
    parser.add_argument(
        "--query",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "examples"
        / "season-0"
        / "query-fam.json",
        metavar="FILE",
        help="検証するQuery FAMのJSONファイル",
    )
    args = parser.parse_args()
    result = run_fixture(args.fixture_dir, args.query)
    summary = {
        "query_ref": result["query_ref"],
        "selected_database_scopes": result["selected_database_scopes"],
        "source_cluster_count": len(result["source_clusters"]),
        "stale_source_count": len(result["freshness_changes"]),
        "last_order_count": len(result["last_orders"]),
        "ontology_assertion_count": len(result["ontology_assertions"]),
        "upstream_time_count": len(result["temporal_result"]["upstream_domain"]),
        "ibd_meta_event_count": len(result["temporal_result"]["ibd_meta"]),
        "clock_profile_count": len(result["temporal_result"]["clock_profiles"]),
        "uninitialized_clock_event_count": sum(
            1
            for event in result["temporal_result"]["ibd_meta"]
            if event["occurred_at"].get("clock_state") == "uninitialized"
        ),
        "uncalibrated_clock_event_count": sum(
            1
            for event in result["temporal_result"]["ibd_meta"]
            if event["occurred_at"].get("calibrated") is False
        ),
        "source_mutation": result["source_mutation"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
