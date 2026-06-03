---
id: O1
title: Single Agent
type: pattern
category: Orchestration
summary: "Run the whole task inside one agent: a single configured LLM with a system prompt, a small tool set, and a ReAct-style inner loop."
when_to_use: "Baseline; one model, one loop"
also_known_as: [Autonomous Agent, Solo Agent, Monolithic Agent, Single-Loop Agent, Tool-Using Assistant]
composes_with: [R4, I2, I3, K8, K11, S3, S5, S6]
related: [V9, V14, O2, O6]
mechanism_refs: [1, 2, 3, 4]
canonical: patterns/O1-Single-Agent.md
derived: true
---

## Description
Run the whole task inside one agent: a single configured LLM with a system prompt, a small tool set, and a ReAct-style inner loop. Use it as the floor against which any multi-step pipeline, router, or multi-agent decomposition must justify its cost. Composes with R4, I2, I3, K8, K11, S3, S5, S6. This is a condensed digest; the canonical file (`patterns/O1-Single-Agent.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task is self-contained within one context window — total input + intermediate scratch + tool outputs + final answer fit comfortably;
- the tool set is small enough that the model can select reliably — typically **$\leq$ 10–15 tools** before selection accuracy degrades, hard-capped by **V13 Tool Budget**;
- the task does not split into roles that are genuinely *distinct in expertise or context* — a "researcher" and a "writer" persona at the same model and same context is not a real split;
- iteration speed and debuggability matter — one agent has one failure domain.

Related: [[R4-ReAct]] · [[I2-Function-Call]] · [[I3-MCP-Server]] · [[K8-Working-Memory]] · [[K11-Observational-Memory]] · [[S3-Persona]] · [[S5-Constraint-Framing]] · [[S6-Output-Template]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[O2-Prompt-Chaining]] · [[O6-Orchestrator-Workers]]
