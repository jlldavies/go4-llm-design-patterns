---
id: R7
title: Reflexion
type: pattern
category: Reasoning
summary: "Improve the reliability of an agent on a task with an automated pass/fail signal by having it retry, with a verbal critique of why the last attempt failed appended to its context — so each retry learns from a linguistic gradient instead of from weights."
when_to_use: Verbal self-critique across retries
also_known_as: [Verbal Reinforcement Learning, Self-Reflection Loop, Episodic Refinement, Reflexion Agent]
siblings: [R17, R8]
related: [H2, O5]
composes_with: [V15, K10, K12]
mechanism_refs: [2, 9, 10]
canonical: patterns/R7-Reflexion.md
derived: true
---

## Description
Improve the reliability of an agent on a task with an automated pass/fail signal by having it retry, with a verbal critique of why the last attempt failed appended to its context — so each retry learns from a linguistic gradient instead of from weights. Composes with V15, K10, K12. Sibling of R17, R8. This is a condensed digest; the canonical file (`patterns/R7-Reflexion.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task has an **automated, objective success criterion** — unit tests, a schema validator, a code executor, a goal-state assertion, a numeric grader, an LLM judge with high agreement to ground truth;
- one-shot accuracy is below the model's ceiling — failures are *diagnosable* rather than fundamental capability gaps;
- you can afford **2–5 retries** in latency and cost, and each retry is a full task re-execution;
- the failures are diverse enough that a verbal critique can identify *what specifically* went wrong (not just "it was wrong").

Related: [[V15-LLM-as-Judge]] · [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]] · [[R17-Self-Consistency-Voting]] · [[R8-Self-Refine]] · [[H2-Episodic-Self-Improvement]] · [[O5-Evaluator-Optimizer]]
