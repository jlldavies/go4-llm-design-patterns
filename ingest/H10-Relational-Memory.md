---
id: H10
title: Relational Memory
type: pattern
category: Humanizers
summary: "Give each user a persistent, structured model of the working relationship — goals, history, preferences, ethical constraints — that the agent reads at every session so it can show up as a continuous collaborator, while guardrails and a hard right-to-deletion keep that continuity from drifting into simulated intimacy."
when_to_use: Per-user relationship record with GDPR erasure support
also_known_as: [User Model Persistence, Relationship State, Long-Term Rapport, Per-User Memory, "\"Human Block\""]
related: [H1, H2, H4, H7, H9, S3, V5]
requires: [H1, K10, K12, V5]
composes_with: [H7, K11, K6, V1, V14]
mechanism_refs: [2, 4, 5]
canonical: patterns/H10-Relational-Memory.md
derived: true
---

## Description
Give each user a persistent, structured model of the working relationship — goals, history, preferences, ethical constraints — that the agent reads at every session so it can show up as a continuous collaborator, while guardrails and a hard right-to-deletion keep that continuity from drifting into simulated intimacy. Requires H1, K10, K12, V5. Composes with H7, K11, K6, V1, V14. This is a condensed digest; the canonical file (`patterns/H10-Relational-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the deployment has *the same user* returning across sessions and benefits from continuity (personal assistants, coaching agents, long-running collaboration agents, learning-companion agents);
- the agent makes user-specific commitments and references prior work ("the project we discussed last week", "the goal you set in January");
- the user explicitly consents to the agent retaining a model of them, and the deployment can implement and surface that consent honestly;
- guardrails (V5) and a deletion path can be wired and tested before the pattern goes live.

Related: [[H1-Identity-Persistence]] · [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]] · [[V5-Guardrail-Layering]] · [[H7-Adaptive-Persona]] · [[K11-Observational-Memory]] · [[K6-Context-Compression]] · [[V1-Human-in-the-Loop]] · [[V14-Trajectory-Logging]] · [[H2-Episodic-Self-Improvement]] · [[H4-Procedural-Skill-Accumulation]] · [[H9-Observational-Identity]] · [[S3-Persona]]
