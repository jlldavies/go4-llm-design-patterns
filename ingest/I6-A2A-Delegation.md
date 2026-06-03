---
id: I6
title: A2A Delegation
type: pattern
category: Integration
summary: "Make a cross-boundary agent call interoperable by default — discover the executor via its Agent Card, submit a typed task, stream status, receive a structured result, and handle failure as a defined protocol event rather than a bespoke integration."
when_to_use: Structured task delegation to another agent via A2A protocol
also_known_as: [Agent-to-Agent Protocol, Agent2Agent, A2A, Cross-Vendor Task Delegation, Inter-System Agent RPC]
related: [I5, O15, I3, V12]
composes_with: [O6, V14, V9, V6, V1]
mechanism_refs: [3, 6, 10, 11]
canonical: patterns/I6-A2A-Delegation.md
derived: true
---

## Description
Make a cross-boundary agent call interoperable by default — discover the executor via its Agent Card, submit a typed task, stream status, receive a structured result, and handle failure as a defined protocol event rather than a bespoke integration. Composes with O6, V14, V9, V6, V1. This is a condensed digest; the canonical file (`patterns/I6-A2A-Delegation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- The orchestrator and at least one delegated executor live in different systems, vendors, organisations, or trust domains.
- Multiple executors might be substitutable for the same skill — selection is by Agent Card capability, not by hardcoded URL.
- The task is long-running enough that streaming status updates are useful (cancellation, partial results, early decisions).
- The pipeline must scale beyond a single codebase or deployment.

Related: [[O6-Orchestrator-Workers]] · [[V14-Trajectory-Logging]] · [[V9-Bounded-Execution]] · [[V6-Prompt-Injection-Shield]] · [[V1-Human-in-the-Loop]] · [[I5-Agent-Card]] · [[O15-Agent-Handoff]] · [[I3-MCP-Server]] · [[V12-Stateless-Reducer]]
