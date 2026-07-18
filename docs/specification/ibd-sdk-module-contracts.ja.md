# IBDSDK module契約

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18  
対象: IBD library、adapter、SDK bundle、第三者plugin

## 1. 目的

IBDを一つのmonolithへ固定せず、低水準contractからprompt／low-code surfaceまで必要なmoduleだけをbundleできるようにする。

共通SDK surfaceはZeroRoomLab-manifestの[Sphere Context SDK共通契約](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/sphere-context-sdk-contract.ja.md)へ従う。IBDSDKはそのIBD実装プロファイルである。

```text
IBD Core Contracts
├─ Meta Catalog SPI
├─ Registry Provider SPI
├─ FAM Splitter SPI
├─ Graph Store SPI
├─ Vector Store SPI
├─ Evidence / RDB Connector SPI
├─ Composite Resolver
├─ SsC
└─ OAE Storage Binding
```

## 2. 共通Envelope

moduleの入出力は最低限、内容と制御メタを分ける。

```yaml
ibd_envelope:
  operation_id: ibd-op://uuid
  store_ref: ibd-store://example
  database_ref: ibd://target
  registry_refs: []
  schema_bundle_ref: schema://example/v1
  fold_ref: fold://example/v1
  query_fam_ref: fam://query
  payload_ref: fam://payload
  policy_refs: []
  provenance_refs: []
  runtime_trace_ref: trace://run
  oae_refs: []
  status: completed
  unknown: []
```

`status`候補は`completed / partial / unavailable / incompatible / unmapped / denied / failed / unknown`を分ける。`unknown`を空配列へ正規化しただけで成功にしない。

## 3. Meta Catalog SPI

```text
resolve_store(store_ref, revision_policy)
resolve_database(database_ref, revision_policy)
resolve_effective_splitter(database_ref)
resolve_storage_bindings(database_ref, capability)
record_receipt(operation_ref, receipt)
```

Store既定値とDatabase overrideの解決経路をreceiptへ残す。MariaDB adapterは標準候補だが、Core APIは`MetaCatalogPort`へ依存する。

接続credential本文を返さない。adapterへは権限scope付き`secret_ref`を渡し、ログ、OAE、Composite FAMへsecretを展開しない。

## 4. Registry Provider SPI

Classification Registry、Schema Bundle、Context Fold Profile、Access Map、Causality Profileをstable refとrevisionで解決する。

Registryは型と定規、Context Registerはbind済み実体である。既存の`Classification Registry`名称は保持し、runtime値をRegistryと呼ばない。

## 5. FAM Splitter SPI

```text
split(source_fam, registry_ref, fold_ref, routing_policy_ref)
  -> candidate routes
     + classification evidence
     + unmapped branches
     + splitter receipt
```

最低出力:

```yaml
split_result:
  splitter_ref: splitter://example@2
  registry_ref: registry://example@4
  fold_ref: fold://example@4
  source_fam_ref: fam://source
  candidates:
    - context_dimension_ref: dimension://finance
      class_ref: class://finance
      database_ref: ibd://finance
      classifier_score:
        value: 0.86
        profile_ref: classifier-score://example@2
  unmapped: []
  evidence_refs: []
  status: completed
```

`classifier_score`、retrieval score、SsC SIN、fusion rankを同じ`score`へ畳まない。

Binding優先順序:

```text
Database override
  -> Store default
  -> unresolved
```

custom Splitter失敗時は`failed`を返す。明示されたfallback policyがある場合だけ次候補を呼び、最初の失敗receiptを消さない。

## 6. Graph／Vector／Evidence Adapter

### 6.1 Graph Store SPI

node、edge、port、Mapping FAM、Last Order、Provenanceを論理Database境界内で検索する。graph relationをvector類似度へ置換しない。

### 6.2 Vector Store SPI

各Binding固有のembedding profile、dimension、metric、score directionへ従い、local candidateを返す。

```yaml
local_retrieval:
  storage_binding_ref: storage://neo4j-a
  embedding_profile_ref: embedding://model-a@7
  metric: cosine
  embedding_dimension: 768
  raw_score: 0.81
  score_direction: higher_is_closer
  local_rank: 3
```

Vector Store SPIはFAM Splitterではない。Neo4jの索引内filterもaccess boundaryやContext classifierの代用品にしない。

### 6.3 Evidence／RDB Connector SPI

ODBC、JDBC、MariaDB、MySQL、PostgreSQL、FileMaker Data API等を、Evidence snapshotとfreshnessのsourceとして接続する。

少なくともconnector revision、query fingerprint、parameter hash、schema／result fingerprint、row count、source cursor、observed time、clock qualityを返す。RDBを伸長検知した場合、過去結果を上書きせず再探索候補を返す。

## 7. Composite Resolver

