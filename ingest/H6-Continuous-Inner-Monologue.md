---
id: H6
title: Continuous Inner Monologue
type: pattern
category: Humanizers
summary: "Maintain a continuous, autonomous inner monologue — a Thinker process separate from the user-facing Responder — that reflects between turns, consolidates across sessions, and writes its conclusions to a shared memory the Responder reads on the next interaction.."
when_to_use: Background reasoning between turns; fast responder reads it
also_known_as: [MIRROR Pattern, Thinker Agent, Inner Monologue, Cognitive Inner Monologue, Vygotskian Inner Speech for LLMs, Background Reasoning Stream]
related: [R16]
composes_with: [H1]
siblings: [H3]
mechanism_refs: [2, 3, 5, 6, 10]
canonical: patterns/H6-Continuous-Inner-Monologue.md
derived: true
---

## Description
Maintain a continuous, autonomous inner monologue — a Thinker process separate from the user-facing Responder — that reflects between turns, consolidates across sessions, and writes its conclusions to a shared memory the Responder reads on the next interaction. Composes with H1. Sibling of H3. This is a condensed digest; the canonical file (`patterns/H6-Continuous-Inner-Monologue.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs in a persistent session or across sessions and the *between-turn* time is wasted today;
- response quality benefits from reflection that does not fit a single turn's latency budget but is not urgent either;
- the agent must monitor for asynchronous conditions (approaching deadlines, drifting commitments, accumulated context) without the user prompting;
- consolidation across sessions matters — what the agent learned today should change what it does tomorrow without retraining;

Related: [[H1-Identity-Persistence]] · [[H3-Entropy-Driven-Curiosity]] · [[R16-Talker-Reasoner]]
