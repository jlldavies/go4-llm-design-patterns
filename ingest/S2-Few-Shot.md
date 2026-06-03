---
id: S2
title: Few-Shot
type: pattern
category: Signal
summary: "Demonstrate the task with examples in the prompt, so the model learns the desired format and behaviour from the demonstrations themselves rather than from a description of them."
when_to_use: "Format control, novel task types, style matching"
also_known_as: [In-Context Learning, Exemplar Prompting, k-Shot Prompting, One-Shot]
related: [S1, S6]
composes_with: [S3, S6, R17, K1]
mechanism_refs: [2, 5, 12]
canonical: patterns/S2-Few-Shot.md
derived: true
---

## Description
Demonstrate the task with examples in the prompt, so the model learns the desired format and behaviour from the demonstrations themselves rather than from a description of them. Composes with S3, S6, R17, K1. This is a condensed digest; the canonical file (`patterns/S2-Few-Shot.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the output format is non-standard or uncommon, and S1 produces inconsistent shapes;
- the task involves a specific style, tone, or reasoning pattern the model would not produce by default;
- a small set of representative examples covers the input distribution;
- you can spend the token budget on demonstrations on every call.

Related: [[S3-Persona]] · [[S6-Output-Template]] · [[R17-Self-Consistency-Voting]] · [[K1-Vanilla-RAG]] · [[S1-Zero-Shot]]
