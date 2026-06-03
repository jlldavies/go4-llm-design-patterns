---
id: K13
title: Retrieval Bundle
type: pattern
category: Knowledge
summary: "Define the exact bundle of operational context a specific agent workflow always needs — not \"relevant documents\" but precisely *these fields from these sources in these shapes* — and then build assembly to deliver that bundle reliably, rather than letting the agent reconstruct it dynamically from raw search results on every run.."
when_to_use: Specify the exact context bundle a workflow always needs — solves the rediscovery problem
also_known_as: [Agent Operating Context, Workflow Context Specification, Typed Memory Contract, Pre-Compiled Context Bundle]
mechanism_refs: [1, 2, 4, 5, 6, 9, 10]
canonical: patterns/K13-Retrieval-Bundle.md
derived: true
---

## Description
Define the exact bundle of operational context a specific agent workflow always needs — not "relevant documents" but precisely *these fields from these sources in these shapes* — and then build assembly to deliver that bundle reliably, rather than letting the agent reconstruct it dynamically from raw search results on every run. This is a condensed digest; the canonical file (`patterns/K13-Retrieval-Bundle.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- you are designing or debugging an agent that runs a specific, recurring workflow type (support, research, document review, financial analysis, procurement, compliance);
- the agent currently rebuilds context from scratch on every run, re-fetching or re-summarizing material it has assembled before;
- the agent's context window is filling with mixed-authority or mixed-freshness content that degrades output reliability;
- you are choosing between retrieval primitives and are not sure which to use — K13 is the prerequisite that answers that question.
