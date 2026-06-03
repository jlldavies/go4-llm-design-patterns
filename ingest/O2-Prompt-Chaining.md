---
id: O2
title: Prompt Chaining
type: pattern
category: Orchestration
summary: "Decompose a task into a known, ordered sequence of LLM calls with deterministic transitions between them, so each step has its own focused setup and can be independently tested, logged, and gated — and so the whole pipeline is predictable in cost and behaviour."
when_to_use: Fixed-sequence pipeline; output of step N feeds step N+1
also_known_as: [Sequential Pipeline, LLM Pipeline, Fixed Workflow, Chain Workflow]
related: [S4, O6, R3, V9, R4, O5]
composes_with: [O4, O3, V15, R20, V14, S6]
mechanism_refs: [2, 3, 5]
canonical: patterns/O2-Prompt-Chaining.md
derived: true
---

## Description
Decompose a task into a known, ordered sequence of LLM calls with deterministic transitions between them, so each step has its own focused setup and can be independently tested, logged, and gated — and so the whole pipeline is predictable in cost and behaviour. Composes with O4, O3, V15, R20, V14, S6. This is a condensed digest; the canonical file (`patterns/O2-Prompt-Chaining.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the sequence of LLM steps is known at design time and does not depend on the input;
- the chain is short enough (~2–7 steps) to be wired by hand and reasoned about end-to-end;
- at least one boundary between steps needs to do real work — inspection, validation, gating, logging, parallel fan-out, or different model settings per step;
- predictable cost, predictable latency, and step-level isolation matter (the failure mode of a single step does not propagate silently);

Related: [[O4-Parallelization]] · [[O3-Routing]] · [[V15-LLM-as-Judge]] · [[R20-Chain-of-Verification]] · [[V14-Trajectory-Logging]] · [[S6-Output-Template]] · [[S4-Instruction-Decomposition]] · [[O6-Orchestrator-Workers]] · [[R3-Plan-and-Solve]] · [[V9-Bounded-Execution]] · [[R4-ReAct]] · [[O5-Evaluator-Optimizer]]
