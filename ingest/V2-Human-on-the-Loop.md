---
id: V2
title: Human-on-the-Loop
type: pattern
category: Reliability
summary: "Preserve meaningful human oversight over an autonomous agent without paying V1's per-action latency: the agent proceeds; the human watches a live trace and can pull the brake."
when_to_use: Monitor and interrupt; agent proceeds by default
also_known_as: [Monitoring Mode, Supervisory Control, HOTL, Brake-Pedal Oversight]
siblings: [V1]
related: [V14, H6, V1]
composes_with: [V10, V9, V17, V15, R4, O6, O8]
conflicts_with: [V1]
mechanism_refs: [1, 2, 5, 11]
canonical: patterns/V2-Human-on-the-Loop.md
derived: true
---

## Description
Preserve meaningful human oversight over an autonomous agent without paying V1's per-action latency: the agent proceeds; the human watches a live trace and can pull the brake. In tension with V1. Composes with V10, V9, V17, V15, R4, O6, O8. Sibling of V1. This is a condensed digest; the canonical file (`patterns/V2-Human-on-the-Loop.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the actions are **reversible** — they can be undone, retried, or rolled back without lasting harm;
- the agent operates within **established, well-understood** parameters with a measured track record (V16 Offline Eval has set a baseline; V17 Online Eval is in production);
- the workflow is **long-running** or high-frequency, so V1's per-step latency would defeat its purpose;
- a **readable trace** (V14 Trajectory Logging) exists — without it there is nothing for the supervisor to watch;

Related: [[V1-Human-in-the-Loop]] · [[V10-Checkpointing]] · [[V9-Bounded-Execution]] · [[V17-Online-Eval]] · [[V15-LLM-as-Judge]] · [[R4-ReAct]] · [[O6-Orchestrator-Workers]] · [[O8-Loop-Agent]] · [[V14-Trajectory-Logging]] · [[H6-Continuous-Inner-Monologue]]
