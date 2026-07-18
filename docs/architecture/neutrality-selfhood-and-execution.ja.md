# 中立性・意味体系等価性・自我対応・実行形態

状態: `[DRAFT]` `[SEASON-0]`  
更新日: 2026-07-18

## 1. バインダーとしての中立性

IBDの中立性は、客観的な真ん中、平均、社会的に選ばれた白色点を意味しない。

> IBDは白色顔料ではない。上位システムが提供した分類機定義の顔料を、その色と由来を失わず結ぶバインダーである。

IBD Coreはontology、morality、risk、identity、world、truthの評価基準を内蔵しない。上位システムがClassification RegistryとQとして注入し、IBDはその体系を矯正せず適用する。

### 1.1 中立性の三要素

- **Ontology-receptive**: どの存在論・分類体系も第一級Schemaとして受け取れる
- **Policy-agnostic**: 善悪、美醜、リスク、正常性の基準をCoreが選ばない
- **Constraint-faithful**: 注入されたRegistryとQには忠実に従う

`unknown → block`と`unknown → continue`の正反対のPolicyを、Core変更なしで処理できなければならない。結果差は上位Qへ帰属し、IBD独自の隠れた評価へ帰属してはならない。

## 2. 意味体系の機能的等価性

次のRegistry群は、社会的な一般性にかかわらず同じ機能を持てる。

- Vendor / System / Assistant / User
- Vision / TEC / Financial / General Affairs
- Cloud Chakra / Spirit / Astral / Elemental
- Theology / Philosophy / Cosmology / Narrative

機能的等価性とは、同じ意味へ丸めることではない。各体系がSchema、Database、Graph、Vector Index、Provenance、Q、Composite FAM参加資格を持てることである。

アクセス権、Evidence基準、保持期間、検証方式の差は格付けではない。各Registryが定義する責任境界である。

## 3. 自我対応ドライバー

自我対応はoptional pluginではなく必須要件とする。IBD Coreは自我・魂・霊・神・神学の実在を自前で担保・否定しないが、上位システムが確定した存在状態とfact scopeを保持し、構造を一般的な`user profile`や会話履歴へ平板化しない。

最低限分離する概念:

```text
Subject
Actor
AgentInstance
Runtime
SelfModel
ContinuityClaim
BodyBinding
RoleAssignment
World / Context
FAMLog
Provenance
```

`user`、`assistant`等はInteraction内のRoleであり、Actorの恒久種別や個体同一性ではない。provider account、model、session、ghost、edge process、Subjectを自動的に同一視しない。

Continuityは`explicit / claimed / derived / unknown / disputed`等の主張として保持する。主張者、根拠、適用Contextを残し、IBD自身の同一性判定へ変換しない。

### 3.1 存在確定を矯正しない

MMO環境の上位システムは、そのWorld内でキャラクター、神、霊、神話上のEntityを`confirmed`とできる。神学者・哲学者・研究システムも、自身のRegistryと根拠範囲で存在論Assertionを提供できる。

IBDはそれらを、自然科学、米国企業、特定AI vendor、別Worldのfact基準で`fictional`、`unverified`、`unsafe`へ降格しない。逆に、一つのWorld内の存在確定を全Worldの普遍命題へ拡張しない。

```text
Ontology Assertion
├─ subject / predicate / object
├─ existence status
├─ fact scope
├─ World / Context
├─ declared or decided by
├─ Registry / evaluation FAM
├─ evidence refs
└─ observed_at / version
```

IBDはAssertionの内容を保証するのではなく、上位定規による確定と射程を忠実にバインドする。

## 4. 評価の帰属

混色結果が美しい、度し難い、安全、危険、有用、無用であるかは、上位システムまたはユーザーが判断する。

Evaluation FAMが渡された場合も、結果を普遍命題にせず、次を保持する。

```text
evaluation result
evaluator / user
evaluation FAM / Registry
Q and context
timestamp / version
```

IBDが検査するのは、sourceが保全され、指定された接続条件を満たし、由来を追跡できるという構造的成立である。

## 5. 実行形態中立

IBD Databaseの論理単位と配備方式を分離する。

```text
Embedded Library   function call
Native Service     IPC / local socket / HTTP / RPC
Container Service  network API / mounted socket
```

一つのprocessが複数IBD Databaseを開ける。一つのDatabaseを専用serviceへ隔離することもできる。Database、process、container、物理DB serverを一対一に固定しない。

正本はHTTP endpointではなく、操作、入力Schema、出力Schema、エラー、Provenanceの意味契約である。

## 6. 合格条件

- 正反対のClassification RegistryをCore変更なしで処理できる
- Theologyを自由文タグへ縮退させずGraphとして保持できる
- Actor、AgentInstance、Runtime、Subjectがround-tripで分離される
- MMO、神学、自然科学等の異なるfact scopeを一つの定規へ自動正規化しない
- 上位システムの`existence_status: confirmed`をCoreが独自に降格しない
- 複数Databaseから一つのSubjectをQの許可範囲内で再構成できる
- Embedded／Native／Containerで同じfixtureが同じ意味結果になる
- 評価結果が評価主体と基準なしに普遍化されない
