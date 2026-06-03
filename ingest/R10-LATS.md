---
id: R10
title: Language Agent Tree Search (LATS)
type: pattern
category: Reasoning
summary: "Search the solution space of an agentic task with full Monte Carlo Tree Search — selection by UCB, expansion, simulation, and value backpropagation — using the LLM as action generator, value estimator, and verbal critic, so the agent can revisit any node, redirect from any dead end, and converge on high-quality trajectories on problems that defeat single-path patterns."
when_to_use: MCTS + ReAct + Reflexion unified
also_known_as: [LATS, MCTS for LLM Agents, Monte Carlo Agent Search]
siblings: [R9]
related: [R4, R7, R9, V9, R3]
composes_with: [V14, V15, R11, O17]
mechanism_refs: [5, 7, 8]
canonical: patterns/R10-LATS.md
derived: true
---

## Description
Search the solution space of an agentic task with full Monte Carlo Tree Search — selection by UCB, expansion, simulation, and value backpropagation — using the LLM as action generator, value estimator, and verbal critic, so the agent can revisit any node, redirect from any dead end, and converge on high-quality trajectories on problems that defeat single-path patterns. Composes with V14, V15, R11, O17. Sibling of R9. This is a condensed digest; the canonical file (`patterns/R10-LATS.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is hard enough that ReAct (R4), Reflexion (R7), and Tree of Thoughts (R9) have all been tried and demonstrably fail;
- the task admits a useful value signal — a verifier, a test suite, a programmatic correctness check, or at minimum a reliable LLM critic — that can score partial trajectories;
- correctness or quality is worth roughly 10$\times$ ToT's cost (10–100$\times$ ReAct's);
- the task is bounded enough that a tree with depth in the tens and branching factor of 3–5 can plausibly contain a solution.

Related: [[V14-Trajectory-Logging]] · [[V15-LLM-as-Judge]] · [[R11-Buffer-of-Thoughts]] · [[O17-Agent-Isolation]] · [[R9-Tree-of-Thoughts]] · [[R4-ReAct]] · [[R7-Reflexion]] · [[V9-Bounded-Execution]] · [[R3-Plan-and-Solve]]
