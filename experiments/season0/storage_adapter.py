#!/usr/bin/env python3
"""外部依存なしのSeason 0 FAM Document Store参照実装。

Issue #3の低レベルstorage契約を検証するためのfile-backed reference実装である。
本番storage adapter（Neo4j/SQLite/PostgreSQL等）の正本ではない。次を分離して保存する。

- L-axis: parent/children/siblings/prev/next。canonical/structural topology
- mL-axis: before/after。run/revisionごとに変化し得るruntime semantic trace

L-axisをruntime実行順ログへ変換せず、mL-axisを静的node adjacencyへ丸めない。
revision不一致・未取得はUNKNOWN / Last Orderとして返し、推測で補完しない。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

L_AXIS_KEYS = {"parent", "children", "siblings", "prev", "next"}
ML_AXIS_KEYS = {"before", "after"}


class ContractError(ValueError):
    """FAM Document Storeが保存契約に違反した場合のエラー。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True))
        stream.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


@dataclass
class LastOrder:
    """schemas/draft/last-order.schema.jsonへ写像するUNKNOWN応答。"""

    last_order_id: str
    famlog_ref: str
    branch_ref: str
    status: str
    reason_code: str
    requested_next: dict[str, Any]
    resume_when: list[str]
    purpose_ref: str
    issued_by: str
    reason_detail: str | None = None
    stopped_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "ibd.last-order/0.1.0-draft",
            "last_order_id": self.last_order_id,
            "famlog_ref": self.famlog_ref,
            "branch_ref": self.branch_ref,
            "status": self.status,
            "stopped_at": self.stopped_at,
            "reason": {"code": self.reason_code, "detail": self.reason_detail},
            "last_completed_operation": None,
            "requested_next": self.requested_next,
            "resume_when": self.resume_when,
            "source_observation_refs": [],
            "purpose_ref": self.purpose_ref,
            "issued_by": self.issued_by,
        }


def _require_axis_separation(l_topology: dict[str, Any]) -> None:
    leaked = ML_AXIS_KEYS.intersection(l_topology)
    if leaked:
        raise ContractError(
            f"l_topologyへmL-axis key({sorted(leaked)})を混在できません。"
            "before/afterはappend_ml_traceで別途保存してください"
        )


def _require_ml_shape(route: list[dict[str, Any]]) -> None:
    for step in route:
        leaked = L_AXIS_KEYS.intersection(step)
        if leaked:
            raise ContractError(
                f"mL routeへL-axis key({sorted(leaked)})を混在できません。"
                "prev/nextはl_topologyの構造参照として別途保存してください"
            )
        if "before" not in step or "after" not in step:
            raise ContractError("mL routeの各stepはbeforeとafterを持つ必要があります")


