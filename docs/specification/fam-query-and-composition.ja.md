# Query FAMとComposite FAM契約

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18

## 1. Query FAM

Query FAMは次を必須の意味フィールドとする。

```yaml
query_fam:
  ψ:
    situation: 現在の状況
  ∇φ:
    requested_methods: []
  λ:
    purpose: 目的・到達条件
  Q:
    registry_refs: []
    fold_refs: []
    database_scopes: []
    access_map_refs: []
    evidence_sources: []
    score_calibration_refs: []
    permissions: {}
    freshness: {}
    stop_conditions: []
```

∇φは空でもよい。その場合、IBDはψとλ、Qに適合する既知の探索技候補を返す。λは生成物の形式だけでなく、何のために探索するかを保持する。

## 2. Composite FAM

```yaml
composite_fam:
  composite_fam_id: fam:composite:uuid
  query_ref: fam:query:uuid
  ψ: {}
  ∇φ:
    modules: []
    assembly_graph: []
  λ: {}
  Q: {}
  evidence_bindings: []
  local_retrieval_runs: []
  transformation_receipts: []
  oae_refs: []
  last_orders: []
  unresolved_slots: []
  provenance: {}
```

## 3. 結合検査

最低限、次を検査する。

- source DatabaseがQに明示されている
- Registry versionとclassifier profileが取得可能
- input／output portが接続可能
- cross-database mappingが明示されている
- source／target FoldとAccess Mapが解決できる
- Transformer実行が必要な場合はtransformation receiptがある
- required Evidence、Tool、Capabilityが存在する
- permissionとstop conditionを満たす
- deprecated／incompatible moduleでない
- 過去のfailure、refutation、Last Orderが検査された
- Evidenceとembeddingの鮮度が分かる
- 異storeのraw scoreを直接sortしていない
- calibrationとfusionにprofile revisionがある

評価基準が存在しないことを、失敗や許可へ自動変換しない。上位Qの規約に従って未評価状態を保持する。

## 4. RecipeとRun Trace

```text
Recipe
= どの情報子クラスターをどの条件・順序で組み合わせるか

Run Trace
= 実際にどの枝を辿り、何を観測し、どこで停止したか
```

Recipeを実行結果で上書きしない。Run Traceから新しい探索技候補を抽出する場合も、人間または上位システムの昇格判断を必要とする。

Run TraceはIBDがどの枝を実行したかの技術証跡であり、OAEと同義ではない。観測、解釈、分類、Fold越境をOAEとして保存する場合も、`oae_refs`で接続し、ObserverとCauseをRun Traceから推定生成しない。

## 5. local retrievalとscoreの分離

異なるvector storeは、それぞれのembedding profileとmetricでlocal retrievalを行う。

```yaml
local_retrieval_run:
  storage_binding_ref: storage://graph-a
  embedding_profile_ref: embedding://model-a@7
  metric: cosine
  raw_score: 0.81
  local_rank: 3
  calibration_profile_ref: calibration://a-to-sin@2
  calibrated_sin: 0.73
  uncertainty: 0.08
```

`classifier_score`、`raw_score`、`calibrated_sin`、`fusion_rank`は同じ値ではない。calibrationなしのraw scoreをDatabase横断で直接比較しない。

## 6. 非破壊性

- Composite FAMはsource clusterを参照し、変更しない
- source Registryへ新しい分類を逆流させない
- mix結果の永続化は新しいSchema Bundleとして明示する
- derived relationにはsource、mapping、Q、versionを付ける
- キャッシュを正本にしない
