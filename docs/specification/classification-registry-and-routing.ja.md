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

### 1.1 RegistryとContext Register

Registryは分類の型、定規、境界、unknown、routeを定義する。Context Registerは、そのRegistryへbindされたFAM、Assertion、観測、値の管理実体である。IBDは両者を同義にしない。

既存の`Classification Registry`名称は維持する。runtimeの分類結果や情報子クラスターをRegistryと呼ばない。

### 1.2 Context Dimension RefとFold Profile

Registryはclassごとに`context_dimension_ref`を関連付けられる。複数Dimensionを一つのFoldへ束ねる場合は、上位SystemがFold Profileを明示する。

```yaml
context_fold:
  fold_ref: fold://accounting-operation/v1
  dimension_refs:
    - dimension://financial
    - dimension://tec
    - dimension://supply
  context_dimension_count: 3
```

`context_dimension_count`は軸数であり、Splitterが返したcandidate数ではない。同じ3DでもDimension IDやRegistry revisionが違えば互換としない。

### 1.3 IBD Store Manifest

```yaml
store_id: ibd-store://project-a
meta_catalog_binding_ref: catalog://project-a
default_splitter_binding_ref: splitter-binding://zrl-default@1
database_refs:
  - ibd://finance
```

IBD Storeは複数IBD Databaseの管理境界である。MariaDBをMeta Catalogの標準adapterにできるが、StoreとMariaDB serverを同義にしない。

## 2. IBD Database Manifest

```yaml
database_id: ibd://finance
schema_bundle_ref: schema://finance/v1
context_fold_profile_ref: fold://accounting-operation/v1
registry_refs:
  - atlantis.accounting.v1
splitter_binding_ref: null
isolation:
  default_cross_database_read: deny
  default_cross_database_write: deny
storage_bindings: []
```

`storage_bindings`は論理Databaseをgraph、vector、metadata、object、external evidenceへ接続する。物理製品はSeason 0のCore契約に固定しない。

`splitter_binding_ref`が未指定の場合はStoreの既定Bindingを継承する。Database overrideは一つの有効Bindingへ解決し、解決経路をreceiptへ残す。

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

### 6.1 FAM Splitter SPI

```text
split(source_fam, registry_ref, fold_ref, routing_policy_ref)
  -> candidate routes + evidence + unmapped + splitter receipt
```

ZeroRoomLab標準SplitterをIBDSDKへ同梱できるが、同じSPIを満たす第三者Splitterへ差替可能にする。SplitterはRegistry外のclassやDatabaseを生成しない。

### 6.2 Bindingの解決

```text
Database override
  -> Store default
  -> unresolved
```

一つのDatabaseで複数Splitterを実行するensembleは、単一Bindingの内部profileとして明示する。Binding候補を暗黙順序で総当たりしない。

### 6.3 failureとfallback

custom Splitterが失敗した場合は`failed`とreceiptを返す。上位Policyが明示的に許可した場合だけ別Bindingへfallbackし、最初の失敗を隠さない。

分類score、local retrieval score、SsCの校正SIN、Compositeのfusion rankは別namespaceで保持する。
