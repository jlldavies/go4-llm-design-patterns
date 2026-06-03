---
id: H1
title: Identity Persistence
type: pattern
category: Humanizers
summary: "Give the agent a single, durable identity that survives context resets — a self-representation loaded first, every time, that defines who the agent is, what it values, how it speaks, and what it has promised — so users encounter the same agent each session rather than a fresh stranger wearing the same name.."
when_to_use: Stable persona loaded at position 0 every session
also_known_as: [Genesis State, Core Self Injection, Autobiographical Anchor, Persistent Persona, Persona Memory Block]
related: [S3, H7, H9]
composes_with: [K10, K12, V6, V5, H5, V1]
mechanism_refs: [2, 4, 5, 10]
canonical: patterns/H1-Identity-Persistence.md
derived: true
---

## Description
Give the agent a single, durable identity that survives context resets — a self-representation loaded first, every time, that defines who the agent is, what it values, how it speaks, and what it has promised — so users encounter the same agent each session rather than a fresh stranger wearing the same name. Composes with K10, K12, V6, V5, H5, V1. This is a condensed digest; the canonical file (`patterns/H1-Identity-Persistence.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs across multiple sessions and users expect continuity (personal assistants, coding agents on a long-lived codebase, coaching agents);
- the agent makes commitments that must be honoured later ("I'll follow up next week", "next time, do X differently");
- a multi-agent system needs each agent to be a *distinguishable* and *consistent* contributor;
- trust depends on predictable values and voice — safety-relevant tone, regulated domain register, brand identity.

Related: [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]] · [[V6-Prompt-Injection-Shield]] · [[V5-Guardrail-Layering]] · [[H5-Constitutional-Self-Alignment]] · [[V1-Human-in-the-Loop]] · [[S3-Persona]] · [[H7-Adaptive-Persona]] · [[H9-Observational-Identity]]
