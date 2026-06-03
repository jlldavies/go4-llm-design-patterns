---
id: R19
title: Step-Back Prompting
type: pattern
category: Reasoning
summary: "Improve reasoning on specific, detail-heavy questions by first answering a strictly more abstract version of them — extracting the underlying principle, concept, or class of fact — and then applying that principle back to the specific case.."
when_to_use: Abstract to principle before answering
also_known_as: [Abstraction Prompting, Take-a-Step-Back, Principle-First Reasoning]
mechanism_refs: [1, 5, 7]
canonical: patterns/R19-Step-Back-Prompting.md
derived: true
---

## Description
Improve reasoning on specific, detail-heavy questions by first answering a strictly more abstract version of them — extracting the underlying principle, concept, or class of fact — and then applying that principle back to the specific case. This is a condensed digest; the canonical file (`patterns/R19-Step-Back-Prompting.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the question is specific and detail-heavy but rests on a generalisable concept, law, or class the model knows;
- a single CoT pass produces confident-but-wrong intermediate steps that ignore the relevant principle;
- the task domain has *named* principles or concepts (physics laws, legal doctrines, biological mechanisms, accounting standards) and a successful answer reduces to "apply principle X";
- the system has a retrieval layer and the abstract answer is more likely to be in the corpus than the specific answer.
