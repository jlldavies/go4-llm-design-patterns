---
id: K1
title: Vanilla RAG
type: pattern
category: Knowledge
summary: "Ground a model's response in a specific, external, updatable corpus by retrieving the passages relevant to each query at query time and injecting them into the prompt — without retraining the model."
when_to_use: Q&A over external corpus; citations required
also_known_as: [Naive RAG, Basic Retrieval, Classic Retrieval-Augmented Generation]
related: [K2, K3, K4, K5, K9, K11]
composes_with: [K6, K7, S6, V15, V16, R4]
mechanism_refs: [1, 4]
canonical: patterns/K1-Vanilla-RAG.md
derived: true
---

## Description
Ground a model's response in a specific, external, updatable corpus by retrieving the passages relevant to each query at query time and injecting them into the prompt — without retraining the model. Composes with K6, K7, S6, V15, V16, R4. This is a condensed digest; the canonical file (`patterns/K1-Vanilla-RAG.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is question-answering over a static or slowly-changing document corpus — product documentation, policies, manuals, a knowledge base;
- answers must be grounded in, and cite, specific sources;
- the corpus is too large for the context window, but any single query needs only a small, locally-coherent slice of it;
- the knowledge changes often enough that retraining is impractical.

Related: [[K6-Context-Compression]] · [[K7-Context-Pruning]] · [[S6-Output-Template]] · [[V15-LLM-as-Judge]] · [[V16-Offline-Eval]] · [[R4-ReAct]] · [[K2-Query-Transformation]] · [[K3-GraphRAG]] · [[K4-RAPTOR]] · [[K5-Adaptive-RAG]] · [[K9-Long-Context]] · [[K11-Observational-Memory]]
