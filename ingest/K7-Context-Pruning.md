---
id: K7
title: Context Pruning
type: pattern
category: Knowledge
summary: "Reclaim context-window space by deleting content that has served its purpose, without summarising or altering what remains.."
when_to_use: Remove spent spans without lossy summarisation
also_known_as: [Selective Recall, Context Cleaning, Relevance Filtering, Tool-Result Dropping]
mechanism_refs: [2, 3, 4, 5]
canonical: patterns/K7-Context-Pruning.md
derived: true
---

## Description
Reclaim context-window space by deleting content that has served its purpose, without summarising or altering what remains. This is a condensed digest; the canonical file (`patterns/K7-Context-Pruning.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent produces large tool outputs that get fully consumed — database queries, file reads, API responses;
- retrieved documents have been used and the sub-task that needed them is finished;
- errors have been handled, or intermediate outputs are now redundant.
