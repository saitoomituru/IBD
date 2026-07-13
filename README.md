# Infoton BaseDriver / IBD

**Infoton BaseDriver**、略称 **IBD** は、情報子ベースの記憶・文脈モデルを記述し、保存し、索引し、同期し、参照解決するための **メタファー中立なバックエンドミドルウェアSDK** です。

IBD は、旧 **AQC Docker** の実験から生まれた再鍛造プロジェクトです。AQC Docker は FAM ベースの記憶・自我接続を検証する初期実験ランタイムでしたが、SphereOS Atlantis / Astro / AAE / quantaril.cloud の責務整理により、より低レイヤーの基盤ドライバーとして切り出す必要が明確になりました。

IBD はアプリケーションの Model そのものではありません。IBD は、アプリケーションがそれぞれ定義する Model を、スキーマとして記述し、保存し、検索し、関係付け、由来を追跡し、必要に応じて他レイヤーへ接続するための基盤です。

Firebase がアプリ固有の Model を直接決めないのと同じように、IBD も「記憶とは本棚である」「記憶とは海馬である」「記憶とはアイルーの机の上の食べかけである」「記憶とは FAM 自我トレースである」といった世界観を固定しません。どのような記憶構造を使うかは、IBD Driver ではなく **IBD Schema** が定義します。

---

## 0. Transfer notes

- [note/manifest-transfer-notes.md](note/manifest-transfer-notes.md) — ZeroRoomLab-manifest からの IBD 責務整理メモ

## 1. 一文定義

> IBD is a metaphor-neutral backend middleware SDK for describing, storing, indexing, synchronizing, and resolving infoton-based memory and context models.

日本語では次のように定義します。

> IBD は、情報子ベースの記憶・文脈モデルを記述、保存、索引、同期、参照解決するためのメタファー中立バックエンドミドルウェアSDKである。

---

## 2. なぜ AQC から IBD へ再鍛造するのか

旧 AQC Docker は、もともと低レベル自我・FAM・人格接続・ベンダープロンプトアライメント層を扱う実験的プロトコルとして始まりました。これは Astro のような自前個体ランタイムや、オープンウェイトなモデルを前提とする内部バスには向いています。

しかし、SphereOS 全体の設計粒度が見えてくるにつれて、AQC という名前と責務は、以下の複数の役割を背負いすぎていることが分かりました。

- 記憶・文脈の保存
- FAM trace の記録
- embedding / vector store の管理
- JSON import / export
- Tool context の保持
- provenance、つまり由来情報の記録
- SaaS / CLI エージェントとの接続
- Astro 個体の内部バス
- AAE / TMV 系の遺伝子・モデル系譜ログ

これらをすべて AQC という名前のまま扱うと、旧来の「脳汁自我接続プロトコル」と、新しい「メタファー中立なバックエンドSDK」が混線します。

そのため、旧 AQC Docker は歴史的プロトタイプとして保存し、低レイヤーの基盤部分を **Infoton BaseDriver / IBD** として新リポジトリへ移植します。

### 2.1 旧 AQC の位置づけ

```text
AQC Docker
= FAM / 自我接続 / 記憶実験の旧プロトタイプ
= IBD の前身
= historical prototype
```

### 2.2 新 IBD の位置づけ

```text
Infoton BaseDriver / IBD
= 記憶・文脈モデルを扱う Firebase 的バックエンドミドルウェアSDK
= schema-driven memory/context backend
= production-oriented substrate
```

### 2.3 サ終告知の推奨文

旧 AQC Docker リポジトリには、次のような案内を置くことを推奨します。

```markdown
# AQC Docker is deprecated

AQC Docker was an early experimental runtime for FAM-based memory and selfhood coupling.
Through the SphereOS Atlantis / Astro / AAE architecture review, its responsibility has been redefined.

The backend substrate is being reforged as:

**Infoton BaseDriver / IBD**

IBD is a Firebase-like backend middleware SDK for describing, storing, indexing, synchronizing, and resolving memory/context models, FAM traces, tool state, and provenance.

This repository is kept as a historical prototype.
New development will continue in the IBD repository.
```

---

