---
id: V17
title: Online Eval
type: pattern
category: Reliability
summary: "Make the deployed system answer the question *\"is it still working?\"* on its own, continuously, by sampling its live traces, judging them against rubrics that need no ground truth, and surfacing drift as an alert — so quality and safety regressions that only appear in production are detected from the run itself, not from a customer complaint.."
when_to_use: Real-time quality metrics in production
also_known_as: [Production Monitoring, Live Quality Tracking, Continuous Eval, Reference-Free Eval, Drift Monitoring, Real-Time LLM Observability]
mechanism_refs: [1, 7]
canonical: patterns/V17-Online-Eval.md
derived: true
---

## Description
Make the deployed system answer the question *"is it still working?"* on its own, continuously, by sampling its live traces, judging them against rubrics that need no ground truth, and surfacing drift as an alert — so quality and safety regressions that only appear in production are detected from the run itself, not from a customer complaint. This is a condensed digest; the canonical file (`patterns/V17-Online-Eval.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent is in production with non-trivial traffic ($\geq$ ~1000 requests/day) — below that, sampling produces too few datapoints for drift to be statistically distinguishable from noise;
- the answer to *"is it still working?"* needs to be available faster than the next manual review cycle;
- ground truth at production volume is unavailable or unaffordable, but the team can articulate quality and safety rubrics;
- regulatory or operational commitments require continuous monitoring (financial services, healthcare, EU AI Act Article 15 — accuracy and robustness monitoring through the lifecycle);
