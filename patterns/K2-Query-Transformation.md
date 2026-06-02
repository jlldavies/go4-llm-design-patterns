# K2 — Query Transformation

> Rewrite, expand, or decompose the user's raw query into one or more derived queries chosen to retrieve better, before any retrieval is performed.

**Also Known As:** Query Rewriting, Pre-Retrieval Query Optimisation. (HyDE, Rewrite-Retrieve-Read, Multi-Query, RAG-Fusion, and Step-Back Query are *variants* of this pattern — see Variants.)

**Classification:** Category II — Knowledge · Band II-A Retrieval strategy · a pre-retrieval stage that composes in front of K1 Vanilla RAG and its other refinements.

---

## Intent

Improve retrieval quality by transforming the user's raw query into a form better matched to the corpus, in the moment between the user submitting the query and the retriever running.

## Motivation

The query a user types is frequently a poor retrieval key. K1 Vanilla RAG embeds that raw query and searches with it directly — which fails in several recurring, and distinct, ways:

- **Query/document space mismatch.** A short question ("What's our refund window?") and the passage that answers it ("Customers may return items within 30 days of delivery for a full refund…") are written in different registers. The embedding model defines a learned bilinear similarity metric (mechanism 1) — a contraction in d_model space. Questions and answers were not co-trained as synonyms in this metric; their distributional contexts differ. A question tokens-distribution and an answer tokens-distribution sit in different regions of the learned similarity surface even when one definitively answers the other.
- **Under-specified queries.** "How does it handle errors?" — *it* is unresolved; the query carries almost nothing to match on.
- **Conversational queries.** In multi-turn chat the real query is spread across turns ("…and what about the enterprise tier?"). The raw final turn is not a standalone retrieval key.
- **Compound queries.** "Compare the refund and warranty policies" needs two different passages; a single embedding splits the difference and retrieves neither well.

These cannot be fixed downstream. You do not control how the corpus phrases its answers, and you cannot fix the embedding model without retraining it. The one available leverage point is the query itself, before retrieval runs. Query Transformation inserts exactly one stage there: it converts the raw query into one or more *derived* queries selected to retrieve well.

This is what distinguishes it from K1, which never touches the query. The pattern's defining claim: **retrieval is only as good as its key, so generate a better key.**

## Variants

The variants differ only in *what the Transformer produces*:

- **HyDE (Hypothetical Document Embeddings).** The Transformer generates a hypothetical *answer* to the query; that answer's embedding, not the query's, drives the search — because a hypothetical answer sits in the same region of vector space as real answers. The mechanism: hypothetical answer text has the same distributional character as real answer text — it activates the same features in the embedding model's learned projection. Query text has a different distributional character (interrogative structure, brevity, pronoun density) and maps to a different region of the same learned metric. The strongest variant for query/document register mismatch. *Risk: a confidently wrong hypothesis retrieves documents supporting the wrong answer.* (Gao et al., 2022.)
- **Query Rewriting (Rewrite-Retrieve-Read).** The Transformer rephrases the raw query into a standalone, well-formed retrieval query, resolving pronouns and folding in conversational context. Essential for multi-turn systems. (Ma et al., 2023.)
- **Query Expansion.** The Transformer adds synonyms, related terms, and alternate phrasings, widening what the search can match. The cheapest variant; the classic information-retrieval move, predating LLMs.
- **Multi-Query / Decomposition (RAG-Fusion).** The Transformer emits *several* derived queries — sub-questions of a compound query, or paraphrases. Retrieval runs for each and the result sets are merged, usually by reciprocal rank fusion.
- **Step-Back Query.** The Transformer abstracts the query to a more general question, retrieves the underlying principle, then answers the specific. Shares its mechanism with the Reasoning pattern **R19 Step-Back Prompting**, applied here to the retrieval key.

A system may chain more than one (rewrite, then decompose).

## Applicability

Use Query Transformation when:

- raw-query retrieval (K1) shows misses on questions that *do* have answers in the corpus;
- queries are short, ambiguous, or phrased unlike the corpus;
- the system is conversational and queries depend on prior turns;
- queries are compound and need several distinct passages.

Do not bother when:

- queries already resemble the corpus (e.g. the corpus is itself a FAQ);
- retrieval is not the measured bottleneck;
- latency budgets are tight — every variant adds at least one LLM call to the critical path.

## Decision Criteria

K2 is right when K1's retrieval is failing on *query-side* problems — and not on corpus-side ones.

**1. Measure K1 retrieval recall.** On a labelled set of queries with known relevant chunks, count top-k hits. If recall is high (~90% or above), K2 has nothing useful to add. If recall is low, continue.

