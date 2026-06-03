---
id: H3
title: Entropy-Driven Curiosity
type: pattern
category: Humanizers
summary: "Detect when an agent's own output distribution has collapsed — the agent is \"thinking the same thoughts in a loop\" — and act on the detection by raising sampling temperature or injecting a contrarian cue, so the loop escapes its local optimum and resumes productive search."
when_to_use: Drive exploration by seeking to reduce uncertainty
also_known_as: [Deadlock Break, Novelty Seeking, Intrinsic Motivation, Entropy-Based Intrinsic Drive]
related: [H1, R4, R3, R7, R9, R10, R17, H7]
composes_with: [V9, V15, R20, K11, H2, V20]
conflicts_with: [R17]
mechanism_refs: [1, 3, 7]
canonical: patterns/H3-Entropy-Driven-Curiosity.md
derived: true
---

## Description
Detect when an agent's own output distribution has collapsed — the agent is "thinking the same thoughts in a loop" — and act on the detection by raising sampling temperature or injecting a contrarian cue, so the loop escapes its local optimum and resumes productive search. In tension with R17. Composes with V9, V15, R20, K11, H2, V20. This is a condensed digest; the canonical file (`patterns/H3-Entropy-Driven-Curiosity.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs a reasoning loop (R4, R3, R7, R9, R10) that can stall — "stalled" meaning observable output diversity collapses while no progress is made;
- the task admits multiple valid approaches (creative, exploratory, open-ended research, brainstorming) so injected novelty has somewhere productive to go;
- the agent is long-running and the cost of silent monotony is material (autonomous research, long-horizon planning, content generation);
- H1 Identity Persistence is in place — H3 perturbs *expression*, not identity, and needs a stable identity layer to perturb relative to.

Related: [[R17-Self-Consistency-Voting]] · [[V9-Bounded-Execution]] · [[V15-LLM-as-Judge]] · [[R20-Chain-of-Verification]] · [[K11-Observational-Memory]] · [[H2-Episodic-Self-Improvement]] · [[V20-Schema-Validation]] · [[H1-Identity-Persistence]] · [[R4-ReAct]] · [[R3-Plan-and-Solve]] · [[R7-Reflexion]] · [[R9-Tree-of-Thoughts]] · [[R10-LATS]] · [[H7-Adaptive-Persona]]
