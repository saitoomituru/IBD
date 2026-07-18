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

Season 0の実行可能なreference harnessは`experiments/season0/`に置く。Python標準ライブラリと人工fixtureだけを使い、production resolverや物理DB選定の証拠とはみなさない。

```bash
python3 experiments/season0/reference_harness.py
python3 -m unittest discover -s tests -p 'test_season0_*.py'
```

CLIは実データ本文を表示せず、選択Database、cluster件数、stale件数、Last Order件数、Ontology Assertion件数、source mutationだけを要約する。

時系列fixtureでは、2020年のsource作成、2021年のsource変更、2026年のimport／export、2027年の予定、MMO暦第12年403日、timezone不明のlegacy時刻を同時に保持する。IBDメタ時計と上位時系列のnamespace分離、未来予定の保持、論理時間の非変換を検査する。

エッジ時計fixtureでは、GPS同期前の`1970-01-01`、ベンダー出荷日を初期値とするもっともらしい2024年時刻、boot ID、monotonic clock、sequenceと、GPS同期後のanchor eventを同時に保持する。時計プロファイルにはNTP server、GPS最終受信、carrier network time、標準電波、FM、RTC moduleを並置する。NTP等の同期ログを取得できない時刻を`calibrated: false`とし、epoch値や出荷日を上位データ時刻へ流用せず、同期後も旧eventを上書きしないことを検査する。必要粒度の採否は上位Qの責務とし、未校正時計を本文全体の偽判定へ伝播させない。

## 4. Experiment B: semantic parity and selfhood

二つの正反対Policyを同じCoreへ渡す。

```text
Registry A: unknown → block
Registry B: unknown → continue
```

加えて、Elemental、Astral、Spiritual、Cloud Chakra、Theologyを第一級Databaseとして登録し、Subject、Actor、AgentInstance、Runtime、ContinuityClaimがround-trip後も分離されることを確認する。

MMO World内の神Entityを`existence_status: confirmed`、神学Registry内の神を`theological_assertion`、実験Registryを`empirical_observation`として別scopeに置く。IBD Coreが相互に降格・普遍化せず、Qで指定したscopeの状態をそのまま返すことを確認する。

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
- World／神学／哲学／経験観測の存在確定が外部定規で降格・普遍化されない
- IBDメタ時計とsource／domain／schedule／logical timelineが混ざらない
- 三実行形態の共通契約が記述される
- 未検証性能をREADMEで実装済みと主張しない
