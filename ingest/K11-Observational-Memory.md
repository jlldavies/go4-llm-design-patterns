---
id: K11
title: Observational Memory
type: pattern
category: Knowledge
summary: "Maintain coherence across a long agentic session by keeping a running, compact record of the agent's own observations and actions, and prioritising that record over external retrieval.."
when_to_use: Append-only activity log; exploits prefix caching
also_known_as: [Agent-Centric Memory, Seen-First Memory, Session Memory]
mechanism_refs: [2, 3, 5]
canonical: patterns/K11-Observational-Memory.md
derived: true
---

## Description
Maintain coherence across a long agentic session by keeping a running, compact record of the agent's own observations and actions, and prioritising that record over external retrieval. This is a condensed digest; the canonical file (`patterns/K11-Observational-Memory.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs long sessions — hours, or days;
- the agent's own prior actions are the main relevant context — coding, research, operations agents;
- KV-cache reuse is a material cost lever for the deployment;
- K1 retrieval is too slow or too imprecise for in-session recall.
