# Neo4j Vector／Embedding周辺ライブラリー調査

状態: `[RESEARCH]` `[SEASON-0]` `[OWNERSHIP-OPEN]`  
観測日: 2026-07-18  
主対象: Neo4j 2026.06、埋め込み実行系、類似検索、再順位付け、検索評価

## 1. 調査範囲と結論

この文書は第三者製品・ライブラリーの調査であり、FAMスプリッター、分類機、Registry拡張の実装仕様ではない。FAMスプリッターは別プロジェクトへ分離する可能性を残し、どのリポジトリーが埋め込み生成前の分類・分割を所有するかは未決とする。

調査結果は次のとおりである。

- Neo4jは埋め込みを生成しなくても、アプリケーションや別サービスが生成したvectorを保存・検索できる。
- Neo4j 2026.06はnode／relationshipのvector index、Cypher 25 `SEARCH`、索引内filter、HNSW設定、scalar／binary量子化を備える。IBDの候補発見実験には十分な機能範囲である。
- 埋め込み生成はNeo4j GenAI Pluginへ固定されない。Sentence Transformers、Text Embeddings Inference、FastEmbed、Infinity、Ollama、llama.cpp等を同じ比較面へ置ける。
- 検索器の比較にはFaissのexact searchを正解集合の基準にし、Neo4j、hnswlib、USearch等のANN結果をRecallで測る構成が扱いやすい。
- 製品互換性は「同じ次元数」や「同じmodel名」だけでは成立しない。入力template、query／document task、tokenizer、pooling、正規化、切り詰め、次元短縮、量子化、runtime revisionまで含む生成pipelineの一致が必要である。
- どの分類を混ぜるか、何をfactとするか、どの候補集合を探索するかはこの調査の対象外であり、上位システムまたは将来のFAMスプリッター側の契約で決める。

したがってPhase 0の次の一手は、製品採用ではなく、同一の人工評価集合と同一の生成済みvectorを使った相互比較である。

## 2. Neo4jのvector機能

Neo4jの[Vector indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)による2026.06時点の要点を示す。

| 項目 | 公式仕様の要約 | 調査上の意味 |
|---|---|---|
| Edition | Vector indexはCommunity／Enterpriseの両方で使用可能 | Communityを最小検証候補にできる |
| vector property | `LIST<INTEGER \| FLOAT>`を索引化可能 | 外部engineの出力をdriver経由で投入できる |
| native `VECTOR` | 2025.10導入。保存にはEnterprise／Auraのblock formatが必要 | Community比較ではlistを使う |
| entity | nodeとrelationship | FAMの物理表現をnodeだけに固定しない |
| dimension | `1..4096`、明示指定推奨 | 4096次元以下の候補modelをそのまま比較可能 |
| similarity | `cosine`／`euclidean`、既定`cosine` | engine側の正規化・metricと揃える必要がある |
| filter | 2026.01から追加propertyによる索引内filter | 論理範囲を絞ったANNの挙動を検証できる |
| provider | Cypher 25では自動選択、現行は`vector-2026.06` | Neo4j更新時の再現性項目になる |
| state | `POPULATING`から`ONLINE`へ遷移 | 計測前のhealth checkが必要 |

### 2.1 検索APIとfilter

