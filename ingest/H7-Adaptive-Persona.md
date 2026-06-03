---
id: H7
title: Adaptive Persona
type: pattern
category: Humanizers
summary: "Close the style gap between agent and user: infer how this user prefers to be communicated with — from explicit corrections, implicit engagement signals, and their own register — and apply those parameters at generation time, while explicitly preserving the identity invariants H1 holds constant."
when_to_use: Per-user style model; adapts communication to each person
also_known_as: [User-Calibrated Style, Preference-Driven Voice, Dynamic Persona, User Style Model]
requires: [H1]
composes_with: [K10, K12, H10, H2, V5]
related: [S3, H9, H1]
mechanism_refs: [2, 5]
canonical: patterns/H7-Adaptive-Persona.md
derived: true
---

## Description
Close the style gap between agent and user: infer how this user prefers to be communicated with — from explicit corrections, implicit engagement signals, and their own register — and apply those parameters at generation time, while explicitly preserving the identity invariants H1 holds constant. Requires H1. Composes with K10, K12, H10, H2, V5. This is a condensed digest; the canonical file (`patterns/H7-Adaptive-Persona.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent serves *individual users* over time (personal assistants, coding assistants, coaches, educational agents);
- the user base is heterogeneous in expertise, register, or format preference (a single persona will misfit a meaningful fraction);
- explicit style corrections ("be more concise", "stop the jargon", "more detail next time") appear in the interaction logs — these are unambiguous signals the static persona is mispriced;
- a stable identity core already exists (**H1** in place) that the adaptation surface can vary against.

Related: [[H1-Identity-Persistence]] · [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]] · [[H10-Relational-Memory]] · [[H2-Episodic-Self-Improvement]] · [[V5-Guardrail-Layering]] · [[S3-Persona]] · [[H9-Observational-Identity]]
