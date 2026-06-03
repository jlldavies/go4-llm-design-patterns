---
id: R20
title: Chain-of-Verification
type: pattern
category: Reasoning
summary: "Reduce hallucination in a single-shot answer by interrogating it: surface the factual claims the answer rests on as explicit verification questions, answer each one independently of the draft, and rewrite the draft from those answers.."
when_to_use: Generate answer; verify each claim independently
also_known_as: [CoVe, Verify-Then-Revise, Question-Driven Self-Verification]
siblings: [R8, R7, R17]
related: [O5]
mechanism_refs: [1, 3, 7, 10]
canonical: patterns/R20-Chain-of-Verification.md
derived: true
---

## Description
Reduce hallucination in a single-shot answer by interrogating it: surface the factual claims the answer rests on as explicit verification questions, answer each one independently of the draft, and rewrite the draft from those answers. Sibling of R8, R7, R17. This is a condensed digest; the canonical file (`patterns/R20-Chain-of-Verification.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the task produces a **fluent factual answer** (biographies, list questions, entity descriptions, summaries with named entities, long-form factual writing) and hallucination of names, dates, or attributes is the dominant failure;
- there is **no automated pass/fail signal** — if there were, **R7 Reflexion** is stronger and cheaper per round;
- you cannot or do not want to add retrieval — **K1 Vanilla RAG** or **K5 Adaptive RAG** are usually a better fix when a corpus exists, but they are infrastructure CoVe does not require;
- the budget tolerates **2–5$\times$ the single-shot cost** (one extra plan call, one batch or N independent answer calls, one revision call);

Related: [[R8-Self-Refine]] · [[R7-Reflexion]] · [[R17-Self-Consistency-Voting]] · [[O5-Evaluator-Optimizer]]
