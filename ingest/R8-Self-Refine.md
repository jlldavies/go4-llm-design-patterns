---
id: R8
title: Self-Refine
type: pattern
category: Reasoning
summary: "Improve the quality of an output by having the same model that produced it write a critique of it and revise from that critique, iterating until a stopping condition — without any external evaluator, ground-truth signal, or second model.."
when_to_use: Iterative in-session quality improvement
also_known_as: [Generate-Critique-Refine, Iterative Self-Improvement, Self-Feedback Refinement, Self-Editing Loop]
siblings: [R7, R17]
related: [O5]
composes_with: [S6, V9]
mechanism_refs: [1, 4, 7]
canonical: patterns/R8-Self-Refine.md
derived: true
---

## Description
Improve the quality of an output by having the same model that produced it write a critique of it and revise from that critique, iterating until a stopping condition — without any external evaluator, ground-truth signal, or second model. Composes with S6, V9. Sibling of R7, R17. This is a condensed digest; the canonical file (`patterns/R8-Self-Refine.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- single-shot output is *close* but consistently misses a constraint, a polish step, or a structural improvement the model would recognise if asked;
- there is **no automated pass/fail signal** (no tests, no schema, no executor) — if there were, **R7 Reflexion** is stronger and cheaper per round;
- the task is open-ended enough that voting across samples (R17) does not apply — there is no "modal answer" to converge on (creative writing, structured drafting, summarisation, code review);
- the budget tolerates 2–5$\times$ the single-shot cost for a measurable quality lift;

Related: [[S6-Output-Template]] · [[V9-Bounded-Execution]] · [[R7-Reflexion]] · [[R17-Self-Consistency-Voting]] · [[O5-Evaluator-Optimizer]]
