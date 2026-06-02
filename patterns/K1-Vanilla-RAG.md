# K1 — Vanilla RAG

> Retrieve the documents most relevant to a query from an external corpus, place them in the model's context window, and have the model answer from that supplied evidence rather than from its trained weights alone.

**Also Known As:** Naive RAG, Basic Retrieval, Classic Retrieval-Augmented Generation

**Classification:** Category II — Knowledge · Band II-A Retrieval strategy · *base pattern of the band* — K2 Query Transformation, K3 GraphRAG, K4 RAPTOR, and K5 Adaptive RAG are all refinements of this pattern.

---

## Intent

Ground a model's response in a specific, external, updatable corpus by retrieving the passages relevant to each query at query time and injecting them into the prompt — without retraining the model.

## Motivation

The problem Vanilla RAG solves is narrow and exact: **you need a model to answer over a body of knowledge it was not trained on** — because the knowledge is proprietary, or private, or changes faster than the model's training cycle — **and you need the answer to be traceable to a source.**

Three approaches present themselves first. Each fails in a way that defines what RAG must do.

1. **Rely on the model's weights.** The model knows only what was in its training set, up to its cutoff. Proprietary documents were never in it; last week's events are absent. And even where the model does know a fact, it cannot point to where the fact came from — so the answer cannot be audited, and cannot be trusted in any setting where being wrong is expensive.

2. **Fine-tune the model on the corpus.** This is expensive, slow, and must be repeated every time the corpus changes. It still yields no citations. Facts absorbed as weights blur into everything else the model knows and can be overwritten by later training (catastrophic forgetting). Fine-tuning teaches *behaviour and style* well; it is a costly and unreliable way to teach *facts*.

3. **Put the whole corpus in the prompt.** This works only while the corpus is small. Cost scales linearly with every token, on every call; answer quality degrades as the window fills (the "lost in the middle" effect) (mechanism 4); and most real corpora simply do not fit.

Vanilla RAG closes precisely the gap these leave. It makes the model's knowledge **external, updatable, selective, and citable.** The corpus lives outside the model, in an index. At query time only the handful of passages relevant to *this* query are brought in. Updating the system's knowledge means re-indexing, not retraining. Every answer can carry the source of each passage it drew on.

The underlying division of labour is the pattern's unique contribution: **the model's parameters supply language and reasoning; the retrieved passages supply facts.** Lewis et al. (2020) formalised this separation and named it.

## Applicability

Use Vanilla RAG when:

- the task is question-answering over a static or slowly-changing document corpus — product documentation, policies, manuals, a knowledge base;
- answers must be grounded in, and cite, specific sources;
- the corpus is too large for the context window, but any single query needs only a small, locally-coherent slice of it;
- the knowledge changes often enough that retraining is impractical.

Do **not** reach for Vanilla RAG when:

- the query needs synthesis across the *whole* corpus or multi-hop reasoning over entity relationships — use **K3 GraphRAG**;
- queries vary widely in the level of abstraction they need — use **K4 RAPTOR**;
- the entire working corpus fits comfortably in the context window — use **K9 Long Context** and skip retrieval;
- many queries are answerable from the model's own knowledge, and retrieval would only inject noise — gate it with **K5 Adaptive RAG**;
- the agent workflow requires assembling a typed operational bundle from multiple sources — customer records from a CRM, policy from a structured document, prior history from a graph, governing metrics from a warehouse. K1 retrieves semantically similar prose; it cannot retrieve table rows, graph edges, or document sections by structure. Use **K13 Retrieval Bundle** to specify what the workflow needs and choose shape-appropriate primitives per field, of which K1 may be one.

**The rediscovery failure mode** applies specifically to agents — not chatbots — and is a signal to reach for K13 upstream of K1. Agents that re-fetch the same context every run, re-summarize documents summarized last time, or ask users for information the system has, are suffering from rediscovery: the absence of a specified, pre-assembled bundle. Measured at production scale, rediscovery can consume up to 85% of agent compute (PineCone, 2025). K1 as the only retrieval layer leaves the agent responsible for assembling its own operating context dynamically, which is where rediscovery begins.

## Decision Criteria

