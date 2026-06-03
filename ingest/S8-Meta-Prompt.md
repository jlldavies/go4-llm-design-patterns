---
id: S8
title: Meta-Prompt
type: pattern
category: Signal
summary: "Replace hand-crafted prompt engineering with a measured generate-evaluate-select loop, in which an LLM proposes candidate prompts, an evaluator scores them against a task signal, and the best candidate is kept and iterated on."
when_to_use: "Self-optimising workflows, automated prompt tuning"
also_known_as: [Auto-Prompting, Prompt Optimisation, Self-Generated Prompts, Automatic Prompt Engineering, Recursive Meta Prompting]
related: [R17, V15, S1, S6, S9, K12, O5]
composes_with: [V9, V14, S3, S5, S6]
siblings: [R7]
mechanism_refs: [2, 5]
canonical: patterns/S8-Meta-Prompt.md
derived: true
---

## Description
Replace hand-crafted prompt engineering with a measured generate-evaluate-select loop, in which an LLM proposes candidate prompts, an evaluator scores them against a task signal, and the best candidate is kept and iterated on. Composes with V9, V14, S3, S5, S6. Sibling of R7. This is a condensed digest; the canonical file (`patterns/S8-Meta-Prompt.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- you have a measurable evaluation signal — graded examples, a verifier, an LLM judge, or unit tests — and can run it cheaply against many candidate prompts;
- the prompt must generalise across a distribution of inputs, not just please a few favourite examples;
- the production task is high-volume enough that a one-off optimisation cost amortises across many calls;
- manual prompt engineering has plateaued and you suspect non-obvious wins remain.

Related: [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[S3-Persona]] · [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[R7-Reflexion]] · [[R17-Self-Consistency-Voting]] · [[V15-LLM-as-Judge]] · [[S1-Zero-Shot]] · [[S9-Constitutional-Framing]] · [[K12-Karpathy-Memory]] · [[O5-Evaluator-Optimizer]]
