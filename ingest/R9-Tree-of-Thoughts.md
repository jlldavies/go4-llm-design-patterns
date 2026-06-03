---
id: R9
title: Tree of Thoughts
type: pattern
category: Reasoning
summary: "Solve problems where the right reasoning path is not obvious upfront by having the LLM expand a tree of candidate partial solutions, score the promise of each, expand the best, and backtrack from dead ends — substituting *search over a structured space* for a single linear chain of thought.."
when_to_use: BFS/DFS over reasoning states; complex planning
also_known_as: [ToT, Deliberate Problem Solving, Branching Reasoning]
mechanism_refs: [2, 5, 7]
canonical: patterns/R9-Tree-of-Thoughts.md
derived: true
---

## Description
Solve problems where the right reasoning path is not obvious upfront by having the LLM expand a tree of candidate partial solutions, score the promise of each, expand the best, and backtrack from dead ends — substituting *search over a structured space* for a single linear chain of thought. This is a condensed digest; the canonical file (`patterns/R9-Tree-of-Thoughts.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the problem has a **large search space** where the first plausible reasoning path is often wrong — Game of 24, mathematical puzzles, mini-crosswords, planning under constraints, creative writing with hard constraints;
- you can write a **reasonable evaluator** for *partial* solutions — "this state can plausibly reach a valid solution" or "this state cannot";
- one-shot CoT (R1/R2) demonstrably fails or saturates well below the model's ceiling;
- you can afford **5–50$\times$ the LLM calls of CoT** for the lift in quality;
