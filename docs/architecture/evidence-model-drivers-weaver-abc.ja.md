# IBD Evidence Model Drivers：SELECT / MATCH / FIT

状態：`SEASON-0 / DESIGN-CONTRACT / NOT IMPLEMENTED`

学派の理論正本：[Manifest / Weaver A-B-CとOAE](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/weaver-abc-evidence-scope-and-oae.ja.md)

## 抽象データモデルとDriver
`SELECT / MATCH / FIT` は「一致を得る」という共通抽象モデルの異なるEvidence投影。**同一モデルでも実装は同一ではない**。FQueryの `Q(self).file.fit` 等、ファイル名patternを探索するPluginと、IBDのトポロジカル情報子モデルDriverは独立した実装境界を持つ。抽象操作名だけで互換性・同一アルゴリズム・完了状態を宣言しない。相互接続には能力・入力型・比較射程・出力Evidence型のbindingが必要。

| Driver / Weaver対応案 | 比較領域 | 主な結果 |
|---|---|---|
| SELECT / A | SQL等の離散値・キー・条件 | source/time/scopeに拘束されたFact |
| MATCH / B | Fold背景に拘束された言語ベクトル近傍・方向 | contextual Evidence |
| FIT / C | 情報子clusterとトポロジカルgraph構造 | structural Evidence |

これは学派の研究モデル。Weaverの三水準とIBD Driverの対応は独自の工学仮説であり、標準的なDB分類ではない。MATCHのembedding媒体選定はInfinite Core側のcapability resolutionに委譲し、IBDに固定しない（FQuery #39とQ宣言仕様を参照）。FITのgraph表現、保存、構造一致条件は未設計・未実装ならそのように扱う。

## エビデンス契約
Model Driverは比較の種類、対象/source revision、World、時間、scope、Observer/rule ref、結果、unknown/uncertainty、provenanceを保持できる設計とする。具体的なSchemaは既存IBD/FAM境界と照合して確定し、ここで新APIを作ったことにはしない。異種型は単一similarity/validへ潰さない。

### Non-promotion fixtures
1. SELECT: `sensor S at time T = 2℃`。河川全体の代表温度や普遍熱収支は**非証明**。
2. FIT: 本末転倒とマルコ2:27の目的/手段関係を限定的に構造対応評価。文献同一起源を**非証明**。
3. SELECTで異なる原典が取得されてもFITは未評価または独立判定、falseを自動付与しない。
4. OAEが未評価なら`not-evaluated`とし`false`へ縮約しない。

## OAE / FQueryとの境界
IBDは証拠を型付きで取得・参照する。OAEは指定Observerとruleの評価射程を管理し、出典の確定や構造の同一性を無断で横断しない。FQueryは操作・経路を宣言し、Core自体はOAE verdictの発行主体にならない。独立Driverの実装完了を主張しない。

受入条件：型の区別、再現できるsource/scope、4種negative fixture、モデルとPluginの非同一性、未実装状態の明記。
