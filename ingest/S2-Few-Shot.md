---
id: S2
title: Few-Shot
type: pattern
category: Signal
summary: "Demonstrate the task with examples in the prompt, so the model learns the desired format and behaviour from the demonstrations themselves rather than from a description of them.."
when_to_use: "Format control, novel task types, style matching"
also_known_as: [In-Context Learning, Exemplar Prompting, k-Shot Prompting, One-Shot]
related: [S1]
composes_with: [R17]
mechanism_refs: [2, 5, 12]
canonical: patterns/S2-Few-Shot.md
derived: true
---

## Description
Demonstrate the task with examples in the prompt, so the model learns the desired format and behaviour from the demonstrations themselves rather than from a description of them. Composes with R17. This is a condensed digest; the canonical file (`patterns/S2-Few-Shot.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the output format is non-standard or uncommon, and S1 produces inconsistent shapes;
- the task involves a specific style, tone, or reasoning pattern the model would not produce by default;
- a small set of representative examples covers the input distribution;
- you can spend the token budget on demonstrations on every call.

Related: [[R17-Self-Consistency-Voting]] · [[S1-Zero-Shot]]
