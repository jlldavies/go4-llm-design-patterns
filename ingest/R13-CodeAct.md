---
id: R13
title: CodeAct
type: pattern
category: Reasoning
summary: "Make the agent's Action a *program*, not a tool call — so one step can call several tools, branch on what they return, loop, and keep intermediate results in variables — and execute that program in a sandbox whose stdout, return value, and stack traces become the next Observation."
when_to_use: Python as action language; ~20pp accuracy gain over JSON tool calls
cost: medium
also_known_as: [Executable Code Actions, Code-as-Action, Programmatic Tool Calling, Code Agent]
siblings: [R4, R5]
related: [V8, V9, R14, I2, I3]
composes_with: [V14, O6, R7, K6, K7]
requires: [V8]
mechanism_refs: [2, 3, 4]
canonical: patterns/R13-CodeAct.md
derived: true
---

## Description
Make the agent's Action a *program*, not a tool call — so one step can call several tools, branch on what they return, loop, and keep intermediate results in variables — and execute that program in a sandbox whose stdout, return value, and stack traces become the next Observation. Requires V8. Composes with V14, O6, R7, K6, K7. Sibling of R4, R5. This is a condensed digest; the canonical file (`patterns/R13-CodeAct.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task naturally needs multi-tool coordination per step — A's output is B's input, possibly conditioned on a check;
- intermediate results are large or numerous (search hits, file contents, dataframes, lists) and should *not* bloat the LLM context;
- control flow (loops over collections, conditional branches, retries) is part of the action, not the reasoning;
- the model is strong enough to write correct Python against the available tool surface (modern frontier or tool-tuned mid-size models);

Related: [[V8-Tool-Sandboxing]] · [[V14-Trajectory-Logging]] · [[O6-Orchestrator-Workers]] · [[R7-Reflexion]] · [[K6-Context-Compression]] · [[K7-Context-Pruning]] · [[R4-ReAct]] · [[R5-ReWOO]] · [[V9-Bounded-Execution]] · [[R14-Program-of-Thoughts]] · [[I2-Function-Call]] · [[I3-MCP-Server]]
