# Category II — Knowledge Patterns

A **Knowledge pattern** is a design pattern for supplying a language model with information it does not hold in its weights, curated to suit the task at hand. Knowledge patterns separate *what the model reasons over* from *what the model was trained on*.

## Usage

A language model's trained knowledge is fixed, generic, and opaque: frozen at the training cutoff, holding no proprietary or task-specific information, and unable to cite its own sources. Relying on weights alone produces answers that are stale, ungrounded, and unauditable, and the only way to change what such a model knows is to retrain it.

Knowledge patterns remove that rigidity. They insert a curation step between an information source and the model, so that what the model sees can be selected, updated, compressed, and cited without touching the weights. This is the shift the field named the move from *prompt engineering* to *context engineering*, and it is what separates Category II from Category I. Apply a Knowledge pattern whenever:

- the task needs current, proprietary, or private information;
- answers must be grounded in, and traceable to, specific sources;
- a task or conversation runs long enough to strain the context window;
- an agent must carry knowledge across turns or across sessions.

## Forces

Every Knowledge pattern resolves the same three forces in tension. A pattern is the right choice for a situation when it balances them in the way that situation demands.

1. **The context window is finite and not free.** Cost rises linearly with tokens; quality falls non-linearly as they accumulate (the "lost in the middle" effect, where a fact buried in a long context is a fact poorly used). The geometric explanation: U-shaped recall is a consequence of how Q-K inner products distribute over sequence positions — the model's learned projection matrices exhibit recency bias and start-of-context anchoring from training (mechanism 4). The context window is not neutral storage: it is an O(n²) compute surface (mechanism 2) with a non-uniform positional quality distribution. Curation is the process of minimising n and placing the highest-signal content at positions the learned attention metric attends to most reliably. You cannot simply put everything in.

2. **The relevant information lives outside the model.** It is in a corpus, a database, the last forty turns of conversation, or something the agent did three sessions ago. It must be brought in, and brought in selectively.

3. **The model cannot be trusted to know what it does not know.** Left alone it answers confidently from stale weights. Some patterns therefore make retrieval conditional, corrective, or self-critiqued rather than automatic. 'Grounding' is an architectural property, not a prompting outcome: weights-only generation is stochastic sampling from a learned distribution (mechanism 7) and inherently cannot cite sources, because there is no architectural mechanism to attribute a sampled token to a training document. Knowledge patterns are how grounding is achieved.

A Knowledge pattern is, in each case, a disciplined answer to one question: how to get the right information into a limited window, at the right time, and keep it coherent for the length of the task.

## Structure

All Knowledge patterns share one skeleton. They interpose a **curation stage** between a source of information and the model's context window:

```
  Source ────▶ Curation ────▶ Context Window ────▶ LLM ────▶ Response
 (corpus,      (select,        (the working set
  history,      retrieve,       the model
  prior         compress,       reasons over)
  sessions)     filter)
```

Patterns differ in *what the source is* — an external corpus, the running conversation, a persistent memory store — and in *what the curation stage does* — retrieve by similarity, traverse a graph, summarise, prune, recall an episode. The three bands below group the patterns by the question they answer: how to bring external knowledge *in* (II-A), how to curate the *live window* (II-B), and how to *persist* knowledge beyond it (II-C). They are orthogonal concerns rather than alternatives: a production system typically instantiates a pattern from each band at once, which is why the bands are axes to span, not a menu to choose from.

## The Four Data Shapes — Matching Retrieval to Information Type

A recurring error in agent design is applying a single retrieval primitive across all data types. The attention bilinear form (mechanism 1) captures distributional semantic similarity — effective for prose, but structurally wrong for three other shapes. Choosing the wrong shape primitive produces systematic retrieval failure regardless of retrieval quality, because better embeddings still cannot represent document hierarchy, table semantics, or graph edges.

| Shape | Where meaning lives | What chunk retrieval misses | Correct primitive |
|---|---|---|---|
| **Fuzzy prose** | Word choice, phrasing, semantic proximity | Nothing — this is what vector search was designed for | K1 Vanilla RAG, K2 Query Transformation |
| **Structured documents** | Section hierarchy, cross-references, schedules, definitions that control distant clauses | Structural relationships: a clause 3 pages from its controlling definition; a schedule that overrides a general term | K4 RAPTOR (hierarchical tree); document-tree approaches |
| **Governed tabular data** | Column semantics, row relationships, metric definitions, lineage, access controls | All numeric and relational structure; converting a table to prose destroys aggregation semantics and data governance | Semantic layer + tabular-native retrieval; not vector search |
| **Relational knowledge** | Edges between entities: supplier-to-shipment, customer-to-failure-pattern, incident-to-root-cause | Graph edges have no embedding equivalent; chunk retrieval cannot represent entity relationships | K3 GraphRAG; knowledge graph retrieval |

