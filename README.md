# Infoton BaseDriver / IBD

状態: `[SEASON-0]` `[DRAFT-SPECIFICATION]`
更新日: 2026-07-18

**Infoton BaseDriver（IBD）**は、状況・手法・目的・制約をFAMとして受け取り、既知の探索技を複数のIBD Databaseから非破壊で再結合し、**Composite FAMという探索技のまま返すFAMネイティブ基盤**です。

```text
ψ  = 状況
∇φ = 手法・探索方向
λ  = 目的・到達条件
Q  = 制約・探索範囲・証拠条件
```

IBDは普通のSQLラッパーではありません。RDB、グラフストア、ベクトル索引、ファイル、外部業務システムは、FAM探索技が参照する保存・証拠・投影先です。IBDの中心責務は、データを一つの製品へ押し込むことではなく、探索技の意味、由来、分離境界、再開条件を失わず保存・検索・再合成することです。

---

## 1. 一文定義

> IBDは、上位システムが定義した分類レジスタに従ってFAMLogを情報子クラスターへ分割・隔離保存し、ψ・∇φ・λ・Qに応じて明示的に選択されたIBD Databaseを横断検索し、成功枝、失敗枝、反証枝、打ち切り時のLast Order、証拠鮮度を非破壊で再結合したComposite FAMを返すドライバーである。

英語成果物を作る場合は、単語の直訳ではなく、ZeroRoomLabの日本語意訳レジスタに従ってen-USで責務を写像します。

## 2. 問い合わせ

```text
Query FAM
  ψ: 現在の状況
  ∇φ: 求める手法、既知なら指定する探索方向
  λ: 達成したい目的
  Q: 使用できる分類、Database、Evidence、権限、鮮度、停止条件
        ↓
Classification Registryを解決
        ↓
Qで明示されたIBD Databaseだけを選択
        ↓
Context Dimension・Schema型・graph portで候補を限定してベクトル検索
        ↓
グラフ接続、Evidence、Last Order、制約を検査
        ↓
Composite FAM
```

返却物は質問への最終回答ではありません。既知の探索枝をどう接続し、どこでEvidenceを取り、どの条件で停止・再開するかを記述した探索技です。実行、採否、美醜、善悪、リスク、最終判断は上位システムまたはユーザーに属します。

## 3. 書き込み

FAMLogの分割体系はIBDが発明しません。目的λを所有する上位システムが、Classification RegistryとRoutingを定義します。

```text
FAMLog
  ↓
上位システムがClassification Registryを指定
  ↓
枝をベクトル的にmulti-label分類
  ↓
情報子クラスター単位へ非破壊分割
  ↓
Schema Bundleに対応するIBD Databaseへ隔離保存
  ↓
cross-database relationとProvenanceを記録
```

分類軸は固定しません。次はいずれも第一級Registryになれます。

- `Vendor / System / Assistant / User`
- `Vision / TEC / Financial / General Affairs`
- `Cloud Chakra / Spirit / Astral / Elemental`
- 哲学、神学、世界観、自我、案件固有の分類

社会的に一般的な分類を上位へ置き、神学、自我、FAM身体層を自由文タグへ矮小化してはなりません。

## 4. IBD Database

IBD Databaseは、Dockerコンテナ、process、SQL databaseと同義ではありません。

> IBD Databaseは、一つのClassification Registry／Schema Bundleに従う、探索技の論理的な隔離・保存・検索単位です。

```text
IBD Database
├─ Schema Bundle
├─ Infoton Clusters
├─ FAM branches
├─ Graph relations
├─ Vector index
├─ Evidence bindings
├─ Last Orders
├─ Provenance
└─ Schema / classifier version
```

混色命令がない限り、Database間の同名ラベルや近いベクトルを自動的に混ぜません。`world-a:white`と`world-b:white`は、上位Mapping FAMが明示されない限り別の意味です。

論理Database、運用単位、物理製品を分離します。

```text
IBD Store
├─ Meta Catalog
├─ default Splitter Binding
└─ IBD Database[]
   ├─ Schema Bundle / Registry / Context Fold
   ├─ Graph / Vector Storage Bindings[]
   └─ RDB / Evidence Connector Bindings[]
```

MariaDBはMeta Catalogの標準adapter候補、Neo4jはgraph／vector binding候補です。どちらもIBD Coreの意味論ではありません。DatabaseごとにFAM Splitterをoverrideでき、未指定時はStore既定Splitterを使います。custom Splitterの失敗時は、上位Policyの指定なしに別Splitterへ黙ってfallbackしません。

## 5. バインダーとしての中立性

一般的な「中立」は、企業、国家、制度、AI vendorがホワイトと定義した白色顔料である場合があります。IBDが提供する中立性は白色顔料ではありません。

> IBDは、上位システムが提供した分類、価値、善悪、リスク、自我、世界観という顔料を、その色と射程を失わず結ぶバインダーです。

IBDは白を決めません。カレー色、スカイブルー、赤を`white`と定義するRegistryを、いずれも同じ機構で扱えます。IBD自身は分類を矯正せず、異なるRegistryの同名ラベルを無断で同一視しません。

