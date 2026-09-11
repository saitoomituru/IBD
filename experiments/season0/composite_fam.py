#!/usr/bin/env python3
"""Issue #4向けComposite FAM binder参照実装。

`docs/specification/fam-query-and-composition.ja.md`(2026-09-10、
`[2026-09-CORRECTIVE]`)の§2形状、および`schemas/draft/
composite-fam.schema.json`(0.2.0-draft、同narrativeへ統一済み)に従う。

2026-09-11 統一receipt:
  旧0.1.0-draft schema(`source_clusters`必須、DB/vector cluster検索専用)
  とnarrative §2(`∇φ.modules`形状)の不一致を、ZeroRoomLab-manifest
  `note/narrative/情報子工学マガジン_FOLD本文.md` 3.3節のFIT/MATCH/SELECT
  語彙で解釈し統一した。`∇φ.modules`/`assembly_graph`はFIT(構造一致)、
  `local_retrieval_runs`はMATCH(ベクトル近傍)、`evidence_bindings`は
  SELECT(fact pointer)に対応し、3つは互いに排他ではなく同じComposite FAM
  envelopeの中で並立する別種の探索結果として保持する。本moduleは
  FITとSELECT(+OAE)だけを実装し、MATCH(vector近傍検索)は実装しない
  ため`local_retrieval_runs`は常に空配列を返す(未実装を実装済みに
  見せない)。`reference_harness.py`の独自出力(DB/cluster/vector検索、
  `schema_version: "ibd.reference-harness-result/0.1.0-draft"`)は
  MATCH/SELECT寄りの別実装として残し、本moduleへの統合は行っていない
  (両者は同じstore抽象class契約の異なる実装候補であり、統合の要否は
  別途の判断とする)。

本binderはstorage_adapter.FamDocumentStoreの上で、Qが明示した
mappingだけを解決する。selector文字列からFold境界を暗黙生成せず
(§7)、fact/refFAMの内容をmergeしない(§8)。
"""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from typing import Any


class ContractError(ValueError):
    """Composite FAM合成契約に違反した場合のエラー。"""


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _subject_ref(fam_ref: str, revision_ref: str) -> str:
    """storage_adapter.record_oaeが使うsubject_ref規約(`<fam_ref>@<revision_ref>`)に合わせる。"""

    return f"{fam_ref}@{revision_ref}"


def compose(
    store: Any,
    query_ref: str,
    mapping: list[dict[str, Any]],
    psi: dict[str, Any] | None = None,
    lam: dict[str, Any] | None = None,
    q: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Qが明示したmappingだけをresolveし、非破壊のComposite FAMを返す。

    mapping各entryは{"fam_ref", "revision_policy", "role"}を必須とする。
    roleは"fam"または"refFAM"で呼び出し側が明示し、IBDは推論しない。
    未解決slotは黙って捨てず、unresolved_slots + last_ordersへ残す。
    """

    if not mapping:
        raise ContractError("composeには最低1件のmapping entryが必要です")

    modules: list[dict[str, Any]] = []
    unresolved_slots: list[dict[str, Any]] = []
    last_orders: list[dict[str, Any]] = []
    oae_refs: list[str] = []
    evidence_bindings: list[str] = []
    resolved_fam_refs: set[str] = set()

    for entry in mapping:
        for required in ("fam_ref", "revision_policy", "role"):
            if required not in entry:
                raise ContractError(f"mapping entryに{required}が必要です")
        if entry["role"] not in ("fam", "refFAM"):
            raise ContractError(f"roleはfamまたはrefFAMが必要です: {entry['role']}")

        fam_ref = entry["fam_ref"]
        resolution = store.resolve(fam_ref, entry["revision_policy"])
        if resolution["status"] != "resolved":
            unresolved_slots.append(
                {
                    "fam_ref": fam_ref,
                    "requested_role": entry["role"],
                    "revision_policy": entry["revision_policy"],
                    "reason": resolution["last_order"]["reason"]["code"],
                }
            )
            last_orders.append(resolution["last_order"])
            continue

        revision_ref = resolution["revision_ref"]
        resolved_fam_refs.add(fam_ref)
        modules.append(
            {
                "fam_ref": fam_ref,
                "revision_ref": revision_ref,
                "role": entry["role"],
                "l_topology": resolution["document"]["l_topology"],
                "provenance": resolution["document"].get("provenance", {}),
            }
        )

        subject = _subject_ref(fam_ref, revision_ref)
        for oae_record in store.list_oae_for_subject(subject):
            oae_refs.append(oae_record["oae_ref"])

        for evidence_ref in entry.get("evidence_refs", []):
            if store.get_evidence(evidence_ref) is not None:
                evidence_bindings.append(evidence_ref)
            else:
                unresolved_slots.append(
                    {"evidence_ref": evidence_ref, "reason": "EVIDENCE-NOT-FOUND"}
                )

    # assembly_graphはmapping内で明示的に要求されたfam_ref同士の関係だけを表す。
    # fold_refsを辿って未要求のfam_refを新規解決しない(§7: 暗黙のFold越境をしない)。
    assembly_graph: list[dict[str, Any]] = []
    for module in modules:
        document = store.get(module["fam_ref"], module["revision_ref"])
        for fold_ref in document.get("fold_refs", []):
            if fold_ref["fam_ref"] in resolved_fam_refs:
                assembly_graph.append(
                    {"from_fam_ref": module["fam_ref"], "to_fam_ref": fold_ref["fam_ref"]}
                )

    composite_fam_id = f"fam:composite:{uuid.uuid4()}"
    result = {
        "schema_version": "ibd.composite-fam/0.2.0-draft",
        "composite_fam_id": composite_fam_id,
        "query_ref": query_ref,
        "ψ": copy.deepcopy(psi) if psi is not None else {},
        "∇φ": {"modules": modules, "assembly_graph": assembly_graph},
        "λ": copy.deepcopy(lam) if lam is not None else {},
        "Q": copy.deepcopy(q) if q is not None else {},
        "evidence_bindings": evidence_bindings,
        "local_retrieval_runs": [],  # MATCH(vector近傍)は本moduleが実装しないため常に空
        "transformation_receipts": [],
        "oae_refs": oae_refs,
        "last_orders": last_orders,
        "unresolved_slots": unresolved_slots,
        "provenance": {
            "resolver": "ibd-season0-composite-fam-binder",
            "source_mutation": False,
            "mapping_hash": _canonical_hash(mapping),
        },
    }
    return result
