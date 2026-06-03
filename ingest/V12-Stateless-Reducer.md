---
id: V12
title: Stateless Reducer
type: pattern
category: Reliability
summary: "Force all agent state to be explicit, external, and passed in — so the agent function itself holds no hidden state between invocations and is, in the functional sense, a pure reducer over its inputs."
when_to_use: "Reduce accumulated state to a deterministic, replayable summary"
also_known_as: [Pure Agent, Functional Agent, Agent-as-Reducer, Agent `foldl`, State-Separation Pattern, 12-Factor Agents Factor 12]
composes_with: [V10, V14]
related: [O4, O6, O15, I6, V16, V10, K11, K12]
mechanism_refs: [3, 10]
canonical: patterns/V12-Stateless-Reducer.md
derived: true
---

## Description
Force all agent state to be explicit, external, and passed in — so the agent function itself holds no hidden state between invocations and is, in the functional sense, a pure reducer over its inputs. Composes with V10, V14. This is a condensed digest; the canonical file (`patterns/V12-Stateless-Reducer.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent will be checkpointed (V10), retried, replayed, or run in parallel (O4, O6);
- agent code will be deployed across multiple processes or containers (any production agent at scale);
- reproducibility from recorded inputs is a requirement (regression testing via V16, debugging from V14 traces);
- the agent participates in O15 Agent Handoff or I6 A2A Delegation — state must serialise across the boundary.

Related: [[V10-Checkpointing]] · [[V14-Trajectory-Logging]] · [[O4-Parallelization]] · [[O6-Orchestrator-Workers]] · [[O15-Agent-Handoff]] · [[I6-A2A-Delegation]] · [[V16-Offline-Eval]] · [[K11-Observational-Memory]] · [[K12-Karpathy-Memory]]