K1 is right when the task needs grounded answers from an external corpus and neither raw weights alone nor a long window fits.

**1. Score the deficits.** Does the task hit any of the three weights-only deficits — staleness, generic-not-proprietary knowledge, no citations? If none, you do not need K1. If any, retrieval-augmented architecture is the right frame.

**2. Size the corpus against the window.** Tokenize the working set (or estimate). Call it **C**.
- C ≤ ~50% of an affordable usable window → consider **K9 Long Context** instead; simpler architecture if you can afford the per-call cost.
- C >> any affordable window → K1 (or K3 / K4) is the only viable option.
- C in between → benchmark both K1 and K9 on your actual query workload.

**3. Check the query shape.** Are queries local and fact-style, answerable from a small slice of the corpus? K1 fits. Multi-hop or whole-corpus synthesis → **K3 GraphRAG**. Varying abstraction levels (precise facts *and* thematic summaries from the same corpus) → **K4 RAPTOR**.

**4. Corpus update frequency.** How often does the corpus change?
- Frequently → K1's rebuild-the-index cycle is cheap and natural; fine-tuning would be wrong.
- Stable but you still need citations → K1's auditability still wins over weights-only or fine-tuning.
- Never changes and citations do not matter → fine-tuning is at least a candidate.

**5. Citation requirement.** If answers must be traceable to specific sources (regulated domains, customer support, research), K1 is mandatory — weights-only and fine-tuning cannot deliver citations.

**Quick test — K1 is the right base when:**

- the corpus does not fit any affordable window (C >> window), *and*
- queries are well-defined and locally answerable, *and*
- citation or auditability is a requirement, *and*
- the corpus changes often enough that retraining is impractical.

If the working set fits an affordable window, prefer **K9 Long Context**. If queries are relational or global, upgrade to **K3 GraphRAG**. If queries span abstraction levels, **K4 RAPTOR**. If many queries do not need retrieval at all, or silent retrieval misses are costly, wrap K1 with **K5 Adaptive RAG**.

## Structure

Vanilla RAG runs in two phases — an offline phase that builds the index, and an online phase that serves each query.

