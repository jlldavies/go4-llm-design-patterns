---
id: R1
title: Zero-Shot CoT
type: pattern
category: Reasoning
summary: "Elicit explicit intermediate reasoning from a capable instruction-tuned model by adding a single short trigger phrase to an otherwise zero-shot prompt, so the model writes its working out before committing to an answer instead of jumping straight to a guess.."
when_to_use: Elicit reasoning without examples
also_known_as: ["\"Let's think step by step\"", Zero-Shot Chain-of-Thought, Zero-Shot-CoT, Trigger-Phrase CoT]
mechanism_refs: [1, 2, 3, 7]
canonical: patterns/R1-Zero-Shot-CoT.md
derived: true
---

## Description
Elicit explicit intermediate reasoning from a capable instruction-tuned model by adding a single short trigger phrase to an otherwise zero-shot prompt, so the model writes its working out before committing to an answer instead of jumping straight to a guess. This is a condensed digest; the canonical file (`patterns/R1-Zero-Shot-CoT.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task involves arithmetic, multi-step inference, symbolic reasoning, or commonsense composition, and a bare S1 call returns the wrong answer or skips the reasoning;
- you have no curated examples to put in the prompt — or the cost of curating them is not yet justified;
- you want the cheapest possible reasoning lift over S1 (one extra sentence in the prompt, one call);
- the model is large and instruction-tuned enough to follow the trigger (small models often ignore it).
