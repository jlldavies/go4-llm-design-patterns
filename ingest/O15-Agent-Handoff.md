---
id: O15
title: Agent Handoff
type: pattern
category: Orchestration
summary: "Move a live interaction from one agent to another inside the same system without losing context, so the user does not repeat themselves and the receiving agent starts from the conversation's true state — not from zero, and not from a noisy transcript."
when_to_use: Structured state transfer between agents mid-task
also_known_as: [Context Transfer, Agent-to-Agent Transfer, Conversation Handoff, Transfer Tool, Swarm Handoff]
related: [I6, O3, O17]
composes_with: [O6, V14, V9, V1, S6, V6]
mechanism_refs: [2, 4, 5]
canonical: patterns/O15-Agent-Handoff.md
derived: true
---

## Description
Move a live interaction from one agent to another inside the same system without losing context, so the user does not repeat themselves and the receiving agent starts from the conversation's true state — not from zero, and not from a noisy transcript. Composes with O6, V14, V9, V1, S6, V6. This is a condensed digest; the canonical file (`patterns/O15-Agent-Handoff.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- The system has multiple agents and a conversation may need to switch between them mid-interaction.
- Specialist routing is determined dynamically by conversation state, not by a fixed up-front classifier (which would be O3 Routing).
- The receiving agent needs structured evidence — extracted entities, action outcomes, tool state — not just a chat history.
- Voice-to-text, automated-to-human, or general-to-specialist escalation is part of the design.

Related: [[O6-Orchestrator-Workers]] · [[V14-Trajectory-Logging]] · [[V9-Bounded-Execution]] · [[V1-Human-in-the-Loop]] · [[S6-Output-Template]] · [[V6-Prompt-Injection-Shield]] · [[I6-A2A-Delegation]] · [[O3-Routing]] · [[O17-Agent-Isolation]]
