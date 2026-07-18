# Evidence鮮度とLast Order契約

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18

## 1. 目的

過去の探索技が参照したEvidence Sourceの状態と、探索を打ち切った地点を保存し、後から再探索の必要性と再開入口を返せるようにする。

## 2. Evidence Observation

```yaml
observation_id: ibd:evidence-observation:uuid
connector_id: construction.production
source_object: quantity-records
query_fingerprint: sha256:...
parameter_hash: sha256:...
schema_fingerprint: sha256:...
result_hash: sha256:...
row_count: 18241
observed_at: 2026-07-18T00:00:00+09:00
source_cursor: cursor-or-null
source_max_updated_at: 2026-07-17T23:59:59+09:00
dependent_branches:
  - fam:branch:quantity-audit
```

秘密値、credential、取得データ本文をメタ記録へ埋め込まない。再現に必要なauthority scopeとquery template referenceを別に保持できる。

## 3. 鮮度状態

```text
fresh       観測条件とソース指紋が有効
stale       ソースが伸長・変更し、依存枝の再探索が必要
unknown     比較材料が不足
unreachable sourceへ到達できず確認不能
```

`unknown`や`unreachable`をCoreが`fresh`または`stale`へ矯正しない。上位Qが処理方針を決める。

## 4. Last Order

```yaml
last_order_id: ibd:last-order:uuid
famlog_ref: famlog:uuid
branch_ref: fam:branch:uuid
status: suspended
stopped_at: fam:node:uuid
reason:
  code: evidence_unavailable
last_completed_operation: {}
requested_next:
  operation: fetch_archived_quantity
  required_evidence: []
resume_when:
  - connector_available
source_observation_refs: []
purpose_ref: fam:lambda:uuid
issued_by: upper-system-ref
```

Last Orderは命令の正当性や価値をIBDが承認したことを意味しない。どの探索枝が、誰のQとλの下で、何を要求して止まったかを保存する。

## 5. 再探索

Evidence Sourceの変化を検出した場合:

1. 過去Observationを変更しない
2. 新しいObservationを追加する
3. result／schema／cursor差分を記録する
4. dependent branchを特定する
5. 影響を受けるRecipeを列挙する
6. 再探索候補をComposite FAMへ返す

再探索を自動実行するかは上位Qまたは実行主体が決める。

## 6. 非破壊条件

- 過去のresult hashを最新値で上書きしない
- RDBの全データ複製を必須にしない
- sourceが伸びたことと、過去の探索が誤りだったことを同一視しない
- 再探索結果で旧Run Traceを消さない
