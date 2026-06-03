---
id: K2
title: Query Transformation
type: pattern
category: Knowledge
summary: "Improve retrieval quality by transforming the user's raw query into a form better matched to the corpus, in the moment between the user submitting the query and the retriever running."
when_to_use: Improve retrieval by rewriting the query first
also_known_as: [Query Rewriting, Pre-Retrieval Query Optimisation]
related: [K1, K5, R19]
composes_with: [K3, K4, K5]
mechanism_refs: [1, 8]
canonical: patterns/K2-Query-Transformation.md
derived: true
---

## Description
Improve retrieval quality by transforming the user's raw query into a form better matched to the corpus, in the moment between the user submitting the query and the retriever running. Composes with K3, K4, K5. This is a condensed digest; the canonical file (`patterns/K2-Query-Transformation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- raw-query retrieval (K1) shows misses on questions that *do* have answers in the corpus;
- queries are short, ambiguous, or phrased unlike the corpus;
- the system is conversational and queries depend on prior turns;
- queries are compound and need several distinct passages.

Related: [[K3-GraphRAG]] · [[K4-RAPTOR]] · [[K5-Adaptive-RAG]] · [[K1-Vanilla-RAG]] · [[R19-Step-Back-Prompting]]
