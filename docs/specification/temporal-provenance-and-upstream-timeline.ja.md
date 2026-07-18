# 実行環境時刻と上位時系列契約

状態: `[DRAFT]` `[SEASON-0]`
更新日: 2026-07-18

## 1. 目的

IBD実行環境が記録する監査時刻と、上位システム・原資料・業務・物語・カレンダーが管理する時系列を混同せず、import、export、migration、projectionを通して元の時間的意味を保持する。

## 2. 時系列の区分

### 2.1 IBD実行環境の証跡

```text
ibd_record_created_at
ibd_record_modified_at
ingested_at
imported_at
exported_at
indexed_at
projected_at
migrated_at
```

これらはIBD record、処理、adapter、runtimeの証跡であり、上位Entityが作成・変更・発生した時刻ではない。

各eventは「いつ」だけでなく、operation、target、runtime／actorを持ち、実行環境がいつ何をしたかを再構成できるようにする。

### 2.2 上位システムの時系列

```text
source_created_at / source_modified_at
occurred_at / observed_at
effective_from / effective_to
valid_from / valid_to
scheduled_for
business_period
world_timeline_position
```

roleと意味は上位Schemaが定義する。IBDは一般的な業務時刻へ強制変換しない。

### 2.3 実時間でない上位時間

上位時系列はtimestampである必要がない。

```text
MMO暦12年403日
world tick 88421
turn 17
物語第3章・戴冠後
2026年度第2四半期
契約工程 day 45
```

これらは上位World／Schema内の論理座標である。明示的なMapping FAMなしに、IBD実行環境のtimestamp、UTC、Gregorian calendarへ変換しない。

## 3. importとexport

importは新しいIBD監査eventを追加するが、原資料の作成・変更時刻を上書きしない。

```text
source_created_at = 2020-04-01T09:00:00+09:00
imported_at       = 2026-07-18T10:30:00+09:00
```

exportも同様に`exported_at`を追加する。exportしたことだけを根拠に、`source_modified_at`、`occurred_at`、`scheduled_for`を変更しない。

## 4. 未来時刻

`scheduled_for`、契約予定、MMO event予定、予測、暦上の将来日等は、実行環境の現在時刻より未来でも正当な値になり得る。未来であることだけを異常、clock skew、未検証へ変換しない。

clock skew検査を適用する場合は、対象roleと許容範囲を上位Qが明示する。

## 5. timestamp表現

解析可能な時刻はRFC 3339形式のoffset付き値を使用し、IANA timezoneを別に保持する。offsetだけをtimezone名とみなさない。

```yaml
raw_value: "2020/04/01 09:00 JST"
normalized_value: "2020-04-01T09:00:00+09:00"
zone_id: Asia/Tokyo
utc_offset: "+09:00"
timezone_status: explicit
precision: second
calendar_system: gregorian
authority_ref: source:legacy-system
```

timezoneがない場合:

```yaml
raw_value: "2020-04-01 09:00"
normalized_value: null
zone_id: null
utc_offset: null
timezone_status: unknown
```

実行環境のtimezoneを黙って補わない。上位システムが補完した場合は`derived`とし、規則と主体をProvenanceへ残す。

## 6. 論理時間座標

```yaml
coordinate_kind: world_day
coordinate_system: mmo-a.calendar.v2
raw_value: "第12年403日"
value: 403
unit: world_day
era_ref: era:mmo-a-year-12
world_ref: world:mmo-a
authority_ref: system:mmo-a
real_time_mapping_status: not_mapped
```

`value`は数値、文字列、構造体のいずれでもよい。順序比較、加減算、周期、実時間対応の可否はcoordinate systemまたは上位Mapping FAMが定義する。

## 7. 変更時刻

次を別々に扱う。

- IBD envelopeが変わった時刻
- source recordが変わったと上位が宣言した時刻
- domain Entityの意味内容が変わった時刻
- projection／indexだけが再生成された時刻
- timestampの解釈だけを訂正した時刻

projection、reindex、export、metadata補修だけで上位`modified_at`を更新しない。

## 8. append-only監査event

IBD実行証跡は原則としてeventを追加する。