Most production agent workflows need more than one shape. This is the correct diagnosis — not a complexity failure. The error is assuming one primitive covers all shapes. See **K13 Retrieval Bundle** for the design-time specification process that maps each required field to its correct shape primitive.

**Context rot** is the failure mode produced by mixing shapes incorrectly — or by loading mixed-authority, mixed-freshness, inferred-alongside-confirmed content into a single context window. The model cannot distinguish which sources are authoritative, treats stale alongside current as equal, blends sources it should cite separately, and gives wrong emphasis to facts that are present but not reliably attended to (mechanism 4). A larger context window does not fix context rot — it compounds it (mechanism 2: O(n²) attention cost with M4 positional under-attendance). The goal is appropriate context assembled from the correct shapes, not maximum context from a single search.

## Examples

**II-A — Retrieval.** Bringing external knowledge into context.
- **K1 Vanilla RAG** — retrieve top-k semantically similar chunks at query time.
- **K2 Query Transformation** — rewrite, expand, or decompose the query before retrieval (HyDE, multi-query, step-back).
- **K3 GraphRAG** — index the corpus as an entity-relationship graph for multi-hop and global-synthesis queries.
- **K4 RAPTOR** — index the corpus as a recursive summary tree; retrieve at the abstraction level the query needs.
- **K5 Adaptive RAG** — wrap retrieval in an evaluate-and-control loop (Self-RAG and Corrective RAG are variants).

**II-B — Context-window management.** Curating the finite window during a task.
- **K6 Context Compression** — summarise context that no longer fits (lossy).
- **K7 Context Pruning** — remove spent or irrelevant spans without summarising (lossless).
- **K8 Working Memory / Scratchpad** — an explicit in-context space the model writes to itself.
- **K9 Long Context** — hold the whole working set in a large window instead of retrieving.

**II-C — Memory.** Persisting knowledge beyond the live window. The model's weights do not change between sessions — all persistence is file retrieval, not model learning (mechanism 10). This is the single most important mechanical fact about this band: no capability accrues in the model; improvement is entirely in the quality of what is retrieved and injected into context.
- **K10 Long-Term Memory** — an external store of flat fact-shaped items, retrieved by similarity (episodic, semantic, procedural variants).
- **K11 Observational Memory** — the raw activity record as primary memory; cache-friendly; the Karpathy framing's *raw-log* branch.
- **K12 Karpathy Memory** — the LLM curates structured, dense notes the agent reads; the Karpathy framing's *curated-notes* branch.
- **K13 Retrieval Bundle** — before writing retrieval code, specify the exact operational context bundle a workflow type always needs — by field, by data shape, by source authority, by freshness — then build assembly to deliver it reliably. Addresses the *rediscovery problem* (agents re-fetching and re-assembling the same context every run, consuming up to 85% of agent compute on re-discovery rather than task execution).

## See also

- **Category I — Signal patterns** — shape *what you say* to the model; Knowledge shapes *what it sees*.
- **Category III — Reasoning patterns** — govern what the model *does* with the context that Knowledge assembles.
- **Category IV — Orchestration patterns** — Agent Isolation (delegating a sub-task to a fresh, clean context) was formerly classified here as a Knowledge pattern; its mechanism is sub-agent delegation, so it now lives with the Orchestration patterns. Mechanistically, subagent decomposition in Orchestration bounds the n² context cost per agent (mechanism 6) and is a complementary architectural axis to the within-context management patterns (K6/K7/K9): the choice is between managing one large context or decomposing into bounded sub-contexts.
- **Category V — Reliability patterns** — V11 Error Compaction and the evaluation patterns intersect with context curation.

*The reframing of this category as "context engineering" follows Tobi Lütke and Andrej Karpathy (June 2025) and Gartner (July 2025).*

---

## Quick Reference

### II-A — Retrieval

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K1 | **Vanilla RAG** | Naive RAG | Retrieve relevant chunks at query time | Simple Q&A, static corpora, citations required |
| K2 | **Query Transformation** | HyDE, multi-query | Transform the raw query to retrieve better | Query/document mismatch; ambiguous queries |
| K3 | **GraphRAG** | Graph Retrieval | Index corpus as entity-relationship graph | Multi-hop relational queries; global synthesis |
| K4 | **RAPTOR** | Hierarchical RAG | Index corpus as recursive summary tree | Variable abstraction; hierarchical documents |
| K5 | **Adaptive RAG** | Self-RAG, Corrective RAG | Wrap retrieval in evaluate-and-control loop | Mixed query streams; factuality-critical |
| K13 | **Retrieval Bundle** | Agent Operating Context | Specify exact context bundle before writing retrieval code | Recurring workflows; rediscovery cost measurable |

