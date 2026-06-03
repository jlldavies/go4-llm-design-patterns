---
id: R11
title: Buffer of Thoughts
type: pattern
category: Reasoning
summary: "Replace re-deriving a reasoning structure on every hard problem with retrieving and instantiating a previously distilled *thought-template*, so the cost of search is paid once across a problem family rather than every problem in it.."
when_to_use: Reusable reasoning patterns distilled from prior runs
also_known_as: [BoT, Meta-Buffer Reasoning, Template-Augmented Reasoning, Thought-Augmented Reasoning]
mechanism_refs: [2, 5, 9, 10]
canonical: patterns/R11-Buffer-of-Thoughts.md
derived: true
---

## Description
Replace re-deriving a reasoning structure on every hard problem with retrieving and instantiating a previously distilled *thought-template*, so the cost of search is paid once across a problem family rather than every problem in it. This is a condensed digest; the canonical file (`patterns/R11-Buffer-of-Thoughts.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the problem stream contains recurring abstract structures (mathematical puzzles, code-generation patterns, planning skeletons);
- ToT or LATS quality is desired but per-problem cost is unacceptable;
- a curation / distillation phase across solved problems is affordable;
- problem-shape is a recognisable feature you (or the LLM) can extract.
