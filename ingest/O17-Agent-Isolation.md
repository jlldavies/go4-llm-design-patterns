---
id: O17
title: Agent Isolation
type: pattern
category: Orchestration
summary: "When a sub-task does not need the parent's accumulated context, spawn the sub-agent with a fresh window holding only that sub-task's brief and inputs — so the sub-agent reasons over a tight, on-topic context instead of inheriting whatever the parent happens to be carrying."
when_to_use: Fresh isolated context per sub-task — mandatory companion to O6
also_known_as: [Clean Context, Context Quarantine, Fresh Context Delegation, Sub-Agent Spawn, Isolate]
composes_with: [O6, O4, V14]
related: [V9, K6, O15, K10, K12]
siblings: [O7]
mechanism_refs: [2, 3, 6]
canonical: patterns/O17-Agent-Isolation.md
derived: true
---

## Description
When a sub-task does not need the parent's accumulated context, spawn the sub-agent with a fresh window holding only that sub-task's brief and inputs — so the sub-agent reasons over a tight, on-topic context instead of inheriting whatever the parent happens to be carrying. Composes with O6, O4, V14. Sibling of O7. This is a condensed digest; the canonical file (`patterns/O17-Agent-Isolation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a sub-task is self-contained — its inputs can be enumerated explicitly and do not require the parent's accumulated reasoning;
- the parent's context contains material the sub-agent should *not* see (noise, prior attempts, sensitive data, conflicting frames);
- sub-tasks will run in parallel — each needs its own window anyway (composes naturally with **O4 Parallelization**);
- the parent's context is approaching its window limit and the sub-task's work would push it over;

Related: [[O6-Orchestrator-Workers]] · [[O4-Parallelization]] · [[V14-Trajectory-Logging]] · [[O7-Supervisor-Hierarchy]] · [[V9-Bounded-Execution]] · [[K6-Context-Compression]] · [[O15-Agent-Handoff]] · [[K10-Long-Term-Memory]] · [[K12-Karpathy-Memory]]
