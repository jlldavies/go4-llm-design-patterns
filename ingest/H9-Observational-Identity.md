---
id: H9
title: Observational Identity
type: pattern
category: Humanizers
summary: "Give an agent a persistent, queryable model of its own demonstrated capabilities, attempted tasks, outstanding commitments, and known limitations — each entry timestamped and confidence-scored, each subject to decay — so the agent can route on, communicate about, and reason from its own track record rather than guessing.."
when_to_use: Explicit model of own capabilities and knowledge state
also_known_as: [Self-Knowledge Model, Capability Self-Awareness, Epistemic Self-Model, Metacognitive State, Self-Model]
related: [HA5]
mechanism_refs: [2, 5, 9, 10]
canonical: patterns/H9-Observational-Identity.md
derived: true
---

## Description
Give an agent a persistent, queryable model of its own demonstrated capabilities, attempted tasks, outstanding commitments, and known limitations — each entry timestamped and confidence-scored, each subject to decay — so the agent can route on, communicate about, and reason from its own track record rather than guessing. This is a condensed digest; the canonical file (`patterns/H9-Observational-Identity.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs across multiple sessions and tasks recur, so a track record is genuinely informative;
- the agent must accurately communicate its own limitations to users or to a router ("I have done X seven times, never Y");
- a multi-agent system needs capability-based routing — **O3 Routing** or **O6 Orchestrator-Workers** with worker selection by demonstrated competence;
- users ask "what do you remember about X?" or "have we tried this before?" as a normal part of the interaction;
