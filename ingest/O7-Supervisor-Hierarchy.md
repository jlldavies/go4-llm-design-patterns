---
id: O7
title: Supervisor Hierarchy
type: pattern
category: Orchestration
summary: "Scale orchestration past the point where a single coordinator can hold all worker context, by stacking O6 Orchestrator-Workers nodes into a tree where every supervisor manages only its direct children.."
when_to_use: O6 applied recursively; supervisor of supervisors
also_known_as: [Hierarchical Agents, Multi-Level Delegation, Tree of Agents, Nested Supervisors, Hierarchical Multi-Agent System]
mechanism_refs: [2, 4, 8]
canonical: patterns/O7-Supervisor-Hierarchy.md
derived: true
---

## Description
Scale orchestration past the point where a single coordinator can hold all worker context, by stacking O6 Orchestrator-Workers nodes into a tree where every supervisor manages only its direct children. This is a condensed digest; the canonical file (`patterns/O7-Supervisor-Hierarchy.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- O6 is provably bottlenecked — the orchestrator's context fills with worker chatter, or its tool surface exceeds the V13 budget, or coordination latency dominates;
- the domain has natural hierarchical decomposition — project $\to$ workstream $\to$ task, research goal $\to$ strategy $\to$ hypothesis-action, ticket $\to$ triage-class $\to$ resolution-step;
- worker count exceeds the ~5–10 a single orchestrator can coordinate cleanly;
- different sub-tree branches need genuinely different coordination policies (the Generation-branch supervisor in co-scientist runs a tournament; the Reflection-branch supervisor runs a review queue).
