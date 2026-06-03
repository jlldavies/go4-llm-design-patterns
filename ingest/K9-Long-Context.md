---
id: K9
title: Long Context
type: pattern
category: Knowledge
summary: "Make the model's full working knowledge available by loading it all into the context window, trading per-call token cost for the elimination of a retrieval system."
when_to_use: Whole corpus fits in window; repeated queries
also_known_as: [Context Stuffing, No-RAG, Full-Context Prompting]
related: [K1, K3, K4, K11]
composes_with: [K6]
mechanism_refs: [2, 4, 5]
canonical: patterns/K9-Long-Context.md
derived: true
---

## Description
Make the model's full working knowledge available by loading it all into the context window, trading per-call token cost for the elimination of a retrieval system. Composes with K6. This is a condensed digest; the canonical file (`patterns/K9-Long-Context.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the working set fits comfortably inside a context window you can afford to pay for;
- the task needs free synthesis across the whole set — whole-document QA, full-file code reasoning, cross-document comparison;
- the scale does not justify building and operating retrieval infrastructure;
- prompt caching can amortise the repeated long prefix across many queries.

Related: [[K6-Context-Compression]] · [[K1-Vanilla-RAG]] · [[K3-GraphRAG]] · [[K4-RAPTOR]] · [[K11-Observational-Memory]]
