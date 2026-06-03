---
id: V13
title: Tool Budget
type: pattern
category: Reliability
summary: "Keep the per-agent tool catalogue small enough that the model's tool-selection accuracy stays in the usable range and the tool schemas do not consume the context budget the actual task needs — by enforcing a hard cap on tool count, a measured cap on schema-token cost, and a discipline of dynamic-load-only-what-the-task-requires.."
when_to_use: Limit active schema tokens — every schema token costs n² attention
also_known_as: [Tool Scope Limit, Tool Inventory Cap, Capability Pruning, Tool Catalogue Discipline, MCP Tax Mitigation]
related: [I3, V3, V9]
composes_with: [I2, O17, V14, K6, V11]
conflicts_with: [I3]
mechanism_refs: [1, 2, 3]
canonical: patterns/V13-Tool-Budget.md
derived: true
---

## Description
Keep the per-agent tool catalogue small enough that the model's tool-selection accuracy stays in the usable range and the tool schemas do not consume the context budget the actual task needs — by enforcing a hard cap on tool count, a measured cap on schema-token cost, and a discipline of dynamic-load-only-what-the-task-requires. In tension with I3. Composes with I2, O17, V14, K6, V11. This is a condensed digest; the canonical file (`patterns/V13-Tool-Budget.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent has more than five tools, *or* will plausibly acquire more (any MCP-using agent qualifies);
- one or more MCP servers are configured, or are likely to be added — schema costs scale with server count, not just tool count;
- the agent runs on a model where the working context is also where reasoning happens (so schema tokens compete with the task);
- tool-selection accuracy is observable as a quality lever (i.e. the agent must reliably pick the right tool, not just have access to a wide set);

Related: [[I3-MCP-Server]] · [[I2-Function-Call]] · [[O17-Agent-Isolation]] · [[V14-Trajectory-Logging]] · [[K6-Context-Compression]] · [[V11-Error-Compaction]] · [[V3-Rule-of-Two]] · [[V9-Bounded-Execution]]
