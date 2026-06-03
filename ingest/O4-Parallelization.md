---
id: O4
title: Parallelization
type: pattern
category: Orchestration
summary: "When sub-tasks of a request are genuinely independent of each other, run them simultaneously across distinct LLM calls and aggregate the results programmatically, so wall-clock latency collapses from the sum of the calls to the maximum.."
when_to_use: Independent sub-tasks run concurrently
also_known_as: [Fan-Out / Fan-In, Concurrent LLM Calls, Parallel Execution]
siblings: [R12]
related: [O2, O6, O11, O12, R17]
composes_with: [O6, O17, O2, V15]
mechanism_refs: [2, 6, 7]
canonical: patterns/O4-Parallelization.md
derived: true
---

## Description
When sub-tasks of a request are genuinely independent of each other, run them simultaneously across distinct LLM calls and aggregate the results programmatically, so wall-clock latency collapses from the sum of the calls to the maximum. Composes with O6, O17, O2, V15. Sibling of R12. This is a condensed digest; the canonical file (`patterns/O4-Parallelization.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the work decomposes into sub-tasks with no data dependency between them;
- the decomposition is known at design time (no dynamic delegation needed);
- wall-clock latency is a binding constraint, or higher confidence from an ensemble is needed;
- your serving stack and rate-limit budget actually permit concurrent calls.

Related: [[O6-Orchestrator-Workers]] · [[O17-Agent-Isolation]] · [[O2-Prompt-Chaining]] · [[V15-LLM-as-Judge]] · [[R12-Skeleton-of-Thought]] · [[O11-Blackboard]] · [[O12-Debate-Deliberation]] · [[R17-Self-Consistency-Voting]]
