---
id: S3
title: Persona
type: pattern
category: Signal
summary: "Frame the model's response distribution at the identity level — selecting a domain, a register, and a decision style in one move — so every subsequent turn inherits that framing without restating it."
when_to_use: "Domain expertise framing, tone alignment"
also_known_as: [Role Prompting, Expert Identity, Character Prompting, the Persona Pattern]
related: [H1, S9, K5, K12, R4, V15]
composes_with: [S5, S6, O4, O6]
mechanism_refs: [1, 2, 4, 7]
canonical: patterns/S3-Persona.md
derived: true
---

## Description
Frame the model's response distribution at the identity level — selecting a domain, a register, and a decision style in one move — so every subsequent turn inherits that framing without restating it. Composes with S5, S6, O4, O6. This is a condensed digest; the canonical file (`patterns/S3-Persona.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task benefits from a *domain register* — security, medicine, law, finance, engineering — where the right vocabulary and the right caution profile materially change the answer;
- the session is long enough that voice consistency across turns matters;
- a multi-agent system needs distinct, recognisable contributors (Planner / Critic / Coder);
- the task implies a *style* the model would not produce by default (terse Unix maintainer; patient first-grade teacher; formal legal counsel).

Related: [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[O4-Parallelization]] · [[O6-Orchestrator-Workers]] · [[H1-Identity-Persistence]] · [[S9-Constitutional-Framing]] · [[K5-Adaptive-RAG]] · [[K12-Karpathy-Memory]] · [[R4-ReAct]] · [[V15-LLM-as-Judge]]
