---
id: K3
title: GraphRAG
type: pattern
category: Knowledge
summary: Answer queries that require connecting information across many documents — multi-hop relationship questions and whole-corpus synthesis — by indexing the corpus as a graph of entities and relationships instead of a flat set of chunks.
when_to_use: Multi-hop reasoning; entity relationships; global synthesis
cost: high
also_known_as: [Graph Retrieval, Entity Graph RAG, Knowledge-Graph RAG, Microsoft GraphRAG]
related: [K1, K9]
siblings: [K4]
composes_with: [K2, K5]
mechanism_refs: [1, 2, 6, 8]
canonical: patterns/K3-GraphRAG.md
derived: true
---

## Description
Answer queries that require connecting information across many documents — multi-hop relationship questions and whole-corpus synthesis — by indexing the corpus as a graph of entities and relationships instead of a flat set of chunks. Composes with K2, K5. Sibling of K4. This is a condensed digest; the canonical file (`patterns/K3-GraphRAG.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the corpus is large and rich in entities and relationships;
- queries trace relationships ("how is X connected to Y") or ask for corpus-wide themes;
- the domain is relational by nature — intelligence analysis, legal discovery, scientific literature, fraud and risk networks.

Related: [[K2-Query-Transformation]] · [[K5-Adaptive-RAG]] · [[K4-RAPTOR]] · [[K1-Vanilla-RAG]] · [[K9-Long-Context]]
