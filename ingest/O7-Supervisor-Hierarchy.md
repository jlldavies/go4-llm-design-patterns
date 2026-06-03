---
id: O7
title: Supervisor Hierarchy
type: pattern
category: Orchestration
summary: "Scale orchestration past the point where a single coordinator can hold all worker context, by stacking O6 Orchestrator-Workers nodes into a tree where every supervisor manages only its direct children."
when_to_use: O6 applied recursively; supervisor of supervisors
also_known_as: [Hierarchical Agents, Multi-Level Delegation, Tree of Agents, Nested Supervisors, Hierarchical Multi-Agent System]
related: [O6, V9, V14, O10, O11, O16]
composes_with: [O4, O17, S6, R4]
mechanism_refs: [2, 4, 8]
canonical: patterns/O7-Supervisor-Hierarchy.md
derived: true
---

## Description
Scale orchestration past the point where a single coordinator can hold all worker context, by stacking O6 Orchestrator-Workers nodes into a tree where every supervisor manages only its direct children. Composes with O4, O17, S6, R4. This is a condensed digest; the canonical file (`patterns/O7-Supervisor-Hierarchy.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- O6 is provably bottlenecked — the orchestrator's context fills with worker chatter, or its tool surface exceeds the V13 budget, or coordination latency dominates;
- the domain has natural hierarchical decomposition — project $\to$ workstream $\to$ task, research goal $\to$ strategy $\to$ hypothesis-action, ticket $\to$ triage-class $\to$ resolution-step;
- worker count exceeds the ~5–10 a single orchestrator can coordinate cleanly;
- different sub-tree branches need genuinely different coordination policies (the Generation-branch supervisor in co-scientist runs a tournament; the Reflection-branch supervisor runs a review queue).

Related: [[O4-Parallelization]] · [[O17-Agent-Isolation]] · [[S6-Output-Template]] · [[R4-ReAct]] · [[O6-Orchestrator-Workers]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[O10-Swarm]] · [[O11-Blackboard]] · [[O16-Hybrid-Control-Flow]]
