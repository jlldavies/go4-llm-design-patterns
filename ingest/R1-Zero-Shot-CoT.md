---
id: R1
title: Zero-Shot CoT
type: pattern
category: Reasoning
summary: "Elicit explicit intermediate reasoning from a capable instruction-tuned model by adding a single short trigger phrase to an otherwise zero-shot prompt, so the model writes its working out before committing to an answer instead of jumping straight to a guess."
when_to_use: Elicit reasoning without examples
cost: baseline
also_known_as: ["\"Let's think step by step\"", Zero-Shot Chain-of-Thought, Zero-Shot-CoT, Trigger-Phrase CoT]
related: [S1, R3, R4, R14, R17, R7, R8, O6, O4]
siblings: [R2]
mechanism_refs: [1, 2, 3, 7]
canonical: patterns/R1-Zero-Shot-CoT.md
derived: true
---

## Description
Elicit explicit intermediate reasoning from a capable instruction-tuned model by adding a single short trigger phrase to an otherwise zero-shot prompt, so the model writes its working out before committing to an answer instead of jumping straight to a guess. Sibling of R2. This is a condensed digest; the canonical file (`patterns/R1-Zero-Shot-CoT.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task involves arithmetic, multi-step inference, symbolic reasoning, or commonsense composition, and a bare S1 call returns the wrong answer or skips the reasoning;
- you have no curated examples to put in the prompt — or the cost of curating them is not yet justified;
- you want the cheapest possible reasoning lift over S1 (one extra sentence in the prompt, one call);
- the model is large and instruction-tuned enough to follow the trigger (small models often ignore it).

Related: [[R2-Few-Shot-CoT]] · [[S1-Zero-Shot]] · [[R3-Plan-and-Solve]] · [[R4-ReAct]] · [[R14-Program-of-Thoughts]] · [[R17-Self-Consistency-Voting]] · [[R7-Reflexion]] · [[R8-Self-Refine]] · [[O6-Orchestrator-Workers]] · [[O4-Parallelization]]
