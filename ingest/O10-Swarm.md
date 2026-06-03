---
id: O10
title: Swarm / Mesh
type: pattern
category: Orchestration
summary: "Coordinate a fleet of specialised agents without a central orchestrator, by giving each agent the authority to hand control to any peer it deems better suited to the current step."
when_to_use: No central controller; shared environment coordination
also_known_as: [Peer-to-Peer Agents, Decentralised Agents, Agent Mesh, Network of Agents, Multi-Agent Handoff Network]
related: [O7, O6, O11, O3, V9, V14]
composes_with: [O15, O17, S6, R4]
mechanism_refs: [1, 2, 3]
canonical: patterns/O10-Swarm.md
derived: true
---

## Description
Coordinate a fleet of specialised agents without a central orchestrator, by giving each agent the authority to hand control to any peer it deems better suited to the current step. Composes with O15, O17, S6, R4. This is a condensed digest; the canonical file (`patterns/O10-Swarm.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task topology is naturally a graph, not a tree — flows where any specialist can hand to any other (customer support, role-played dialogue, multi-stage creative pipelines with cycles);
- the set of specialisations is small (typically 2–8 agents) and well-named, so each agent can reasonably know which peer to hand to;
- routing depends on conversational *content* the active agent already holds, so passing the decision to a separate supervisor would just duplicate work;
- the failure cost of a missed handoff is low — the user can be re-routed, the conversation can recover.

Related: [[O15-Agent-Handoff]] · [[O17-Agent-Isolation]] · [[S6-Output-Template]] · [[R4-ReAct]] · [[O7-Supervisor-Hierarchy]] · [[O6-Orchestrator-Workers]] · [[O11-Blackboard]] · [[O3-Routing]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]]
