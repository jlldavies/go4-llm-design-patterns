---
id: R17
title: Self-Consistency Voting
type: pattern
category: Reasoning
summary: "Improve the reliability of a reasoning step by sampling N independent attempts at the *same* prompt and selecting the answer they most agree on, instead of trusting a single greedy decode.."
when_to_use: Sample N reasoning paths; majority vote
also_known_as: [Self-Consistency, Self-Consistency Decoding, Ensemble Sampling, Majority Vote, SC Prompting]
siblings: [R7, R8]
related: [O5, S8, V15, H3]
composes_with: [V9, V15]
conflicts_with: [H3]
mechanism_refs: [2, 7, 8]
canonical: patterns/R17-Self-Consistency-Voting.md
derived: true
---

## Description
Improve the reliability of a reasoning step by sampling N independent attempts at the *same* prompt and selecting the answer they most agree on, instead of trusting a single greedy decode. In tension with H3. Composes with V9, V15. Sibling of R7, R8. This is a condensed digest; the canonical file (`patterns/R17-Self-Consistency-Voting.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task has an objectively correct or strongly preferred answer (math, multiple-choice, classification, code with tests, structured extraction);
- the model's accuracy is below its capability ceiling — single-shot is noisy but often nearly right;
- you can afford N$\times$ the cost and latency of a single call;
- you need a confidence signal alongside the answer (agreement rate is one).

Related: [[H3-Entropy-Driven-Curiosity]] · [[V9-Bounded-Execution]] · [[V15-LLM-as-Judge]] · [[R7-Reflexion]] · [[R8-Self-Refine]] · [[O5-Evaluator-Optimizer]] · [[S8-Meta-Prompt]]
