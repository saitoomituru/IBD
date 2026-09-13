#!/usr/bin/env python3
"""FQueryプラグイン(plugins/ibd)から呼び出す最小JSON-over-stdio CLI。

stdinから1つのJSON requestを読み、FamDocumentStoreのput/resolve/OAE
put/reloadを実行し、stdoutへ1つのJSON responseを書く。本番Resolverでは
なくreference実装への最小bridgeであり、Neo4j/SQLite/PostgreSQL等の
本番backend選定(IBD #3/#4のUser Gate)を代替しない。evidence/
module-graphはまだ接続していない(put/resolve/put_oae/resolve_with_oae
のみ)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_sibling_module(name: str, filename: str):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_STORAGE = _load_sibling_module("season0_storage_adapter", "storage_adapter.py")
_ADAPTER = _load_sibling_module("season0_fquery_fam_adapter", "fquery_fam_adapter.py")


def _handle(request: dict[str, Any]) -> dict[str, Any]:
    operation = request.get("operation")
    root = request.get("root")
    if not root:
        return {"status": "error", "reason": "root-required"}
    store = _STORAGE.FamDocumentStore(root)

    if operation == "put":
        document = request.get("document")
        if document is None:
            return {"status": "error", "reason": "document-required"}
        stored = store.put(document)
        return {"status": "ok", "operation": "put", "document": stored}

    if operation == "resolve":
        fam_ref = request.get("fam_ref")
        revision_policy = request.get("revision_policy")
        if not fam_ref or not revision_policy:
            return {"status": "error", "reason": "fam_ref-and-revision_policy-required"}
        result = store.resolve(fam_ref, revision_policy)
        return {"status": "ok", "operation": "resolve", "result": result}

    if operation == "put_oae":
        subject_ref = request.get("subject_ref")
        oae_ref = request.get("oae_ref")
        envelope = request.get("envelope")
        if not subject_ref or not oae_ref or envelope is None:
            return {"status": "error", "reason": "subject_ref-and-oae_ref-and-envelope-required"}
        recorded = store.record_oae(subject_ref, oae_ref, envelope)
        return {"status": "ok", "operation": "put_oae", "record": recorded}

    if operation == "resolve_with_oae":
        fam_ref = request.get("fam_ref")
        revision_policy = request.get("revision_policy")
        if not fam_ref or not revision_policy:
            return {"status": "error", "reason": "fam_ref-and-revision_policy-required"}
        result = _ADAPTER.reload_fquery_fam_with_oae(store, fam_ref, revision_policy)
        return {"status": "ok", "operation": "resolve_with_oae", "result": result}

    return {"status": "error", "reason": f"unknown-operation:{operation}"}


def main() -> int:
    raw = sys.stdin.read()
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as error:
        print(json.dumps({"status": "error", "reason": f"invalid-json-request:{error}"}, ensure_ascii=False))
        return 1

    try:
        response = _handle(request)
    except (_STORAGE.ContractError, _ADAPTER.ContractError) as error:
        print(json.dumps({"status": "error", "reason": f"contract-error:{error}"}, ensure_ascii=False))
        return 1
    except Exception as error:  # noqa: BLE001 -- CLI境界でraw tracebackをstdout契約へ漏らさない
        print(json.dumps({"status": "error", "reason": f"unexpected-error:{type(error).__name__}:{error}"}, ensure_ascii=False))
        return 1

    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