**2. Diagnose the misses.** For each missed query, ask: was the answer *in* the corpus but the retriever did not find it (**query-side**), or was the answer not in the corpus (**corpus-side**)?
- Query-side → K2 is the right fix.
- Corpus-side → use **K5 Adaptive RAG** (quality-gated fallback to web search), or expand the corpus.

**3. Categorise the query-side misses.** This picks the variant:
- Short queries vs long-form answers (register mismatch) → **HyDE**.
- Multi-turn conversational queries with unresolved references → **Rewriting**.
- Compound queries needing several distinct passages → **Multi-Query / RAG-Fusion**.
- Queries pitched too specifically for the corpus → **Step-Back**.

**4. Latency budget check.** Every transform adds at least one LLM call before retrieval. If the latency budget is sub-second, a better embedder or hybrid retrieval may beat K2 on cost-per-improvement.

**5. Compose, do not replace.** K2 sits in front of K1. Total cost becomes `transform + N × retrieve + generate`. The smallest model that gets the transform right minimises that overhead — the Transformer does not need the system's strongest model. This is mechanically correct: the transform is a classification/rephrasing task, not a reasoning task. Small models are appropriate for routing and classification (mechanism 8); using a large model here pays for capacity that the task does not require.

**Quick test — K2 is the right pattern when:**

- K1 retrieval recall is measurably below target on a labelled set, *and*
- the misses are query-side (answers exist in the corpus but are not found), *and*
- the latency budget tolerates one extra LLM call per query, *and*
- one of the four variants fits the dominant miss pattern.

If misses are corpus-side, use **K5 Adaptive RAG** instead. If the corpus is small enough to fit a window, **K9 Long Context** skips retrieval entirely. If retrieval recall is already high, K2 is overhead.

## Structure

```
  Raw query ──▶ Query Transformer ──▶ Derived query / queries ──▶ [ K1 retrieval ] ──▶ …
                (LLM rewrites,          (better retrieval keys)
                 expands, or
                 decomposes the query)
```

Query Transformation is a *stage*, not a pipeline of its own. Everything downstream of "derived query" is unchanged K1 (or any of K3–K5). The pattern's entire substance is the Transformer and what it emits.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Raw query** | the user's actual input | — → raw query | be retrieved on directly when it is a poor key — that poorness is the pattern's whole motivation. |
| **Query Transformer** | converting the raw query into derived queries | raw query (+ history) → derived queries | change the user's intent — a rewrite that alters meaning is a silent failure. The defining participant; absent from K1. |
| **Conversation history** *(rewriting variant)* | the references a follow-up turn depends on | prior turns → resolution context | be passed wholesale — only the turns the current query actually depends on. |
| **Derived queries** | the improved retrieval keys | — → one or more queries | — |
| **Retriever / index / Generator** | retrieval and answering | derived query → answer | — these are K1's participants, invoked unchanged. |

## Collaborations

The user submits a raw query. The Query Transformer takes it — and, for the rewriting variant, the conversation history — and produces one or more derived queries according to its variant: a hypothetical document, a rewritten query, an expanded query, a set of sub-queries, or an abstracted query. Each derived query is then passed to the Retriever exactly as a raw query would be in K1. If the variant produced multiple queries, retrieval runs once per query and a merge step (typically reciprocal rank fusion) combines and deduplicates the result sets. From there the pattern hands off entirely to K1: assemble the prompt, generate, cite.

## Consequences

**Benefits**
- Recovers retrieval hits that raw-query search misses; the single highest-leverage fix for K1 recall problems.
- Makes conversational RAG viable — without rewriting, multi-turn retrieval is unreliable.
- Multi-query variants turn compound questions, which K1 handles badly, into several questions it handles well.

**Costs**
- At least one extra LLM call before retrieval, on every query: added latency and token cost.
- Multi-query variants multiply retrieval cost and require a merge step.
- One more component to evaluate and monitor.

**Risks and failure modes**
- *Hallucinated transform* — HyDE's hypothetical answer is wrong, or a rewrite changes the user's intent; retrieval is then confidently aimed at the wrong place. The failure is invisible — downstream it looks like an ordinary K1 retrieval miss.
- *Over-transformation* — expanding or abstracting a query that was already precise dilutes it.
- *Latency stacking* — the transform call is pure addition to the critical path: transform, then retrieve, then generate.

## Implementation Notes

