---
id: R6
title: Self-Ask
type: pattern
category: Reasoning
summary: Close the *compositionality gap* — the failure mode in which a model can answer each sub-fact of a multi-hop question individually but cannot combine them — by forcing the model to ask and answer its own follow-up questions before composing the final answer..
when_to_use: Multi-hop factual questions; sub-question chains
also_known_as: [Follow-Up Question Decomposition, Compositional Decomposition, Self-Ask Prompting]
mechanism_refs: [2, 3, 5, 7]
canonical: patterns/R6-Self-Ask.md
derived: true
---

## Description
Close the *compositionality gap* — the failure mode in which a model can answer each sub-fact of a multi-hop question individually but cannot combine them — by forcing the model to ask and answer its own follow-up questions before composing the final answer. This is a condensed digest; the canonical file (`patterns/R6-Self-Ask.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the question is compositional — two to four hops requiring distinct sub-facts;
- the model can plausibly know each sub-fact in isolation but consistently misses the combination;
- you want the decomposition to be *visible* for audit, debug, or operator inspection;
- the sub-questions are answerable by clean recall or a single tool call each (search, RAG, calculator), not by exploratory action.