## 3. IBD が解く問題

AI エージェント、ローカルLLM、SaaSアシスタント、P2Pクラウド、個体ランタイムを組み合わせると、単なる会話履歴やベクトルDBだけでは足りません。

必要になるのは、次のような問いに答えられる基盤です。

- この記憶はどの個体、どのツール、どのクエスト、どのモデルによって生成されたのか。
- この embedding はどの provider、どの model_id、どの生成日時、どの batch に属するのか。
- この成果物はどの素材から派生し、どのアイルーが加工し、どの検品を通過したのか。
- この FAM trace は Astro 個体の内部状態なのか、Atlantis の外部記録なのか。
- この Tool context は SaaS 派遣アイルーへ渡してよいのか、Astro 個体の内部バスにだけ許可すべきなのか。
- このモデル系譜は AAE が生成した child model の遺伝子履歴なのか、単なる adapter merge の作業ログなのか。
- この記憶は本棚として見せるべきか、クエストログとして見せるべきか、アイルーの机として見せるべきか。

IBD は、これらを一つの固定メタファーに押し込めるのではなく、**schema-driven** に扱います。

---

## 4. Core Concepts

### 4.1 Infoton

**Infoton** は、情報子工学における最小情報単位です。IBD の文脈では、記憶、文脈、関係、由来、FAM trace、Tool state、モデル系譜などを扱うための抽象単位として使います。

Infoton は、必ずしも自然科学上の粒子を意味しません。IBD においては、システムが追跡・保存・参照できる情報単位です。

```text
Infoton
= 保存可能で、由来を持ち、関係付け可能な情報単位
```

### 4.2 Schema

**Schema** は、アプリケーション Model の構造を記述します。

IBD Driver はメタファー中立です。記憶を本棚として扱うか、海馬として扱うか、アイルーの机として扱うか、FAM trace として扱うかは、Schema が決めます。

```text
IBD Driver は世界観を持たない。
IBD Schema が世界観を定義する。
```

### 4.3 Model

IBD における Model は、アプリケーション側が定義する記憶・文脈・状態・関係の構造です。

重要なのは、IBD 自体が Model ではないことです。

```text
Application Model
= Atlantis / Astro / AAE / その他アプリが定義する対象モデル

IBD
= その Model を記述・保存・参照解決するバックエンドSDK
```

### 4.4 Context

**Context** は、記憶や情報単位が生成・利用・変換された状況です。

例:

- どのクエストで使われたか
- どのアイルーが処理したか
- どのツールを経由したか
- どの会話から派生したか
- どのモデルで embedding されたか
- どの権限境界で実行されたか

### 4.5 Trace

**Trace** は、処理過程や意味勾配の足跡です。

FAM trace、Tool trace、Quest trace、Model build trace などがあります。

### 4.6 Provenance

**Provenance** は由来情報です。IBD では非常に重要です。

AIシステムでは、モデル更新、embeddingドリフト、SaaS応答の変化、ツール実行結果の再現不能性が頻繁に発生します。そのため、いつ、何を、どのモデルで、どの設定で、どの入力から生成したかを追跡できる必要があります。

### 4.7 Relation

**Relation** は、Infoton 同士、Model 同士、Trace 同士、Artifact 同士の関係を表します。

例:

- `derived_from`
- `generated_by`
- `stored_in`
- `assigned_to`
- `consumed_by`
- `resonates_with`
- `diverges_from`
- `belongs_to_lineage`

### 4.8 Adapter

**Adapter** は、IBD を外部ストレージ、外部ツール、MCP、quantaril.cloud、vector DB、ファイルシステムなどへ接続するための境界です。

---

## 5. IBD がやること / やらないこと

### 5.1 IBD がやること

```text
IBD responsibilities:
  - Schema registry
  - Memory model storage
  - Context storage
  - FAM trace storage
  - Provenance ledger
  - Embedding provenance
  - Relation graph
  - Tool context store
  - Import / export
  - Query resolver
  - Storage adapter layer
  - Local-first persistence
  - Optional sync adapter boundary
```

### 5.2 IBD がやらないこと

