---
id: K6
title: Context Compression
type: pattern
category: Knowledge
summary: "Keep a long-running task within the context window by summarising older or bulky content into a denser form, preserving as much of its information as the reclaimed space allows."
when_to_use: Reduce context size; session history management
also_known_as: [Conversation Compression, History Summarisation, Context Summarisation, Compaction]
related: [K7, K9, K4, K10, K11, K12]
composes_with: [K8]
mechanism_refs: [1, 2, 4, 7]
canonical: patterns/K6-Context-Compression.md
derived: true
---

## Description
Keep a long-running task within the context window by summarising older or bulky content into a denser form, preserving as much of its information as the reclaimed space allows. Composes with K8. This is a condensed digest; the canonical file (`patterns/K6-Context-Compression.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is a long-running agent session — at scale this is mandatory, not optional;
- a multi-turn conversation has grown past roughly half the window;
- the agent produces bulky tool outputs (SQL results, file contents, API dumps) that accumulate.

Related: [[K8-Working-Memory]] · [[K7-Context-Pruning]] · [[K9-Long-Context]] · [[K4-RAPTOR]] · [[K10-Long-Term-Memory]] · [[K11-Observational-Memory]] · [[K12-Karpathy-Memory]]
