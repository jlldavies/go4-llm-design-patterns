---
id: O12
title: Debate / Deliberation
type: pattern
category: Orchestration
summary: "Use *adversarial argument between agents holding opposing positions* — not independent critique, not iterative self-refinement — to surface the assumptions, counter-evidence, and failure modes a single agent's reasoning would not see, then synthesise the exchange into a more accurate or better-considered final answer."
when_to_use: Two agents argue opposing positions; synthesiser integrates
also_known_as: [Multi-Agent Debate]
related: [O9, O5, R17, O11]
composes_with: [V15]
mechanism_refs: [1, 3, 5]
canonical: patterns/O12-Debate-Deliberation.md
derived: true
---

## Description
Use *adversarial argument between agents holding opposing positions* — not independent critique, not iterative self-refinement — to surface the assumptions, counter-evidence, and failure modes a single agent's reasoning would not see, then synthesise the exchange into a more accurate or better-considered final answer. Composes with V15. This is a condensed digest; the canonical file (`patterns/O12-Debate-Deliberation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a single agent or a same-direction ensemble produces *confidently wrong* answers on the task — failure mode is over-confidence, not under-confidence;
- the question admits genuinely contested positions where the right answer depends on weighing evidence (factual claims under uncertainty, strategic decisions, hypothesis evaluation, risk assessment, ambiguous interpretation);
- you can afford 2 $\times$ R $\times$ N LLM calls (R debaters $\times$ N rounds + synthesis), typically 6–15 calls per question;
- the synthesis step has a meaningful judgment to make — i.e., a coherent synthesiser agent (or human) exists to weigh the exchange;

Related: [[V15-LLM-as-Judge]] · [[O9-Multi-Agent-Reflection]] · [[O5-Evaluator-Optimizer]] · [[R17-Self-Consistency-Voting]] · [[O11-Blackboard]]
