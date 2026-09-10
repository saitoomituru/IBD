# IBD 責務境界 2026-09

状態: `[CANONICAL-CORRECTIVE]` `[SEASON-0]`
更新日: 2026-09-10

## 目的

FQuery の selector / traversal / Fold 参照境界と、SphereOS Atlantis の World / Portal / Transformer 責務が更新されたため、IBD が所有する責務と所有しない責務を再固定する。

IBD は **保存・検索・再合成の基盤**である。IBD Core は、World の真理、refFAM の優劣、Portal の必要性、人格の最終判断を決めない。

## 一文定義

> IBD は、上位 System が与えた FAM / refFAM / Registry / Fold / Q / provenance を意味改変せず保存・検索し、指定された範囲だけを Composite FAM として返す FAM-native binder / resolver である。

## 責務境界

```text
ZeroRoomLab-manifest
  共通定規・用語・責務境界

FAM / refFAM
  FAM    = fact / experience / state を含む情報構造
  refFAM = fact-free な形而上学・認識論・問い方・分類法・検証法

FQuery
  self / this
  parent / children / siblings
  prev / next       = L-axis traversal
  before / after    = mL-axis traversal
  fam_ref / Fold-scoped selector
        ↓
IBD
  storage / retrieval / graph / vector / evidence / provenance
        ↓
Composite FAM
```

## IBD が所有する

- FAM / FAMLog / OAE ref / refFAM artifact の保存・取得
- Registry / Schema Bundle / Database binding の保持
- graph / vector / RDB / file / enterprise connector への adapter
- Evidence binding、freshness、revision、hash、provenance
- Last Order の保存と再取得
- 上位 Q が指定した範囲での local retrieval
- 明示 Mapping / Access Map が与えられた場合の非破壊 Composite FAM
- source と derived projection の分離
- unknown / unavailable / unresolved の保持

## IBD が所有しない

- FQuery 文法の制定
- `self` / `this`、`prev` / `next`、`before` / `after` の意味再定義
- refFAM に fact を書き込むこと
- refFAM A と refFAM B の優劣・真偽裁定
- 異なる Fold / World / Registry の暗黙 merge
- Portal / Bridge / Transformer が必要かという上位 orchestration 判定
- ASTRO の人格・identity・continuity の制定
- AAE の model / system-call runtime の実行責務
- OAE の因果帰属を検索結果から創作すること

## refFAM の保存規則

IBD は refFAM を保存できるが、refFAM の意味契約を変更しない。

```text
ordinary FAM
  observed fact / state / experience

refFAM
  ontology / epistemology / reusable method
  fact-free
```

refFAM と fact が衝突した場合、IBD がどちらかを修正して整合させてはならない。source、scope、revision、Registry を保ったまま両方を返し、評価・修正・fork は上位 System / Observer へ返す。

## FQuery との境界

FQuery は「何を欲しいか、どの参照を辿るか」を記述する。IBD は「どこに保存されているか、どう取り出すか」を解決する。

```text
FQuery selector / traversal
        ↓ intent
IBD adapter / query planner
        ↓ storage-specific operation
Neo4j / SQLite / PostgreSQL / JDBC / ODBC / File / External System
```

FQuery selector を backend 固有 query へ変換しても、FQuery の semantic pointer を backend 都合で再定義しない。

## L / mL 保存規則

FQuery 正本に従い、次を分離して保持する。

```text
L-axis
  parent / children / siblings / prev / next
  canonical / structural topology

mL-axis
  before / after
  actual semantic-processing route
  run / revision ごとに変化し得る
```

IBD は mL runtime trace を L static topology へ上書きしない。逆に L の接続だけから実際に通った mL route を推定しない。

## Atlantis / Portal との境界

異なる Fold / World / refFAM scope の接続可否は Atlantis / 上位 orchestration の責務である。

```text
Atlantis
  boundary detection
  direct / Portal / Gate / Bottom decision
        ↓
Access Map / Transformer
        ↓
OAE / transformation receipt
        ↓
IBD
  receipt / source / result / provenance を保存
```

IBD は Portal の必要性を勝手に決めず、Portal が実行されたという receipt だけを保存・検索できる。

## 受入条件

- [ ] FQuery grammar と IBD query adapter を別 contract として扱う
- [ ] refFAM と ordinary FAM を保存時に混同しない
- [ ] L topology と mL runtime trace を別 relation / record として保持できる
- [ ] cross-Fold を similarity だけで自動 merge しない
- [ ] Portal / Transformer receipt を source 改変なしで保存できる
- [ ] backend 変更後も FAM identity / revision / provenance を保持する
- [ ] IBD の検索成功を上位 World の採用・真実へ昇格しない

## 正本参照

- ZeroRoomLab-manifest: `docs/theory/sphere-context-dimension-os.ja.md`
- ZeroRoomLab-manifest: `docs/theory/sphere-context-sdk-contract.ja.md`
- ZeroRoomLab-manifest: `docs/theory/ibd-fam-native-binder.ja.md`
- FQuery: `docs/specification/fquery-selector-traversal-normalization.ja.md`
- FQuery: `docs/specification/fam-reference-boundary.ja.md`
- SphereOS-Atlantis: World / Portal / causal gate contract

実装 status は各 repository の current revision と test receipt を優先し、本書だけで未実装機能を実装済みへ昇格しない。
