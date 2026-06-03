---
id: O8
title: Loop Agent
type: pattern
category: Orchestration
summary: "Improve a single carried state across rounds by running the same sequence of distinct agents — each with its own role, prompt, and output contract — on the state, until a termination judge says the state is good enough or a hard bound trips.."
when_to_use: Long-running workflows; periodic trigger
also_known_as: [Agentic Loop, Iterative Multi-Agent Pipeline, Cyclic Workflow, Generate-Critique-Evolve Loop]
mechanism_refs: [1, 2, 3]
canonical: patterns/O8-Loop-Agent.md
derived: true
---

## Description
Improve a single carried state across rounds by running the same sequence of distinct agents — each with its own role, prompt, and output contract — on the state, until a termination judge says the state is good enough or a hard bound trips. This is a condensed digest; the canonical file (`patterns/O8-Loop-Agent.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task improves measurably with repeated passes by the same multi-agent pipeline (generate $\to$ critique $\to$ revise; search $\to$ synthesise $\to$ evaluate $\to$ refine);
- distinct roles must do distinct work each round — a single ReAct loop would conflate them;
- termination has a definable signal (criterion met, stagnation detected, budget exhausted), not "the model decides it's done";
- the cycle's state object (draft, hypothesis set, codebase) can be carried and mutated round by round.
