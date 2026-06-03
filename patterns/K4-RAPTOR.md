# K4 — RAPTOR

> Index the corpus offline as a tree of recursively-built summaries, so that retrieval can pull from whichever level of abstraction the query needs — a specific leaf fact, a section-level summary, or a document-level synthesis.

**Also Known As:** Recursive Abstractive Processing for Tree-Organized Retrieval, Hierarchical RAG, Summary-Tree RAG

**Classification:** Category II — Knowledge · Band II-A Retrieval · a *structured-index* pattern — an alternative offline index to K1's flat vector store.

---

## Intent

Answer queries that vary in scope — from a precise fact to a broad theme — by indexing the corpus as a multi-level summary tree and retrieving from the level of abstraction the query requires.

## Motivation

K1 Vanilla RAG retrieves chunks at a *single fixed granularity*: whatever the chunk size was set to. That forces an unwinnable trade-off. Small chunks answer precise factual queries well but cannot answer "what is this document about" — no single small chunk carries the gist. Large chunks carry the gist but dilute precise lookups and waste context. Any one chunk size is wrong for some of the queries the system will receive.

The deeper problem: **queries arrive at different altitudes.** "What dosage did the trial use?" needs a leaf fact. "How does Chapter 4 differ from Chapter 7?" needs two section-level summaries. "What is the book's central argument?" needs a root-level synthesis. A flat index has only one altitude.

RAPTOR builds an index that has all of them. It clusters the leaf chunks, summarises each cluster, clusters those summaries, summarises again, and recurses until a single root remains. The result is a tree: leaves are the original chunks, internal nodes are progressively more abstract summaries. Retrieval then matches the query to the level that fits it. The geometric reason this works: in K1's flat vector space (mechanism 1), query vectors for different altitudes of question land near embeddings of corresponding abstraction — a specific fact query is closest to leaf embeddings, a thematic query is closest to document-level summary embeddings. The RAPTOR tree populates the similarity space at every altitude, so retrieval by nearest-neighbour finds the level the query needs. The tree gives K1's missing dimension — *abstraction* — and that is RAPTOR's unique contribution.

This is a different problem from K3 GraphRAG. K3 preserves *relationships* between entities; K4 preserves *levels of abstraction* over content. A graph is not a tree of summaries, and a relationship query is not an abstraction-level query. They are two patterns.

## Applicability

Use RAPTOR when:

- the corpus has natural hierarchical structure — books, legal codes, technical manuals, long reports;
- the query stream is *diverse in scope*, mixing pinpoint facts with broad thematic questions;
- a single chunk size has been observed to fail one end of that range.

Do not use it when:

