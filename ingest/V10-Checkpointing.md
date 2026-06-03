---
id: V10
title: Checkpointing
type: pattern
category: Reliability
summary: "Externalise the agent's working state to a durable store at each step boundary, so failures, terminations, and human pauses become resumable events instead of restart-from-zero events.."
when_to_use: Replayable agent state; recovery without restart
also_known_as: [State Snapshot, Agent State Persistence, Savepoint, Durable Execution]
composes_with: [V12, V14]
related: [V9, K8, V14, K11]
mechanism_refs: [3, 5]
canonical: patterns/V10-Checkpointing.md
derived: true
---

## Description
Externalise the agent's working state to a durable store at each step boundary, so failures, terminations, and human pauses become resumable events instead of restart-from-zero events. Composes with V12, V14. This is a condensed digest; the canonical file (`patterns/V10-Checkpointing.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs long enough that failure or interruption is realistic (multi-step plans, long-horizon research, multi-turn human-in-the-loop workflows);
- V1 (Human-in-the-Loop) is on the table — meaningful pauses are not possible without it;
- V9 (Bounded Execution) is in force — checkpointing is what makes a hit limit recoverable instead of pure loss;
- O15 (Agent Handoff) is required — the state must be serialised to transfer between agents;

Related: [[V12-Stateless-Reducer]] · [[V14-Trajectory-Logging]] · [[V9-Bounded-Execution]] · [[K8-Working-Memory]] · [[K11-Observational-Memory]]
