# Context Dimension OSにおけるIBDとIBDSDK

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-08-03
主たる射程: Layer A（IBD実装プロファイル）

## 1. 共通正本とIBDの境界

Context Dimension、D Fold、Registry／Context Register、Access Map、Transformer、OAEの共通定義は、ZeroRoomLab-manifestの[Sphere Context Dimension OSアーキテクチャ](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/sphere-context-dimension-os.ja.md)を正本候補とする。

IBDはその存在論や因果定規を再定義しない。IBDが担当するのは、上位RegistryへbindされたContext Register、FAM、Assertion、OAE参照を隔離保存し、Qで指定された範囲だけを検索し、由来を保ったComposite FAMへ非破壊結合する実装プロファイルである。

```text
Sphere共通契約
  Registry / Context Register / D Fold / Access Map / Transformer / OAE
                               ↓ bind
IBD実装プロファイル
  Store / Database / Storage Binding / Pool Occurrence Driver / Resolver / SsC / Adapter
```

`Pool Occurrence Driver`は旧称「FAM Splitter」。命名経緯・FIT/MATCH/SELECT occurrenceとの対応は[Pool Occurrence Driver](pool-occurrence-driver.ja.md)を参照。

霊的Presentation、神学、魔術、物理、Worldの定義は上位SDK／Registryに属する。IBDはそれらを第一級に保持できなければならないが、自前の正解へ制定しない。

## 2. 独立した軸

```text
technical Layer L     技術依存、実行順序、deployment責務
Context Dimension D   Foldへ束ねる等価な意味軸
Fold nesting G        Fold containerを包むnesting depth
Layer A / B / C        文書・主張の評価scope
SDK Surface S         L経路を構成するSDK／toolchain入口の抽象度
embedding dimension   vector表現の座標数
```

IBD文書内で単に「層」と書く場合、どの軸かを明示する。FAMの`λ`、既存schemaのlegacy `layer`、port型を技術Layer `L`へ自動変換しない。

正本三軸は`L / D / G`である。`S`は有効なSDK surface分類だが、Gを置換する独立三軸目ではない。
IBDは上位Foldから渡された`fold_nesting_depth`を、SDK surface番号、database階層、FAM再帰深度から
推定せず保持する。

**軸の混同禁止**: この`G`(Fold nesting — Fold containerを包むnesting depth)は、FQuery Issue #41やSphereOS Atlantis由来のFold7G研究草稿(ZeroRoomLab-manifest `note/20260819-2212__SphereDOS_Fold7G_Fold8G_registry_upgrade_memo.ja.md`、`G7 World`〜`G1 Reality/Substrate`という意味的スコープレジストリ)とは別軸である。前者はFold container参照の交差回数を数えるscalarで自動推定禁止、後者はWorld/Position/Causality等の階層ラベル(ordinal registry)。同じ記号Gを共有するが同一視・自動変換しない。

`4D Fold`は四つのContext Dimensionを束ねるというarityであり、四つのDatabase、四次元vector、技術Layer 4を意味しない。同じ4DでもDimension IDとRegistry revisionが異なれば互換ではない。

## 3. IBDの論理・管理・物理単位

### 3.1 IBD Store

IBD Storeは、一つの上位運用境界に属する複数IBD Databaseと、その接続メタを管理する単位である。

```text
IBD Store
├─ Meta Catalog
├─ default Pool Occurrence Binding
├─ SDK / connector profiles
├─ Access Map / calibration refs
└─ IBD Database[]
   ├─ Schema Bundle
   ├─ Classification Registry refs
   ├─ Context Fold Profile
   ├─ effective Pool Occurrence Binding
   ├─ Graph / Vector Storage Bindings[]
   ├─ RDB / Evidence Connector Bindings[]
   └─ OAE / Provenance refs
```

IBD Storeはprocess、container、RDB serverと同義ではない。一つのprocessで複数Storeを開く実装も、Storeごとにserviceを分ける実装も可能である。

### 3.2 IBD Database

IBD Databaseは、一つのSchema BundleとClassification Registry群へ従う論理的な隔離・保存・検索単位である。上位Systemが制定した「スキーマの塊」を一つのIBD Databaseへbindできる。

一つのIBD Databaseは複数の物理Storage Bindingを持てる。Neo4j database、vector index、MariaDB／MySQL／PostgreSQL、ODBC／JDBC source、FileMaker Data API、file、object storeを一対一へ固定しない。

### 3.3 Storage Binding

Storage Bindingは論理Databaseを物理製品へ接続するadapter設定である。

- graph／vector storeは探索枝と関係を検索する
- RDB／外部業務sourceはEvidenceとsnapshotを供給する
- Meta Catalogは接続定義、revision、hash、freshness、secret refを管理する
- credential本文はCatalogへ保存せず、authority付き`secret_ref`だけを持つ

物理storeの製品が同じでも、別IBD Databaseの隔離境界を自動解除しない。

## 4. Meta Catalog Port

IBD Coreは`MetaCatalogPort`を契約として持つ。MariaDB adapterを標準同梱・既定deployment profileにできるが、MariaDBそのものをIBD意味論へしない。

Meta Catalogが管理する候補:

- Store／Database manifestとrevision
- Registry、Schema Bundle、Context Fold refs
- default／override Pool Occurrence Binding
- graph／vector／RDB／Evidence connector metadata
- embedding、metric、calibration profile
- Access Map、Mapping FAM、Transformer capability refs
- OAE、Run Trace、Last Order、Evidence snapshot refs
- runtime clockとcalibration metadata
- credentialではなく`secret_ref`とauthority scope

Embedded Libraryでは別のCatalog adapterを差し込める。adapter差でQuery FAMやComposite FAMの意味を変えない。

## 5. Pool Occurrence Driver(旧FAM Splitter)

