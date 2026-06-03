---
id: R18
title: Graph of Thoughts
type: pattern
category: Reasoning
summary: "Solve problems whose natural decomposition is not a tree by reasoning over a directed acyclic graph of thoughts in which sub-results can be *aggregated* — merged, sorted, deduplicated, combined — and not only expanded and pruned.."
when_to_use: DAG of reasoning operations; non-linear thought
also_known_as: [GoT, Graph-of-Thought Reasoning, Graph of Operations]
siblings: [R9, R10]
related: [R17]
mechanism_refs: [2, 5, 7, 8]
canonical: patterns/R18-Graph-of-Thoughts.md
derived: true
---

## Description
Solve problems whose natural decomposition is not a tree by reasoning over a directed acyclic graph of thoughts in which sub-results can be *aggregated* — merged, sorted, deduplicated, combined — and not only expanded and pruned. Sibling of R9, R10. This is a condensed digest; the canonical file (`patterns/R18-Graph-of-Thoughts.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the problem decomposes into sub-problems whose **sub-results must be combined**, not just chosen between (sort-merge, multi-source synthesis, set operations, multi-shard summarisation);
- a tree-shaped search (R9 ToT, R10 LATS) keeps discarding work that could have been merged;
- the quality gain from fusing partials clearly exceeds the extra LLM cost of running the aggregator;
- you have a way to validate aggregated thoughts (an LLM-judge, a deterministic check, or a structural constraint) so a bad merge does not silently poison the graph;

Related: [[R9-Tree-of-Thoughts]] · [[R10-LATS]] · [[R17-Self-Consistency-Voting]]
