---
id: R14
title: Program of Thoughts
type: pattern
category: Reasoning
summary: "For tasks whose hard part is computation — arithmetic, algebra, financial sums, statistical operations, symbolic manipulation — let the model write a short program and let a Python (or equivalent) interpreter compute the answer, instead of asking the model to compute in natural-language tokens."
when_to_use: Delegate computation to a deterministic interpreter
also_known_as: [PoT, Program-Aided Language Models, Code-Augmented Reasoning, Computational Reasoning, Disentangled Computation]
siblings: [R13]
related: [R1, R2, V8, R7, R5]
composes_with: [R17, V9, V14, O4]
mechanism_refs: [2, 7]
canonical: patterns/R14-Program-of-Thoughts.md
derived: true
---

## Description
For tasks whose hard part is computation — arithmetic, algebra, financial sums, statistical operations, symbolic manipulation — let the model write a short program and let a Python (or equivalent) interpreter compute the answer, instead of asking the model to compute in natural-language tokens. Composes with R17, V9, V14, O4. Sibling of R13. This is a condensed digest; the canonical file (`patterns/R14-Program-of-Thoughts.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task requires numerical or symbolic computation — arithmetic, percentages, ratios, statistics, financial formulas, date math, unit conversion, simple algebra;
- correctness on the computation step is non-negotiable (financial, scientific, engineering, regulatory contexts);
- the program to compute the answer is short and self-contained — input values are in the prompt or fetched once;
- the answer is a value (number, string, list) the interpreter can print, not a long-form narrative.

Related: [[R17-Self-Consistency-Voting]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[O4-Parallelization]] · [[R13-CodeAct]] · [[R1-Zero-Shot-CoT]] · [[R2-Few-Shot-CoT]] · [[V8-Tool-Sandboxing]] · [[R7-Reflexion]] · [[R5-ReWOO]]
