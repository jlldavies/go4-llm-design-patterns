---
id: DECISION-signal
title: Signal — Decision Guide
type: decision-guide
summary: How to choose among Signal patterns.
canonical: patterns/SIGNAL-DECISION.md
derived: true
---

## Decision Flow

```
Start with S1 (Zero-Shot). Upgrade only when you can measure the gap.

Is format control or style matching the core problem?
  → S2 (Few-Shot): static examples if possible; dynamic only if required
    ⚠ Dynamic S2 breaks prefix cache for all upstream stable patterns

Does the task need domain expertise framing or a specific tone?
  → S3 (Persona): bundle with S5/S6/S9 in a single stable system prompt

Are there specific behaviours the model must never exhibit?
  → S5 (Constraint Framing): explicit prohibition list alongside task description

Does a downstream system need consistent structured output?
  → S6 (Output Template): output skeleton in system prompt

Does the task have multiple steps where order matters?
  → S4 (Instruction Decomposition): numbered steps in the instruction

Do values or principles need runtime enforcement?
  → S9 (Constitutional Framing): self-critique loop against explicit principles

Does the prompt itself need to be optimised automatically?
  → S8 (Meta-Prompt): requires V15 (LLM-as-Judge) or R17 as evaluator
    ⚠ Measure cost before using; much more expensive than S1–S6/S9
```

## Caching Guide

S3, S5, S6, and S9 are **setup-band** patterns. Bundle them together in a single stable system prompt — this is the cacheable prefix unit. Provider prefix caching (Anthropic: ~5 min TTL, ~10% cost on cache hits) reduces the cost of this bundle to near-zero for all calls within the TTL window.

| Pattern | Cacheable? | Notes |
|---|---|---|
| S1 Zero-Shot | Yes — full prompt | Cheapest baseline |
| S2 Few-Shot (static) | Yes | Stable prefix; caches cleanly |
| S2 Few-Shot (dynamic/RAG) | **No** | Changes prefix every call; forfeits cache for all upstream patterns |
| S3 Persona | Yes | Bundle with S5, S6, S9 |
| S4 Instruction Decomposition | Yes | Merge into S3 block when possible |
| S5 Constraint Framing | Yes | Bundle with S3, S6, S9 |
| S6 Output Template | Yes | Bundle with S3, S5, S9 |
| S8 Meta-Prompt | Partial | Only meta-prompt prefix caches |
| S9 Constitutional Framing | Yes | Bundle with S3, S5, S6 |