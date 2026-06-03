---
id: K5
title: Adaptive RAG
type: pattern
category: Knowledge
summary: "Make retrieval conditional and self-correcting, so the system retrieves only when retrieval helps and recovers when retrieval fails, instead of retrieving blindly on every query and trusting whatever returns.."
when_to_use: Gate retrieval; self-critique retrieved results
also_known_as: [Self-Reflective RAG, Adaptive Retrieval, Agentic RAG]
mechanism_refs: [2, 7, 8]
canonical: patterns/K5-Adaptive-RAG.md
derived: true
---

## Description
Make retrieval conditional and self-correcting, so the system retrieves only when retrieval helps and recovers when retrieval fails, instead of retrieving blindly on every query and trusting whatever returns. This is a condensed digest; the canonical file (`patterns/K5-Adaptive-RAG.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the query stream is mixed — some queries need retrieval, some are answerable from weights;
- the task is factuality-critical and a silent retrieval miss is unacceptable;
- the corpus may be stale or incomplete, so retrieval failure is a realistic event.
