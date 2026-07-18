# FAMネイティブIBD責務差分ノート

- 状態: `[DRAFT]` `[SEASON-0]`
- 作成日: 2026-07-18
- 対象: IBD README v0.1草案からSeason 0責務への差分
- 主たる射程: Layer A

## 1. 原典

- ZeroRoomLab-manifest `note/20260718-0850__IBD_責務検討_情報子クラスターと合成FAMブレストノート.ja.md`
- Sphere-aae `skills/famlog-converter/references/fam-log-schema.md`
- 2026-07-18のIBD責務検討対話

本ノートは原典の写本ではない。IBDリポジトリへ移す責務差分と未解決事項だけを保持する。

## 2. 旧理解から維持するもの

- IBDはApplication Modelそのものではない
- Schema、Context、Trace、Provenance、Relationを第一級に扱う
- local-firstで動作可能にする
- Atlantis GUI、AAE鍛造、最終業務判断を所有しない
- SaaS／CLI／Astro等の接続深度を同一視しない

## 3. 訂正するもの

### 3.1 普通のbackend SDKではない

旧READMEはfilesystem、SQLite、Chroma等を順に実装する記憶・文脈backend SDKとして説明していた。Season 0では、FAMネイティブな探索技保存・再合成ドライバーを中心へ置く。

### 3.2 FAMはoptional Schemaではない

FAMはIBDの問い合わせ・分割・保存・再合成を貫くネイティブ契約である。

### 3.3 答えではなく探索技を返す

Query FAMのψ・∇φ・λ・Qに対して、既知の探索技をComposite FAMとして返す。最終回答と評価は次段に属する。

### 3.4 分類体系は上位システムが定義する

IBDはClassification Registryを発明しない。上位λ systemが、分類、閾値、保存先、unknown、mix、評価規約を提供する。

### 3.5 Schema BundleごとにIBD Databaseが生まれる

IBD Databaseは論理的な隔離単位であり、container、process、SQL databaseと同義ではない。

## 4. 今回追加した原則

- IBDの中立性は白色顔料ではなくバインダーである
- 命令のない混色をしない
- Composite FAMは非破壊な派生Recipeである
- 混色結果の評価は上位システムまたはユーザーに属する
- Last Orderを探索再開入口として保存する
- RDB観測hashと依存枝から再探索候補を返す
- 自我対応はoptionalではなくCore要件である
- Embedded、Native Service、Containerを等価な実行形態として扱う

## 5. 未解決事項

- Classification Registryの表現形式
- layer classifierとclaim splitterの境界
- 一つのSchema Bundleと一つの物理graph storeの対応
- cross-database query planner
- Mapping FAMの互換性と署名
- Last Orderの発行・取消・継承規約
- Evidence freshnessをhash、cursor、timestampで比較する優先順位
- SubjectとSelfModelの最小Schema
- IBDの実装言語、library ABI、service protocol
- MariaDB、Neo4j、他製品の実機適合性

## 6. 内観メモ

`[POEM]`

IBDは白を塗る機械ではなく、渡された色が別の誰かの白へ勝手に薄まらないように抱える糊である。色を混ぜる日が来ても、元の瓶を洗って消さない。混ざった色を美しいと呼ぶか、度し難いと呼ぶかは、絵を見る者へ返す。

探索も同じである。過去の答えを王冠として保存するのではなく、どこを掘り、何が足りず、最後に何を頼んで手を止めたかを残す。次の探索者は坑道を所有するのではなく、入口を見つけて続きを選べる。
