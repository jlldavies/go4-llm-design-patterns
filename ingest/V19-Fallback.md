---
id: V19
title: Fallback / Graceful Degradation
type: pattern
category: Reliability
summary: "Make every failure mode of the primary path land on a *named, pre-declared, cheaper* execution path so the system answers something useful instead of an error, while loudly signalling that it has degraded.."
when_to_use: Defined behaviour when primary path fails
also_known_as: [Graceful Degradation, Circuit-Breaker Fallback, Failover, Degraded-Mode Path, Recovery Lane]
mechanism_refs: [8]
canonical: patterns/V19-Fallback.md
derived: true
---

## Description
Make every failure mode of the primary path land on a *named, pre-declared, cheaper* execution path so the system answers something useful instead of an error, while loudly signalling that it has degraded. This is a condensed digest; the canonical file (`patterns/V19-Fallback.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the primary path has known, frequent failure modes — rate limits, timeouts, provider outages, V9 caps, guardrail rejections, V15 judge failures;
- the user-facing contract requires *an answer* — silently returning an error is worse than returning a degraded answer with a disclaimer;
- a cheaper / simpler / cached / deterministic path can answer at least a subset of queries adequately;
- the system is in production and the cost of a hard failure (a 500, a stuck workflow, a human waiting) exceeds the cost of a degraded answer.
