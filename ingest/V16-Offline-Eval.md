---
id: V16
title: Offline Eval
type: pattern
category: Reliability
summary: "Establish a held-out, versioned suite of inputs and expected outputs (or pass criteria), run it against the agent on every change, and gate deployment on the result — so quality, safety, and cost have a numeric baseline that any change must clear before it reaches users.."
when_to_use: Batch evaluation against held-out test cases before deployment
also_known_as: [Regression Testing, Pre-Production Eval, Validation Suite, Eval Harness, Eval-Driven Development]
mechanism_refs: [7]
canonical: patterns/V16-Offline-Eval.md
derived: true
---

## Description
Establish a held-out, versioned suite of inputs and expected outputs (or pass criteria), run it against the agent on every change, and gate deployment on the result — so quality, safety, and cost have a numeric baseline that any change must clear before it reaches users. This is a condensed digest; the canonical file (`patterns/V16-Offline-Eval.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a change to prompts, model, tools, or orchestration logic is about to ship;
- the agent has a stable enough specification that "right answer" or "acceptable answer" can be defined per case;
- regressions on previously-handled cases are unacceptable (which is almost always);
- adversarial or compliance-sensitive behaviours must be re-verified on every deploy;
