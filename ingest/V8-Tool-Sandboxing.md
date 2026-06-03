---
id: V8
title: Tool Sandboxing
type: pattern
category: Reliability
summary: "Execute every tool call — particularly any LLM-generated code — in a constrained, ephemeral environment whose access to filesystem, network, processes, time, memory, and cost is enumerated and enforced from outside the agent, so that no reasoning error, hallucinated command, or successful prompt injection can damage the host, exfiltrate data, or run unbounded.."
when_to_use: Confine LLM-generated code to a restricted execution environment
also_known_as: [Isolated Execution, Code Execution Isolation, Capability Restriction, Sandboxed Runtime]
related: [R13, R14, V3, V9, I2]
composes_with: [V9, V14, V6, V4, V5]
mechanism_refs: [7]
canonical: patterns/V8-Tool-Sandboxing.md
derived: true
---

## Description
Execute every tool call — particularly any LLM-generated code — in a constrained, ephemeral environment whose access to filesystem, network, processes, time, memory, and cost is enumerated and enforced from outside the agent, so that no reasoning error, hallucinated command, or successful prompt injection can damage the host, exfiltrate data, or run unbounded. Composes with V9, V14, V6, V4, V5. This is a condensed digest; the canonical file (`patterns/V8-Tool-Sandboxing.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent executes LLM-generated code (**R13 CodeAct, R14 Program of Thoughts** — mandatory, no exceptions);
- the agent invokes any tool that writes to filesystem, performs network I/O, or spawns processes with LLM-supplied parameters;
- the system is multi-tenant — one user's tool execution must not affect another's environment or data;
- the agent satisfies the Lethal Trifecta (V3) and V8 is being used to remove the external-communication condition from the Quarantined LLM;

Related: [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[V6-Prompt-Injection-Shield]] · [[V4-Dual-LLM]] · [[V5-Guardrail-Layering]] · [[R13-CodeAct]] · [[R14-Program-of-Thoughts]] · [[V3-Rule-of-Two]] · [[I2-Function-Call]]