- Transform with a small, fast model. The transform does not need the system's strongest model and it sits on the latency path.
- Measure first. Instrument K1 retrieval recall and confirm the misses are query-side; Query Transformation does nothing for a corpus that simply lacks the answer (that is K5 Adaptive RAG's job).
- HyDE: generate a *short* hypothetical answer — length adds latency without signal. Generating several and averaging their embeddings reduces the hallucination risk.
- Rewriting: pass only the relevant prior turns, not the whole history.
- Multi-query: reciprocal rank fusion is the standard robust merge; deduplicate chunks across result sets before assembly.
- The Transformer is driven by a prompt — a Signal-layer artefact. Version and evaluate it like any other prompt.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** K2 inserts a query-transformation *stage* in front of K1. Variants differ in what the Transformer emits; each then hands off to K1 unchanged.

**The chain (multi-query variant):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Transform the raw query into N derived queries | `LLM` | Transformer session |
| 2 | For each derived query, run K1's retrieve | `code` (each call is K1) | K1 |
| 3 | Merge result sets via reciprocal rank fusion | `code` | |
| 4 | Compose prompt + generate the answer | `LLM` | K1 Generator |

The other variants share the shape and differ in step 1: **HyDE** emits one hypothetical *answer document* (step 2 embeds and retrieves on that); **Rewriting** emits one standalone query, resolving references against conversation history; **Step-Back** emits one more-abstract query.

**Skeleton:**

```
multi_query_rag(query):
    derived = Transformer(query)                   # LLM   — multi-query session
    pools = [K1.retrieve(q) for q in derived]      # code (each retrieve is K1)
    merged = reciprocal_rank_fusion(pools)         # code
    return K1.Generator(merged, query)             # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Transformer (multi-query)** | small fast generalist | role: "rephrase as N differently-worded search queries"; output contract: one query per line, no numbering | the query |
| **Transformer (HyDE)** | small fast generalist | role: "write a brief plausible answer paragraph to be used only as a retrieval key — accuracy does not matter, similarity to real answer documents does"; length constraint: short | the query |
| **Transformer (rewriting)** | small fast generalist | role: "rephrase the latest turn as a standalone query, resolving pronouns and folding in references from the supplied conversation history" | latest turn + the relevant prior turns |
| **K1 sessions** | as K1 | as K1 | as K1 |

**Specialist-model note.** No specialist required — a tight setup on a small fast generalist is sufficient. K2's whole cost is per-query latency: every transform is an extra LLM call on the critical path, so the *smallest* model that gets it right wins.

## Open-Source Implementations

- **LangChain** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — ships `MultiQueryRetriever`, a HyDE retriever, and query-rewriting chains as first-class components.
- **LlamaIndex** — [`github.com/run-llama/llama_index`](https://github.com/run-llama/llama_index) — query-transformation modules and sub-question query engines.
- **RAG-Fusion** — [`github.com/Raudaschl/rag-fusion`](https://github.com/Raudaschl/rag-fusion) — the reference implementation of the multi-query variant with reciprocal rank fusion.

## Known Uses

- **LangChain** and **LlamaIndex** ship Query Transformation as first-class retrievers (MultiQueryRetriever, HyDE retriever, query-rewriting chains, sub-question engines).
- **Perplexity** and other answer engines rewrite and decompose queries before searching.
- Conversational enterprise assistants (e.g. Microsoft Copilot) rewrite follow-up turns into standalone queries as standard practice.
- **RAG-Fusion** is a widely adopted community implementation of the multi-query variant.

## Related Patterns

- **Refines** K1 Vanilla RAG — Query Transformation is a stage placed in front of K1 and presupposes its architecture.
- **Composes with** K3 GraphRAG and K4 RAPTOR (a better key helps any retriever) and **K5 Adaptive RAG** (Query Transformation fixes query-side misses; K5's quality gate and fallback catch corpus-side misses — complementary, often paired).
- **Distinct from** K5 Adaptive RAG — K5 decides *whether* to retrieve and *whether retrieval worked*; K2 decides *with what key* to retrieve. Different questions; they compose cleanly.
- **Shares mechanism with** R19 Step-Back Prompting — the same abstraction move, applied to the retrieval key rather than the reasoning chain.
- **Note on fundamentality** — the Transformer is, in isolation, a single LLM generation step driven by a Signal-layer prompt. That is precisely why HyDE alone does not earn a pattern number: the pattern is the *stage* in the retrieval architecture, not the prompt inside it. The stage is fundamental; the prompt is an adaptor.

## Sources

- Gao et al. (2022) — "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE).
- Ma et al. (2023) — "Query Rewriting for Retrieval-Augmented Large Language Models" (Rewrite-Retrieve-Read).
- Zheng et al. (2023) — "Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models."
- RAG-Fusion (community, 2023–2024); LangChain and LlamaIndex query-transformation documentation.
