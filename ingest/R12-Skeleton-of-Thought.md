---
id: R12
title: Skeleton-of-Thought
type: pattern
category: Reasoning
summary: "Cut end-to-end latency on long-form, structurally separable answers by writing the outline once and expanding every point in parallel, instead of decoding the whole answer token-by-token in a single sequential stream.."
when_to_use: Outline first; generate sections in parallel
also_known_as: [SoT, Outline-First Generation, Parallel Decoding via Skeleton]
siblings: [O4]
related: [R3, S4]
mechanism_refs: [6, 7]
canonical: patterns/R12-Skeleton-of-Thought.md
derived: true
---

## Description
Cut end-to-end latency on long-form, structurally separable answers by writing the outline once and expanding every point in parallel, instead of decoding the whole answer token-by-token in a single sequential stream. Sibling of O4. This is a condensed digest; the canonical file (`patterns/R12-Skeleton-of-Thought.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the expected answer is long-form and naturally decomposes into 3+ roughly-independent sections;
- wall-clock latency matters more than incremental accuracy;
- parallel-call budget is available (either parallel API requests or batched decoding on a hosted model);
- coherence *between* sections is not load-bearing — each section can stand on its own given the outline.

Related: [[O4-Parallelization]] · [[R3-Plan-and-Solve]] · [[S4-Instruction-Decomposition]]
