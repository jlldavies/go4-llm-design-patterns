---
id: K4
title: RAPTOR
type: pattern
category: Knowledge
summary: Answer queries that vary in scope — from a precise fact to a broad theme — by indexing the corpus as a multi-level summary tree and retrieving from the level of abstraction the query requires..
when_to_use: Variable abstraction levels; document trees
also_known_as: [Recursive Abstractive Processing for Tree-Organized Retrieval, Hierarchical RAG, Summary-Tree RAG]
mechanism_refs: [1, 7, 8]
canonical: patterns/K4-RAPTOR.md
derived: true
---

## Description
Answer queries that vary in scope — from a precise fact to a broad theme — by indexing the corpus as a multi-level summary tree and retrieving from the level of abstraction the query requires. This is a condensed digest; the canonical file (`patterns/K4-RAPTOR.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the corpus has natural hierarchical structure — books, legal codes, technical manuals, long reports;
- the query stream is *diverse in scope*, mixing pinpoint facts with broad thematic questions;
- a single chunk size has been observed to fail one end of that range.
