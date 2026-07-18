# Classification Registry、Database隔離、Routing契約

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18

## 1. Classification Registry

分類語彙、意味、境界、モデル、保存先、競合処理は上位システムが定義する。

```yaml
registry_id: atlantis.accounting.v1
supplied_by: atlantis.accounting
semantic_scope: project-accounting
version: 1
classifier_profile: embedding.fam.v1
classes:
  - class_id: finance
    description: 財務に属する探索枝
    database_ref: ibd://finance
routing_policy:
  mode: multi_label
  below_threshold: unclassified
  cross_registry_mix: explicit_only
```

IBDはclassを追加・削除・矯正しない。分類結果にはRegistry、model、version、score、根拠spanまたはevidence refを付ける。

## 2. IBD Database Manifest

```yaml
database_id: ibd://finance
schema_bundle_ref: schema://finance/v1
registry_refs:
  - atlantis.accounting.v1
isolation:
  default_cross_database_read: deny
  default_cross_database_write: deny
storage_bindings: []
```

`storage_bindings`は論理Databaseをgraph、vector、metadata、object、external evidenceへ接続する。物理製品はSeason 0のCore契約に固定しない。

## 3. 分類結果

```yaml
classification:
  registry_ref: atlantis.accounting.v1
  classifier_profile: embedding.fam.v1
  candidates:
    - class_id: finance
      score: 0.86
  selected:
    - finance
  evidence_refs: []
  decision: multi_label
```

社会的な一般性、vendor preference、分類名の宗教性・哲学性をscore補正へ使わない。補正が必要なら上位Registryが明示する。

## 4. 隔離

明示的な命令がない場合:

- 他Databaseをvector候補集合へ入れない
- 同名classを同一視しない
- cross-database edgeを自動生成しない
- source clusterを別Databaseへ複製しない

## 5. 混色

混色には次を要求する。

```yaml
composition:
  enabled: true
  source_databases:
    - ibd://world-a
    - ibd://world-b
  mapping_fam_ref: fam:mapping:a-to-b
  mode: non_destructive
  write_back: false
```

Mapping FAMなしで同名classを結合しない。結合できない場合はsourceを変更せず、未解決slotまたはLast Orderを返す。

## 6. Routingの責務

Splitterは候補分類と根拠を出す。Registryが保存先を決める。IBD adapterが決定的に書き込む。expert selection、価値判断、最終的な評価は別段に置く。
