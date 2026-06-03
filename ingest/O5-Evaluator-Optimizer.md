---
id: O5
title: Evaluator-Optimizer
type: pattern
category: Orchestration
summary: "Improve output quality by separating the generator and the judge into two distinct agents — different sessions, typically different setups, potentially different models — so the evaluation is genuinely independent of the work it scores, and the generator iterates on a feedback signal it cannot foresee or sandbag.."
when_to_use: Generator + judge in a quality improvement loop
also_known_as: [Generator-Critic, Judge-Optimizer, Separate Evaluator, Two-Agent Refinement]
related: [R8, R7, O9]
composes_with: [V15, V9]
mechanism_refs: [1, 3, 5, 7]
canonical: patterns/O5-Evaluator-Optimizer.md
derived: true
---

## Description
Improve output quality by separating the generator and the judge into two distinct agents — different sessions, typically different setups, potentially different models — so the evaluation is genuinely independent of the work it scores, and the generator iterates on a feedback signal it cannot foresee or sandbag. Composes with V15, V9. This is a condensed digest; the canonical file (`patterns/O5-Evaluator-Optimizer.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- output quality is the constraint and self-evaluation has measurably shared blind spots — R8 on a labelled sample shows the same-model critic accepting work humans reject;
- the success criteria are concrete enough to write a judge rubric against (correctness, completeness, format, tone, factual support) but not concrete enough for a deterministic check (no test runner, no schema validator);
- you can afford two agent slots and the per-iteration cost of running both;
- the task tolerates 2–5 sequential refinement rounds — the loop is strictly sequential by construction (output N+1 needs feedback N);

Related: [[V15-LLM-as-Judge]] · [[V9-Bounded-Execution]] · [[R8-Self-Refine]] · [[R7-Reflexion]] · [[O9-Multi-Agent-Reflection]]
