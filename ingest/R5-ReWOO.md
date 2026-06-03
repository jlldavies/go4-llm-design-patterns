---
id: R5
title: ReWOO
type: pattern
category: Reasoning
summary: "Separate reasoning from observation so the model plans all tool invocations once, with placeholders for the results, and never re-enters the loop until every external call has completed and the evidence is ready to synthesise."
when_to_use: Independent tool calls; 5$\times$ token efficiency vs ReAct
also_known_as: [Reasoning Without Observation, Decoupled Reasoning, Plan-Execute-Solve, Foreseeable Reasoning]
related: [R4, R3, R7, R9, R10, S6, S2]
composes_with: [O4, V9, V14, K7, O3]
conflicts_with: [R4]
mechanism_refs: [2, 5, 7, 8]
canonical: patterns/R5-ReWOO.md
derived: true
---

## Description
Separate reasoning from observation so the model plans all tool invocations once, with placeholders for the results, and never re-enters the loop until every external call has completed and the evidence is ready to synthesise. In tension with R4. Composes with O4, V9, V14, K7, O3. This is a condensed digest; the canonical file (`patterns/R5-ReWOO.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task decomposes into tool calls whose *choice* and *arguments* are knowable upfront — typically independent lookups across multiple sources, multi-hop Q&A with a known hop structure, report generation from enumerated data sources;
- token efficiency or latency-via-parallelism is a material lever;
- the tool calls can run in parallel or with simple variable substitution (one tool's output feeds the next as a value, not as a branching decision);
- the working set of tools is small and stable (no need for the model to *discover* tools mid-run).

Related: [[R4-ReAct]] · [[O4-Parallelization]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[K7-Context-Pruning]] · [[O3-Routing]] · [[R3-Plan-and-Solve]] · [[R7-Reflexion]] · [[R9-Tree-of-Thoughts]] · [[R10-LATS]] · [[S6-Output-Template]] · [[S2-Few-Shot]]