```
OFFLINE — indexing (once; refreshed when the corpus changes)

  Documents ──▶ Chunker ──▶ Embedding model ──▶ Vector index
                                                 (vectors + chunk text
                                                  + source metadata)

ONLINE — retrieval and generation (every query)

  Query ──▶ Embedding model ──▶ Similarity search ──▶ Top-k chunks
                                  (in the index)            │
                                                            ▼
            System prompt + retrieved chunks + query ──▶ Prompt assembler
                                                            │
                                                            ▼
                                                       Generator (LLM)
                                                            │
                                                            ▼
                                                  Grounded, cited answer
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Corpus** | the source of truth | — → documents | be assumed clean — every downstream quality ceiling inherits from it. |
| **Chunker** | splitting documents into retrievable units | document → chunks | split carelessly across semantic boundaries; a fact straddling two chunks is retrievable by neither. |
| **Embedding model** | mapping text to vectors | text → vector | differ between indexing and querying — the same model and vector space must serve both. |
| **Vector index** | storing vectors and answering similarity search | vectors + query vector → top-k chunks | be the sole retrieval signal; pair with keyword search for exact terms, names, and codes. |
| **Retriever** | turning a query into candidate chunks | query → top-k chunks | judge sufficiency of what it returns — that is K5's job, not K1's. |
| **Reranker** *(optional)* | precision over a wide candidate set | candidates → narrowed set | fetch anything; it refines an existing set, it does not retrieve. |
| **Prompt assembler** | composing system prompt + chunks + query | parts → prompt | drop source metadata — the Generator needs it to cite. |
| **Generator (LLM)** | producing the grounded, cited answer | prompt → answer | answer from weights when the context is silent — it should say the context does not cover it. |

## Collaborations

**Offline.** The Chunker divides each document in the Corpus into chunks. The Embedding model converts each chunk to a vector. The Vector index stores each vector alongside its chunk text and source metadata. This phase runs once and is repeated only when the Corpus changes.

**Online.** When a query arrives, the Embedding model converts it to a vector *using the same model and space as the chunks* — this shared space is the invariant the pattern depends on; if query and chunks are embedded differently, similarity is meaningless. **The same-model invariant is a geometric requirement (mechanism 1).** Each embedding model defines its own learned bilinear similarity surface — its own $g_{\mu\nu} = W_Q W_K^T$ (using the query/key framing of retrieval). Vectors from different embedding models live in incompatible learned spaces: a dot product between a vector from Model A and a vector from Model B measures nothing meaningful, because the bilinear forms are different. Mixing embedding models for indexing and querying — for example, indexing with text-embedding-3-large and querying with Cohere embed-v3 — is the retrieval equivalent of multiplying matrices from different coordinate systems. The result is arbitrary. This is a common practitioner error in systems that switch embedding providers mid-deployment without re-indexing the corpus. The Retriever searches the Vector index for the top-k chunks nearest the query vector. If a Reranker is present, the Retriever returns a wider candidate set and the Reranker narrows it. The Prompt assembler builds the prompt from system instructions, the retrieved chunks (with their source metadata), and the query. The Generator answers from the supplied chunks and cites them by their metadata.

## Consequences

**Benefits**
- *Grounding and attribution.* Answers are anchored in supplied passages and can cite their sources, making them auditable.
- *Updatable knowledge.* New or changed knowledge is absorbed by re-indexing; the model is never retrained.
- *Bounded cost.* Only k chunks enter the prompt per call, regardless of corpus size.
- *Model-agnostic and transparent.* Works with any model; the retrieved set can be inspected to see exactly what the answer was based on.

**Costs**
- Retrieval infrastructure: an embedding pipeline and a vector store to build and operate.
- Offline indexing cost, paid again on every corpus refresh.
- Per-query latency for query embedding and similarity search.
- Chunking quality dominates output quality and is not a one-time decision.

**Risks and failure modes**
- *Retrieval miss* — the chunk that holds the answer is not in the top-k; the model then answers from weights or declines.
- *Boundary split* — a fact straddles two chunks, so neither is fully relevant.
- *Distractor chunks* — retrieved-but-irrelevant text that the model latches onto.
- *Lost in the middle* — even correctly retrieved chunks are used poorly when the assembled prompt is long (mechanism 4).
- *False confidence* — the model presents an answer as grounded when the retrieved text does not actually support it.
- *Stale index* — the corpus has changed but the index has not.

## Implementation Notes

- **Chunk size** is the primary tuning lever: 256–512 tokens for precise factual lookup, 1024+ tokens where narrative coherence matters. Chunk on semantic boundaries (headings, paragraphs), not fixed character counts; overlapping chunks reduce boundary-split loss.
- **Embedding model** must be identical for indexing and querying. Domain-tuned embeddings outperform generic ones on specialised corpora.
- **Top-k** is typically 3–8. Larger k raises recall but lowers precision and consumes context.
- **Hybrid retrieval** — combine dense (embedding) similarity with sparse (BM25 keyword) search. This consistently beats either alone, especially for exact terms, names, and codes.
  - **Why hybrid retrieval is mechanistically necessary (mechanism 1).** Dense embedding retrieval computes similarity as a dot-product contraction in a learned vector space — the same bilinear structure as transformer attention (mechanism 1). This learned metric rewards distributional co-occurrence: words that appear in similar contexts are nearby in the embedding space. Exact terms, proper names, codes, and identifiers may not appear as embedding neighbors even when lexically identical, because the model learned to generalize over surface form rather than preserve it. BM25 fills exactly this gap — it is a lexical match that is immune to the distributional smoothing of embedding models. The combination is mechanistically complementary, not stylistically so.
- **Reranking** — retrieve a wide candidate set (e.g. 30) and rerank with a cross-encoder down to the final few (e.g. 5); this materially improves precision for modest extra latency.
- Always carry **source metadata** into the prompt so the Generator can cite.
- **Contextual retrieval** (Anthropic, 2024): prepend a short chunk-situating summary to each chunk before embedding, reducing ambiguity for chunks that lose meaning out of context.

## Implementation Sketch

> An `LLM` step is a configured session — model + setup loaded once + per-call prompt — not a bare call; `code` steps are deterministic wiring.

**Composition:** K1 is the base of band II-A. It has two chains: an offline index build and an online retrieve-then-generate. K1 is mostly deterministic — only two LLM sessions, an embedder and the final generator.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Offline: chunk each document at semantic boundaries | `code` | |
| 2 | Offline: embed each chunk | `LLM` | Embedder session |
| 3 | Offline: store (vector, text, source metadata) | `code` | |
| 4 | Online: embed the query — *same* embedder | `LLM` | Embedder session |
| 5 | Online: similarity search → top-k chunks | `code` | |
| 6 | Online: compose prompt (system + chunks + query) | `code` | S6 output template |
| 7 | Online: generate the grounded, cited answer | `LLM` | Generator session |

**Skeleton:**

```
OFFLINE:
    for each chunk in corpus:
        store.add(Embed(chunk), chunk.text, source)   # code + LLM (embedder)