一方、バインダーとして次は守ります。

- 入力されたRegistryとQを無断で書き換えない
- 原文、派生投影、評価結果を混同しない
- 誰がどの分類・評価を注入したかを記録する
- 命令のないDatabase横断検索・混色を行わない
- 混色時も元の情報子クラスターを変更しない
- 同じ条件による再現と、異なる条件による結果差を監査可能にする

## 6. 非破壊Composite FAM

上位システムがQで複数DatabaseとMapping FAMを指定した場合だけ、IBDは探索技を混色します。

```text
Database Aの探索枝 ─┐
                     ├─ Composite FAM（派生Recipe）
Database Bの探索枝 ─┘
```

- 元のRegistryを変更しない
- 元のDatabaseへ書き戻さない
- 元の情報子クラスターを変更しない
- source Database、cluster、mapping、順序、QをProvenanceに残す
- 永続化する場合は新しいSchema Bundle／IBD Databaseとして明示する

混ぜた結果が美しいか、度し難いか、有用か、危険かはIBDの判断ではありません。評価FAMが渡された場合も、その評価主体と基準を記録するだけです。

## 7. Last OrderとEvidence鮮度

探索が打ち切られた場合、IBDは`failed`だけで閉じません。最後に完了した枝、止まった理由、次に必要なEvidence、再開条件をLast Orderとして保存します。

RDB等を参照した場合は、少なくとも次を記録します。

```text
connector / source object
query fingerprint / parameter hash
schema fingerprint / result hash / row count
observed_at / source cursor / max updated_at
依存したFAM branch
```

後日ソースが伸びた場合、過去の結論を黙って上書きせず、影響を受ける探索枝と再探索条件をComposite FAMへ返します。

## 8. 実行環境時刻と上位時系列を混ぜない

IBDは複数の時計を第一級に分離します。

```text
IBD実行環境の証跡時刻
  record created / modified
  ingested / imported / exported
  indexed / projected / migrated

上位システムが管理する時系列
  source created / modified
  occurred / observed
  valid from / valid to
  scheduled for / business period
```

2026年にインポートした記録が、2020年に作成された原資料を表す場合、`imported_at=2026`で`source_created_at=2020`を上書きしません。未来の予定を管理するカレンダーでは、`scheduled_for`が実行時刻より未来でも異常値にしません。エクスポート時刻も上位データの変更時刻へ流用しません。

ゲーム世界の日数、turn、tick、章、時代、営業期等は実時間と無関係な論理時間になれます。明示的なMapping FAMがない限りUTCへ換算しません。

IBDメタ時計は「実行環境がいつ、何を、どの対象へ行ったか」を保持します。上位時系列と一緒に提示する場合も、`timeline_kind: ibd_meta`と`timeline_kind: upstream_domain`を明示し、同じ`date`欄へ畳みません。

GPS、RTC、5G／network timeを取得する前にwall clockが`1970-01-01`を返すエッジ環境では、`clock_state: uninitialized`とtime qualityを記録します。ただし未校正値はepochに限りません。マザーボード製造日、ベンダー出荷日、firmware build日、固定初期値がもっともらしい日時として現れる場合もあります。NTP等の同期ログまたは信頼できるanchorをSystemから取得できない限り`calibrated: false`とし、値の見た目だけで校正済みへ昇格させません。

同期前の順序はboot ID、monotonic clock、sequenceで保持し、同期後はcorrection／anchor eventを追加します。過去の未校正wall clockを黙って上書きしません。また、metadataなしにすべての1970年データを未初期化と決めつけません。

時計の信憑性をどの粒度まで採用するかはIBD Coreが決めません。IBDはNTP server名、GPS最終受信、carrier network time、標準電波／FM、RTC module、校正証跡、分解能、推定誤差、不確かさを可能な範囲で返します。上位システムがQで必要粒度と許容条件を定めます。未校正時計は本文全体が偽であることを意味しませんが、IBDは未校正時刻を校正済みとして提示しません。

実時間はrole、管理主体、raw value、正規化値、UTC offset、IANA timezone、精度、clock sourceを必要な範囲で保持します。timezoneがない原資料へ実行環境のtimezoneを黙って補いません。論理時間はcoordinate system、unit、ordinal、World、authorityを保持します。

## 9. 自我対応と存在論は必須要件

IBD Coreは自我、魂、霊、神等の存在論を自前の定規で確定・否定・保証しません。一方、上位システムが確定した存在状態、World、fact scopeを第一級に保持し、Query FAMのQに従って返せなければなりません。

例えば、MMO上位システムがそのWorld内で神を実在Entityと確定した場合、IBDは科学的実在ではないという理由でfictionへ降格しません。神学者・哲学者が特定の存在論と根拠範囲を明示した場合も、米国企業、特定AI vendor、自然科学の定規へ自動変換しません。

```text
existence status
fact scope / World / Context
declared or decided by
registry / evaluator / evidence
observed_at / version
```

