# K3 — GraphRAG

> Index the corpus offline as a graph of entities and the relationships between them; answer queries by traversing that graph or synthesising over its community summaries, rather than by retrieving isolated chunks.

**Also Known As:** Graph Retrieval, Entity Graph RAG, Knowledge-Graph RAG, Microsoft GraphRAG

**Classification:** Category II — Knowledge · Band II-A Retrieval · a *structured-index* pattern — an alternative offline index to K1's flat vector store.

---

## Intent

Answer queries that require connecting information across many documents — multi-hop relationship questions and whole-corpus synthesis — by indexing the corpus as a graph of entities and relationships instead of a flat set of chunks.

## Motivation

K1 Vanilla RAG retrieves the handful of chunks most similar to the query. That works when the answer sits in a few passages. It fails *structurally* — not for lack of tuning — on two classes of query:

- **Multi-hop, relational queries.** "Which suppliers does our highest-risk vendor depend on?" The answer is not contained in any single chunk; it is a *path* through several documents. Similarity retrieval has no notion of a path. More precisely, K1's retrieval is a nearest-neighbour search in a learned bilinear similarity space (mechanism 1). A multi-hop answer corresponds to a path through many nodes of that space, not a single point — the search has no vocabulary for paths. Retrieving more chunks does not help, because the answer is not *in* the chunks individually — it is in the relationships between them, which a flat index discards.
- **Global synthesis queries.** "What are the main themes across these 500 incident reports?" No chunk contains the answer; it is a property of the corpus as a whole. Top-k retrieval returns k chunks and is structurally blind to the other 495.

The fix is not better retrieval but a better *index*. GraphRAG builds one. It extracts entities and the relationships among them into a graph, detects communities of densely connected entities, and summarises each community. A query then either traverses entity relationships (multi-hop) or reads and synthesises over community summaries (global). The graph preserves exactly the structure — paths and whole-corpus organisation — that K1's flat vector store throws away. That preserved structure is GraphRAG's unique contribution.

## Applicability

Use GraphRAG when:

- the corpus is large and rich in entities and relationships;
- queries trace relationships ("how is X connected to Y") or ask for corpus-wide themes;
- the domain is relational by nature — intelligence analysis, legal discovery, scientific literature, fraud and risk networks.

Do not use it when:

- queries are local factual lookups — K1 is cheaper and just as good;
- the corpus is small, or changes constantly (graph construction is expensive to repeat);
- entity extraction would be unreliable on the corpus (noisy or highly informal text).

## Decision Criteria

K3 is right when queries need relationship-tracing or whole-corpus synthesis *and* the corpus has the entity structure to support a useful graph.

**1. Sample-test K1 on the hard queries.** Pick 20 real queries skewed toward multi-hop ("how does X connect to Y?") and global ("what are the main themes across this corpus?") types. Run K1. If K1 handles them, you do not need K3 — the cost of the offline graph build is wasted.

**2. Score entity density.** Is the corpus rich in named entities and relationships? Legal cases, scientific literature, intelligence reports, financial filings — yes. Plain narrative or unstructured prose — questionable. Without entity density, graph construction is expensive *and* the graph is sparse.

**3. Cost the offline build.** Realistic ceiling: one extraction LLM call per chunk + one summary LLM call per detected community. For tens of thousands of chunks this is minutes-to-hours of compute on a capable model. Confirm the budget before committing.

**4. Update frequency.** If the corpus changes daily, the rebuild cost is prohibitive — K1 is cheaper to refresh. K3 fits stable or slowly-changing corpora.

**5. Hybrid, not replacement.** Most production deployments run K1 alongside K3 — K1 for local lookups, K3 for graph queries. Plan the **router** (which queries take which path), not just the index.

**Quick test — K3 is the right addition when:**

- a meaningful share of real queries demand multi-hop or global synthesis K1 cannot serve, *and*
- the corpus is rich in entities and relationships, *and*
- the build cost (extractions $\times$ chunks + community summaries) is affordable on the corpus's update cycle, *and*
- you accept running K1 alongside K3, not just replacing K1.

If queries vary in *abstraction level* rather than relationship complexity, use **K4 RAPTOR**. If the corpus is small enough to load, **K9 Long Context** can give synthesis without the graph build, at higher per-call cost. If only a few outlier queries fail, add **K2 Query Transformation** first — it is cheaper than a full graph build.

## Structure