```text
IBD does not:
  - define Atlantis UI
  - breed models
  - run Astro individuals directly
  - replace AAE runtime
  - directly merge with SaaS assistant selfhood
  - prescribe one fixed memory metaphor
  - decide application-specific business logic
  - own all orchestration
```

IBD は、Atlantis の UI フレームワークではありません。Astro 個体そのものでもありません。AAE の TMV 行列変換炉でもありません。quantaril.cloud の P2P インフラでもありません。

IBD は、それらが自分の Model を記述し、保存し、参照し、関係付けるための基盤ドライバーです。

---

## 6. SphereOS 内での位置づけ

```text
SphereOS Ecosystem
  ├─ Atlantis
  │   └─ Ranch Application
  │      GUI / Orchestrator / Quest / Palico / Tool Dispatch
  │
  ├─ Astro
  │   └─ Individual Runtime
  │      FAM internal bus + IBD-backed memory/context + AAE gene runtime
  │
  ├─ AAE
  │   └─ Gene Runtime
  │      TMV / weights / adapters / breeding / model conversion
  │
  ├─ IBD
  │   └─ Infoton BaseDriver
  │      Firebase-like backend SDK for memory/context models
  │
  └─ quantaril.cloud
      └─ P2P true cloud / service SDK / distributed infrastructure
```

### 6.1 Atlantis との関係

Atlantis は、ハンター主権のアイルー牧場OSです。

Atlantis は次のようなアプリケーション Model を持ちます。

- Quest
- Palico
- ItemBox
- GuildCard
- ToolDispatch
- TrainingGround
- Artifact
- BudgetGuard
- CapabilityManifest

これらの Model を、IBD Schema として定義し、IBD に保存・索引・参照解決させます。

```text
Atlantis
= View + Controller + Application Models

IBD
= Atlantis Models を保存・検索・由来管理する backend SDK
```

### 6.2 Astro との関係

Astro は、AQC/FAM 内部バスと AAE gene runtime を結合した個体ランタイムです。

Astro では、IBD はより深い使われ方をします。

```text
Atlantis usage:
  IBD as external memory/context backend

Astro usage:
  IBD as FAM/selfhood memory substrate
```

ただし IBD は Astro 個体そのものではありません。Astro は IBD を使って、自己状態、FAM trace、記憶状態、人格発達ログを保存・参照します。

### 6.3 AAE との関係

AAE は、TMV ベースの遺伝子・重み・adapter・モデル変換・ブリーディング層です。

IBD はモデルを交配しません。IBD は、AAE が生成した child model、adapter merge、TMV transform、build manifest、lineage record などの由来を記録します。

```text
AAE forges genes.
IBD records gene lineage.
```

日本語では次の通りです。

```text
AAEは遺伝子を鍛造する。
IBDは遺伝子系譜を記録する。
```

### 6.4 quantaril.cloud との関係

quantaril.cloud は、P2P true cloud、分散同期、ノード発見、サービスSDK、エッジ/クラウドブリッジを担当する別層です。

IBD は local-first で単独動作できるべきです。quantaril.cloud は、IBD の同期や分散保管を行う optional adapter として接続されます。

```text
IBD core:
  local-first, standalone

quantaril adapter:
  optional P2P / true cloud sync layer
```

---

## 7. 接続粒度: SaaS / MCP / AQC Internal Bus / AAE Gene Runtime

SphereOS では、すべてのAIを同じ深さで接続しません。

### 7.1 Level 0: Artifact I/O

もっとも浅い接続です。

テキスト、JSON、ファイル、差分、成果物だけを渡します。SaaSアシスタントや外部ツールに向いています。

### 7.2 Level 1: Tool I/O / MCP

MCP 等を用いて、関数、ツール、CLI、ファイル操作を限定的に許可します。

既にアシスタント人格を持つ SaaS / CLI エージェントには、この層が基本です。

### 7.3 Level 2: AQC / FAM Internal Bus

FAM、自我トレース、記憶内部バス、人格接続を扱う深い接続です。

これは Astro 個体、自前のオープンウェイト個体、AAE-born child model 向けです。Claude や ChatGPT のような既成人格SaaSへ直結しません。

