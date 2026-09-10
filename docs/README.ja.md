# IBD Docs Index

IBD の仕様・アーキテクチャ・研究文書を、2026-09 時点の FAM / FQuery / SphereOS 責務境界から辿る索引です。

## まず読む

1. [2026-09 責務境界](./architecture/responsibility-boundary-2026-09.ja.md)
2. [Classification Registry と Routing](./specification/classification-registry-and-routing.ja.md)
3. [Query FAM と Composite FAM](./specification/fam-query-and-composition.ja.md)
4. [IBDSDK module contract](./specification/ibd-sdk-module-contracts.ja.md)
5. [Ontology Assertion と fact scope](./specification/ontology-assertion-and-fact-scope.ja.md)
6. [Evidence freshness と Last Order](./specification/evidence-freshness-and-last-order.ja.md)
7. [Log Horizon と FAM JSON pointer](./specification/log-horizon-and-fam-json-pointers.ja.md)
8. [Temporal provenance と upstream timeline](./specification/temporal-provenance-and-upstream-timeline.ja.md)

## 横断責務

```text
FQuery     = selector / traversal / query intent
Atlantis   = World / Fold orchestration / Portal
ASTRO      = Actor / persona / identity / continuity
AAE        = model / system-call execution runtime
IBD        = storage / retrieval / evidence / provenance
```

IBD は FQuery grammar、World の真理、Portal 判定、人格 identity、model runtime を所有しません。

## 文書状態

Season 0 の既存文書は履歴として保持します。2026-09 の corrective 文書と矛盾する古い表現がある場合、履歴を silent rewrite せず、corrective 文書を優先し、Issue で migration を追跡します。
