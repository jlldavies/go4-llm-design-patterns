---
id: S6
title: Output Template
type: pattern
category: Signal
summary: "Replace open-ended generation of \"content plus format\" with the simpler task of filling content into a predefined skeleton, so downstream parsers, chained LLM calls, and human reviewers see a consistent shape every run."
when_to_use: "Structured data extraction, consistent formatting"
also_known_as: [Template Filling, Structured Output, Format Forcing, Skeleton Prompting]
composes_with: [S2, S4, S5, V15]
related: [O2, I2, S1, S3]
mechanism_refs: [2, 4, 5, 7]
canonical: patterns/S6-Output-Template.md
derived: true
---

## Description
Replace open-ended generation of "content plus format" with the simpler task of filling content into a predefined skeleton, so downstream parsers, chained LLM calls, and human reviewers see a consistent shape every run. Composes with S2, S4, S5, V15. This is a condensed digest; the canonical file (`patterns/S6-Output-Template.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- output is parsed programmatically, or chained to another LLM call (see **O2 Prompt Chaining**);
- consistent format across runs is a business or display requirement;
- the task is multi-field structured extraction;
- the format is non-obvious, easy to drift on, or has changed before.

Related: [[S2-Few-Shot]] · [[S4-Instruction-Decomposition]] · [[S5-Constraint-Framing]] · [[V15-LLM-as-Judge]] · [[O2-Prompt-Chaining]] · [[I2-Function-Call]] · [[S1-Zero-Shot]] · [[S3-Persona]]
