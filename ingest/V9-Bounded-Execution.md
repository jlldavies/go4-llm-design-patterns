---
id: V9
title: Bounded Execution
type: pattern
category: Reliability
summary: "Apply hard, externally-enforced limits on every dimension along which an agent loop can run away — iterations, tool calls, tokens, wall-clock, and dollars — so that a miscalibrated agent fails fast at a known bound instead of consuming unbounded resources before someone notices.."
when_to_use: "Hard caps on steps, cost, wall-time, depth — required for every loop"
also_known_as: [Circuit Breaker]
composes_with: [V10, V14, V1]
mechanism_refs: [2, 3, 4]
canonical: patterns/V9-Bounded-Execution.md
derived: true
---

## Description
Apply hard, externally-enforced limits on every dimension along which an agent loop can run away — iterations, tool calls, tokens, wall-clock, and dollars — so that a miscalibrated agent fails fast at a known bound instead of consuming unbounded resources before someone notices. Composes with V10, V14, V1. This is a condensed digest; the canonical file (`patterns/V9-Bounded-Execution.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent contains *any* loop — reasoning loop, evaluator loop, refine loop, search loop, recovery loop (this is essentially every R-band loop pattern, every loop-shaped orchestration pattern, and every adaptive K-pattern);
- the agent calls tools and the cost of an unbounded tool-call sequence is material;
- the deployment is production or anywhere unattended (no human in the room to notice a runaway);
- one component's budget overrun would cascade into shared rate limits, shared cost pools, or shared queues.

Related: [[V10-Checkpointing]] · [[V14-Trajectory-Logging]] · [[V1-Human-in-the-Loop]]