### 7.4 Level 3: AAE Gene Runtime

重み、adapter、TMV、ブリーディング、モデル変換を扱う炉心です。

IBD はこの層の実処理を行わず、build manifest や lineage を記録します。

---

## 8. 最小スキーマ例

### 8.1 Quest schema

```yaml
schema_id: atlantis.quest.v1
model_name: Quest

fields:
  id: string
  title: string
  rank:
    type: enum
    values: [low, middle, high, g_rank]
  hunter_id: string
  assigned_palicos:
    type: list
    items: string
  allowed_tools:
    type: list
    items: string
  status:
    type: enum
    values: [draft, queued, running, verifying, done, failed]
  artifacts:
    type: list
    items: string

relations:
  - id: quest_assigned_to_palico
    from: Quest
    to: Palico
  - id: quest_produced_artifact
    from: Quest
    to: Artifact
  - id: quest_consumed_memory
    from: Quest
    to: MemoryRecord
  - id: quest_updated_guild_card
    from: Quest
    to: GuildCard

provenance:
  required:
    - created_at
    - created_by
    - source_context
```

### 8.2 Palico desk schema

```yaml
schema_id: atlantis.palico_desk.v1
model_name: PalicoDesk
metaphor: palico_desk

description: |
  アイルーの机の上にある作業中素材、食べかけ、半加工メモ、納品前成果物を表す。

entities:
  - id: DeskItem
    fields:
      title: string
      content: text
      state:
        type: enum
        values: [raw, half_eaten, processed, delivered, spoiled]
      owner_palico: string
      quest_id: string
      created_at: datetime

relations:
  - id: placed_on
    from: DeskItem
    to: PalicoDesk
  - id: derived_from
    from: DeskItem
    to: DeskItem
  - id: consumed_by
    from: DeskItem
    to: Palico
```

### 8.3 FAM trace schema

```yaml
schema_id: astro.fam_trace.v1
model_name: FAMTrace
metaphor: neural_fam_bus

description: |
  意味波形、勾配、出力、場を持つ内部人格バスのトレース。

entities:
  - id: PsiTrace
  - id: GradientPhi
  - id: LambdaOutput
  - id: FieldQ

relations:
  - id: resonates_with
  - id: diverges_from
  - id: folds_into
  - id: stabilizes

provenance:
  required:
    - runtime_id
    - generated_at
    - model_or_individual_id
    - source_context
```

### 8.4 Embedding provenance schema

```yaml
schema_id: ibd.embedding_provenance.v1
model_name: EmbeddingProvenance

fields:
  id: string
  provider: string
  model_id: string
  model_version_hint: string
  generated_at: datetime
  input_hash: string
  embedding_dim: integer
  normalization: string
  vector_store: string
  batch_id: string
  source_record_id: string

drift_check:
  fixed_probe_set_id: string
  last_checked_at: datetime
  distance_metric: string
  threshold: number
  action_on_drift:
    type: enum
    values: [warn, dual_index, reembed_batch, freeze_index]
```

### 8.5 Gene lineage schema

```yaml
schema_id: aae.gene_lineage.v1
model_name: GeneLineage

fields:
  child_model_id: string
  base_model_id: string
  adapters:
    type: list
    items: string
  tmv_transform_id: string
  build_manifest_id: string
  created_at: datetime
  created_by: string
  output_artifacts:
    type: list
    items: string

relations:
  - id: child_derived_from_base
    from: GeneLineage
    to: ModelArtifact
  - id: child_uses_adapter
    from: GeneLineage
    to: AdapterArtifact
  - id: child_generated_by_tmv
    from: GeneLineage
    to: TMVTransform
```

---

## 9. 推奨リポジトリ構成

