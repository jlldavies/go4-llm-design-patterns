---
id: H10
title: Relational Memory
type: pattern
category: Humanizers
summary: "Give each user a persistent, structured model of the working relationship — goals, history, preferences, ethical constraints — that the agent reads at every session so it can show up as a continuous collaborator, while guardrails and a hard right-to-deletion keep that continuity from drifting into simulated intimacy.."
when_to_use: Per-user relationship record with GDPR erasure support
also_known_as: [User Model Persistence, Relationship State, Long-Term Rapport, Per-User Memory, "\"Human Block\""]
requires: [H1, K10, K12]
composes_with: [H7, K11, V1, H1, H5]
related: [H9, S3, H1, K10, K12, V5, H7]
mechanism_refs: [2, 4, 5]
canonical: patterns/H10-Relational-Memory.md
derived: true
---

## Description
Give each user a persistent, structured model of the working relationship — goals, history, preferences, ethical constraints — that the agent reads at every session so it can show up as a continuous collaborator, while guardrails and a hard right-to-deletion keep that continuity from drifting into simulated intimacy. Requires H1, K10, K12. Composes with H7, K11, V1, H1, H5. This is a condensed digest; the canonical file (`patterns/H10-Relational-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the deployment has *the same user* returning across sessions and benefits from continuity (personal assistants, coaching agents, long-running collaboration agents, learning-companion agents);
- the agent makes user-specific commitments and references prior work ("the project we discussed last week", "the goal you set in January");
- the user explicitly consents to the agent retaining a model of them, and the deployment can implement and surface that consent honestly;
- guardrails (V5) and a deletion path can be wired and tested before the pattern goes live.

Related: [[H1-Identity-Persistence]] · [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]] · [[H7-Adaptive-Persona]] · [[K11-Observational-Memory]] · [[V1-Human-in-the-Loop]] · [[H5-Constitutional-Self-Alignment]] · [[H9-Observational-Identity]] · [[S3-Persona]] · [[V5-Guardrail-Layering]]