class FamDocumentStore:
    """put/get/resolve/listRevisions/hasを提供するfile-backed FAM Document Store。

    再起動後も同じrootディレクトリへ新しいインスタンスを向ければrehydrateできる。
    プロセス内キャッシュへ依存せず、都度ディスクから読み直す。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _document_path(self, fam_ref: str, revision_ref: str) -> Path:
        return self.root / "documents" / fam_ref / f"{revision_ref}.json"

    def _revision_index_path(self, fam_ref: str) -> Path:
        return self.root / "revisions" / f"{fam_ref}.json"

    def _ml_trace_path(self, fam_ref: str) -> Path:
        return self.root / "mltrace" / f"{fam_ref}.jsonl"

    def put(self, document: dict[str, Any]) -> dict[str, Any]:
        """FAM identity/revision/provenance、Fold/fam_ref boundary、L-axisを保存する。"""

        for required in ("fam_ref", "revision_ref", "l_topology"):
            if required not in document:
                raise ContractError(f"documentに{required}が必要です")
        _require_axis_separation(document["l_topology"])

        stored = copy.deepcopy(document)
        stored.setdefault("fold_refs", [])
        stored.setdefault("q_refs", {})
        stored.setdefault("oae_refs", [])
        stored.setdefault("provenance", {})
        stored["provenance"].setdefault("stored_at", _utc_now())

        fam_ref = document["fam_ref"]
        revision_ref = document["revision_ref"]
        _write_json(self._document_path(fam_ref, revision_ref), stored)

        index_path = self._revision_index_path(fam_ref)
        index = _read_json(index_path) if index_path.exists() else {"fam_ref": fam_ref, "revisions": []}
        if revision_ref not in [entry["revision_ref"] for entry in index["revisions"]]:
            index["revisions"].append({"revision_ref": revision_ref, "stored_at": stored["provenance"]["stored_at"]})
        _write_json(index_path, index)
        return copy.deepcopy(stored)

    def has(self, fam_ref: str, revision_ref: str) -> bool:
        return self._document_path(fam_ref, revision_ref).exists()

    def list_revisions(self, fam_ref: str) -> list[str]:
        index_path = self._revision_index_path(fam_ref)
        if not index_path.exists():
            return []
        return [entry["revision_ref"] for entry in _read_json(index_path)["revisions"]]

    def get(self, fam_ref: str, revision_ref: str) -> dict[str, Any] | None:
        path = self._document_path(fam_ref, revision_ref)
        if not path.exists():
            return None
        return _read_json(path)

    def resolve(self, fam_ref: str, revision_policy: dict[str, Any]) -> dict[str, Any]:
        """revision_policyに従いdocumentを返す。未取得・不一致はLast Orderで返す。

        revision_policyは{"mode": "pinned", "revision_ref": "..."}または
        {"mode": "latest"}のいずれかを要求する。latestを既定にはしない。
        """

        mode = revision_policy.get("mode")
        if mode not in ("pinned", "latest"):
            raise ContractError("revision_policy.modeはpinnedまたはlatestが必要です")

        revisions = self.list_revisions(fam_ref)
        if not revisions:
            return {
                "status": "unknown",
                "fam_ref": fam_ref,
                "last_order": self._unknown_last_order(
                    fam_ref, reason_code="FAM-REF-NOT-FOUND"
                ).to_dict(),
            }

        if mode == "pinned":
            revision_ref = revision_policy.get("revision_ref")
            if not revision_ref:
                raise ContractError("mode=pinnedにはrevision_refが必要です")
            if revision_ref not in revisions:
                return {
                    "status": "unknown",
                    "fam_ref": fam_ref,
                    "revision_ref": revision_ref,
                    "last_order": self._unknown_last_order(
                        fam_ref, reason_code="REVISION-NOT-FOUND", revision_ref=revision_ref
                    ).to_dict(),
                }
        else:
            revision_ref = revisions[-1]

        document = self.get(fam_ref, revision_ref)
        return {"status": "resolved", "fam_ref": fam_ref, "revision_ref": revision_ref, "document": document}

    def resolve_module_graph(
        self, fam_ref: str, revision_ref: str, revision_policy_for_refs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """fam_ref経由のcross-FAM参照をinline copyせずmodule graphとして返す。

        visited (fam_ref, revision_ref)を管理し、循環参照でも無限展開しない。
        """

        revision_policy_for_refs = revision_policy_for_refs or {"mode": "latest"}
        visited: set[tuple[str, str]] = set()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        cycle_refs: list[dict[str, Any]] = []

        def walk(current_fam_ref: str, current_revision_ref: str) -> None:
            key = (current_fam_ref, current_revision_ref)
            if key in visited:
                cycle_refs.append({"fam_ref": current_fam_ref, "revision_ref": current_revision_ref})
                return
            visited.add(key)
            document = self.get(current_fam_ref, current_revision_ref)
            if document is None:
                nodes.append(
                    {
                        "fam_ref": current_fam_ref,
                        "revision_ref": current_revision_ref,
                        "status": "unknown",
                    }
                )
                return
            nodes.append(
                {
                    "fam_ref": current_fam_ref,
                    "revision_ref": current_revision_ref,
                    "status": "resolved",
                    "l_topology": document["l_topology"],
                }
            )
            for fold_ref in document.get("fold_refs", []):
                child_fam_ref = fold_ref["fam_ref"]
                child_policy = fold_ref.get("revision_policy", revision_policy_for_refs)
                resolved = self.resolve(child_fam_ref, child_policy)
                edges.append(
                    {
                        "from_fam_ref": current_fam_ref,
                        "from_revision_ref": current_revision_ref,
                        "to_fam_ref": child_fam_ref,
                        "to_status": resolved["status"],
                    }
                )
                if resolved["status"] == "resolved":
                    walk(child_fam_ref, resolved["revision_ref"])

        walk(fam_ref, revision_ref)
        return {
            "root_fam_ref": fam_ref,
            "root_revision_ref": revision_ref,
            "nodes": nodes,
            "edges": edges,
            "inline_expansion": False,
            "cycle_refs": cycle_refs,
        }

    def append_ml_trace(
        self, fam_ref: str, run_ref: str, revision_ref: str, route: list[dict[str, Any]]
    ) -> None:
        """mL-axis runtime traceをrun identity付きで追記する。L-axisは上書きしない。"""

        _require_ml_shape(route)
        _append_jsonl(
            self._ml_trace_path(fam_ref),
            {
                "run_ref": run_ref,
                "revision_ref": revision_ref,
                "recorded_at": _utc_now(),
                "route": route,
            },
        )

    def get_ml_trace(self, fam_ref: str, run_ref: str | None = None) -> list[dict[str, Any]]:
        entries = _read_jsonl(self._ml_trace_path(fam_ref))
        if run_ref is None:
            return entries
        return [entry for entry in entries if entry["run_ref"] == run_ref]

    def _unknown_last_order(
        self, fam_ref: str, reason_code: str, revision_ref: str | None = None
    ) -> LastOrder:
        detail = f"fam_ref={fam_ref}"
        if revision_ref:
            detail += f" revision_ref={revision_ref}"
        return LastOrder(
            last_order_id=f"last-order:{fam_ref}:{reason_code}",
            famlog_ref=f"famlog:{fam_ref}",
            branch_ref="main",
            status="resumable",
            reason_code=reason_code,
            reason_detail=detail,
            requested_next={"action": "put-missing-revision", "fam_ref": fam_ref, "revision_ref": revision_ref},
            resume_when=["missing-revision-stored"],
            purpose_ref="ibd.fam-document-store.resolve",
            issued_by="ibd-storage-adapter",
        )
