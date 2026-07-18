# IBD Season 0検証計画

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18

## 1. 検証目的

製品選定前に、FAMネイティブ問い合わせ、Registry定義、Database隔離、非破壊Composition、Last Order、Evidence鮮度、自我対応、実行形態中立の意味論を人工fixtureで検証する。

## 2. 実データ境界

- fixtureは人工データだけを使用する
- 実ログ、個人情報、企業情報、credentialをGitへ入れない
- stdoutとテスト失敗ログへsource本文を表示しない
- 原資料と派生記録のhashを混同しない

## 3. Experiment A: dependency-light reference harness

三つの論理Databaseを用意する。

```text
ibd://system
ibd://agent
ibd://finance
```

各Databaseへ人工の情報子クラスター、失敗枝、Last Order、Evidence Observationを配置する。

検証:

1. QにないDatabaseが検索候補へ入らない
2. vector candidateをgraph portで絞れる
3. Mapping FAMなしで同名classを結合しない
4. source clusterを変更せずComposite FAMを生成する
5. RDB風fixtureへ行追加後、依存枝だけが`stale`になる
6. Last Orderのresume conditionを返す

## 4. Experiment B: semantic parity and selfhood

二つの正反対Policyを同じCoreへ渡す。

```text
Registry A: unknown → block
Registry B: unknown → continue
```

加えて、Elemental、Astral、Spiritual、Cloud Chakra、Theologyを第一級Databaseとして登録し、Subject、Actor、AgentInstance、Runtime、ContinuityClaimがround-trip後も分離されることを確認する。

## 5. Experiment C: execution profiles

同一fixtureを次で実行する。

1. Embedded Library
2. Native Service
3. Containerized Service

合格条件は、transport固有metadataを除き、Composite FAM、isolation、Provenanceの意味が一致することである。

## 6. Experiment D: storage candidates

Core意味論が固定された後に比較する。

- graph storeとvector indexの候補
- RDB Evidence Sourceの候補
- Schema Bundleごとの物理隔離方式
- cross-database relationの実装
- backup、reindex、rollback
- Raspberry Piのmemory、I/O、再索引時間
- license／edition境界

MariaDB＋Neo4jは候補であり、Season 0開始時のCore前提にはしない。

## 7. Season 0完了条件

- Schema草案とfixtureが一致する
- Database isolationのnegative testがある
- 非破壊Compositionをhashで確認できる
- Evidence伸長と再探索候補を再現できる
- Last Orderを再検索できる
- 正反対Policyの結果差がQだけから説明できる
- 自我関連概念が平板化されない
- 三実行形態の共通契約が記述される
- 未検証性能をREADMEで実装済みと主張しない