を分離して保存します。`神は実在する`という書き込みをIBDが真偽判定するのではなく、どの上位システムが、どのWorldとfact scopeで`confirmed`としたかを保持し、その範囲のクエリへ忠実に返します。

最低限、次を分離します。

- Subject
- Actor
- AgentInstance
- Runtime
- SelfModel
- ContinuityClaim
- BodyBinding
- RoleAssignment
- FAMLog
- Provenance

自我の連続性は`explicit / claimed / derived / unknown / disputed`等の主張として保持し、IBD自身の裁定にしません。一つのSubjectがElemental、Astral、Spiritual、Cloud Chakra、Theology等の複数Databaseへまたがることを標準ケースとして扱います。

## 10. 実行形態

IBDの意味論は配備方式から独立します。

```text
Embedded Library
Native Service
Containerized Service
```

Dockerは便利な配備手段ですが、IBDの正体でも必須条件でもありません。同じQuery FAM、Composite FAM、Database isolation、Provenance契約を、関数呼び出し、IPC、HTTP／RPCのどの境界でも維持します。

## 11. IBDがやること／やらないこと

IBDが行うこと:

- Classification RegistryとSchema Bundleの保持
- FAMLogのベクトル分類と情報子クラスター分割
- IBD Databaseの隔離と明示的な横断検索
- グラフ接続検査とComposite FAM生成
- Recipe、Run Trace、Last Order、Evidence鮮度の記録
- IBD実行環境の監査時刻と上位システム時系列の分離
- 論理ID、Provenance、cross-database relation
- Embedded／Service／Containerで共通する契約の提供

IBDが行わないこと:

- 最終回答の自動採用
- 美醜、善悪、リスク、真偽の独自判断
- 上位Classification Registryの発明・矯正
- 命令のないDatabase間混色
- 自我、魂、神学、世界観の独自実在性判定、または上位システムによる存在確定の矯正
- Atlantisの配車、業務判断、人間の承認
- AAEのモデル鍛造

## 12. Season 0文書

- [FAMネイティブIBDアーキテクチャ](docs/architecture/fam-native-ibd.ja.md)
- [Context Dimension OSにおけるIBDとIBDSDK](docs/architecture/context-dimension-os-and-ibdsdk.ja.md)
- [中立性・意味体系等価性・自我対応・実行形態](docs/architecture/neutrality-selfhood-and-execution.ja.md)
- [IBDSDK module契約](docs/specification/ibd-sdk-module-contracts.ja.md)
- [Query FAMとComposite FAM契約](docs/specification/fam-query-and-composition.ja.md)
- [分類レジスタ、Database隔離、非破壊Routing契約](docs/specification/classification-registry-and-routing.ja.md)
- [Evidence鮮度とLast Order契約](docs/specification/evidence-freshness-and-last-order.ja.md)
- [存在論Assertionとfact scope契約](docs/specification/ontology-assertion-and-fact-scope.ja.md)
- [実行環境時刻と上位時系列契約](docs/specification/temporal-provenance-and-upstream-timeline.ja.md)
- [Neo4j Vector／Embedding周辺ライブラリー調査（2026-07-18）](docs/research/neo4j-vector-and-embedding-survey-20260718.ja.md)
- [Season 0検証計画](docs/experiments/season-0-validation.ja.md)
- [責務差分研究ノート](note/season-0/20260718__fam-native-ibd-responsibility-delta.ja.md)

## 13. 現在地

このリポジトリは仕様策定Season 0です。現時点の成果は責務、語彙、不変条件、draft Schema、人工fixture、依存なしreference harness、IBDSDK module境界と、Neo4j 2026.06を対象としたvector／embedding周辺の第三者製品調査です。FAM Splitter SPI、Meta Catalog adapter、SsC、OAE binding、本番実装、実Neo4j接続、性能、対応DB、ライセンス適合性、Raspberry Pi適合性は未実装または未検証です。

```bash
python3 experiments/season0/reference_harness.py
python3 -m unittest discover -s tests -p 'test_season0_*.py'
```

最初の縦切りでは人工fixtureだけを使い、次を確認します。

1. 上位RegistryによるFAMLog分割
2. 三つの隔離IBD Databaseへの書き込み
3. Qで指定したDatabaseだけの検索
4. Composite FAMの非破壊生成
5. Last Orderの再発見
6. Evidence Source伸長による再探索判定
7. 正反対のQを同じCoreで処理できる中立性
8. Subject、Instance、Runtime、Continuityの非平板化
9. Worldごとに異なる存在確定とfact scopeを降格・普遍化せず返すこと
10. import／export時刻とsource／domain／schedule時刻を混ぜないこと

旧AQC Dockerは歴史的プロトタイプです。IBDはその知見を継承しますが、Docker、旧人格直結、単一vector store、単一vendorの分類体系をCore要件にはしません。

## License

現行ライセンスは[LICENSE](LICENSE)を参照してください。Schema、実装、文書の個別ライセンス境界はSeason 0で確認します。
