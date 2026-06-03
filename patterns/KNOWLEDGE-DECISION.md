# Knowledge Pattern Selection

## Decision Flow

```
Is this a recurring workflow type with known context requirements?
  → K13 (Retrieval Bundle): specify the exact context bundle BEFORE writing retrieval code
    Prevents the rediscovery problem (up to 85% of token budget on context assembly)

Does the entire working set fit an affordable context window?
  → Benchmark K9 (Long Context) vs K1 (Vanilla RAG) at your actual corpus size
    K9 wins when: corpus fits, queries are diverse, retrieval precision is hard to tune
    K1 wins when: corpus is large, queries are targeted, caching matters

Do you need in-context retrieval?
  Are queries multi-hop or relational? → K3 (GraphRAG)
  Variable abstraction levels required? → K4 (RAPTOR)
  Factuality-critical, possibly stale corpus? → K5 (Adaptive RAG)
  Query/document mismatch suspected? → K2 (Query Transformation) wrapping K1
  Default retrieval: → K1 (Vanilla RAG)

Does the context window need management during a session?
  Remove spent/irrelevant spans (lossless)? → K7 (Context Pruning) — preserves prefix cache
  Summarise overflowing history (lossy)? → K6 (Context Compression)
    ⚠ K6 and K7 invalidate the provider prefix cache
  Agent needs explicit scratchpad? → K8 (Working Memory)

Do you need cross-session memory?
  Flat facts across sessions? → K10 (Long-Term Memory)
  Append-only activity log + prefix caching? → K11 (Observational Memory)
  LLM-curated structured notes? → K12 (Karpathy Memory)
  K11 and K12 are complementary branches of the same memory strategy — run together
```

## Context Budget Guide

| Pattern | Context cost | Cache impact |
|---|---|---|
| K1 Vanilla RAG | Chunks only (variable) | Neutral |
| K2 Query Transformation | 1–3 extra LLM calls | Neutral |
| K3 GraphRAG | High (graph + summaries) | Neutral |
| K4 RAPTOR | Medium (hierarchical summaries) | Neutral |
| K5 Adaptive RAG | +1–2 LLM calls per query | Neutral |
| K6 Context Compression | Saves tokens; **breaks prefix cache** | Cache-busting |
| K7 Context Pruning | Saves tokens; **breaks prefix cache** | Cache-busting |
| K8 Working Memory | Small scratchpad overhead | Neutral if at end of context |
| K9 Long Context | Full corpus in window | High but cacheable |
| K10 Long-Term Memory | Retrieved facts only | Neutral |
| K11 Observational Memory | Append-only log | **Cache-friendly** |
| K12 Karpathy Memory | Dense curated notes | Cacheable if stable |
| K13 Retrieval Bundle | Design-time specification; no runtime cost | Enables caching discipline |
