---
id: O8
title: Loop Agent
type: pattern
category: Orchestration
summary: "Improve a single carried state across rounds by running the same sequence of distinct agents — each with its own role, prompt, and output contract — on the state, until a termination judge says the state is good enough or a hard bound trips."
when_to_use: Long-running workflows; periodic trigger
also_known_as: [Agentic Loop, Iterative Multi-Agent Pipeline, Cyclic Workflow, Generate-Critique-Evolve Loop]
related: [O2, R4, R7, O5, O6, V9]
composes_with: [O4, O9, V14, V15, K6, K7]
mechanism_refs: [1, 2, 3]
canonical: patterns/O8-Loop-Agent.md
derived: true
---

## Description
Improve a single carried state across rounds by running the same sequence of distinct agents — each with its own role, prompt, and output contract — on the state, until a termination judge says the state is good enough or a hard bound trips. Composes with O4, O9, V14, V15, K6, K7. This is a condensed digest; the canonical file (`patterns/O8-Loop-Agent.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task improves measurably with repeated passes by the same multi-agent pipeline (generate $\to$ critique $\to$ revise; search $\to$ synthesise $\to$ evaluate $\to$ refine);
- distinct roles must do distinct work each round — a single ReAct loop would conflate them;
- termination has a definable signal (criterion met, stagnation detected, budget exhausted), not "the model decides it's done";
- the cycle's state object (draft, hypothesis set, codebase) can be carried and mutated round by round.

Related: [[O4-Parallelization]] · [[O9-Multi-Agent-Reflection]] · [[V14-Trajectory-Logging]] · [[V15-LLM-as-Judge]] · [[K6-Context-Compression]] · [[K7-Context-Pruning]] · [[O2-Prompt-Chaining]] · [[R4-ReAct]] · [[R7-Reflexion]] · [[O5-Evaluator-Optimizer]] · [[O6-Orchestrator-Workers]] · [[V9-Bounded-Execution]]