```
OFFLINE — graph construction (expensive; once per corpus version)

  Corpus ──▶ Entity extraction ──▶ Relationship extraction ──▶ Entity graph
                                                                  │
                                              Community detection ◀┘
                                                      │
                                              Community summaries

ONLINE — query

  Query ──▶ Router ──┬─ local  ─▶ traverse entity neighbourhood ─▶ Generator ─▶ Answer
                     └─ global ─▶ map-reduce over community summaries ─▶ Generator ─▶ Answer
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Corpus** | the source documents | — $\to$ documents | — |
| **Entity Extractor** | identifying entities | chunk $\to$ entities | invent entities — extraction error is the pattern's dominant failure mode. |
| **Relationship Extractor** | identifying relationships | entities + chunk $\to$ edges | assert relationships the text does not support. |
| **Graph store** | holding the entity-relationship graph | entities + edges $\to$ queryable graph | — |
| **Community Detector** | clustering densely-connected entities | graph $\to$ communities | be an LLM step — it is a deterministic graph algorithm (e.g. Leiden). |
| **Community Summariser** | summarising each community | community $\to$ summary | summarise across community boundaries; one summary covers one community. |
| **Query Router** | classifying local vs global | query $\to$ route | send a thematic query down the local path or vice versa — the route picks the whole retrieval strategy. |
| **Traverser / Synthesiser** | executing the chosen route | query + graph $\to$ evidence | mix routes; local walks neighbourhoods, global map-reduces summaries. |
| **Generator (LLM)** | producing the final answer | evidence $\to$ answer | — |

## Collaborations

**Offline.** The Entity Extractor and Relationship Extractor run an LLM over every chunk to populate the Graph store. The Community Detector partitions the graph; the Community Summariser writes one summary per community. This phase is costly and runs once per corpus version.

**Online — local.** For an entity-centric query, the Router selects local search; the Traverser walks the neighbourhood of the relevant entities, gathering connected facts and the paths between them; the Generator answers from that subgraph.

**Online — global.** For a thematic query, the Router selects global search; the system map-reduces over community summaries — each summary contributes a partial answer, which are reduced into a whole-corpus synthesis; the Generator produces the final answer.

## Consequences

**Benefits**
- Uniquely handles multi-hop relational queries and whole-corpus synthesis — the queries K1 cannot reach. The offline build cost is paid once and amortised across many queries; per-query cost is then only the traversal or map-reduce step. This makes the K1+K3 hybrid mechanically efficient: K1's n² online attention (mechanism 2) serves local queries cheaply, K3's pre-built structure serves relational queries without per-query extraction cost.
- Relationships are explicit and inspectable; the graph is itself a useful artefact.
- Community summaries are reusable across many global queries.

**Costs**
- Very expensive offline build: an LLM call per chunk for extraction, plus summarisation across all communities.
- Storage for the graph and all summary levels.
- Full rebuild cost whenever the corpus changes materially.
- Higher query latency, especially for global map-reduce.

**Risks and failure modes**
- *Extraction error propagation* — a missed or wrong entity/relationship corrupts the graph, and the error is hard to detect downstream. Graph quality caps answer quality absolutely.
- *Over-engineering* — applied to a corpus whose queries are mostly local, GraphRAG pays a large build cost for no gain over K1.

## Implementation Notes

- **Microsoft GraphRAG** is the reference open-source implementation; study it before building your own.
- Use a graph community algorithm such as **Leiden** for community detection.
- **Local search** for entity-centric queries; **global search** (map-reduce over community summaries) for thematic ones. Routing between them is itself a design decision.
- A **hybrid** with K1 — GraphRAG for global/relational queries, Vanilla RAG for local lookups — is common and often the right answer; do not treat GraphRAG as a wholesale replacement.
- Extraction is the cost and quality bottleneck. Use a capable extraction model and validate the graph on a sample before trusting it.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** K3 has a heavy offline chain (extract $\to$ graph $\to$ communities $\to$ community summaries) and a routed online chain (local traversal *or* global map-reduce). Chains an Extractor, a Summariser, a Router, per-community generators, a Reducer, and a final Generator.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Offline: extract entities + typed relationships from each chunk | `LLM` | Extractor session |
| 2 | Offline: assemble the graph from extractions | `code` | |
| 3 | Offline: detect communities (Leiden) | `code` | deterministic algorithm |
| 4 | Offline: summarise each community | `LLM` | Summariser session |
| 5 | Online: classify query as local vs global | `LLM` (or rule) | Router session |
| 6 | Online (local): walk entity neighbourhood, gather evidence | `code` | |
| 7 | Online (global): per-community partial answer — this is a subagent decomposition by context bounding (mechanism 6): each community summary is processed in its own bounded context; only the compact partial answer enters the Reducer. The pattern is mechanically optimal for whole-corpus synthesis because it avoids placing all community summaries into one n²-expensive context. | `LLM` $\times$ N | Per-community generator |
| 8 | Online (global): reduce partials to one answer | `LLM` | Reducer session |
| 9 | Online: produce the final cited answer | `LLM` | Generator session |

**Skeleton:**

```
OFFLINE:
    for chunk in chunks(corpus):
        entities, edges = Extractor(chunk)        # LLM — extraction
        graph.add(entities, edges)                 # code
    for community in leiden(graph):                # code (algorithm)
        community.summary = Summariser(community) # LLM