```yaml
audit_event:
  timeline_kind: ibd_meta
  event_type: imported
  operation: import_record
  target_ref: ibd:record:example
  occurred_at:
    normalized_value: "2026-07-18T10:30:00+09:00"
    zone_id: Asia/Tokyo
    utc_offset: "+09:00"
    timezone_status: execution_environment
  runtime_ref: ibd:runtime:local
  clock_source: system_clock
```

過去eventを最新時刻で上書きしない。時計訂正が必要な場合はcorrection eventと対象event refを追加する。

### 8.1 エッジ環境の未初期化・未校正時計

GPS、RTC、5G／network time等の時刻authorityを取得する前に、wall clockがUnix epoch付近を返す環境を想定する。

```yaml
event_id: ibd:audit-event:boot-unsynchronized
timeline_kind: ibd_meta
event_type: record_created
operation: initialize_runtime_record
target_ref: ibd:runtime:edge-01
occurred_at:
  raw_value: "1970-01-01T00:00:00+00:00"
  normalized_value: "1970-01-01T00:00:00+00:00"
  zone_id: Etc/UTC
  utc_offset: "+00:00"
  timezone_status: execution_environment
  clock_state: uninitialized
  clock_reading_status: placeholder
  calibrated: false
  calibration_evidence_status: unavailable
  calibration_authority_ref: null
  clock_initialization_basis: unix_epoch_default
boot_id: boot:edge-01:1
monotonic_ns: 1824000
sequence: 1
```

この時刻は監査eventのraw wall clockとして保存するが、上位データの日付、実時間の発生順、Evidence鮮度へ使用しない。同期前eventの局所順序には`boot_id + monotonic_ns + sequence`を使う。

未校正時計はepochを返すとは限らない。次も初期値になり得る。

- マザーボード／RTCの製造日
- ベンダー出荷日
- firmware／imageのbuild日
- last-known timeまたは固定factory default

したがって値が2024年等のもっともらしい日付でも、NTP、GPS、PTP、5G／network time、署名済み時刻等の校正証跡をSystemから取得できなければ`calibrated: false`とする。同期済みであることを日時の見た目から推測しない。ログの取得不能は、同期していないことの完全な証明ではないが、IBDが校正済み時刻として使用する根拠もない。この場合は`calibration_evidence_status: unavailable`を保持する。

同期後は次のようなeventを追加する。

```yaml
event_type: clock_synchronized
operation: synchronize_clock
clock_authority: gps
calibrated: true
calibration_evidence_status: verified
calibration_authority_ref: gps:edge-01
anchor:
  boot_id: boot:edge-01:1
  monotonic_ns: 9824000
  synchronized_instant: "2026-07-18T10:00:00+09:00"
  uncertainty_ms: 25
```

未初期化・未校正eventを同期後時刻で破壊的に書き換えない。必要ならcorrection relationと不確かさを追加する。`calibrated: true`への遷移は、校正authority、同期ログ／anchor、対象boot、monotonic位置、不確かさを参照できるeventとして記録する。

`1970-01-01`という値だけで未初期化と断定しない。実際の1970年資料もあり得るため、`clock_state`、platform状態、time authority、boot情報を根拠に判定する。

### 8.2 時計プロファイル

IBDはeventのwall clock値だけでなく、Systemが時計を成立させる前提と観測可能な校正metadataを別の時計プロファイルとして保持する。

```yaml
profile_id: ibd:clock-profile:edge-01
runtime_ref: ibd:runtime:edge-01
calibration_policy_ref: system:edge-01:clock-policy
reported_resolution_ns: 1000000
sources:
  - source_kind: ntp_server
    server_name: ntp.internal.example
    last_success_at: null
    evidence_status: unavailable
  - source_kind: gps_receiver
    device_ref: gps:edge-01
    last_received_at: "2026-07-18T10:00:00+09:00"
    evidence_status: verified
  - source_kind: carrier_network_time
    carrier_ref: carrier:sim-01
  - source_kind: radio_controlled_clock
    device_ref: radio-clock:edge-01
  - source_kind: fm_time_signal
    station_ref: fm:station-01
  - source_kind: rtc_module
    device_ref: rtc:edge-01
    model: example-rtc
```