Composite ResolverはQで許可されたDatabaseごとのlocal resultを受け、graph compatibility、Mapping FAM、Access Map、Evidence、Last Orderを検査してComposite FAMを派生生成する。

```text
local retrieval runs
  + graph relations
  + explicit Mapping FAM
  + calibration / fusion policy
  + Evidence freshness
  + Last Orders
      ↓
non-destructive Composite FAM
```

Access Mapは変換可能性、Mapping FAMは探索recipe、Transformerは能動実行、transformation receiptは実行証跡である。どれかを別のものとして捏造しない。

## 8. SsC: SIN-to-sin Converter研究interface

### 8.1 目的

SsCは異なるvector storeのraw scoreを同一vector空間へ変換するmoduleではない。各store内で成立したlocal retrievalを、明示的な校正profileを介して共通の`meta SIN`へ射影し、上位SIN検索射程を各store固有thresholdへ逆射影する研究moduleである。

```text
local raw score + metric + calibration profile
  -> calibrated meta SIN + uncertainty

target meta SIN range + calibration profile
  -> store-local threshold / range | inverse-unavailable
```

Query vector自体は別embedding空間へ翻訳しない。Query FAMのtext／構造を各storeのembedding engineへ渡し、そのstore内で検索する。

### 8.2 必須metadata

- raw scoreとlocal rank
- metricとscore direction
- embedding model／runtime／dimension／normalization
- calibration dataset fingerprint
- calibration profile revision
- calibrated SINとuncertainty
- inverse mappingの可否と有効範囲
- source rankとfusion policy

### 8.3 数理境界

`0..2`を`0..π`へ写し`sin(θ)`だけを返す素朴な方式は、`sin(θ) = sin(π - θ)`のため前半・後半を逆変換できない。採用する場合はsector、angle、cos成分等を別に保持する必要がある。

`atan`は単調な有界写像候補になり得るが、異なるscore分布、metric、model品質を自動的に校正しない。校正dataset、単調性、飽和、外挿、逆関数、uncertaintyを別に検証する。

したがってSeason 0では、`meta SIN`の名称とinterfaceを研究対象として保持し、特定の三角関数を規格として確定しない。

## 9. OAE Storage Binding

OAEの共通意味schemaはManifest側の正本確定後にversionする。IBD側は先に次を保持する。

- `oae_refs`
- source Event／FAM／Run Trace refs
- Observer、Recorder、Interpreter、Initiator、Executor、Transformer、Causal Contributorのrole-preserving binding
- source／target Fold refs
- Access Map、Mapping FAM、transformation receipt refs
- Registry、fact scope、Provenance
- runtime timestampとclock quality

入力に因果帰属がない場合、adapterがCauseを推定生成しない。Run TraceをOAE本体へ自動変換しない。

## 10. capability negotiation

moduleはnameだけでなくversion、capability、supported schema、error semanticsを公開する。

```yaml
module_capability:
  module_ref: module://ibd/splitter@1
  sdk_surface: S1
  supported_contracts:
    - ibd-splitter-spi@0.1-draft
  optional_capabilities:
    - multi-label
    - evidence-spans
  fallback_policy: explicit_only
```

互換でないmoduleを「best effort」でsilent接続しない。`incompatible`、`adapter-required`、`human-review-required`を返す。

## 11. SDK surfaceとdomain bundle

IBDSDKは`S0 envelope`、`S1 SPI`、`S2 domain-facing SDK`を直接提供し、S3 workflow、S4 prompt compilerから利用できるようにする。

AstroSDKやAtlantis SDKはIBDSDKの全moduleを必須同梱せず、目的に必要なcapabilityとD Fold Manifestをbundleする。bundleが高級語彙を持つことを技術Layerの常時上位とみなさない。

## 12. Season 0互換方針

既存`0.1.0-draft`schemaのrequired fieldを増やさない。`additionalProperties: false`のschemaへfieldを追加する場合はoptionalとして明示し、必須化は`0.2.0-draft`で行う。

新規schema候補:

- `ibd-store-manifest.schema.json`
- `context-fold-profile.schema.json`
- `splitter-binding.schema.json`
- `score-calibration-profile.schema.json`
- `transformation-receipt.schema.json`

文書でcontractを固定した後、fixture、validator、negative testを追加する。未実装のSPIを実装済みと表示しない。

## 13. 関連文書

- [Context Dimension OSにおけるIBDとIBDSDK](../architecture/context-dimension-os-and-ibdsdk.ja.md)
- [Classification Registry、Database隔離、Routing契約](classification-registry-and-routing.ja.md)
- [Query FAMとComposite FAM契約](fam-query-and-composition.ja.md)
- [Evidence鮮度とLast Order契約](evidence-freshness-and-last-order.ja.md)