- all queries are at the same altitude (just tune K1's chunk size);
- the corpus is flat and unstructured;
- the corpus changes constantly — the tree must be rebuilt.

## Decision Criteria

K4 is right when the query stream spans abstraction levels K1's single chunk size cannot serve.

**1. Test K1 at two chunk sizes.** Run real queries at small chunks (256–512 tokens — good for precise facts) and large chunks (1024+ tokens — good for thematic). If neither size serves both ends of the stream, K4 earns its cost.

**2. Profile the query mix.** Sample real queries. What share need:
- Pinpoint facts (leaf nodes)?
- Section-level summaries (mid-level nodes)?
- Document-level synthesis (high-level / root nodes)?

If at least ~20% of queries fall into each band, K4's multi-level index pays off.

**3. Corpus structure check.** Does the corpus have *natural* hierarchy — books, legal codes, technical manuals, long reports? RAPTOR works much better on naturally hierarchical content than on flat heterogeneous corpora.

**4. Build cost.** Roughly 20–40% additional LLM summarisation calls on top of K1's chunk count, spread across tree levels. A one-off cost, but not free.

**5. Update tolerance.** The tree rebuilds when the corpus changes. Stable corpora (finalised reports, published codebases) suit K4; living corpora favour K1.

**Quick test — K4 is the right pattern when:**

- queries vary in scope across at least two abstraction levels, *and*
- K1 at any single chunk size fails one end of that range, *and*
- the corpus has natural hierarchy worth indexing, *and*
- the corpus is stable enough that the recursive build amortises.

If queries are relational rather than abstraction-varying, use **K3 GraphRAG**. If the working set is small enough, **K9 Long Context** synthesises across levels without a pre-built tree. If only a few queries fail, **K2 Query Transformation** may close the gap more cheaply.

## Structure

```
OFFLINE — tree construction (once per corpus version)

  Leaf chunks ──▶ Cluster ──▶ Summarise each cluster ──▶ Summary nodes
        ▲                                                     │
        └──────────────── recurse until one root ─────────────┘

  Result:            Root (whole-corpus synthesis)
                    /        |        \
              Summary     Summary     Summary       (mid-level)
              /  |  \      /  |  \     /  |  \
            chunk chunk chunk ...                   (leaves = original chunks)

ONLINE — query

  Query ──▶ retrieve across tree levels ──▶ nodes at matching abstraction ──▶ Generator ──▶ Answer
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Corpus / leaf chunks** | the original document chunks | — $\to$ chunks | be discarded — the leaves stay in the retrievable pool alongside the summaries. |
| **Clusterer** | grouping nodes at each level | nodes $\to$ clusters | use hard clustering only — soft clusters let content relevant to several themes appear under each. |
| **Summariser** | writing a summary node per cluster | cluster $\to$ summary node | lose specific facts to gist; each summarisation level compounds the loss above it. |
| **Summary tree** | the multi-level index | leaves + summary levels $\to$ queryable tree | — |
| **Retriever** | searching across tree levels | query $\to$ nodes at the matching level | confine search to one level — a query's altitude is not known in advance. |
| **Generator (LLM)** | answering from the retrieved nodes | query + nodes $\to$ answer | — |

## Collaborations

**Offline.** The Clusterer groups the leaf chunks; the Summariser writes one summary node per cluster. Those summary nodes are themselves clustered and summarised, and the process recurses until a single root node remains. Every level is embedded and stored.

**Online.** The Retriever searches the embedded tree. Two traversal strategies exist: *collapsed-tree* search treats all nodes at all levels as one pool and retrieves the best matches regardless of level; *tree-traversal* search descends the tree level by level. Either way, a precise query surfaces leaf nodes, a broad query surfaces high-level summary nodes, and the Generator answers from whatever level was returned.

## Consequences

**Benefits**
- Serves precise and broad queries from one index — no chunk-size compromise.
- High-level nodes give whole-document and whole-section synthesis that flat retrieval cannot produce.
- The collapsed-tree strategy is simple to implement over an existing vector store.

**Costs**
- Offline build cost: many LLM summarisation calls, one per cluster at every level.
- Storage for every summary level on top of the leaves.
- Rebuild required when the corpus changes.

**Risks and failure modes**
- *Compression loss* — each summarisation level discards detail; a fact present in a leaf may not survive into the summary above it, so a query that lands at the wrong level can miss it. An additional risk: LLM summarisation is stochastic (mechanism 7). Unlike a deterministic code step, the same cluster summarised twice may produce different summaries — important for reproducibility and for diagnosing index quality regressions between builds.
- *Summary drift* — errors in a low-level summary propagate up into every summary above it.
- *Clustering quality* — poor clusters produce incoherent summaries.

## Implementation Notes

- The **collapsed-tree** retrieval strategy (search all levels as a single pool) is reported to perform well and is the simplest to build — start there.
- RAPTOR uses **soft clustering** (a node may belong to more than one cluster), which handles content that is relevant to several themes.
- Keep leaf chunks in the retrievable pool — RAPTOR augments flat retrieval, it does not replace the leaves.
- Summarisation prompt quality directly sets index quality; version and evaluate it.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring.

**Composition:** Offline recursive build — cluster, summarise, cluster the summaries, recurse — then an online search across *all* tree levels as one pool (collapsed-tree retrieval). Chains K1's Embedder, a Summariser, and a Generator.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Offline: embed leaf chunks | `LLM` | K1 Embedder |
| 2 | Offline: soft-cluster the current level | `code` | |
| 3 | Offline: summarise each cluster $\to$ new summary nodes | `LLM` | Summariser session |
| 4 | Offline: embed the new summary nodes | `LLM` | K1 Embedder |
| 5 | Offline: recurse to step 2 until one root remains | `code` | |
| 6 | Online: embed the query | `LLM` | K1 Embedder |
| 7 | Online: top-k across *all* tree levels as one pool | `code` | collapsed-tree |
| 8 | Online: generate the answer from the retrieved nodes | `LLM` | Generator |

**Skeleton:**

```
OFFLINE — build the tree:
    level = [Node(c, Embed(c)) for c in leaves]
    while len(level) > 1:
        next = []
        for cluster in soft_cluster(level):       # code
            s = Summariser(cluster)                # LLM
            next.append(Node(s, Embed(s)))         # LLM (embed)
        tree.append(next); level = next            # code

ONLINE:
    all_nodes = flatten(tree)                      # code — collapsed pool
    nodes = top_k(Embed(query), all_nodes, k=8)    # LLM (embed) + code
    return Generator(query, nodes)                  # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **K1 Embedder** | specialist text-embedding model — identical for indexing and query (as K1) | model choice is the setup | one text |
| **Summariser** | generalist — note that cluster summarisation is a structured generation task, not complex reasoning; a mid-tier model matched to the task complexity (mechanism 8) may yield comparable index quality at substantially lower build cost. Sample and measure on representative clusters before committing to a frontier model. | role: summarise this cluster into one coherent summary; preservation contract: *"preserve specific facts and named entities, not just the general gist"*; length target | a cluster of texts |
| **Generator** | main generalist | role; grounding and citation rules | retrieved nodes + the query |

**Specialist-model note.** The Embedder is a specialist (as K1). The Summariser is the quality lever for the entire index — each level summarises the level below, so summary errors compound upward through the tree. Pick a capable model and evaluate the summaries on a sample of clusters before trusting the index.

## Open-Source Implementations

- **RAPTOR** — [`github.com/parthsarthi03/raptor`](https://github.com/parthsarthi03/raptor) — the official implementation from the originating research (MIT-licensed), with a demo notebook.
- **LlamaIndex** — [`github.com/run-llama/llama_index`](https://github.com/run-llama/llama_index) — ships a RAPTOR pack implementing both collapsed-tree and tree-traversal retrieval.

## Known Uses

- The **RAPTOR** reference implementation from the originating research.
- **LlamaIndex** ships a RAPTOR pack.
- Hierarchical-retrieval deployments over books, legal codes, and long technical documentation.

## Related Patterns

- **Refines** K1 Vanilla RAG — an alternative offline index; RAPTOR's leaves *are* a K1 index, with summary levels added above.
- **Sibling of** K3 GraphRAG — both are structured offline indexes, but K3 indexes *relationships* and K4 indexes *abstraction levels*; they target different query classes and are distinct patterns.
- **Composes with** K2 Query Transformation and K5 Adaptive RAG.
- **Competes with** K9 Long Context — a large window lets the model synthesise across a document without a pre-built summary tree, at higher per-query cost.
- **Related to** K6 Context Compression — both summarise, but to opposite ends: K6 compresses live context to *save space*; K4 summarises offline to *build an index*.

## Sources

- Sarthi et al. (2024) — "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval."
- LlamaIndex RAPTOR pack documentation.
