---
id: DECISION-reliability
title: Reliability — Decision Guide
type: decision-guide
summary: How to choose among Reliability patterns.
canonical: patterns/RELIABILITY-DECISION.md
derived: true
---

## Decision Flow

```
Does the agent take irreversible or high-blast-radius actions?
  YES → V1 (Human-in-the-Loop) at those decision boundaries
  MONITOR only → V2 (Human-on-the-Loop)
  Two independent confirmations required → V3 (Rule of Two)

Does the agent process untrusted external content?
  YES:
    Private data + untrusted content + external comms? → V3 (lethal trifecta check)
    Route untrusted content to quarantined model → V4 (Dual LLM)
    Inject structural defences at prompt boundaries → V6 (Prompt Injection Shield)

Does the agent run in a loop or have no natural exit condition?
  YES → V9 (Bounded Execution) — REQUIRED; hard caps on steps, cost, wall-time
    ⚠ V20 retry loops expand context ~2× per retry; include in V9 token cap calculation

Does the agent generate or execute code?
  YES → V8 (Tool Sandboxing): restrict filesystem, network, clock

Does the agent have more than 10 active tools?
  YES → V13 (Tool Budget): hard limit on active schema tokens
    Tool selection accuracy: 43% at low counts → 14% at high counts (3× degradation)

Does the agent need to recover from partial failure without restart?
  YES → V10 (Checkpointing): replayable state snapshots

Are there multiple safety boundaries (input, tool calls, output)?
  YES → V5 (Guardrail Layering): safety checks at all four points

Is output conformance to a schema required?
  YES → V20 (Schema Validation): validate-and-reask loop
    Bundle with V9: each retry expands context

Is output quality measurable?
  Pre-deployment → V16 (Offline Eval)
  In production → V17 (Online Eval)
  Second model as judge → V15 (LLM-as-Judge)

Is full observability required (compliance, debugging)?
  YES → V14 (Trajectory Logging): OTel-compatible trace from day 1

Does the agent need declarative policy enforcement outside the prompt?
  YES → V7 (AgentSpec): deterministic policy; not probabilistic like S9
```

## Must-Have Baseline

Every production agent needs at minimum: **V9 + V14**. Add V1 at any irreversible action boundary. Add V5 at any external input boundary.