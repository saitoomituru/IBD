#!/usr/bin/env python3
"""FQueryプラグイン(plugins/ibd)から呼び出す最小JSON-over-stdio CLI。

stdinから1つのJSON requestを読み、FamDocumentStoreのput/resolveを実行し、
stdoutへ1つのJSON responseを書く。本番Resolverではなくreference実装への
最小bridgeであり、Neo4j/SQLite/PostgreSQL等の本番backend選定
(IBD #3/#4のUser Gate)を代替しない。evidence/oae/module-graphはまだ
接続していない(put/resolveのみ)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_STORAGE_ADAPTER_PATH = Path(__file__).resolve().parent / "storage_adapter.py"
_SPEC = importlib.util.spec_from_file_location("season0_storage_adapter", _STORAGE_ADAPTER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_STORAGE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _STORAGE
_SPEC.loader.exec_module(_STORAGE)


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
    except _STORAGE.ContractError as error:
        print(json.dumps({"status": "error", "reason": f"contract-error:{error}"}, ensure_ascii=False))
        return 1
    except Exception as error:  # noqa: BLE001 -- CLI境界でraw tracebackをstdout契約へ漏らさない
        print(json.dumps({"status": "error", "reason": f"unexpected-error:{type(error).__name__}:{error}"}, ensure_ascii=False))
        return 1

    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
