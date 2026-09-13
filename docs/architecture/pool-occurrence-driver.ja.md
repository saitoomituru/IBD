# Pool Occurrence Driver(旧FAM Splitter)

状態: `[DESIGN-CORRECTIVE]` `[SEASON-0]` `[NAMING-FIXED / IMPLEMENTATION-PENDING]`
更新日: 2026-09-13
主たる射程: Layer A(工学・実装責務)
supersedes: 本書内の各節に記載する「FAM Splitter」表記(旧)

## 0. 経緯(2026-09-13、ブレスト集約)

旧`FAM Splitter`SPI(`split(source_fam, registry_ref, fold_ref, routing_policy_ref) -> candidate routes`)は、実際には二つの異なる工程を一つの語へ押し込んでいた。

1. FAM構造を開いて分解する工程 — 2026-09-13にFQuery側で「DeFold」(可逆・局所編集。既存Foldを開いて再展開する。破壊しない)として正式に切り出された責務。正本: FQuery `docs/specification/fam-q-declaration-execution.ja.md` 4節、manifest `docs/theory/fam-q-declaration-execution-model.ja.md`
2. 分解された候補を、`FIT`(構造一致)/`MATCH`(ベクトル近傍)/`SELECT`(fact pointer)という3語彙のドライバーでRegistry classへ照合し、格納先candidateを決める工程 — IBDに残る責務

(1)がDeFoldとしてFQuery側の正式責務になったことで、IBD側に残った(2)を指すには「Splitter」という語はもはや不正確である。(2)は「分解」ではなく「既に分解された候補を、異種データソース(RDB／vector／graph／file／object)へどう照合・接続するかを管理する」責務であり、この文書はその責務に`Pool Occurrence Driver`という正式名称を与える。

命名の経緯(ブレスト要点):
- FileMakerの Table Occurrence(TO): 同一base tableを、用途ごとに異なるrelationship graph文脈で複数回インスタンス化し、循環参照を避ける仕組み。この「同じ実体を用途ごとにoccurrenceとして名付け直す」発想を踏襲する
- ただしIBDが扱うのは「Table」に限らない(RDB／vector／graph／file／objectを横断する)ため、「Table」ではなく中立語の「Pool」を採用する
- 「叡智オカレンス」は不採用: `叡智`はrefFAM/wisdom densityの文脈で既に厳密に定義された語(答えを生み、疑い、追試し、更新する可搬手続き)であり、かつRaphael APIの哲学的アンカー(「叡智の王」)として既に占有されている。Storage照合ドライバーの命名へ転用すると語彙衝突を起こす
- 「探索オカレンス」も不採用: `探索`はFAM側で既に「探索技」「探索語彙」(FIT/MATCH/SELECT自体を指す表現、`compose_fam.py`のコメント含む)として使われており、driver層の名前に使うと意味が二重化する
- 「ソースオカレンス」も不採用: `source_fam`は旧SPI署名で既に「分類対象として渡される入力FAM」という狭い意味で予約済みであり、driver層の名前に転用すると衝突する
- 「バレーオカレンス」も不採用: 語自体に衝突はないが、命名根拠として持ち出した「コモンズ」がmanifestの`gift-commons`(ZeroRoomLabの既定ライセンス哲学、OPEN/non-exclusive)という別ドメインの重い語を借用することになる

## 1. Pool Occurrence Driverの定義

```text
Pool Occurrence Driver
├─ 入口(source)adapter層
│    RDB / Vector DB / Graph DB / file / object store / 将来追加分を任意接続
├─ 抽象関係管理
│    どのcommandでどのadapterが反応するか
│    どのfieldをどう関連付けるか(FileMaker TOのrelationship graph相当)
└─ 出口(sink)adapter層
     既存RDB / DynamoDB等の外部書き込み先を任意接続
```

IBD自身がPool Occurrence Driverである。IBDはFQuery/SphereOS Atlantisに専属せず、FIT/MATCH/SELECTという可搬語彙を使いたい別のnativeプロジェクトからも中立に呼べるlayerとして設計する。

## 2. FIT / MATCH / SELECT = 3つのOccurrence

FIT/MATCH/SELECTは、Pool Occurrence Driverという単一の抽象クラスに対する3つの具体occurrenceとして位置づける(FileMaker TOにおける「同一base tableの複数occurrence」に相当)。