Pool Occurrence DriverはIBDSDK内の疎結合library／SPIとする。RDB／Vector DB／Graph DB／file／object等、異種データソースを抽象化したPoolに対し、FIT(構造一致)／MATCH(ベクトル近傍)／SELECT(fact pointer)という3つのoccurrenceで照合・ルーティングする。詳細な定義、命名経緯、TO型循環参照正規化は[Pool Occurrence Driver](pool-occurrence-driver.ja.md)を参照。

```text
source FAM / FAMLog
  + Registry base
  + upper-system Registry Schema
  + target Fold Profile
  + routing policy
      ↓
route candidates / tags / evidence / unknown / receipt
```

Storeは既定Pool Occurrence Bindingを一つ持てる。各IBD Databaseは必要な場合だけ一つのBindingでoverrideする。未指定DatabaseはStore既定値を継承する。

ZeroRoomLab標準Pool Occurrence Driverを既定同梱できるが、第三者は互換SPIへ独自Driverを差し込める。custom Occurrence Driverが失敗した場合、上位Policyが許可しない限り標準Driverへsilent fallbackしない。

Pool Occurrence Driverは候補分類と根拠を返す。Registryが許可classと保存先を定義し、IBD adapterが決定済みrouteへ書き込む。Driver自身が未知のDatabaseを作らない。

## 6. D Fold bundleと技術依存

AstroSDK、Atlantis SDK、業務SDKは、IBDSDKより「上の意味階層」ではない。必要なContext Dimensionとcapabilityを束ねるdomain bundleである。

```text
Astro 4D Fold
  Cloud Chakra / Spiritual / Elemental / Astral

Actor 4D Fold
  User / Assistant / System / Vendor
```

両者は同じ4Dでも自動互換ではない。接続にはFold ID、Dimension ID、Registry revision、Access Mapを要求する。

技術的には同じIBDSDK libraryを使う場合も、remote serviceを使う場合もある。Context Dの数からdeployment Lを推定しない。

## 7. Access Map、Mapping FAM、Transformer、OAE

```text
Access Map
  sourceとtargetの参照・変換可能性、条件、lossを定義

Mapping FAM
  実際の探索技として接続順序・変換recipeを記述

Transformer
  Mappingを能動実行するAgency／function

transformation receipt
  入出力、Fold、Registry、Transformer、結果を記録

OAE
  観測された変換・解釈・作用のContext管理単位
```

Access MapがあるだけではEffectは発生していない。Run TraceはIBD実行枝の技術証跡であり、OAEと同義ではない。一つのRun Traceが複数OAEを生成する場合も、OAE候補を一つも生成しない場合もある。

IBD Season 0では共通OAE本体schemaを複製せず、`oae_refs`、role-preserving envelope、storage bindingを先に設計する。Observer、Recorder、Interpreter、Initiator、Executor、Transformer、Causal Contributorを平板な`actor`へ畳まない。

## 8. local retrievalとcross-store合成

一つのIBD Database内では、Databaseが採用したembedding profile、dimension、metricへ揃えたvector indexを検索する。同一Database内のgraph relationは構造として辿れる。

異なるDatabase／store間ではraw vectorやraw scoreを直接比較しない。

```text
Query FAMのtext / structure
  ├─ store A固有embedding → local search A → local result / rank
  └─ store B固有embedding → local search B → local result / rank
                                          ↓
                Mapping FAM + calibration + Composite Resolver
                                          ↓
                                  Composite FAM
```

上位FAMから下位FAMを検索するとき、異なるContext Dimensionへの入口はtext query、構造query、明示Access Mapで選べる。すべてを一つのvector空間へ痩せさせない。

## 9. 実行形態

```text
Embedded Library
Native Service
Containerized Service
```

三形態はtransportと運用特性が違うが、同じStore／Database／Pool Occurrence Driver／OAE参照／Provenance契約を維持する。Dockerだけを正本にせず、Nativeだけを標準にせず、App内libraryだけを特権化しない。

## 10. 不変条件

1. Manifestの共通存在論をIBD固有schemaとして再発明しない。
2. RegistryとContext Registerを混同しない。
3. IBD Store、IBD Database、Storage Binding、processを同義にしない。
4. MariaDB、Neo4j、DockerをCore意味論にしない。
5. 正本三軸`L / D / G`を保持し、SDK surface `S`でGを置換しない。
6. D数またはGの深さだけでFold互換性を決めない。
7. Databaseの指定なしに横断vector検索しない。
8. 異storeのraw scoreを直接sortしない。
9. custom Pool Occurrence Driverの失敗を無断fallbackで隠さない。
10. Run TraceをOAEへ自動昇格しない。
11. Context権限からOS／Database credentialを推定昇格しない。

## 11. Season 0で未確定

- Meta Catalogの本番adapterとHA構成
- Store／Databaseの物理隔離粒度
- Pool Occurrence Driver標準実装とplugin transport(旧FAM Splitter、詳細は[pool-occurrence-driver.ja.md](pool-occurrence-driver.ja.md))
- SsCの校正関数、SIN定義、逆射影可能条件
- 共通OAE schema確定後のIBD binding version
- Graph／Vector／RDB connectorの正式採用

## 12. 関連文書

- [FAMネイティブIBDアーキテクチャ](fam-native-ibd.ja.md)
- [Pool Occurrence Driver(旧FAM Splitter)](pool-occurrence-driver.ja.md)
- [IBDSDK module契約](../specification/ibd-sdk-module-contracts.ja.md)
- [Classification Registry、Database隔離、Routing契約](../specification/classification-registry-and-routing.ja.md)
- [Neo4j Vector／Embedding周辺ライブラリー調査](../research/neo4j-vector-and-embedding-survey-20260718.ja.md)
