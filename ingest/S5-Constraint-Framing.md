---
id: S5
title: Constraint Framing
type: pattern
category: Signal
summary: "Give the model an explicit, enumerable list of forbidden behaviours at session setup, so prohibitions are addressed as a first-class concern rather than left implicit in the positive instructions or scattered across the task description.."
when_to_use: "Safety-sensitive tasks, known failure modes"
also_known_as: [Negative Prompting, Boundary Definition, What-Not-To-Do, Hard Constraints, the Prohibition Block]
composes_with: [S3, S6]
related: [S9, V5, V7, H5]
mechanism_refs: [2, 4, 7]
canonical: patterns/S5-Constraint-Framing.md
derived: true
---

## Description
Give the model an explicit, enumerable list of forbidden behaviours at session setup, so prohibitions are addressed as a first-class concern rather than left implicit in the positive instructions or scattered across the task description. Composes with S3, S6. This is a condensed digest; the canonical file (`patterns/S5-Constraint-Framing.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a persona (**S3**) implies authority the model does not have ("as your doctor…") — S5 disclaims it. This is a *mandatory* pairing, not optional: persona without S5 is the false-expertise failure mode.

Related: [[S3-Persona]] · [[S6-Output-Template]] · [[S9-Constitutional-Framing]] · [[V5-Guardrail-Layering]] · [[V7-AgentSpec]] · [[H5-Constitutional-Self-Alignment]]
