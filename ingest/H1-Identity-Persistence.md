---
id: H1
title: Identity Persistence
type: pattern
category: Humanizers
summary: "Give the agent a single, durable identity that survives context resets — a self-representation loaded first, every time, that defines who the agent is, what it values, how it speaks, and what it has promised — so users encounter the same agent each session rather than a fresh stranger wearing the same name.."
when_to_use: Stable persona loaded at position 0 every session
also_known_as: [Genesis State, Core Self Injection, Autobiographical Anchor, Persistent Persona, Persona Memory Block]
mechanism_refs: [2, 4, 5, 10]
canonical: patterns/H1-Identity-Persistence.md
derived: true
---

## Description
Give the agent a single, durable identity that survives context resets — a self-representation loaded first, every time, that defines who the agent is, what it values, how it speaks, and what it has promised — so users encounter the same agent each session rather than a fresh stranger wearing the same name. This is a condensed digest; the canonical file (`patterns/H1-Identity-Persistence.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs across multiple sessions and users expect continuity (personal assistants, coding agents on a long-lived codebase, coaching agents);
- the agent makes commitments that must be honoured later ("I'll follow up next week", "next time, do X differently");
- a multi-agent system needs each agent to be a *distinguishable* and *consistent* contributor;
- trust depends on predictable values and voice — safety-relevant tone, regulated domain register, brand identity.