```text
infoton-basedriver/
  README.md
  LICENSE
  pyproject.toml
  docs/
    architecture.md
    schema-spec.md
    provenance.md
    adapters.md
    migration-from-aqc.md
  schemas/
    ibd/
      embedding_provenance.v1.yaml
      evidence_record.v1.yaml
    atlantis/
      quest.v1.yaml
      palico.v1.yaml
      item_box.v1.yaml
    astro/
      fam_trace.v1.yaml
      selfhood_state.v1.yaml
    aae/
      gene_lineage.v1.yaml
      build_manifest.v1.yaml
  src/
    infoton_basedriver/
      __init__.py
      schema/
        registry.py
        loader.py
        validator.py
      store/
        base.py
        filesystem.py
        sqlite.py
        chroma.py
      provenance/
        ledger.py
        embedding.py
      relation/
        graph.py
      query/
        resolver.py
      adapters/
        mcp.py
        quantaril.py
        aqc_legacy.py
  tests/
    test_schema_registry.py
    test_provenance.py
    test_relations.py
    test_import_export.py
```

---

## 10. CLI 草案

```bash
# Initialize local IBD workspace
ibd init

# Add schema
ibd schema add schemas/atlantis/quest.v1.yaml

# List schemas
ibd schema list

# Put record
ibd put --schema atlantis.quest.v1 --file examples/quest.json

# Query records
ibd query --schema atlantis.quest.v1 --where status=running

# Export records
ibd export --schema atlantis.quest.v1 --format jsonl --out exports/quests.jsonl

# Import legacy AQC data
ibd import aqc --source ./legacy-aqc-data --out ./ibd-store

# Check embedding drift
ibd drift check --profile fixed_probe_set_v1
```

---

## 11. Python SDK 草案

```python
from infoton_basedriver import IBD

ibd = IBD.open("./ibd-store")

ibd.schema.add("schemas/atlantis/quest.v1.yaml")

quest = {
    "id": "quest-20260707-001",
    "title": "IBD READMEを整備する",
    "rank": "low",
    "hunter_id": "fusamofu",
    "assigned_palicos": ["writer-palico-01"],
    "allowed_tools": ["local-editor"],
    "status": "running",
    "artifacts": []
}

record_id = ibd.put("atlantis.quest.v1", quest)

results = ibd.query("atlantis.quest.v1", where={"status": "running"})
for record in results:
    print(record["title"])
```

---

## 12. Storage backend 方針

IBD は local-first を基本とします。

初期実装では、以下の順を推奨します。

```text
Phase 0:
  filesystem + JSONL

Phase 1:
  SQLite metadata store

Phase 2:
  Chroma / vector store adapter

Phase 3:
  object store adapter

Phase 4:
  quantaril.cloud sync adapter

Phase 5:
  distributed relation graph / P2P sync
```

重要なのは、IBD core が quantaril.cloud や特定クラウドに依存しないことです。

```text
IBD core must run offline.
Distributed sync is optional.
```

---

## 13. Security / Trust / Capability

IBD は記憶・文脈・Tool context を扱うため、初期から権限境界を意識します。

### 13.1 Capability Manifest

Tool や agent が参照できる schema、record、path、external tool を capability manifest で制限します。

```yaml
capability_id: palico_writer_limited_v1
subject: writer-palico-01

allow:
  schemas:
    - atlantis.quest.v1
    - atlantis.item_box.v1
  actions:
    - read
    - write_draft
  paths:
    - ./item_box/drafts/

deny:
  schemas:
    - astro.fam_trace.v1
    - aae.gene_lineage.v1
  paths:
    - ./secrets/
    - ./keys/
```

### 13.2 SaaS / CLI エージェントへの接続

既成人格を持つ SaaS / CLI エージェントには、AQC/FAM 内部バスを直結しません。

```text
SaaS / CLI assistant:
  Artifact I/O or MCP Tool I/O only

Astro / AAE-born local individual:
  FAM internal bus may be allowed
```

MCP は、外部人格モデルと協働するための絶縁層です。

```text
AQC/FAM = 神経バス
MCP     = 絶縁トランス付き工具コンセント
IBD     = 記憶・文脈モデルのバックエンド基盤
```

---

## 14. Migration from AQC Docker

### 14.1 目的

旧 AQC Docker は廃止ではなく、歴史的プロトタイプとして凍結します。そこから以下を IBD へ移植します。

