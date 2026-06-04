---
id: S1
title: Zero-Shot
type: pattern
category: Signal
summary: State the task and submit it.
when_to_use: "Simple, well-defined tasks within model priors"
also_known_as: [Direct Instruction, Vanilla Prompting, Instruction-Only Prompting, Naked Prompt]
related: [S2, S3, S4, S5, S6, S8, S9, R17, K6, R7, O6]
mechanism_refs: [1, 2, 3, 7]
canonical: patterns/S1-Zero-Shot.md
derived: true
---

## Description
State the task and submit it. Nothing else. S1 is the floor against which every other Signal pattern is the upgrade — it names the *do-nothing-extra* default so that adding anything else becomes a conscious decision rather than an unexamined habit. This is a condensed digest; the canonical file (`patterns/S1-Zero-Shot.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is well-defined and unambiguous to a competent reader without examples;
- the output format is common enough to sit inside the model's training distribution (summary, classification, translation, plain answer);
- iteration speed or unit cost dominates the design — every added token is paid on every call;
- you do not yet have measurements that justify any upgrade.

Related: [[S2-Few-Shot]] · [[S3-Persona]] · [[S4-Instruction-Decomposition]] · [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[S8-Meta-Prompt]] · [[S9-Constitutional-Framing]] · [[R17-Self-Consistency-Voting]] · [[K6-Context-Compression]] · [[R7-Reflexion]] · [[O6-Orchestrator-Workers]]
