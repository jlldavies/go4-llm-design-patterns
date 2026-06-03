---
id: K8
title: Working Memory / Scratchpad
type: pattern
category: Knowledge
summary: "Externalise the model's working state into a persistent, inspectable region of the context, so intermediate results survive from one step to the next within a task."
when_to_use: Explicit in-context state the model writes to itself
also_known_as: [Scratchpad, Cognitive Scratchpad, Agent Notepad, In-Context Working Memory]
related: [K6, K7, K10, K11, K12, R4, R3, V10]
mechanism_refs: [1, 2, 3, 4, 10]
canonical: patterns/K8-Working-Memory.md
derived: true
---

## Description
Externalise the model's working state into a persistent, inspectable region of the context, so intermediate results survive from one step to the next within a task. This is a condensed digest; the canonical file (`patterns/K8-Working-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a task has multiple steps that build on each other;
- the task involves planning and the plan needs a stable home;
- the agent runs a ReAct or similar loop where observations accumulate;
- losing an intermediate result would cause an error.

Related: [[K6-Context-Compression]] · [[K7-Context-Pruning]] · [[K10-Long-Term-Memory]] · [[K11-Observational-Memory]] · [[K12-Karpathy-Memory]] · [[R4-ReAct]] · [[R3-Plan-and-Solve]] · [[V10-Checkpointing]]
