---
id: S4
title: Instruction Decomposition
type: pattern
category: Signal
summary: "Replace a dense, unstructured instruction with an explicit numbered procedure inside a single prompt, so the model performs each step in order, no step is silently skipped, and the failure mode of any miss is localisable to a specific step.."
when_to_use: Multi-step tasks where order matters
also_known_as: [Step Prompting, Numbered Steps, Chain Instructions, Recipe Prompting]
related: [O2, R4, O4]
siblings: [R3]
composes_with: [S3, S5, S6, S2, V15]
mechanism_refs: [4]
canonical: patterns/S4-Instruction-Decomposition.md
derived: true
---

## Description
Replace a dense, unstructured instruction with an explicit numbered procedure inside a single prompt, so the model performs each step in order, no step is silently skipped, and the failure mode of any miss is localisable to a specific step. Composes with S3, S5, S6, S2, V15. Sibling of R3. This is a condensed digest; the canonical file (`patterns/S4-Instruction-Decomposition.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task has a clear sequential process (validate $\to$ transform $\to$ format $\to$ output) and you can enumerate the steps at design time;
- previous single-instruction prompts produced output that skipped requirements or fused steps;
- steps are short enough that one model context can hold all of them with room for the data;
- you need auditability — to point at *which* step was dropped when output is wrong;

Related: [[S3-Persona]] · [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[S2-Few-Shot]] · [[V15-LLM-as-Judge]] · [[R3-Plan-and-Solve]] · [[O2-Prompt-Chaining]] · [[R4-ReAct]] · [[O4-Parallelization]]
