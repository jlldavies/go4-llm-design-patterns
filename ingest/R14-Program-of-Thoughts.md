---
id: R14
title: Program of Thoughts
type: pattern
category: Reasoning
summary: "For tasks whose hard part is computation — arithmetic, algebra, financial sums, statistical operations, symbolic manipulation — let the model write a short program and let a Python (or equivalent) interpreter compute the answer, instead of asking the model to compute in natural-language tokens.."
when_to_use: Delegate computation to a deterministic interpreter
also_known_as: [PoT, Program-Aided Language Models]
siblings: [R13]
related: [V8]
composes_with: [R17]
mechanism_refs: [2, 7]
canonical: patterns/R14-Program-of-Thoughts.md
derived: true
---

## Description
For tasks whose hard part is computation — arithmetic, algebra, financial sums, statistical operations, symbolic manipulation — let the model write a short program and let a Python (or equivalent) interpreter compute the answer, instead of asking the model to compute in natural-language tokens. Composes with R17. Sibling of R13. This is a condensed digest; the canonical file (`patterns/R14-Program-of-Thoughts.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task requires numerical or symbolic computation — arithmetic, percentages, ratios, statistics, financial formulas, date math, unit conversion, simple algebra;
- correctness on the computation step is non-negotiable (financial, scientific, engineering, regulatory contexts);
- the program to compute the answer is short and self-contained — input values are in the prompt or fetched once;
- the answer is a value (number, string, list) the interpreter can print, not a long-form narrative.

Related: [[R17-Self-Consistency-Voting]] · [[R13-CodeAct]] · [[V8-Tool-Sandboxing]]
