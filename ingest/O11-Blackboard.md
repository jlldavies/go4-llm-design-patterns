---
id: O11
title: Blackboard System
type: pattern
category: Orchestration
summary: "Replace a fixed plan or a central orchestrator's task assignments with a shared memory whose evolving state, read by a thin control unit, decides which specialist runs next — so the set and order of contributors adapts to what has accumulated, not to what was decreed up front.."
when_to_use: Asynchronous shared state; agents post and consume
also_known_as: [Shared Memory Board, Global Workspace, bMAS]
related: [O6, K10, O2]
composes_with: [K10]
mechanism_refs: [2, 4, 6]
canonical: patterns/O11-Blackboard.md
derived: true
---

## Description
Replace a fixed plan or a central orchestrator's task assignments with a shared memory whose evolving state, read by a thin control unit, decides which specialist runs next — so the set and order of contributors adapts to what has accumulated, not to what was decreed up front. Composes with K10. This is a condensed digest; the canonical file (`patterns/O11-Blackboard.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent population is large, heterogeneous, or open — a central planner cannot reliably enumerate "who does what";
- the problem shape is genuinely unknown until evidence accumulates — the right next move depends on what has just been written;
- multiple specialists need to see one another's intermediate conclusions to make their own decisions (mutual context, not isolation);
- the audit trail of *how* a conclusion was reached matters as much as the answer itself.

Related: [[K10-Long-Term-Memory]] · [[O6-Orchestrator-Workers]] · [[O2-Prompt-Chaining]]