```text
FIT     構造一致    ∇φ.modules / assembly_graph
MATCH   ベクトル近傍  local_retrieval_runs
SELECT  fact pointer evidence_bindings
```

正本: `docs/specification/fam-query-and-composition.ja.md` §2(2026-09-10、`[CORRECTIVE]`)、`experiments/season0/composite_fam.py`のコメント。この3語彙は真偽の分類ではなく探索方法であり、互いに排他ではなく同じComposite FAM内で併存する。

現状の実装カバレッジ(`composite_fam.py`): FIT+SELECTのみ実装、MATCH(vector近傍検索)は未実装のまま`local_retrieval_runs: []`で明示保持している。

## 3. 入口/出口adapterモデル

```text
source-side adapter(入口)
  RDB(SQL) / Vector DB / Graph DB / file / object store
      ↓ Pool Occurrence Driver(FIT/MATCH/SELECT occurrence経由で照合)
sink-side adapter(出口)
  既存RDB(SQL) / DynamoDB等 / 将来追加分
```

入口・出口ともに任意のadapterを追加できる疎結合SPIとする。新しいsource(例: 別のvector DB)や新しいsink(例: 既存DynamoDB)を追加しても、Pool Occurrence Driver自体の契約(FIT/MATCH/SELECT occurrence、relationship管理)は変わらない。

## 4. TO型循環参照正規化

複数のRegistry/Foldが同一データソースを異なる文脈で参照すると、素朴な実装では参照グラフが循環し得る。FileMaker TOと同じ解法を採る。

```text
同一データソース
  ├─ occurrence A(Registry Xの文脈で命名)
  ├─ occurrence B(Registry Yの文脈で命名)
  └─ occurrence C(Fold Zの文脈で命名)
```

同じ物理データソースであっても、参照する文脈(Registry/Fold)ごとに別のPool Occurrenceとして名付け直すことで、抽象階層からの呼び出し経路を正規化し、参照グラフを非循環(DAG)に保つ。これは既存のIBD不変条件「異なるFold/Registry/Databaseを、同名labelやvector similarityだけでsilent mergeしない」(`context-dimension-os-and-ibdsdk.ja.md`不変条件2/9、`classification-registry-and-routing.ja.md`§4隔離)を弱めるものではなく、むしろ強化する——暗黙mergeの逆で、明示的にoccurrenceを分けて名付け直す機構そのものである。

## 5. Engine主体・GUI追従の疎結合契約

Pool Occurrence DriverはEngine側の責務であり、GUIはEngineの状態を描写する疎結合コンポーネントとして追従する(Engineが主体、GUIが従属)。

