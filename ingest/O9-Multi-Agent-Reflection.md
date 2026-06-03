---
id: O9
title: Multi-Agent Reflection
type: pattern
category: Orchestration
summary: "Get genuinely independent evaluation of an output by running several differently-configured critic agents in parallel against it, then synthesising their critiques — so the verdict reflects multiple lenses no single critic (or self-critique) would produce.."
when_to_use: Multiple independent reviewers on a single output
also_known_as: [Ensemble Critique, Parallel Critique, Devil's Advocate Ensemble, Multi-Critic Review, Reviewer Ensemble]
related: [O5, R8, O12]
siblings: [R17]
composes_with: [O4, V15, S6]
mechanism_refs: [1, 7]
canonical: patterns/O9-Multi-Agent-Reflection.md
derived: true
---

## Description
Get genuinely independent evaluation of an output by running several differently-configured critic agents in parallel against it, then synthesising their critiques — so the verdict reflects multiple lenses no single critic (or self-critique) would produce. Composes with O4, V15, S6. Sibling of R17. This is a condensed digest; the canonical file (`patterns/O9-Multi-Agent-Reflection.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the output needs to clear **multiple distinct lenses** that a single rubric would dilute (security, performance, accuracy, compliance, style, factuality);
- the cost of a missed defect on any one lens is high enough to justify N parallel critic calls plus a synthesiser;
- you can write **N stable, distinct critic personas** with non-overlapping criteria — if the lenses collapse into the same thing, you are paying for redundancy;
- the loop can tolerate at least one synchronous "all critics finish" barrier per round — fan-out latency is the slowest critic, not the average;

Related: [[O4-Parallelization]] · [[V15-LLM-as-Judge]] · [[S6-Output-Template]] · [[R17-Self-Consistency-Voting]] · [[O5-Evaluator-Optimizer]] · [[R8-Self-Refine]] · [[O12-Debate-Deliberation]]