### II-B — Context-Window Management

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K6 | **Context Compression** | Summarisation | Summarise context that no longer fits (lossy) | Long-running agents; context overflow |
| K7 | **Context Pruning** | Selective Recall | Remove spent spans without summarising (lossless) | Spent tool outputs; finished sub-task context |
| K8 | **Working Memory** | Scratchpad | Explicit in-context space model writes to itself | Multi-step reasoning; intermediate state |
| K9 | **Long Context** | Context Stuffing | Hold whole working set in a large window | Working set fits; retrieval not justified |

### II-C — Memory

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K10 | **Long-Term Memory** | Persistent Memory | External store of facts, retrieved by similarity | Cross-session fact storage; preferences |
| K11 | **Observational Memory** | Agent-Centric Memory | Append-only activity log; prefix-cache-friendly | Long-running agents with prefix caching |
| K12 | **Karpathy Memory** | Curated Memory | LLM curates dense structured notes | Read-frequency dominates; structure matters |

---

## K1 — Vanilla RAG

Retrieve the documents most relevant to a query from an external corpus and inject them into the context window, so the model answers from supplied evidence rather than from its trained weights alone.

**Full entry:** [`K1-Vanilla-RAG.md`](K1-Vanilla-RAG.md)

---

## K2 — Query Transformation

Rewrite, expand, or decompose the user's raw query into derived queries chosen to retrieve better, before retrieval runs. HyDE, query rewriting, multi-query, and step-back query are variants.

**Full entry:** [`K2-Query-Transformation.md`](K2-Query-Transformation.md) — *was "K2 HyDE"; HyDE is a variant, not a fundamental pattern.*

---

## K3 — GraphRAG

Index the corpus offline as a graph of entities and relationships; answer multi-hop and global-synthesis queries by traversing that graph rather than retrieving isolated chunks.

**Full entry:** [`K3-GraphRAG.md`](K3-GraphRAG.md)

---

## K4 — RAPTOR

Index the corpus offline as a tree of recursively-built summaries; retrieve from whichever level of abstraction the query needs — a leaf fact, a section summary, or a document-level synthesis.

**Full entry:** [`K4-RAPTOR.md`](K4-RAPTOR.md)

---

## K5 — Adaptive RAG

Wrap retrieval in an evaluation-and-control loop: decide whether retrieval is needed, judge the quality of what returns, and act on the verdict — skip, proceed, re-retrieve, or fall back. Self-RAG and Corrective RAG are variants.

**Full entry:** [`K5-Adaptive-RAG.md`](K5-Adaptive-RAG.md) — *merge of the former K5 Self-RAG and K6 Corrective RAG.*

---

## K6 — Context Compression

When the context window fills, replace stretches of it with shorter summaries — trading fidelity for space so the task can continue.

**Full entry:** [`K6-Context-Compression.md`](K6-Context-Compression.md)

---

## K7 — Context Pruning

Identify spans of the context window that are no longer needed and remove them outright, keeping everything retained at full fidelity. The lossless counterpart of K6.

**Full entry:** [`K7-Context-Pruning.md`](K7-Context-Pruning.md)

---

## K8 — Working Memory / Scratchpad

Give the model an explicit, designated region of the context to write intermediate results, plans, and conclusions into, so working state persists across reasoning steps.

**Full entry:** [`K8-Working-Memory.md`](K8-Working-Memory.md)

---

## K9 — Long Context

Place the entire working set of documents directly into a large context window and let the model attend over all of it, instead of retrieving a selected subset. The architectural alternative to retrieval.

**Full entry:** [`K9-Long-Context.md`](K9-Long-Context.md)

---

## K10 — Long-Term Memory

Persist knowledge in an external store that outlives the context window, and retrieve from it in later sessions, so the agent accumulates and reuses what it learns. Episodic, semantic, and procedural memory are variants.

**Full entry:** [`K10-Long-Term-Memory.md`](K10-Long-Term-Memory.md) — *merge of the former K10 Episodic, K11 Semantic, and K12 Procedural memory.*

---

## K11 — Observational Memory

Treat what the agent has already seen and done within the current session as its primary memory — kept stable, compact, and cache-friendly — rather than re-retrieving it from an external store. The *raw-log* branch of the Karpathy framing of agent memory.

**Full entry:** [`K11-Observational-Memory.md`](K11-Observational-Memory.md)

---

## K12 — Karpathy Memory

Have the LLM itself curate a structured, dense memory — writing, editing, merging, linking entries — so every read is of pre-digested knowledge rather than a raw observation log or a vector of isolated extractions. The *curated-notes* branch of the Karpathy framing; typically paired with K11.

**Full entry:** [`K12-Karpathy-Memory.md`](K12-Karpathy-Memory.md)

---

*Former K13 Agent Isolation has been reclassified to Category IV — Orchestration (O17), where its mechanism — sub-agent delegation — sits more naturally than in the retrieval and memory band.*