ONLINE:
    route = Router(query)                          # LLM (or rule)
    if route == LOCAL:
        evidence = graph.neighbourhood(graph.match(query), hops=2)   # code
    else:  # GLOBAL
        partials = [PerCommunity(c.summary, query) for c in communities]  # LLM × N
        evidence = Reducer(partials, query)         # LLM
    return Generator(query, evidence)               # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Extractor** | capable generalist — *extraction quality caps everything downstream* — but note that entity and relationship extraction is a structured extraction task (not open-ended reasoning); a mid-tier model with strong instruction-following may match a frontier model at a fraction of the cost (mechanism 8). Measure extraction recall on a sample before committing to the most expensive option. | role; strict JSON output schema; the entity-type list; rule: *"do not assert relationships unsupported by the text"*; 2–3 worked extraction examples (S2 few-shot) | one chunk |
| **Summariser** | generalist | role: summarise this community of related entities; *"preserve specific facts and named entities, not just gist"*; length cap | one community |
| **Router** | small fast generalist, *or* a trained binary classifier | role: classify the query as LOCAL (entity-centric) or GLOBAL (thematic); criteria + 2–3 examples | the query |
| **Per-community generator** | small fast generalist | grounding rule; one summary at a time; brief answer | one community summary + the query |
| **Reducer** | main generalist | role: synthesise these partial answers into one coherent answer; deduplicate; cite contributing communities | the partials + the query |
| **Generator** | main generalist | role; citation rules | gathered evidence + the query |

**Specialist-model note.** The Extractor is the cost and quality bottleneck of the entire pattern; treat it as a build dependency and pick a capable model. If the Router is implemented as a trained binary classifier rather than an LLM, that classifier is a specialist with its own labelled-data requirement.

## Open-Source Implementations

- **Microsoft GraphRAG** — [`github.com/microsoft/graphrag`](https://github.com/microsoft/graphrag) — the official reference implementation from the originating research; extraction, Leiden community detection, local and global search.
- **LlamaIndex** — [`github.com/run-llama/llama_index`](https://github.com/run-llama/llama_index) — property-graph index and knowledge-graph query engines.
- **Neo4j GraphRAG** — Neo4j's `neo4j-graphrag` package pairs a property-graph database with LLM extraction for production graph retrieval.

## Known Uses

- **Microsoft GraphRAG** — the open-source reference system, from the originating research.
- **Neo4j** and other graph databases paired with LLM knowledge-graph extraction.
- **LlamaIndex** knowledge-graph indices.
- Enterprise deployments in intelligence analysis, legal e-discovery, and life-sciences literature review.

## Related Patterns

- **Refines** K1 Vanilla RAG — an alternative offline index for queries K1 fails on; the two are routinely run side by side.
- **Sibling of** K4 RAPTOR — both build a structured offline index, but the structures differ in kind: K3's is a relational entity graph, K4's is a hierarchical abstraction tree. They are two patterns, not one, because they target different query classes (relationship-tracing vs abstraction-level matching).
- **Composes with** K2 Query Transformation (a better key helps graph queries too) and K5 Adaptive RAG (gate and quality-check graph retrieval like any other).
- **Competes with** K9 Long Context — for a corpus that fits a large window, the model can sometimes do its own cross-document synthesis without an explicit graph.
- **Conflicts** — none. K3 does not conflict with K1 so much as cover the queries on which K1 *fails*.

## Sources

- Edge et al. (2024) — "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" (Microsoft Research).
- "RAG vs. GraphRAG: A Systematic Evaluation" (arXiv, 2025).
- Microsoft GraphRAG project documentation.
