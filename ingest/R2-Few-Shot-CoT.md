---
id: R2
title: Few-Shot CoT
type: pattern
category: Reasoning
summary: "Elicit step-by-step intermediate reasoning by *demonstrating* it in a small set of in-prompt examples — `(question, reasoning trace, answer)` triples — so the model both adopts the reasoning style and produces the answer in the demonstrated form.."
when_to_use: Show worked reasoning before the target question
also_known_as: [Exemplar Chain-of-Thought, Manual CoT, Demonstration-Based CoT, k-Shot CoT]
related: [R1, S2, R3, R4, R14]
composes_with: [R17, S3, S6, R1]
mechanism_refs: [1, 2, 5]
canonical: patterns/R2-Few-Shot-CoT.md
derived: true
---

## Description
Elicit step-by-step intermediate reasoning by *demonstrating* it in a small set of in-prompt examples — `(question, reasoning trace, answer)` triples — so the model both adopts the reasoning style and produces the answer in the demonstrated form. Composes with R17, S3, S6, R1. This is a condensed digest; the canonical file (`patterns/R2-Few-Shot-CoT.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- R1 Zero-Shot CoT produces inconsistent reasoning shape or shallow reasoning on the target task;
- the task needs a *specific* reasoning form (a named scratchpad layout, a domain-specific derivation, a particular justification structure) that the model will not produce by default;
- 4–8 representative reasoning traces can cover the kinds of inferences the task demands;
- the per-call token cost of carrying those traces is acceptable.

Related: [[R17-Self-Consistency-Voting]] · [[S3-Persona]] · [[S6-Output-Template]] · [[R1-Zero-Shot-CoT]] · [[S2-Few-Shot]] · [[R3-Plan-and-Solve]] · [[R4-ReAct]] · [[R14-Program-of-Thoughts]]
