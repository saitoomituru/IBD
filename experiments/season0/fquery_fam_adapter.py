#!/usr/bin/env python3
"""FQuery canonical FAM(fam.json/0.1.0-draft、kind: "decomposition")を
IBD storage_adapter.FamDocumentStoreが要求するdocument形状へ写像する
Data Driver round-trip adapter。

FQuery #44 Roadmap Gateの`Data Driver round-trip stabilization`段の
最初のsliceである。FQuery selector/traversal文法はここで再定義せず
(responsibility-boundary-2026-09.ja.md)、FQueryの実出力形状から
IBD storageのL-axis/fold_refs/q_refsへ機械的に写像するだけである。

写像で落ちるfieldを喪失しないよう、元のFQuery FAM全体を
`source_document`として非破壊のまま保持する(lossless)。
"""

from __future__ import annotations

import copy
from typing import Any


class ContractError(ValueError):
    """FQuery FAM -> IBD storage document変換契約に違反した場合のエラー。"""


def fquery_decomposition_fam_to_storage_document(fam: dict[str, Any]) -> dict[str, Any]:
    """FQuery `kind: "decomposition"` FAMをFamDocumentStore.put()入力へ写像する。

    L-axis: output_unitsの並びをsiblings(parallel collection)として保持する。
    FQuery sample1の規約(array = sibling collection、index順からmLを生成
    しない)に合わせ、prev/nextは捏造しない。output_unitsが親から見て
    parallelなchildrenであることだけをl_topology.childrenへ表す。
    """

    if fam.get("kind") != "decomposition":
        raise ContractError(f"未対応のFAM kindです(このadapterはdecompositionのみ対応): {fam.get('kind')!r}")
    for required in ("fam_id", "revision_id", "λ"):
        if required not in fam:
            raise ContractError(f"FQuery decomposition FAMに{required}が必要です")

    lam = fam["λ"]
    output_units = lam.get("output_units")
    if not isinstance(output_units, list):
        raise ContractError("λ.output_unitsはarrayでなければなりません")

    children_refs: list[str] = []
    fold_refs: list[dict[str, Any]] = []
    seen_fold_refs: set[str] = set()
    for unit in output_units:
        if not isinstance(unit, dict):
            raise ContractError("output_unitsの各要素はobjectでなければなりません")
        unit_ref = unit.get("Q", {}).get("unit_ref") if isinstance(unit.get("Q"), dict) else None
        if isinstance(unit_ref, str) and unit_ref:
            children_refs.append(unit_ref)
        for found in _find_ref_values(unit, ("fold_ref", "fam_ref")):
            if found not in seen_fold_refs:
                seen_fold_refs.add(found)
                fold_refs.append({"fam_ref": found, "revision_policy": {"mode": "latest"}})

    root_q = fam.get("Q") if isinstance(fam.get("Q"), dict) else {}

    return {
        "fam_ref": fam["fam_id"],
        "revision_ref": fam["revision_id"],
        "l_topology": {
            "parent": None,
            "children": children_refs,
            "siblings": [],
            "prev": None,
            "next": None,
        },
        "fold_refs": fold_refs,
        "q_refs": {
            "observer_ref": root_q.get("observer_ref"),
            "registry_ref": root_q.get("registry_ref"),
            "fact_scope_ref": root_q.get("fact_scope_ref"),
        },
        "provenance": {
            "source": "fquery-canonical-fam",
            "fquery_kind": fam["kind"],
            "fquery_schema_version": fam.get("schema_version"),
            "title": fam.get("title"),
        },
        # 写像で落ちるfield(title_language、index_subjects、output_unitsの
        # 全文、λ.purpose等)を喪失しないよう元documentをlosslessに保持する。
        "source_document": copy.deepcopy(fam),
    }


def persist_fquery_nonlinear_observations(store: Any, replay_fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """FQuery `@fquery/benchmark`のNonlinearObserverOae群(fquery.nonlinear-replay/
    0.1.0-draft)を、対応するFAM subjectへIBD OAE storeとして永続化する。

    Issue #42が要求する永続化対象(observer_ref/oae_rule_ref/source revision/
    candidate FAM revision/verdict branch/receipt)をlosslessなenvelopeとして
    保存する。IBDはobserver_verdictの意味的正しさを裁定しない(record_oaeの
    既存契約どおり)。同一subjectへの複数(相反する)observationも上書きせず
    並存させる。
    """

    if replay_fixture.get("schema_version") != "fquery.nonlinear-replay/0.1.0-draft":
        raise ContractError("fquery.nonlinear-replay/0.1.0-draft以外のfixtureはこのadapterで扱いません")
    observations = replay_fixture.get("observations")
    if not isinstance(observations, list) or len(observations) < 2:
        raise ContractError("observationsは2件以上のarrayが必要です")

    recorded: list[dict[str, Any]] = []
    for observation in observations:
        if observation.get("schemaVersion") != "fquery.nonlinear-observer-oae/0.1.0-draft":
            raise ContractError(f"未対応のOAE schemaVersionです: {observation.get('schemaVersion')!r}")
        candidate_ref = observation["candidateRef"]
        candidate_revision_ref = observation["candidateRevisionRef"]
        subject_ref = f"{candidate_ref}@{candidate_revision_ref}"
        # FQuery(TypeScript)はcamelCase、IBD storage_adapter.record_oaeは
        # observer_ref(snake_case)を要求する。IBD側の必須keyを追加しつつ、
        # 元のcamelCase fieldも消さずlosslessに残す。
        envelope = {key: value for key, value in observation.items() if key != "oaeRef"}
        envelope["observer_ref"] = observation["observerRef"]
        recorded.append(store.record_oae(subject_ref, observation["oaeRef"], envelope))
    return recorded


def _find_ref_values(value: Any, keys: tuple[str, ...]) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for entry in node:
                walk(entry)
            return
        if not isinstance(node, dict):
            return
        for key in keys:
            candidate = node.get(key)
            if isinstance(candidate, str) and candidate:
                found.append(candidate)
        for nested in node.values():
            walk(nested)

    walk(value)
    return found
