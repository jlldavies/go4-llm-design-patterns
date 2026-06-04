---
id: S9
title: Constitutional Framing
type: pattern
category: Signal
summary: "Make the model's value judgement legible, auditable, and updatable — by stating the principles explicitly in the prompt and inserting a self-critique-and-revise step that checks the draft against them before it is returned."
when_to_use: "Alignment enforcement, principle-based self-critique"
also_known_as: [Constitutional AI, Principle-Based Alignment, Runtime Constitution, Self-Critique-and-Revise, CAI-at-Inference]
composes_with: [S3, S5, S6, V9, V7]
related: [V7, H5, R7, V15, S3, S5]
mechanism_refs: [3, 4, 5, 6, 7]
canonical: patterns/S9-Constitutional-Framing.md
derived: true
---

## Description
Make the model's value judgement legible, auditable, and updatable — by stating the principles explicitly in the prompt and inserting a self-critique-and-revise step that checks the draft against them before it is returned. Composes with S3, S5, S6, V9, V7. This is a condensed digest; the canonical file (`patterns/S9-Constitutional-Framing.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the system operates in a context — safety-critical, regulated, brand-sensitive, ethically charged — where outputs must be explainable against stated values, not just produced;
- the operator needs to **audit** outputs against principles, or to **update** the value framing without retraining;
- the constitution captures *interpretive* judgement (when to refuse vs. clarify, how to weigh helpfulness against caution) that cannot be enumerated as flat prohibitions;
- multiple agents in the system must share a consistent value framing across roles;

Related: [[S3-Persona]] · [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[V9-Bounded-Execution]] · [[V7-AgentSpec]] · [[H5-Constitutional-Self-Alignment]] · [[R7-Reflexion]] · [[V15-LLM-as-Judge]]