FileMaker TOのrelationship graphエディタの発想を継承し、GUI表現にはFQueryが既に採用しているReact Flow(Issue #5)を流用できる。ただしEngine(Pool Occurrence Driver)とGUI(Presentation layer)は疎結合マイクロカプセルとして分離し、GUI側の都合でEngine側のPool Occurrence契約(FIT/MATCH/SELECT occurrence、relationship定義)を変更しない。これはFQuery Issue #5が既に明記する「runtimeから独立したcomponent群として提供し、VS Code Webview、Sphere Runner、Electron／Browser、将来IDEから再利用できるPresentation layer」という設計方針と一致する。

## 6. 旧FAM Splitter語彙からの対応表

| 旧語彙(FAM Splitter) | 新語彙(Pool Occurrence Driver) |
|---|---|
| FAM Splitter / FAM Splitter SPI | Pool Occurrence Driver / Pool Occurrence Driver SPI |
| `split(source_fam, registry_ref, fold_ref, routing_policy_ref)` | `resolve_occurrence(source_fam, registry_ref, fold_ref, routing_policy_ref)`(暫定案。実装時に確定) |
| splitter receipt | occurrence receipt |
| default/override Splitter Binding | default/override Pool Occurrence Binding |
| `splitter_binding_ref` | `pool_occurrence_binding_ref` |
| `splitter-binding.schema.json`(未作成draft案) | `pool-occurrence-binding.schema.json`(未作成draft案) |
| custom Splitter | custom Occurrence Driver |
| 標準Splitter(ZeroRoomLab同梱) | 標準Pool Occurrence Driver(ZeroRoomLab同梱) |

責務の実体(候補分類と根拠を返す。Registryが許可classと保存先を定義する。IBD adapterが決定済みrouteへ書き込む。Splitter/Driver自身が未知のDatabaseを作らない)は変更しない。変更するのは名称と、(1)DeFold的分解工程を含意しない、という境界の明確化のみ。

## 7. 決定論境界とOAE発行責務(2026-09-13ブレスト、SsC/鳥卵パラドクス問題)

### 7.1 決定論closureというリトマス試験

IBD/Pool Occurrence Driverが行うあらゆる計算に適用できる一般原則。

```text
入力 → 出力が一意に決定論的に閉じる
  → OAE不要、そのまま出力してよい(IBD Coreの責務)
  例: embedding vector計算、raw score、metric、calibration profileの機械的適用

入力 → 出力が決定論で閉じない(重み・policy・選択・解釈が介在する)
  → OAEとして管理しなければならない(IBD Coreの責務外)
  例: fusion policyによる重み統合、calibrated SINの評価・閾値判断
```

`fam-native-ibd.ja.md`§8不変条件4「最終評価をIBD Coreへ混入させない」を、検証可能な基準へ落とし込んだもの。

### 7.2 OAE発行はFQuery(上位system)の責務、IBDは証跡のみ

IBD自身はOAEを発行しない。`fam-native-ibd.ja.md`§7が既に「IBDが所有するもの」に挙げているのは`OAE参照`であって`OAE発行`ではない——本節はこの既存区分を明文化するのみで、新しい制約を追加するものではない。

```text
IBD(決定論仕事)
  Pool Occurrenceとadapterに指定された実行結果を
  証跡(receipt: どのoccurrence、どのadapter、どの入出力、どの結果)として記録する

FQuery Core(型のみ)
  OAE receiptの型(shape)を持つが、判定・発行はしない
  実装確認済み: FQuery `packages/core/src/types.ts`が
  `OaeConstraintEvaluationReceipt`型を定義。`packages/plugin-sdk/src/
  oae-evaluator.ts`のコメントに明記「Coreはこの判定を呼ばず、返された
  OAEを保存する。domain ruleの中身とObserver verdictの真偽は、この
  helperも裁定しない」

FQuery Plugin(発行)
  IBDの証跡を受け取り、実際にOAEを構成・発行するのはplugin
  (plugin-sdkのevaluator helperを使うが、helper自体も真偽は裁定しない)

Sphere(SphereOS Atlantis)/Astro(SphereASTRO)(意味論の最終的な所有者)
  Observer/Recorder/Interpreter/Initiator/Executor/Transformer/
  Causal Contributorのrole定義、domain ruleの内容、Observer verdictの
  真偽という「OAEの意味」自体はさらに上位のSphere/Astroへ委譲される

上位system(さらに外側)
  IAM(identity/access management)、authority policy
  IBDはcredential本文を持たず`secret_ref`+authority scopeのみ保持する
  (`context-dimension-os-and-ibdsdk.ja.md`§4と同じ境界)
```

SsC(§8、`ibd-sdk-module-contracts.ja.md`)への適用: calibration profileの機械的適用(local raw score ↔ meta SIN変換の実行)はIBD側receiptとして保持できるが、calibrated SINを「一致」「閾値超過」等として評価する行為はFQuery pluginが行い、その行為自体をpluginがOAEとして発行する(evaluator helperは受け取ったOAEの構造を検証するのみで真偽は裁定しない)。

weight統合(Composite Resolverのfusion policy)への適用: 重み付け統合は決定論で閉じないため、どのrefFAMのどのQがこの統合を認可したかをFQuery pluginがOAEとして発行する。IBDはfusion policyの実行結果(fusion rank)をreceiptとして保持するのみで、そのpolicyの正当性は判断しない。FQuery Core自身もそのpolicyの正当性は判断せず、OAE receiptの型だけを保証する。

### 7.3 鳥卵パラドクス問題

Pool Occurrence graphのrelationship解決が循環参照で爆発する問題。FileMakerのrelationship graphがtopology errorを返す構造と同型。

```text
保存(write)時
  循環・爆発しうるtopologyそのものを保存することはNGではない

取り出し(retrieval/traversal)時
  cycle limit n(何階層まで循環探索するか)は
  Pool Occurrence Driver SPIへの正当な入力parameterとして持てる

  ただしn自体の設定は決定論で閉じない policy選択のため、
  FQuery側がOAEとしてこの選択を発行する

  n到達までに決定論的に解決できなかった場合、IBDは
  「決定論的に解決できなかった」を偽らず返す
  (truncateして成功したふりをしない)
```

n到達によるdynamic relationship performance問題(循環参照過多による低速化)自体はIBD Core契約の対象外とし、Pool Occurrence graphを設計する側(Registry/Store定義者)の設計品質問題として明示的にNon-goalへ置く(FileMaker開発者のrelationship graph設計責任と同型)。

### 7.4 resolution_modeとbottom_ref契約

`occurrence_result`(旧`split_result`)の`status`に加え、次を持つ。

```yaml
occurrence_result:
  # ...(既存fields)
  resolution_mode: deterministic  # | bounded-most-likely
  bottom_ref: null                # resolution_mode: bounded-most-likelyのとき必須
  cycle_limit_oae_ref: null       # cycle limit nを承認したFQuery側OAE参照
```

`deterministic`: 完全に決定論的に解決済み。`⊥`なし。
`bounded-most-likely`: cycle limit n到達により打ち切り、最尤(best-effort)で出力。探索限界のbottom(⊥/Last Order、FQuery `Bottomed<T>`union型と同型)を`bottom_ref`として必ず付帯する。これを欠くとLast Orderの⊥がどこで発生したか追跡不能になる。

## 8. 未確定事項(Season 0)

- `resolve_occurrence`等、SPI関数シグネチャの最終名称(本書の対応表は暫定)
- schema draft(`pool-occurrence-binding.schema.json`等)の実ファイル化
- 実装コード(Python `experiments/season0/*.py`)側の識別子改名——現状のPython実装には`splitter`という識別子は存在せず(確認済み)、影響は文書層のみ。ただしFQuery側の`sub_splitters`フィールド名(decomposition schema内、DeFoldの分解tree構造を指す既存フィールド)との整合は別issueで扱う
- Pool Occurrence Driver GUI(React Flow流用)の実装着手はM-F(GUIリファクタ)まで行わない(#44 Roadmap Gate準拠)
- Pool Occurrence Driverの永続化フォーマット(2026-09-13ブレスト追記、2回目の指摘で精緻化): occurrence定義・relationship・bindingは`ψ/∇φ/λ`というFAM JSONのcontent軸ではなく、純粋にL軸(決定論的・構造的topology)とS軸(SDK surface抽象度)に属する資源であり、FAM JSONへ無理に押し込まない。またYAMLはPool間のrelationship(多対多のgraph構造、TOのjoin条件に相当するもの)の表現力が弱いという指摘があり、YAML一本化も前提にしない。候補として、FileMaker BaseElements的なXML(FileMakerのschema/relationship/layout/scriptをXML export・解析できる既存の商用互換資産)、またはFileMaker Data API連携時のXML(FMPXMLRESULT等)と親和性のある構造化XML+schemaを、relationship graph表現の候補とする。これによりFileMaker系ツールチェーンやXMLを読める他DB/cloud基盤からも同じrelationship定義をcommodity資産として読み込める可能性がある。ただしIBD Core実装は`experiments/season0/*.py`のPython中心であり、現状`schemas/draft/*.schema.json`はJSON Schemaで統一済み。XML系形式を採用する場合、(a)どの層(Meta Catalog manifest / occurrence binding / relationship graph)に適用するか、(b)既存JSON Schema系資産との共存方法、(c)Python実装側のXMLパース経路、を切り分けて検討する必要がある。次にこの話題へ戻るときのため、判断材料として記録するのみで今回は確定しない

## 9. 関連文書

- [FAMネイティブIBDアーキテクチャ](fam-native-ibd.ja.md)
- [Context Dimension OSにおけるIBDとIBDSDK](context-dimension-os-and-ibdsdk.ja.md)
- [IBDSDK module契約](../specification/ibd-sdk-module-contracts.ja.md)
- [Classification Registry、Database隔離、Routing契約](../specification/classification-registry-and-routing.ja.md)
- manifest [IBD FAMネイティブBinder](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/ibd-fam-native-binder.ja.md)
- manifest [Sphere Context SDK共通契約](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/sphere-context-sdk-contract.ja.md)
- FQuery [FAM Qの宣言/実行分離とFold/DeFold/unFold](https://github.com/saitoomituru/FQuery/blob/main/docs/specification/fam-q-declaration-execution.ja.md)