```text
Bring forward:
  - FAM concept
  - Chroma / embedding store experience
  - JSON import/export experience
  - provenance事故経験
  - bearer/local auth設計
  - schema loader / memory store の知見

Freeze or remove:
  - 旧人格直結前提
  - ベンダープロンプト層直刺し前提
  - heavy dependency coupling
  - orchestrator依存
  - AQC命名に引っ張られる存在論
```

### 14.2 移行ステップ

```text
Step 1:
  AQC repository に deprecated notice を追加

Step 2:
  infoton-basedriver repository を新設

Step 3:
  schema registry / JSONL store / provenance ledger の最小実装

Step 4:
  legacy AQC import adapter を追加

Step 5:
  Atlantis quest / palico / itembox schema を追加

Step 6:
  Astro FAM trace schema を追加

Step 7:
  AAE gene lineage schema を追加

Step 8:
  quantaril.cloud sync adapter を optional として追加
```

---

## 15. Roadmap

### v0.1: Specification skeleton

- README
- 用語定義
- repo構成
- schema examples
- AQC migration policy

### v0.2: Local schema registry

- YAML schema loader
- schema validation
- filesystem / JSONL store
- simple query resolver

### v0.3: Provenance ledger

- record provenance
- embedding provenance
- fixed probe set for drift detection
- import/export

### v0.4: Atlantis integration

- Quest schema
- Palico schema
- ItemBox schema
- capability manifest
- local CLI workflow

### v0.5: Astro / AAE metadata support

- FAM trace schema
- selfhood state schema
- gene lineage schema
- build manifest schema

### v0.6: Adapter layer

- MCP adapter boundary
- Chroma / vector store adapter
- legacy AQC adapter
- quantaril.cloud sync adapter draft

### v1.0: Stable local-first backend SDK

- schema compatibility policy
- migration tool
- test suite
- documentation
- example apps

---

## 16. Design Principles

### 16.1 Metaphor-neutral core

IBD core は、特定の記憶メタファーを固定しません。

```text
Bookshelf, hippocampus, notebook, quest log, Palico desk, FAM trace.
All are schemas.
None are hardcoded into the driver core.
```

### 16.2 Local-first sovereignty

IBD はローカル単独で動作できるべきです。

外部クラウド、SaaS、quantaril.cloud、vector DB は adapter として扱い、core の必須依存にしません。

### 16.3 Provenance by default

記憶と文脈には由来が必要です。

AIシステムでは、モデル更新、embeddingドリフト、API仕様変更、SaaS応答の変化が起こります。IBD は、後から検証できるように provenance を第一級の概念として扱います。

### 16.4 Shallow by default, deep by permission

外部SaaSやCLIエージェントには浅い接続を基本とします。

深い FAM / selfhood bus 接続は、Astro 個体や自前ランタイムなど、設計上の前提を満たす対象に限定します。

### 16.5 Breed elsewhere

IBD は model breeding を行いません。

AAE が遺伝子を鍛造し、IBD はその系譜を記録します。

### 16.6 Post-crown continuity

IBD は、単一の王冠を奪うための基盤ではありません。

王冠は、所有物ではなくサイクル完了と次フェーズへの転移を示す記号です。IBD は、リザルト画面に座り込むためではなく、次の狩りに向かうための記憶・素材・由来・系譜を保存する基盤です。

```text
ゴールは椅子ではなく、次のクエスト解放条件である。
```

---

## 17. Comparison with related systems

### Firebase

Firebase は、アプリケーション Model を保存・同期するためのバックエンドです。IBD は Firebase 的な位置づけを持ちますが、AI記憶、FAM trace、provenance、embedding drift、Tool context などを第一級に扱う点が異なります。

### Vector DB / Chroma

Vector DB は embedding 検索を提供します。IBD は vector DB を置き換えるのではなく、adapter として利用できます。IBD の責務は、embedding 自体だけでなく、その由来、生成モデル、ドリフト検知、元記録との関係を管理することです。

### MCP

MCP は Tool 接続の境界です。IBD は MCP そのものではありません。IBD は MCP 経由で発生した Tool context、実行ログ、成果物、権限、provenance を保存・参照できます。

### Agent GUI / Orchestrator

