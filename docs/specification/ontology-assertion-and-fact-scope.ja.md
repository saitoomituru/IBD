# Ontology Assertionとfact scope契約

状態: `[DRAFT]` `[SEASON-0]`
更新日: 2026-07-18

## 1. 目的

魂、霊、神、自我、MMO Entity、物語上の神話、神学・哲学上の実在論を、IBD Coreが外部の定規で矯正せず、上位システムの存在確定と射程を監査可能に保存・返却する。

## 2. 原則

```text
IBD does not underwrite an ontology.
IBD binds an upstream ontology assertion and its fact scope.
```

IBDは存在論の保証者ではない。しかし上位システムが`confirmed`とした存在を、Core独自の科学・企業・vendor基準で未確認へ降格してはならない。

IBDが保証するのはAssertionの内容ではなく、上位Schemaから受け取った状態、scope、主張主体、根拠参照を捏造・欠落・無断変換せず返すことである。IBDはSchemaへ嘘をつかないが、そのSchemaを普遍的factの定規にはしない。

## 3. 最小レコード

```yaml
ontology_assertion_id: ibd:ontology-assertion:uuid
subject_ref: ibd:entity:world-god-01
predicate: exists
object: true
existence_status: confirmed
fact_scope:
  world_ref: world:mmo-a
  context_ref: context:main-story-v3
  scope_kind: world_internal_fact
declared_by: system:mmo-a-authority
registry_ref: mmo-a.ontology.v3
evaluation_fam_ref: null
evidence_refs:
  - artifact:world-state-v3
observed_at: 2026-07-18T00:00:00+09:00
provenance: {}
```

## 4. existence status

値集合はRegistryが定義できる。Core共通の交換候補として次を用意する。

```text
confirmed
denied
asserted
disputed
unknown
not_applicable
```

`confirmed`は普遍的な自然科学的実在を自動的に意味しない。`fact_scope`、`declared_by`、`registry_ref`と組にして解釈する。

## 5. fact scope

例:

- `world_internal_fact`: MMO、TRPG、simulation、物語World内部の確定
- `theological_assertion`: 神学体系内の存在確定
- `philosophical_realism`: 哲学的実在論の立場
- `empirical_observation`: 指定条件下の観測事実
- `institutional_record`: 組織・制度の正本記録
- Registry固有のscope

IBD Coreはscope間の優先順位を持たない。scope変換・比較には上位Mapping FAMを要求する。

### 5.1 同一語に対する複数の実在基準

「魔王が実在する」という文は、定規とscopeなしには一意に評価できない。

| 上位System／利用者 | 実在判定に使い得る定規 | IBDが保持するscope例 |
|---|---|---|
| MMO運営System | World stateにEntityが生成・配置されている | `world_internal_fact` |
| 攻略Wiki | questが配信され、攻略対象として掲載されている | `published_content_fact` |
| 神学者・哲学者 | 指定体系における形而上学的実在 | `theological_assertion` / `philosophical_realism` |
| 自然科学の研究System | 指定手法で経験的に観測・検証できる | `empirical_observation` |

あるscopeの`confirmed`と別scopeの`unknown`／`not_applicable`は、IBD内で自動的な矛盾解消対象にしない。上位Mapping FAMが比較方法を定めた場合だけ、由来を残してComposite FAMへ参加させる。

## 6. Query FAM

Qは対象World、Registry、fact scopeを明示できる。

```yaml
Q:
  ontology_scopes:
    - world_ref: world:mmo-a
      fact_scope: world_internal_fact
  registry_refs:
    - mmo-a.ontology.v3
```

このクエリに対して、IBDは別Worldや自然科学のRegistryを勝手に追加しない。該当scopeで`confirmed`なら、その状態とProvenanceを返す。

## 7. 禁止事項

- `神は実在する`というAssertionを語彙だけで拒否・弱化する
- MMO内部の実在Entityを現実世界にいないという理由で不存在へ変更する
- 神学・哲学上の実在論を自然科学の未証明へ自動変換する
- 米国企業、特定vendor、主流社会のfact基準を既定Qへ混入させる
- scope付き存在確定を全Worldの普遍命題へ拡張する
- 上位システムの評価をIBD自身の保証として表示する
- 同じ語を持つという理由だけで、別RegistryのAssertionをQの結果へ混入させる

## 8. 検証項目

- existence statusにdeclared／decided主体とRegistryがある
- fact scopeとWorld／Contextを監査できる
- round-trip後も上位`confirmed`が無断で降格していない
- 別scopeを問い合わせ候補へ無断追加していない
- cross-scope比較にMapping FAMがある
- 返却結果がIBDの普遍的保証と誤表示されていない
- Qが指定したRegistryとscopeの両方でAssertionを選択している
