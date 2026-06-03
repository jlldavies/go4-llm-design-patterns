---
id: V11
title: Error Compaction
type: pattern
category: Reliability
summary: "Keep the cumulative weight of errors, exceptions, and tool failures inside the agent's context window small enough that the agent retains the diagnostic signal but does not lose attention or budget to repeated raw tracebacks.."
when_to_use: Compress errors into compact structured signals
also_known_as: [Compact Errors]
related: [K6, K7]
composes_with: [V14, V9]
mechanism_refs: [2, 3, 4]
canonical: patterns/V11-Error-Compaction.md
derived: true
---

## Description
Keep the cumulative weight of errors, exceptions, and tool failures inside the agent's context window small enough that the agent retains the diagnostic signal but does not lose attention or budget to repeated raw tracebacks. Composes with V14, V9. This is a condensed digest; the canonical file (`patterns/V11-Error-Compaction.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs a loop with tool calls, code execution, or external APIs that fail with non-trivial frequency;
- failures produce verbose tracebacks, HTTP error bodies, or compiler output that consume meaningful context;
- the same class of error can recur across turns and would otherwise be re-appended each time;
- you need the agent to keep the self-healing behaviour (read the error, try again) without window inflation.

Related: [[V14-Trajectory-Logging]] · [[V9-Bounded-Execution]] · [[K6-Context-Compression]] · [[K7-Context-Pruning]]
