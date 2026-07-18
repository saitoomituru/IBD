# FAMネイティブIBDアーキテクチャ

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18  
主たる射程: Layer A（工学・実装責務）

## 1. 目的

IBDを普通のSQLラッパー、単一vector DB、単一graph DB、会話履歴保存器として実装しないため、FAMネイティブな読み取り・書き込み・再合成契約を定める。

## 2. Core mapping

```text
ψ  = 状況
∇φ = 手法・探索方向
λ  = 目的・到達条件
Q  = 制約・探索範囲・証拠条件
```

Query FAMは最終回答を要求するSQL文ではない。現在の状況と目的に対して、再利用可能な探索技を発見・接続する入力契約である。

## 3. 読み取り経路

```text
Query FAM
  ↓
QからRegistry、Database、権限、Evidence条件を解決
  ↓
Databaseごとの候補集合を層・型・portで限定
  ↓
限定集合内をベクトル検索
  ↓
graph port、依存、禁止、mapping、失敗履歴を検査
  ↓
Evidence鮮度とLast Orderの再開条件を検査
  ↓
Composite FAMを派生生成
```

ベクトル類似度は候補発見に使い、Registry境界、Database isolation、graph compatibility、Qを迂回しない。

## 4. 書き込み経路

```text
FAMLog
  ↓
上位システムがClassification RegistryとRoutingを指定
  ↓
claim／branch境界へ分割
  ↓
Registry内でmulti-label分類
  ↓
情報子クラスターへ構造化
  ↓
Schema Bundleに対応するIBD Databaseへ隔離保存
  ↓
cross-database edge、Run Trace、Provenanceを保存
```

分類不能、複数候補、競合は欠損ではない。Registryの規約に従って`unclassified`、`multi-label`、`routing_required`等として保持する。

## 5. 情報子クラスター

```text
Infoton Cluster
├─ reusable FAM branch
├─ input / output ports
├─ classification labels and evidence
├─ required Evidence / Tool / Capability
├─ preconditions / stop conditions
├─ failure / refutation history
├─ source Registry / Database
├─ provenance
└─ version / compatibility
```

文章チャンクやembeddingだけを情報子クラスターと呼ばない。再利用可能な探索技として接続条件と停止条件を持つことが必要である。

## 6. Composite FAM

Composite FAMは原色を変更しない派生Recipeである。

```text
Composite FAM
= selected Infoton Clusters
+ explicit Mapping FAMs
+ assembly graph
+ Evidence bindings and freshness
+ permission / capability bindings
+ Last Orders / unresolved slots
+ provenance
```

自動的に元Databaseへ書き戻さない。繰り返し再現され、上位システムまたはユーザーが昇格を決定した場合だけ、新しい情報子クラスターまたはSchema Bundle候補とする。

## 7. 責務境界

上位システムが所有するもの:

- λとClassification Registry
- 分類語彙、評価基準、Q、Risk Policy
- Database間を混色する命令
- Composite FAMの採否、実行、評価

IBDが所有するもの:

- RegistryとSchemaの忠実な保持
- Database isolation
- ベクトル候補発見
- graph compatibility検査
- 非破壊Composite FAM
- Recipe、Run Trace、Last Order、Provenance

実行主体が所有するもの:

- Composite FAMの実行
- 外部Tool／業務操作
- 実行結果とEvidenceの返却

## 8. 不変条件

1. 命令のないDatabase横断検索・混色をしない。
2. 同名ラベルをRegistryを越えて自動的に同一視しない。
3. Composite FAM生成でsource clusterを変更しない。
4. 最終評価をIBD Coreへ混入させない。
5. 成功枝だけでなく失敗枝、反証枝、凍結枝、Last Orderを返せる。
6. Evidenceの観測時点と依存枝を追跡する。
7. source、projection、embedding、indexを同一の正本とみなさない。
8. 実行形態が変わってもQuery／Composition意味論を変えない。

## 9. 未確定事項

- port型の記述形式
- vector classifierとgraph storeの製品選定
- 一つの論理IBD Databaseを物理的に隔離する粒度
- cross-database edgeの永続化方式
- Composite FAMの署名、互換性、キャッシュ方針
- Raspberry PiとServer Advancedの性能境界