ONLINE:
    chunks  = store.search(Embed(query), k)           # LLM (embedder) + code
    prompt  = compose(system, chunks, query)          # code
    answer  = Generator(prompt)                        # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Embedder** | specialist text-embedding model (e.g. text-embedding-3, BGE) — *must be byte-identical for indexing and querying* | the model choice *is* the setup — embeddings are model-defined | one piece of text |
| **Generator** | main generalist | role (S3); answer format and citation rules (S6); grounding rule: *"answer only from the supplied context; if it is silent, say so"* | retrieved chunks + the query |

**Specialist-model note.** The Embedder is a specialist by construction — it is not a chat model. Domain-tuned embedders (financial, biomedical, code) consistently beat generic ones on specialised corpora; that is a build decision worth measuring before committing to a generic embedder for production.

## Open-Source Implementations

- **LangChain** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — retrieval chains and vector-store integrations.
- **LlamaIndex** — [`github.com/run-llama/llama_index`](https://github.com/run-llama/llama_index) — a data framework built around RAG ingestion, indexing, and querying.
- **Haystack** — [`github.com/deepset-ai/haystack`](https://github.com/deepset-ai/haystack) — production-oriented RAG pipelines.

## Known Uses

- **Perplexity AI** — web-scale RAG over live search results, with inline citations.
- **OpenAI ChatGPT** — file uploads, retrieval over knowledge attached to custom GPTs.
- **Anthropic Claude** — Projects knowledge and attached-file context.
- **Microsoft 365 Copilot** — enterprise RAG grounded in the Microsoft Graph.
- **Glean** — enterprise search and assistant over internal corpora.
- **Managed RAG services** — Amazon Bedrock Knowledge Bases, Google Vertex AI Search, Azure AI Search.
- The default architecture for customer-support assistants and documentation Q&A across the industry.

## Related Patterns

- **Refined by** — every other pattern in band II-A is an upgrade of K1: K2 Query Transformation (improves the retrieval key), K3 GraphRAG and K4 RAPTOR (structured offline indexes for different query classes), and K5 Adaptive RAG (wraps retrieval in a control loop with gate, quality, and recovery — Self-RAG and Corrective RAG are its variants).
- **Composes with** — K6 Context Compression and K7 Context Pruning (manage retrieved chunks once they crowd the window); S6 Output Template (force a citation format); V15 LLM-as-Judge and V16 Offline Eval (evaluate retrieval and answer quality); R4 ReAct (retrieval exposed as a tool the agent calls when it chooses).
- **Competes with** — K9 Long Context (hold the corpus in a large window instead of retrieving) and K11 Observational Memory (recall what the agent has seen rather than retrieve from a corpus). Choosing among K1, K9 and K11 is the primary architectural decision of Category II.
- **Conflicts** — none fundamental within the band. K1 does not conflict with K3/K4 so much as *fail* on the queries they handle (global synthesis, multi-hop relationship tracing); that failure is the signal to upgrade.

## Sources

- Lewis et al. (2020) — "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." The pattern's formal origin.
- Liu et al. (2023) — "Lost in the Middle: How Language Models Use Long Contexts."
- Anthropic (2024) — "Introducing Contextual Retrieval."
- AWS, Google Cloud, and Azure prescriptive guidance on RAG architecture.
