---
id: S1
title: Zero-Shot
type: pattern
category: Signal
summary: State the task and submit it.
when_to_use: "Simple, well-defined tasks within model priors"
also_known_as: [Direct Instruction, Vanilla Prompting, Instruction-Only Prompting, Naked Prompt]
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
