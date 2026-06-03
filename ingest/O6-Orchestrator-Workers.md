---
id: O6
title: Orchestrator-Workers
type: pattern
category: Orchestration
summary: "Have a central LLM decide *at runtime* how to break a goal into sub-tasks and which worker each sub-task goes to, then collect and synthesise the workers' returns — so the decomposition adapts to the specific input instead of being baked into a pipeline.."
when_to_use: Dynamic task decomposition; workers run in isolation
also_known_as: [Hub-and-Spoke, Lead Agent + Subagents, Orchestrator-Subagent, Lead-Researcher Pattern, Manager-Workers, Dispatcher-Workers]
related: [O2, O7, O4, O5, V9, O17, V14]
composes_with: [O4, O17, V14, V15, R4, R13]
mechanism_refs: [4, 6]
canonical: patterns/O6-Orchestrator-Workers.md
derived: true
---

## Description
Have a central LLM decide *at runtime* how to break a goal into sub-tasks and which worker each sub-task goes to, then collect and synthesise the workers' returns — so the decomposition adapts to the specific input instead of being baked into a pipeline. Composes with O4, O17, V14, V15, R4, R13. This is a condensed digest; the canonical file (`patterns/O6-Orchestrator-Workers.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the decomposition into sub-tasks is *not* the same for every input — the count, type, or ordering of sub-tasks depends on what the input contains;
- sub-tasks benefit from running in isolation (clean contexts, specialised prompts, parallel execution);
- the total work would not fit a single agent's context window or tool budget if attempted as one loop;
- you need a clear coordination point for synthesis, audit, and failure-handling.

Related: [[O4-Parallelization]] · [[O17-Agent-Isolation]] · [[V14-Trajectory-Logging]] · [[V15-LLM-as-Judge]] · [[R4-ReAct]] · [[R13-CodeAct]] · [[O2-Prompt-Chaining]] · [[O7-Supervisor-Hierarchy]] · [[O5-Evaluator-Optimizer]] · [[V9-Bounded-Execution]]
