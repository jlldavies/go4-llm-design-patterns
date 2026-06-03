---
id: O3
title: Routing
type: pattern
category: Orchestration
summary: "Make the choice of handler an explicit, inspectable, swappable step, so each input type meets a handler tuned for it and the routing decision itself becomes a first-class object the system can log, test, and improve.."
when_to_use: Classify input; dispatch to specialist prompt or agent
also_known_as: [Classifier-Dispatcher, Intent Router, Query Router, Triage]
mechanism_refs: [1, 8]
canonical: patterns/O3-Routing.md
derived: true
---

## Description
Make the choice of handler an explicit, inspectable, swappable step, so each input type meets a handler tuned for it and the routing decision itself becomes a first-class object the system can log, test, and improve. This is a condensed digest; the canonical file (`patterns/O3-Routing.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- inputs fall into clearly distinct categories that benefit from category-specific handling (different prompts, different tools, different models);
- a generalist handler measurably underperforms specialists on at least one category;
- you want a deliberate cost split — small models for easy categories, larger for hard ones;
- you need an explicit escalation path (human, specialist team, premium tier) for a defined subset of inputs;
