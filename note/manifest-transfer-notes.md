# ZeroRoomLab-manifest からの転送メモ

作成日: 2026-07-13
更新日: 2026-07-18
状態: `[TRANSFERRED]`（初期責務）／`[SUPERSEDED-IN-PART]`（Season 0で再定義）

## 1. 受け取った方針

IBD では、以下の観点を基盤として固定しています。

- IBD はアプリケーション Model そのものではなく、Schema を通じて記憶・文脈を管理する基盤である
- Context / Trace / Provenance / Relation を第一級の概念として扱う
- AQC は旧プロトタイプであり、IBD へ責務を再定義する

## 2. 参照元

- [ZeroRoomLab-manifest のハブ文書](../../../ZeroRoomLab-manifest/ZeroRoomLab-manifest/note/20260713-1531__Quantaril%20Cloud%20Atlantis%E4%B8%96%E4%BB%A3%20%E2%80%95%20%E6%96%87%E6%9B%B8%E4%BD%93%E7%B3%BB%E3%83%9E%E3%83%83%E3%83%97(%E3%83%8F%E3%83%96).md)
- [ZeroRoomLab-manifest の運用モデル](../../../ZeroRoomLab-manifest/ZeroRoomLab-manifest/docs/operations/manifest-operating-model.ja.md)

## 3. 運用上の扱い

この文書は、IBD リポジトリ向けに再構成した要約です。原典の更新は源リポジトリ側で管理し、ここでは参照・要約・運用ルールとして扱います。

## 4. Season 0での更新

2026-07-18の責務検討により、IBDは一般的な記憶・文脈backend SDKから、FAMで問い合わせ、探索技を情報子クラスターとして隔離保存し、Composite FAMとして非破壊再合成するFAMネイティブドライバーへ再定義中です。

現在の差分と未解決事項は、[FAMネイティブIBD責務差分ノート](season-0/20260718__fam-native-ibd-responsibility-delta.ja.md)を参照してください。本メモの初期方針は歴史的な受領記録として残し、Season 0の正本候補を上書きしません。
