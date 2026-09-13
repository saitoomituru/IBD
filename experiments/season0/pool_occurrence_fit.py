#!/usr/bin/env python3
"""FAM Ψ/∇φをPool Occurrence DriverのFIT occurrence(構造一致)向け
graph表現へ写像する最初のmodeling。

`docs/architecture/pool-occurrence-driver.ja.md` §2(FIT/MATCH/SELECT =
3つのOccurrence)が示す「FAM Ψ ↔ Graph Node、FAM ∇φ ↔ Graph Relationship
Type」を、実データ(FQuery #42 live run由来のcandidate-a/candidate-b)で
検証可能な形にする。MATCH/SELECT occurrenceはここでは扱わない
(`experiments/season0/composite_fam.py`のFIT/SELECT実装、MATCH未実装、
という既存カバレッジと同じ区分)。

対象はFQuery固有ではなく、ψ/∇φ/λ/Qという中立FAM形状を持つ任意の
decomposition FAM。FQuery出力を実際に扱う際は`fquery_fam_adapter.py`と
組み合わせて使う。

このmoduleが返すgraphは、Fold境界を越えるcross-document参照
(`storage_adapter.FamDocumentStore.resolve_module_graph`)とは別軸である。
`resolve_module_graph`は複数documentを結ぶFold-level graph、本module
`build_fit_occurrence_graph()`は一つのdocument内部のΨノード同士を結ぶ
intra-FAM graphであり、両者を混同しない。

同じ「FIT」という語を使う`composite_fam.py`の実装(`∇φ.modules`/
`assembly_graph`、複数の選択済みFAM branchを明示Mapping FAMで束ねる
assembly-level FIT)とも別の層である。composite_fam.pyのFITは
「Composite FAM合成時にどのbranchを束ねるか」、本moduleのFITは
「一つのFAM内部のΨノードが∇φで互いにどう繋がっているか」を表し、
どちらも同じPool Occurrence Driver抽象(FIT/MATCH/SELECT)の具体化
だが、扱う粒度が異なる。統合の要否は別途判断する。
"""

from __future__ import annotations

from typing import Any


class ContractError(ValueError):
    """FAM -> FIT occurrence graph変換契約に違反した場合のエラー。"""


def build_fit_occurrence_graph(fam: dict[str, Any]) -> dict[str, Any]:
    """decomposition FAMを、FIT occurrence(構造一致)のnode/edge graphへ変換する。

    - node: 各Ψ保持単位(root FAMおよび各output_unit/sub_splitter)
    - gradient_edges: `∇φ[].gradient_type`を`relationship_type`とするedge。
      `∇φ`が空のunitにはgradient edgeを生成しない(存在しない関係を捏造しない)
    - copy_edges: `Q.copy_role`(例: `translation-witness`)+
      `Q.source_node_ref`を持つunitは、gradient edgeとは別namespaceの
      copy edgeとして表現する(`fam-json-core.ja.md`の既存契約
      「翻訳写本にはcopy_roleとsource_node_refが必要」をgraph edgeへ
      写像するだけで、意味を再定義しない)
    - unclassified_node_refs: gradient_typeもcopy_roleも持たないunitは、
      決定論で閉じない関係を推測せずここへ明示保持する
      (§7.1決定論closureのリトマス試験と同型)
    """

    if fam.get("kind") != "decomposition":
        raise ContractError(f"未対応のFAM kindです(FITはdecompositionのみ対応): {fam.get('kind')!r}")
    for required in ("fam_id", "λ", "ψ"):
        if required not in fam:
            raise ContractError(f"FAMに{required}が必要です")

    root_ref = fam["fam_id"]
    output_units = fam["λ"].get("output_units")
    if not isinstance(output_units, list):
        raise ContractError("λ.output_unitsはarrayでなければなりません")

    nodes: list[dict[str, Any]] = [{"node_ref": root_ref, "psi": fam["ψ"], "node_kind": "root"}]
    gradient_edges: list[dict[str, Any]] = []
    copy_edges: list[dict[str, Any]] = []
    unclassified_node_refs: list[str] = []

    def walk(parent_ref: str, units: list[Any]) -> None:
        for index, unit in enumerate(units):
            if not isinstance(unit, dict):
                raise ContractError("output_units/sub_splittersの各要素はobjectでなければなりません")
            q = unit.get("Q") if isinstance(unit.get("Q"), dict) else {}
            unit_ref = q.get("unit_ref")
            copy_role = q.get("copy_role")
            source_node_ref = q.get("source_node_ref")

            if unit_ref:
                node_ref = unit_ref
            elif source_node_ref:
                # sub_splitterのtranslation-witness等、独自unit_refを
                # 持たないnodeはsource_node_ref由来で決定論的に合成する。
                node_ref = f"{source_node_ref}::copy::{index}"
            else:
                raise ContractError("unitにはQ.unit_refまたはQ.source_node_refのどちらかが必要です")

            nodes.append({"node_ref": node_ref, "psi": unit.get("ψ"), "node_kind": "unit"})

            gradients = unit.get("∇φ")
            if not isinstance(gradients, list):
                raise ContractError("∇φはarrayでなければなりません")

            if gradients:
                for gradient in gradients:
                    gradient_type = gradient.get("gradient_type")
                    if not gradient_type:
                        raise ContractError("∇φの各要素にgradient_typeが必要です")
                    gradient_edges.append({
                        "from_node_ref": parent_ref,
                        "to_node_ref": node_ref,
                        "relationship_type": gradient_type,
                        "source_expression": gradient.get("source_expression"),
                    })
            elif copy_role and source_node_ref:
                copy_edges.append({
                    "from_node_ref": source_node_ref,
                    "to_node_ref": node_ref,
                    "copy_role": copy_role,
                })
            else:
                unclassified_node_refs.append(node_ref)

            lam = unit.get("λ")
            sub_splitters = lam.get("sub_splitters") if isinstance(lam, dict) else None
            if isinstance(sub_splitters, list) and sub_splitters:
                walk(node_ref, sub_splitters)

    walk(root_ref, output_units)

    return {
        "occurrence": "FIT",
        "root_ref": root_ref,
        "nodes": nodes,
        "gradient_edges": gradient_edges,
        "copy_edges": copy_edges,
        "unclassified_node_refs": unclassified_node_refs,
    }
