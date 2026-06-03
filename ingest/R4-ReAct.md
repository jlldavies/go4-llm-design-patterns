---
id: R4
title: ReAct
type: pattern
category: Reasoning
summary: "Let an agent make its next decision *after* seeing the result of its last action, by interleaving short reasoning traces with tool calls and feeding each tool's return back into the model — so the trajectory adapts to what the environment actually says, instead of executing a plan written before any of it was known.."
when_to_use: Adaptive tool use; each action informs the next
also_known_as: [Reason+Act, Reason-and-Act Loop, Think-Act-Observe, Standard Agent Loop, the Agent Loop]
siblings: [R5, R13]
related: [V9, R3, R1, R2]
composes_with: [V14, O6, K8, K6, K7, R7, I2, I3, I4]
conflicts_with: [R5]
mechanism_refs: [2, 3, 4, 7, 12]
canonical: patterns/R4-ReAct.md
derived: true
---

## Description
Let an agent make its next decision *after* seeing the result of its last action, by interleaving short reasoning traces with tool calls and feeding each tool's return back into the model — so the trajectory adapts to what the environment actually says, instead of executing a plan written before any of it was known. In tension with R5. Composes with V14, O6, K8, K6, K7, R7, I2, I3, I4. Sibling of R5, R13. This is a condensed digest; the canonical file (`patterns/R4-ReAct.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task requires tool use, and the *sequence* of tool calls cannot be enumerated up front (each call depends on what the last one returned);
- the environment may surface errors, empty results, or unexpected data that should change the next decision;
- exploratory or open-ended tasks where the path to the answer is unknown (multi-hop question answering, code investigation, web navigation, debugging);
- you want a *visible* reasoning trace per step for inspectability, audit, and debugging.

Related: [[R5-ReWOO]] · [[V14-Trajectory-Logging]] · [[O6-Orchestrator-Workers]] · [[K8-Working-Memory]] · [[K6-Context-Compression]] · [[K7-Context-Pruning]] · [[R7-Reflexion]] · [[I2-Function-Call]] · [[I3-MCP-Server]] · [[I4-CLI-Invocation]] · [[R13-CodeAct]] · [[V9-Bounded-Execution]] · [[R3-Plan-and-Solve]] · [[R1-Zero-Shot-CoT]] · [[R2-Few-Shot-CoT]]
