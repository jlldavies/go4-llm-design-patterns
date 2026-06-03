---
id: K12
title: Karpathy Memory
type: pattern
category: Knowledge
summary: "Give an agent a memory the LLM itself maintains as structured, dense, token-efficient notes — paying more at *write* time so every *read* is cheap, navigable, and useful."
when_to_use: LLM curates dense structured notes; cheap reads
also_known_as: [Curated Memory, Self-Edited Memory]
related: [K10, K11, K6]
composes_with: [S6, V14]
mechanism_refs: [2, 3, 5, 9, 10]
canonical: patterns/K12-Karpathy-Memory.md
derived: true
---

## Description
Give an agent a memory the LLM itself maintains as structured, dense, token-efficient notes — paying more at *write* time so every *read* is cheap, navigable, and useful. Composes with S6, V14. This is a condensed digest; the canonical file (`patterns/K12-Karpathy-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the same memory will be read many times before it is updated (read frequency far exceeds curation frequency);
- the domain or user has structure worth preserving — entity profiles, project notes, evolving understanding;
- read-time token cost is a material lever (long contexts, many turns over the same memory);
- the memory must be human-readable and editable for operators or downstream agents.

Related: [[S6-Output-Template]] · [[V14-Trajectory-Logging]] · [[K10-Long-Term-Memory]] · [[K11-Observational-Memory]] · [[K6-Context-Compression]]
