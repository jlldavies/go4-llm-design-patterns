---
id: H5
title: Constitutional Self-Alignment
type: pattern
category: Humanizers
summary: "Close the loop on the constitution: detect gaps and degradations during operation, propose principle additions or revisions with reasoning and evidence, and route every proposal through a mandatory human reviewer before the active constitution changes.."
when_to_use: Agent proposes constitution updates; humans approve
also_known_as: [Principle Evolution, Adaptive Ethics, Self-Refining Constitution, Governed Constitution Update, Inference-Time Constitutional AI with HITL]
requires: [V1]
mechanism_refs: [2, 3, 10]
canonical: patterns/H5-Constitutional-Self-Alignment.md
derived: true
---

## Description
Close the loop on the constitution: detect gaps and degradations during operation, propose principle additions or revisions with reasoning and evidence, and route every proposal through a mandatory human reviewer before the active constitution changes. Requires V1. This is a condensed digest; the canonical file (`patterns/H5-Constitutional-Self-Alignment.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs long enough that a static constitution will demonstrably drift out of fit (months to years of operation);
- the domain or the user's needs evolve (regulatory change, product evolution, accumulated user preferences);
- the operator can sustain the **mandatory human review infrastructure** — reviewers, queue, escalation, audit;
- principle changes must be auditable, versioned, and reversible.

Related: [[V1-Human-in-the-Loop]]
