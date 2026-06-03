---
id: R16
title: Talker-Reasoner
type: pattern
category: Reasoning
summary: "Decouple the latency budget of *responding* from the latency budget of *thinking*, so the agent can answer every turn within a hard real-time bound while still performing arbitrarily deep reasoning whose results land when they are ready."
when_to_use: Fast responder + slow deliberative reasoner in parallel
also_known_as: [System 1 / System 2 Architecture, Fast-Slow Agent, Dual-Process Agent, Thinking Fast and Slow Agent]
siblings: [H6]
related: [R3, R4, R1]
composes_with: [K8, K12, O3, V9, V14, R3, R4, R7]
mechanism_refs: [2, 3, 8, 10]
canonical: patterns/R16-Talker-Reasoner.md
derived: true
---

## Description
Decouple the latency budget of *responding* from the latency budget of *thinking*, so the agent can answer every turn within a hard real-time bound while still performing arbitrarily deep reasoning whose results land when they are ready. Composes with K8, K12, O3, V9, V14, R3, R4, R7. Sibling of H6. This is a condensed digest; the canonical file (`patterns/R16-Talker-Reasoner.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the system is interactive and the per-turn latency budget is hard (sub-second voice, sub-2s chat) yet the task quality requires multi-step reasoning, tool use, or planning;
- workloads are mixed — most turns are conversational, some require deliberation, and the agent cannot tell in advance how many;
- you can afford concurrent inference (two models or two sessions running in parallel);
- the shared state has a natural place to write deliberation outputs (working memory, a plan slot, a recommendation field) without rewriting the Talker's prompt.

Related: [[K8-Working-Memory]] · [[K12-Karpathy-Memory]] · [[O3-Routing]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[R3-Plan-and-Solve]] · [[R4-ReAct]] · [[R7-Reflexion]] · [[H6-Continuous-Inner-Monologue]] · [[R1-Zero-Shot-CoT]]
