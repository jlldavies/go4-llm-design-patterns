# Conflicts — Knowledge

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Connection A — K6/K7 $\sim$ K11  {#connection-a}

**Type:** Composability Tension ($\sim$)

K6 (Context Compression) rewrites earlier context spans; K7 (Context Pruning) deletes them. Both operations reposition subsequent tokens, changing their sequence offsets and invalidating the KV cache states for those positions and all positions after them (mechanism 3, 5). K11 (Observational Memory) requires append-only writes precisely because any edit to a prior position invalidates the KV cache.

**Interaction:** K6/K7 are incompatible with K11's caching model unless applied only to content appended after the last stable cache boundary. If K11 is the memory store and K6/K7 are applied to that store, prefix caching on the K11 block is impossible.

**Resolution:** When using K11 with K6/K7: apply compression/pruning only to the variable session content that follows the K11 stable prefix. Never compress or prune content inside the K11 stable-prefix region. Treat the K11 boundary as a cache boundary that K6/K7 must not cross.

---

## Connection D — K1 $\leftrightarrow$ K9  {#connection-d}

**Type:** Direct Tension $\leftrightarrow$

K1 (Vanilla RAG) pays n² attention cost at retrieval time over a small context (retrieved chunks only). K9 (Long Context) pays n² at prefill time over a large context (entire document set). The received wisdom — "use K1 for large corpora, K9 for small" — is incomplete.

**The mechanistic correction (mechanism 5):** At high query frequency per session over the same stable document set, K9 + prefix caching can beat K1 on both cost and accuracy. The K9 prefill is paid once (the cache write); subsequent queries over the same corpus pay ~10% of that cost. K1 re-fetches and re-chunks on every query.

**Resolution threshold:** If the number of queries per session over the same stable document set exceeds ~10, model K9 + caching as potentially cheaper than K1. The U-shaped recall disadvantage of K9 (mechanism 4) is real but may be outweighed by the retrieval quality loss of K1 (wrong chunks returned). Measure both.

---

## Knowledge vs Knowledge

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| K1 (Vanilla RAG) | $\uparrow$ | K3 (GraphRAG) | K1 for simple, direct lookup; K3 for multi-hop relational queries. Upgrade when queries require understanding entity relationships. K3 has 2-5× index build cost. |
| K1 (Vanilla RAG) | $\uparrow$ | K4 (RAPTOR) | K1 for specific queries; K4 for breadth across large heterogeneous corpora. Upgrade when query diversity is high and K1 retrieval quality is inconsistent. |
| K1 (Vanilla RAG) | $\leftrightarrow$ | K9 (Long Context) | The primary architectural fork of Category II: retrieve a selected subset, or place the whole working set in a large window. K1 scales to any corpus size; K9 avoids retrieval infrastructure and retrieval misses when the working set fits an affordable window. |
| K6 (Context Compression) | $\leftrightarrow$ | K11 (Observational Memory) | K6 compresses what is in context; K11 prioritises what goes into context. They work together but ordering matters: K11 selects, K6 compresses what K11 selected. |
| K10 (Long-Term Memory) | $\leftrightarrow$ | K12 (Karpathy Memory) | K10 stores flat fact-shaped items in a vector store, retrieved by similarity. K12 stores structured curated notes the LLM authors, retrieved by name/topic/inclusion. The read pattern decides — similarity $\to$ K10; structural navigation $\to$ K12. Often run together (facts in K10, structured understanding in K12), not as alternatives. |
| K11 (Observational Memory) | $\sim$ | K12 (Karpathy Memory) | The *raw-log* and *curated-notes* branches of the Karpathy framing. K11 holds the raw activity record cheaply via caching; K12 has the LLM digest it into structured dense notes. K11 typically feeds K12 — the K12 Curator reads K11's log as input. Cache hostility is the tension: K12 curations change the prefix K11 wants stable, so schedule curations at session boundaries, not mid-session. |

*Note: the former K10 Episodic $\sim$ K11 Semantic tension is now an intra-pattern choice between variants of K10 Long-Term Memory, not a cross-pattern conflict. The former K13 Agent Isolation $\leftrightarrow$ K11 tension moved with Agent Isolation to Orchestration (O17); see O17's Related Patterns.*

## Knowledge vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| K8 (Working Memory) | $\sim$ | R9 (Tree of Thoughts) | ToT generates many branches; all branches share the same working memory. Without explicit per-branch scratchpad management, branches contaminate each other. Each ToT branch needs its own K8 instance. |
| K11 (Observational Memory) | $\sim$ | R5 (ReWOO) | ReWOO plans all observations before executing. K11 provides what the agent has already observed. If K11 contains prior observations relevant to the current plan, inject them before planning — not mid-execution. |
