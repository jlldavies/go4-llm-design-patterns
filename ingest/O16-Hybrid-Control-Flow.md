---
id: O16
title: Hybrid Control Flow
type: pattern
category: Orchestration
summary: "Build a single agent that is competent across all phases of a complex task by stacking the loop primitives each phase needs — exploration on a ReAct loop, planning on plan-execute, repair on generate-test-repair, recovery on bounded retry — rather than trying to force every phase through one primitive."
when_to_use: Stack multiple loop primitives; most production agents are this
also_known_as: [Primitive Stack, Layered Control, Composite Loop Architecture, Stacked-Primitive Scaffold]
composes_with: [R4, R3, R10, O17, O4, V14, V15]
related: [O8, O6, O2, V9]
mechanism_refs: [2, 3, 5]
canonical: patterns/O16-Hybrid-Control-Flow.md
derived: true
---

## Description
Build a single agent that is competent across all phases of a complex task by stacking the loop primitives each phase needs — exploration on a ReAct loop, planning on plan-execute, repair on generate-test-repair, recovery on bounded retry — rather than trying to force every phase through one primitive. Composes with R4, R3, R10, O17, O4, V14, V15. This is a condensed digest; the canonical file (`patterns/O16-Hybrid-Control-Flow.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task has *distinct phases* with different control needs (e.g. explore, plan, implement, verify) and no single primitive serves all of them;
- you have already tried a single-primitive agent (R4 alone, or R3 alone) and observed it fail in specific phases;
- you can name the transitions between phases explicitly (signal, predicate, or judge that ends one layer and starts the next);
- you can bound every loop layer with V9 Bounded Execution — without bounds, a multi-layer scaffold is multiple ways to run forever.

Related: [[R4-ReAct]] · [[R3-Plan-and-Solve]] · [[R10-LATS]] · [[O17-Agent-Isolation]] · [[O4-Parallelization]] · [[V14-Trajectory-Logging]] · [[V15-LLM-as-Judge]] · [[O8-Loop-Agent]] · [[O6-Orchestrator-Workers]] · [[O2-Prompt-Chaining]] · [[V9-Bounded-Execution]]