sourceは構成済みであることと、当該event時点で受信・校正に成功していることを分ける。NTP server名が設定されているだけで`calibrated: true`にしない。GPS最終受信、NTP最終成功、carrier応答、電波時計受信、RTC battery／oscillator状態等は、取得できた範囲と取得主体をProvenance付きで保持する。

### 8.3 信憑性と上位システムの粒度判断

IBDは時計の採否基準を内蔵しない。次のような条件は上位システムがQuery FAMのQとして与える。

```yaml
Q:
  temporal_acceptance:
    evaluation_authority_ref: system:upper:clock-policy
    required_granularity: day
    accepted_calibration_states: [calibrated, uncalibrated]
    maximum_uncertainty_ms: null
    ordering_fallback: [monotonic_ns, sequence]
```

同じ未校正wall clockでも、日単位の分類には採用し、秒単位の証跡には不採用とする上位Policyがあり得る。IBDは校正状態、source、最終受信、分解能、推定精度、不確かさを返し、どの粒度で十分かを裁定しない。

RTC moduleだけで十分な上位Systemもあれば、指定NTP serverによる校正後5分以内、GPS fix quality付き、またはcarrier／標準電波の受信後だけを採用する上位Systemもある。これらはすべてQの条件であり、IBD Coreの固定優先順位ではない。

時計metadataの信憑性は、record本文、Ontology Assertion、World内fact、探索技全体の真偽と独立である。`calibrated: false`は「そのwall clock値を校正済み実時間として立証できない」を意味し、「record内容がすべて偽」を意味しない。逆に未校正状態を隠して校正済み時刻として提示してはならない。

IBDが検査するのはmetadata内部の構造的整合である。たとえば`calibrated: true`なら参照可能な校正authorityとverified Evidenceを要求する。この検査は「その時計精度で上位factを成立させてよいか」の判断ではない。

## 9. メタ時計の提示

IBDメタ情報はQuery結果へ含められる。ただし、上位データと同じ時間軸であるかのように表示しない。

```yaml
temporal_result:
  upstream_domain:
    - role: scheduled_for
      value: "第12年403日"
      coordinate_system: mmo-a.calendar.v2
  ibd_meta:
    - event_type: imported
      occurred_at: "2026-07-18T10:30:00+09:00"
      operation: import_record
```

UI、API、exportでもnamespaceまたは`timeline_kind`を保持する。メタ時計をデータの日付として並べ替えたり、データ時系列をIBD処理履歴として表示したりしない。

## 10. Queryと返却

Query FAMのQは対象timelineとroleを指定できる。

```yaml
Q:
  temporal_scopes:
    - timeline: upstream
      roles: [occurred_at, scheduled_for]
    - timeline: ibd_audit
      roles: [imported_at]
```

IBDは指定されていないtimelineを同じ`date`へ畳まない。並べ替え、鮮度判定、再探索判定に使用したtime roleを結果へ残す。

## 11. 検証項目

- import時刻がsource created／modified時刻を上書きしていない
- export、projection、reindexで上位modified時刻が変わっていない
- 未来のscheduled timeを異常値へ変換していない
- game day、turn、tick等をMapping FAMなしに実時間へ変換していない
- offset、IANA timezone、timezone statusを混同していない
- timezone不明値へ実行環境timezoneを黙って補っていない
- raw valueとnormalized valueを両方追跡できる
- clock correctionが過去eventの破壊的更新になっていない
- 未初期化wall clockが上位データ時刻や鮮度判定へ流用されていない
- 製造日・出荷日・build日等のもっともらしい初期値も、校正証跡なしに確定時刻へ昇格していない
- NTP等の同期ログを取得できない場合に`calibrated: false`と証跡状態を提示できる
- NTP server名、GPS最終受信、carrier／標準電波／FM／RTC等の時計source metadataを保持できる
- 時計信憑性の採否と必要粒度をIBDではなく上位Qが決めている
- 時計の不確かさをrecord本文全体の偽判定へ伝播していない
- 同期前eventの順序をboot ID、monotonic clock、sequenceで復元できる
- `1970-01-01`という値だけで全データをsentinel扱いしていない
- Query結果が使用したtimelineとroleを監査できる
- メタ時計と上位時系列が明示的に区別されている
- IBD監査eventから、いつ、何を、どの対象へ行ったかを再構成できる
