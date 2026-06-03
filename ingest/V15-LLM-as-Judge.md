---
id: V15
title: LLM-as-Judge
type: pattern
category: Reliability
summary: "Turn \"is this output any good?\" into a deterministic, schema-checkable call against a written rubric, so generative quality can be measured automatically — at scale, without human labels, and on dimensions traditional metrics cannot reach.."
when_to_use: Second model evaluates quality; catches errors the first cannot see
also_known_as: [Model-Based Evaluation, AI Evaluation, Inferential Evaluation, LLM-as-a-Judge]
related: [O5, V16, R17]
composes_with: [V14, S6]
mechanism_refs: [1, 4]
canonical: patterns/V15-LLM-as-Judge.md
derived: true
---

## Description
Turn "is this output any good?" into a deterministic, schema-checkable call against a written rubric, so generative quality can be measured automatically — at scale, without human labels, and on dimensions traditional metrics cannot reach. Composes with V14, S6. This is a condensed digest; the canonical file (`patterns/V15-LLM-as-Judge.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the output is generative and no exact reference answer exists (or many references are equally valid);
- quality must be measured at production scale, where human labelling is infeasible;
- the quality dimensions can be written down as a rubric a stranger could apply consistently;
- another pattern that needs an automated scorer is in play — V16, V17, O5, S8.

Related: [[V14-Trajectory-Logging]] · [[S6-Output-Template]] · [[O5-Evaluator-Optimizer]] · [[V16-Offline-Eval]] · [[R17-Self-Consistency-Voting]]
