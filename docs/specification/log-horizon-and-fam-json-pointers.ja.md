# Log HorizonとFAM JSONP観測projection契約

状態: `[DRAFT]` `[SEASON-0]`

制定日: 2026-08-03

命名正本: ZeroRoomLab-manifest [Log Horizon](https://github.com/saitoomituru/ZeroRoomLab-manifest/blob/main/docs/theory/log-horizon.ja.md)

## 1. IBDでの責務

IBDはLog Horizonの先にある完全source状態を保有・再現・証明する装置ではない。Observerが取得できた部分投影と、
取得条件、未観測範囲、再取得手続、由来を保存する。

```text
complete source state
  ↓ Log Horizon
observed projection
  ↓ FAM JSONP pointer／nest
OAE ref + Run Trace + Evidence
  ↓
IBD Store／Database／Storage Binding
```

Run Traceは技術的な実行経路、OAEはObserver、Agency、Effectを保持するContext管理単位であり、同義ではない。

## 2. FAM JSONP

FAMの正本表現はJSONとする。本プロジェクト固有のFAM JSONPは、JSON-LDの`@id`等による意味参照だけでなく、
次へ再帰的に接続できるpointer機構を持つ。

- inlineまたは外部の実vector／embedding artifact
- embedding、変換、検索、再評価等のprocedure
- source FAM、Composite FAM、別WorldのFAM
- API、MCP、Tool、Skill、POSIX／physical port
- 外部source、Schema、artifact、content hash
- traffic／sensor／execution receipt
- OAE、Evidence、Last Order

JSON-LDは必要に応じて生成できる相互運用projectionであり、FAM JSONP正本や実行pointerを置換しない。

## 3. 観測projection envelope

次は説明用の最小構造であり、stable machine schemaの確定ではない。

```json
{
  "fam_id": "fam://observation/log-horizon/001",
  "source_ref": "source://model-or-sensor/001",
  "observation_boundary": {
    "kind": "log_horizon",
    "complete_source_observed": false,
    "observer_ref": "observer://instance/001",
    "execution_envelope_ref": "envelope://runtime/001"
  },
  "grad_phi": [
    {
      "kind": "embedding_projection",
      "pointer": {
        "pointer_type": "vector",
        "target": "vector://embedding/001",
        "content_hash": "sha256:..."
      },
      "procedure_ref": "procedure://embedding/profile-a",
      "source_input_hash": "sha256:..."
    }
  ],
  "elemental_observations": [
    {
      "pointer_type": "traffic_receipt",
      "target": "receipt://api/001",
      "content_hash": "sha256:..."
    }
  ],
  "oae_refs": [
    "oae://observation/001"
  ],
  "unresolved": [
    "provider_internal_state",
    "sensor_out_of_range"
  ],
  "last_order_refs": []
}
```

## 4. Elemental事実とAstral評価

API traffic、HTTP status、syscall result、sensor reading、latency、token、実請求額はElemental observationとして
保存する。「便利」「腐った」「メシウマ」「この財布ではメシまず」は、主体、目的`λ`、制約`Q`を持つAstral truthとして
別FAMへ保存し、Elemental eventをpointerで参照する。

主観を削除してAI自身の評価を無色の事実へ偽装せず、Astral評価を全World共通のElemental判決にも変換しない。

## 5. Horizon別の最低metadata

| 境界 | 最低限保持するもの |
| --- | --- |
| embedding | source input hash、model／profile ref、dimension、metric、vector／artifact ref、receipt |
| LLM／network | request／response hash、公開model ID、capability、authority、traffic、status、clock |
| API／MCP／Tool | Schema／Skill hash、operation、request／response、error、latency、cost receipt |
| physical sensor | instrument ID、range、resolution、calibration、raw reading、clock quality |
| FAM／OAE | source FAM ref、pointer path、Observer、World、unresolved、Last Order |

hashは取得したartifactのbyte identityを支えるが、Horizonの先にあるsource全体、内容の真理、完全性、authorityを
単独では証明しない。

## 6. 再帰pointerの停止条件

FAM JSONP resolverは、少なくとも次を明示する。

```json
{
  "resolution_policy": {
    "max_depth": 8,
    "cycle_action": "last_order",
    "unresolved_action": "retain_pointer",
    "authority_required": true,
    "side_effect_default": "deny"
  }
}
```

循環、権限不足、hash不一致、source到達不能、sensor範囲外、provider内部状態の非公開を、架空の成功または対象不存在へ
変換しない。解決できた枝だけをreceipt付きで追加し、source FAMを変更しない。

## 7. 非主張

- IBDが物理event horizon、Hawking radiation、Higgs粒子を観測するとは主張しない
- FAM JSONP、OAE共通schema、Log Horizon validatorが実装済みとは主張しない
- embedding、traffic、sensor reading、Akasha DB cacheから完全sourceを再構成できるとは主張しない
- `unknown`を`fresh`、`false`、`nonexistent`へ自動変換しない

## 8. 関連

- [Query FAMとComposite FAM契約](fam-query-and-composition.ja.md)
- [Evidence鮮度とLast Order契約](evidence-freshness-and-last-order.ja.md)
- [実行環境時刻と上位時系列契約](temporal-provenance-and-upstream-timeline.ja.md)
- [存在論Assertionとfact scope契約](ontology-assertion-and-fact-scope.ja.md)
