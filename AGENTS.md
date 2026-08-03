# AGENTS.md — IBD

このファイルは、AIエージェントがIBDリポジトリを編集する際のリポジトリ横断コンテキストを定める。

## 実在UXと実在証明（必須）

> 実在の証明はしない。実在を感じさせることだけをやる。

README、技術文書、研究ノート、UX文言を編集するときは、体験を本気で設計する責務と、その中身の哲学的・科学的・医学的真偽をIBD Coreが確定することを分離する。`証明しない`を`体験を適当に作る`へ弱めず、強い実在感を`普遍的な実在証明`へ昇格させない。誰が、どのWorld、Registry、fact scopeで何を確定または主張したかを保持するというIBDの責務へ接続する。

## 読者・AIの非裁定と研究広報保護（必須）

技術はclaim、code、receipt、再現条件、試験境界に基づいて具体的に検証する。量子、霊、巫女、FAM、神話、
独自理論、壮大な構想、強い自己効力感、挑発的なmarketing表現だけから、開発者の正気度、人格、病理、悪意、
詐欺性、違法性を推定しない。agent自身のアクセス不足は`UNKNOWN`であり、対象Worldの不存在や未実施を意味しない。

本人の一次当事者宣言、公開証拠、独立検証、法令・契約・権利・security上の開示境界を別フィールドとして保持する。
公開範囲を超える法務確認、専門家意見、専用再現環境、第三者監査を求める場合、要求する側が法務専門家を継続的に
起用できる費用、技術検証費、必要な権限、安全な開示経路を先に提示する。資金支援は開示の購入や開示義務を意味しない。

大胆な研究目標、いわゆるビッグマウス、自己効力感PRを、研究広報、作品表現、採用、ロビー活動、資金調達の正当な
レジスターとして保持する。完了事実、一次当事者宣言、研究仮説、将来目標、marketing、資金調達、未確認事項へ型分けし、
技術文書の留保をREADME冒頭へ逆流させて声量を奪わない。

正本: ZeroRoomLab-manifest
[読者・AIの非裁定と追加検証コスト責任](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/2c68eb63672e68e600518ba46679542b0914757b/docs/operations/reader-ai-non-adjudication-and-verification-cost.ja.md)

## Log Horizon命名規則（必須）

`Log Horizon`は、物理粒子Observerをsystem-levelへ拡張したとき、仮想粒子とFAMを構成するOAEが、
embedding、全体観測不能なnetwork／model、物理sensor等の先にある完全source状態を直接観測できない、
情報子単位のログの地平を指す。物理学上のevent horizon、Hawking radiation、Higgs粒子、未知の物理粒子の
観測claimへ変換しない。

IBDは、Horizonを越えて取得できたFAM JSONP pointer、vector、traffic、sensor reading、hash、procedure／instrument
profile、OAE ref、freshness、Last Orderを保持する。取得不能を不存在へ変換せず、部分投影をsource全体へ昇格させない。
命名正本はZeroRoomLab-manifestの
[Log Horizon](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/2c68eb63672e68e600518ba46679542b0914757b/docs/theory/log-horizon.ja.md)とする。

## 日本語既定レジスタ（必須）

- 人間向けのREADME、技術文書、研究ノート、commit、PR、issue、code comment、CLI help、検証報告、引継ぎ票は、日本語化によって意味・互換性を壊さない限り日本語を既定とする
- commit subjectとbodyは原則として日本語で書く。形式が必要な場合は、例として`[docs] season-0: FAMネイティブ契約を追加`のように機械可読prefixとscopeを残し、説明を日本語にする
- code identifier、JSON Schema key、protocol field、external API、vendor固有名、安定path、機械可読tokenは、翻訳で互換性・検索性・参照安定性を壊す場合は原語を保持する
- ユーザーが英語成果物を指定した場合、既存の英語正本を編集する場合、外部互換境界が英語を要求する場合だけ英語を出力する
- この規則は前向きに適用し、公開済みGit履歴のrewriteや安定識別子・pathの一括renameを行わない
- 必要な英語技術語を日本語文中に残す場合も、意味、責務、境界、未検証事項は日本語で説明する

## ZeroRoomLab言語レジスタ（必読）

README、技術文書、翻訳、主張表現を編集する前に、ZeroRoomLab-manifestの[コーディングAI向け日本語意訳レジスタ](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/operations/coding-ai-japanese-paraphrase-register.ja.md)を読み、背景ベクトルを取得すること。英語出力は明示がない限りen-USとし、単語の直訳ではなく、日本語原文の意図・読み手の責務・事実強度をen-USで同じ働きをする表現へ写像する。

マニフェストの規約は横断的な背景と説明レジスターを提供する。IBD固有のスキーマ、テスト、ディレクトリ内の指示がある場合は、それらを実装上の優先規約として併読すること。


## MAGIポジショントーク監査（必読）

計画提案、状態評価、README／技術文書の主張変更、component間の優先順位決定、
複数repositoryへ波及する変更の前に、ZeroRoomLab-manifestの
[AGENTS.md §0.4](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/AGENTS.md)、
[Atlantis-MAGISDK 0.2.1](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/atlantis-magi-sdk-0.2.1.ja.md)、
[Context定規・因果・OAE横断監査規約](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/operations/context-ruler-and-causality-audit.ja.md)
を読むこと。

過去の同時点OAEを参照できない場合は`historical-oae-unavailable`とLast Orderを返し、commit、log、
artifactから当時のObserver、Agency role、Intentを遡及生成しない。現在の解釈は現在時刻の
Interpretation OAEとし、反実仮想は元World／元Instance Ghostを変えない7D Fold branchへ分離する。

Declared Position、Position-talk Risk、媒体とclaim scope、外部定規の出所を分離し、
現在のrepository、cwd、vendor、binary実装、一般的な線形roadmapを暗黙のmainへ置かない。
重大なstatus・責務・公開主張・横断変更では、監査結果とUser確認が必要な項目を記録し、
計画をUserへ返してから実行する。
