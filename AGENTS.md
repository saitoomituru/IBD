# AGENTS.md — IBD

このファイルは、AIエージェントがIBDリポジトリを編集する際のリポジトリ横断コンテキストを定める。

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