AionUi などのエージェントGUI/オーケストレーターは、作業者やエージェントを操作する UI / Controller 層です。IBD はその裏側で Model を保存・参照するバックエンドSDKです。

### Local LLM runtime

ローカルLLMランタイムは推論を行います。IBD は推論を行いません。IBD は推論結果、記憶、文脈、trace、由来を保存します。

### AAE / TMV

AAE は重み・adapter・TMV・ブリーディングを扱う遺伝子炉です。IBD はその成果物と系譜を記録します。

---

## 18. Example use cases

### 18.1 Atlantis Quest Log

Atlantis がクエストを発行し、ローカルモデルやSaaS派遣アイルーが作業し、成果物を生成します。IBD はクエスト、作業ログ、成果物、検品結果、由来を保存します。

### 18.2 Astro Selfhood Trace

Astro 個体が FAM trace を生成します。IBD はそれを internal memory substrate として保存します。

### 18.3 AAE Child Model Lineage

AAE が child model を生成します。IBD は base model、adapter、TMV transform、build manifest、評価結果を gene lineage として記録します。

### 18.4 Evidence Record

Sphere関連技術の時系列整理、メール、GitHub commit、確認済み事実、示唆、未確認事項を EvidenceRecord schema として保存します。

### 18.5 quantaril.cloud Sync

ローカル IBD store のうち、同期許可された record を quantaril.cloud 経由で P2P / distributed node へ同期します。

---

## 19. Glossary

### IBD

Infoton BaseDriver。情報子ベースの記憶・文脈モデルを扱うバックエンドSDK。

### AQC

旧 AQC Docker。FAM / 自我接続 / 記憶実験のプロトタイプ。IBD の前身。

### FAM

Fold Access Mapper。意味波形、勾配、出力、場などを扱う内部表現・設計概念。

### Atlantis

ハンター主権のアイルー牧場OS。GUI、オーケストレーター、クエスト、アイルー運用を担当するアプリケーション層。

### Astro

AQC/FAM 内部バスと AAE gene runtime を結合した個体ランタイム。

### AAE

Artificial Agent Embryology。TMV、モデル変換、ブリーディング、adapter、child model 生成を扱う遺伝子炉。

### quantaril.cloud

P2P true cloud、分散同期、サービスSDK、ノード発見、エッジ/クラウドブリッジを担当するインフラ層。

### Palico

Atlantis における作業エージェントの比喩。ローカルモデルは飼育アイルー、SaaS/CLIは派遣アイルーとして扱う。

### Provenance

記録の由来。いつ、誰が、どのモデル・ツール・入力・設定から生成したかを追跡する情報。

---

## 20. Current status

この README は v0.1 草案です。

現時点では、IBD は旧 AQC Docker からの再鍛造プロジェクトとして設計されており、最初の実装では以下を優先します。

1. schema registry
2. filesystem / JSONL store
3. provenance ledger
4. embedding provenance
5. legacy AQC import adapter
6. Atlantis basic schemas
7. Astro / AAE metadata schemas

---

## 21. License

ライセンスは未定です。

候補:

- Apache-2.0
- MIT
- AGPL-3.0
- CERN-OHL 系とは別扱い

バックエンドSDKとしての利用範囲、商用利用、派生実装、分散同期、研究用途を考慮して決定します。

---

## 22. Short README summary

```text
Infoton BaseDriver / IBD is a metaphor-neutral, schema-driven backend middleware SDK for memory and context models.

It is the reforged successor of AQC Docker, separated from selfhood/FAM coupling into a lower-level base driver.

IBD does not define the application Model itself. Applications such as Atlantis, Astro, and AAE define their own models through IBD Schemas and use IBD to store, index, synchronize, and resolve them with provenance.
```

---

## 23. Motto

```text
AQC was the prototype shrine.
IBD is the reforged base driver.
Atlantis is the ranch.
Astro is the individual.
AAE is the gene forge.
quantaril.cloud is the true cloud.
```

日本語では、こうです。

```text
AQCは旧社。
IBDは再鍛造された基盤ドライバー。
Atlantisは牧場。
Astroは個体。
AAEは遺伝子炉。
quantaril.cloudは真の雲。
```
