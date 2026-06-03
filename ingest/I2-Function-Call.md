---
id: I2
title: Function / Tool Call
type: pattern
category: Integration
summary: "Make external actions LLM-routable without giving up typed execution: the LLM reads tool descriptions and picks one with structured arguments; code validates and executes it; the result flows back into the model's context so reasoning continues.."
when_to_use: Model selects and invokes a typed function
also_known_as: [Tool Use]
mechanism_refs: [2, 3]
canonical: patterns/I2-Function-Call.md
derived: true
---

## Description
Make external actions LLM-routable without giving up typed execution: the LLM reads tool descriptions and picks one with structured arguments; code validates and executes it; the result flows back into the model's context so reasoning continues. This is a condensed digest; the canonical file (`patterns/I2-Function-Call.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the choice of *which* action to take depends on interpreting natural-language input, and that interpretation is what the LLM is good at;
- the agent has roughly **1–15 tools** (see V13 Tool Budget) — small enough that every schema can sit in the prompt without crowding it out;
- the tool set is **application-specific** and stable at deploy time (not shared across many agents or clients);
- the model provider already supports function / tool calling natively — no need to invent a parsing layer;
