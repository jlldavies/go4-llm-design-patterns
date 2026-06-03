---
id: K10
title: Long-Term Memory
type: pattern
category: Knowledge
summary: Give an agent continuity beyond a single context by writing knowledge to an external store and retrieving it when relevant — so the agent improves over time without retraining.
when_to_use: Cross-session fact storage; retrieved by similarity
also_known_as: [Persistent Memory, Cross-Session Memory, External Memory, Agent Memory]
related: [K1, K8, K11, K12, H2, H4, H10]
composes_with: [K12]
mechanism_refs: [1, 3, 4, 9, 10]
canonical: patterns/K10-Long-Term-Memory.md
derived: true
---

## Description
Give an agent continuity beyond a single context by writing knowledge to an external store and retrieving it when relevant — so the agent improves over time without retraining. Composes with K12. This is a condensed digest; the canonical file (`patterns/K10-Long-Term-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the system is a personal assistant that should remember the user across sessions;
- the agent works recurring task types — a coding agent on a codebase, a research agent in a domain;
- the system is expected to get better over time.

Related: [[K12-Karpathy-Memory]] · [[K1-Vanilla-RAG]] · [[K8-Working-Memory]] · [[K11-Observational-Memory]] · [[H2-Episodic-Self-Improvement]] · [[H4-Procedural-Skill-Accumulation]] · [[H10-Relational-Memory]]
