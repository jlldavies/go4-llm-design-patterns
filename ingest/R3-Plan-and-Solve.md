---
id: R3
title: Plan-and-Solve
type: pattern
category: Reasoning
summary: "Separate the act of *deciding what to do* from the act of *doing it* by putting them in different LLM calls, so the Planner sees the whole task before committing to an order, the Executor runs efficiently against a stable plan, and the plan itself is an inspectable artifact a human or a downstream component can read, edit, or gate on before any step runs."
when_to_use: "Two-phase: explicit plan, then execute"
also_known_as: [Plan-and-Execute, Explicit Planning, Plan-then-Execute, Upfront Planning]
related: [R1, R2, R4, R5, R9, R10, O6]
siblings: [S4]
composes_with: [O4, K8, V1, V9, V14, R7]
mechanism_refs: [2, 6, 8]
canonical: patterns/R3-Plan-and-Solve.md
derived: true
---

## Description
Separate the act of *deciding what to do* from the act of *doing it* by putting them in different LLM calls, so the Planner sees the whole task before committing to an order, the Executor runs efficiently against a stable plan, and the plan itself is an inspectable artifact a human or a downstream component can read, edit, or gate on before any step runs. Composes with O4, K8, V1, V9, V14, R7. Sibling of S4. This is a condensed digest; the canonical file (`patterns/R3-Plan-and-Solve.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is multi-step and the *order* of steps matters, but the order is not obvious from the input alone — the model needs to survey the whole task before committing;
- a plan written before execution would be useful to inspect, log, gate on, or hand to a human reviewer;
- planning is harder than execution — the steps themselves are individually tractable, the challenge is choosing and sequencing them;
- you want to use a strong (expensive) model for planning and a cheap model — or deterministic code — for execution;

Related: [[O4-Parallelization]] · [[K8-Working-Memory]] · [[V1-Human-in-the-Loop]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[R7-Reflexion]] · [[S4-Instruction-Decomposition]] · [[R1-Zero-Shot-CoT]] · [[R2-Few-Shot-CoT]] · [[R4-ReAct]] · [[R5-ReWOO]] · [[R9-Tree-of-Thoughts]] · [[R10-LATS]] · [[O6-Orchestrator-Workers]]