Cypher 25では[`SEARCH`](https://neo4j.com/docs/cypher-manual/current/clauses/search/)が推奨面である。`db.index.vector.queryNodes`と`db.index.vector.queryRelationships`は2026.04でdeprecatedになったため、新規の比較コードは`SEARCH`を基準にする。

`SEARCH`内の`WHERE`は条件を満たす候補が`LIMIT`件見つかるまで索引内で探索する。一方、通常の`MATCH ... WHERE`はANN結果へのpost-filterになり、要求件数より少なくなる場合がある。2026.06では索引内filterの`IN`も使用できる。

このfilterは候補集合の絞り込み機能であって、FAMスプリッターや分類機ではない。また、共有索引をアクセス制御境界として採用できることも意味しない。

### 2.2 HNSW、量子化、検索拡張

| 設定 | 範囲／既定 | 状態・用途 |
|---|---|---|
| `vector.hnsw.m` | `1..512`／`16` | graph接続数と構築costの調整 |
| `vector.hnsw.ef_construction` | `1..3200`／`100` | 構築costとindex品質の調整 |
| `vector.quantization.type` | `none`／`scalar`／`binary`、既定`scalar` | `binary`はPreview |
| `vector.default_search_expansion_factor` | `1.0..10000.0` | 2026.06 Preview。候補を元vectorで再評価 |

旧`vector.quantization.enabled`は2026.06でdeprecatedである。これらは意味契約ではなく、recall、latency、memoryの調整値として実測する。

### 2.3 scoreとmemory

Neo4jのscoreは`0.0..1.0`だが、異なる検索sourceの生scoreを直接比較できるとは限らない。vector、full-text、構造embedding等を組み合わせる場合はsourceごとのrankを維持し、RRF等のfusionを別工程で比較する。

[Vector index memory configuration](https://neo4j.com/docs/operations-manual/current/performance/vector-index-memory-configuration/)によると、Lucene vector indexはNeo4j page cacheではなくOS filesystem cacheを使う。restart直後のcold状態とwarm状態を分けて測定する必要がある。Raspberry Pi等のedge適合性は、vectorだけでなくNeo4j heap、page cache、OS cache、埋め込みengine、再index時間を合算しなければ判断できない。

## 3. Neo4j側の埋め込み生成面

### 3.1 GenAI Plugin

[Neo4j GenAI Plugin](https://neo4j.com/docs/genai/plugin/current/)の`ai.text.embed`／`ai.text.embedBatch`は、CypherからOpenAI、Azure OpenAI、Google Vertex AI、Amazon Bedrock Titanを呼び出せる。利用可能providerは`CALL ai.text.embed.providers()`で実環境から確認する。旧`genai.vector.encode`系は2025.11でdeprecatedである。

これはserver-side生成を簡潔にする選択肢だが、IBDの必須依存にはしない。外部API、credential、networkを必要とする構成と、offline／edge構成を分けて比較する。

### 3.2 GraphRAG PythonとGDS

[Neo4j GraphRAG Python API](https://neo4j.com/docs/neo4j-graphrag-python/current/api.html)はSentence Transformer、Ollama、OpenAI、Azure OpenAI、Vertex AI、Mistral、Bedrock、custom実装等のadapterを持つ。これはNeo4j server内のGenAI Pluginとは別のapplication-side製品面である。

[Graph Data Scienceのnode embeddings](https://neo4j.com/docs/graph-data-science/current/machine-learning/node-embeddings/)は、FastRP、GraphSAGE、Node2Vec、HashGNN等でgraph topologyをvector化する。文章のsemantic embeddingとは信号が違うため、同一scoreへ暗黙合算せず、別retrieval runとして比較する。

## 4. 互換埋め込み・再順位付け実行系

ここでいう「互換」は、生成したvectorをNeo4jへ保存できるという意味である。各製品間のvectorが相互交換可能という意味ではない。

| 候補 | 形態 | 主な機能 | 向く比較track | repository license観測 | 注意点 |
|---|---|---|---|---|---|
| [Sentence Transformers](https://sbert.net/) | Python library | dense／sparse embedding、CrossEncoder、cosine・dot・L2等 | 最小reference実装、研究、model検証 | [Apache-2.0](https://github.com/huggingface/sentence-transformers/blob/main/LICENSE) | export後もpooling・normalizeを同一にする |
| [Text Embeddings Inference](https://github.com/huggingface/text-embeddings-inference) | REST／gRPC server | embedding、sequence classification／reranking、dynamic batching、telemetry | Linux CPU／GPUの独立service | [Apache-2.0](https://github.com/huggingface/text-embeddings-inference/blob/main/LICENSE) | image、model revision、runtimeを固定する |
| [FastEmbed](https://qdrant.github.io/fastembed/) | Python library | ONNX Runtime、dense／sparse／late interaction、reranker | 軽量application library、CPU／GPU | [Apache-2.0](https://github.com/qdrant/fastembed/blob/main/LICENSE) | query／passage prefixとsupported model実装を確認する |
| [Infinity](https://github.com/michaelfeil/infinity) | REST server／Python | embedding、reranking、CLIP／CLAP／ColPali、dynamic batching | multi-model service、CPU／CUDA／ROCm／MPS | [MIT](https://github.com/michaelfeil/infinity/blob/main/LICENSE) | backend差と最終更新状態を採用前に再確認する |
| [Ollama](https://docs.ollama.com/capabilities/embeddings) | local server | local embedding、batch input | macOS／Linuxの手軽なnative service、edge予備調査 | [MIT](https://github.com/ollama/ollama/blob/main/LICENSE) | `/api/embed`はL2正規化済み。`truncate`、`dimensions`、model tagを記録する |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | C／C++ library・server | GGUF embedding、pooling指定、reranking endpoint | 小型native binary、CPU／Metal／CUDA等 | [MIT](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE) | GGUF量子化、`--pooling`、build revisionで出力を識別する |
| Neo4j GenAI Plugin | Neo4j plugin | vendor API経由のserver-side embedding | Neo4j内完結経路 | 製品Edition・契約を別監査 | offline不可、providerごとの利用条件とsecret管理が必要 |

### 4.1 Sentence Transformersのbackend差

[Sentence Transformersの推論効率化資料](https://sbert.net/docs/sentence_transformer/usage/efficiency.html)はPyTorch、ONNX、OpenVINOと複数量子化構成を扱う。ただしSentence Transformers外でtransformer部分だけをONNX exportすると、通常はtoken embeddingまでしか出ず、poolingと正規化を呼出側が再現する必要がある。runtimeを交換できても、生成pipelineが自動的に同一になるわけではない。

### 4.2 service型とlibrary型

Docker、native service、application libraryのどれかへ設計を固定する根拠はまだない。

- library型はprocess内の再現性を取りやすいが、複数applicationでmodel memoryを共有しにくい。
- service型はbatching、GPU共有、observabilityをまとめやすいが、network、version deployment、認証が増える。
- Neo4j plugin型はCypherから呼びやすいが、Neo4jとprovider双方の運用条件を受ける。

Phase 0では同じ人工入力を各形態へ流し、完全一致または許容誤差、throughput、cold start、memoryを記録してから配置を決める。

## 5. 類似検索・比較器

| 候補 | 種別 | 役割 | repository license観測 | 注意点 |
|---|---|---|---|---|
| [Faiss](https://github.com/facebookresearch/faiss) | dense vector library | `IndexFlatIP`／`IndexFlatL2`をexact基準にし、各種ANNも比較 | [MIT](https://github.com/facebookresearch/faiss/blob/main/LICENSE) | cosineは正規化＋inner productで構成する |
| [hnswlib](https://github.com/nmslib/hnswlib) | 軽量HNSW library | Neo4j Lucene HNSWに対する独立baseline | [Apache-2.0](https://github.com/nmslib/hnswlib/blob/master/LICENSE) | Python filter callbackはGILの影響を受ける |
| [USearch](https://github.com/unum-cloud/usearch) | multi-language HNSW library | f16／i8／binary、memory map、edge候補の比較 | [Apache-2.0](https://github.com/unum-cloud/usearch/blob/main/LICENSE) | projectの自己benchmarkは自環境で再検証する |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | SQLite extension | Raspberry Pi／WASMを含むportableな小規模exact比較 | [Apache-2.0／MIT](https://github.com/asg017/sqlite-vec) | pre-v1で破壊的変更の可能性が明記されている |
| NumPy／SciPy | exact数値計算 | 小fixtureのcosine／dot／L2の独立検算 | 各projectを別監査 | 大規模ANN用途ではない |

Faiss exact searchを近傍の正解集合とし、Neo4j・hnswlib・USearch等について`Recall@k`を取る。これにより、埋め込みmodelの品質とANN indexの近似誤差を分離できる。

## 6. 再順位付けと評価

vector検索だけで最終品質を決めず、第一段の候補発見と第二段のrerankingを分けて測る。

- Sentence Transformers `CrossEncoder`、TEI、FastEmbed、Infinity、llama.cppはreranker候補を提供する。
- [MTEB](https://github.com/embeddings-benchmark/mteb)は多言語・多taskのembedding評価とcustom task作成に使える。
- [BEIR](https://github.com/beir-cellar/beir)は異種domainの情報検索benchmarkとして一般性能の確認に使える。
- [ranx](https://github.com/AmenRa/ranx)はPrecision、Recall、MRR、MAP、NDCG、統計検定、RRF等のrun比較・fusionに使える。

MTEB／BEIRの公開scoreだけで採用を決めない。IBD／FAMで必要な日本語、記号`ψ`・`∇φ`・`λ`・`Q`、短文／長文、似た語彙で別分類の負例を含む人工qrelsを別に作る。ranx自身もclassifier評価用ではないため、FAMスプリッターの分類精度は今回の検索評価へ混ぜない。

## 7. model familyの調査候補

次は採用決定ではなく、local／multilingual比較集合の候補である。

| 候補 | 公式記載から見た特徴 | 調査理由 |
|---|---|---|
| [EmbeddingGemma](https://ai.google.dev/gemma/docs/embeddinggemma) | 約308M、100超の言語、2K context、Matryoshka次元 | edgeと日本語の候補 |
| [Qwen3-Embedding](https://github.com/QwenLM/Qwen3-Embedding) | 0.6B／4B／8B、100超の言語、instruction-aware、対応reranker | 複数size・次元の比較候補 |
| [BGE-M3／FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) | multilingual、dense／sparse／multi-vector、長文対応 | hybrid・late interaction研究候補 |
| [multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct) | 多言語、instructionを使うSentence Transformers／TEI対応model | 既存runtime間の再現比較候補 |

表のlicenseは2026-07-18に各repositoryで観測した識別子であり、依存packageや配布物を含む法務監査ではない。runtimeのOSS licenseとmodel weightのlicense・利用条件も別物である。導入候補を絞った段階で、model card、依存関係、配布条件、商用／再配布条件を個別に監査する。

## 8. 製品間受け渡しで失ってはいけない情報

これはIBD Registryの確定schemaではなく、比較結果を偽らないための観測項目である。どのプロジェクトが所有するかは未決とする。

- model identifier、weight／repository revision、tokenizer revision
- runtime、backend、container／binary revision
- query／document／passageのtask instructionと入力template
- text前処理、文字正規化、field順序、chunking
- pooling、L2 normalization、similarity metric
- 出力dimension、Matryoshka短縮、coordinate type
- float精度、model／output量子化、GGUF variant
- max token、truncationの有無と方向
- batch設定のうち出力へ影響するもの
- 入力hash、出力vector hashまたは許容誤差、生成日時

例として、OllamaはembeddingをL2正規化して返し、Sentence TransformersのONNX exportは構成によってpoolingを含まない。ここを記録せず、両者を「同じmodel」とだけ表示すると互換性を過大にプレゼンする。

## 9. Phase 0の比較track案

### Track A: application library

Sentence Transformers＋PyTorchをreferenceとし、ONNX／OpenVINO、FastEmbedとの出力差と性能を測る。

### Track B: 独立embedding service

TEIとInfinityをLinux CPU／GPU候補として比較する。Dockerは配布形態の一つとして扱い、native実行可能性も別列にする。

### Track C: local／edge

Ollama、llama.cpp、EmbeddingGemma等をmacOS／ARM64から始め、Raspberry Pi実機は後続trackとする。SQLite系比較器はNeo4jの代替決定ではなく、小規模なexact／portable基準として使う。

### Track D: Neo4j-native

GenAI PluginとGDSをoptional trackとする。外部生成vectorの投入経路が成立していることを前提に、Neo4j内生成を必須にはしない。

## 10. 比較実験案

1. 機密を含まない人工の日本語FAM風document、query、qrelsを作る。スプリッターは実装せず、評価用分類を手で固定する。
2. 同一model・同一pipelineで生成したvectorをFaiss exact、Neo4j、hnswlib、USearchへ渡す。
3. embedding差とANN差を分離して、`Recall@k`、`NDCG@k`、`MRR`を測る。
4. Neo4jでは専用index、索引内filter、post-filterの件数・latency差を測る。
5. rerankerなし／あり、RRF等のfusionあり／なしを別runにする。
6. embedding latency、query p50／p95、throughput、cold／warm、RAM、disk、index build時間を測る。
7. 同一revisionの再実行でvector hashまたは数値誤差を比較する。
8. macOS native、Linux native、Docker、将来のARM64実機を別環境として記録する。

## 11. 今回決めないこと

- FAMスプリッターの配置、API、schema、分類model
- IBDがembedding metadataの正本を所有するか
- 本番Neo4j採用とCommunity／Enterprise／Auraの選択
- embedding／reranking modelの採用
- Docker、native service、application libraryの優先順位
- 神学、ゲーム、財務、vision、System／Assistant／user等の分類体系
- 共有索引をsecurity boundaryにできるか

この調査は選択肢と比較条件を揃えるところまでであり、FAMの存在論・分類基準を第三者libraryへ委譲するものではない。
