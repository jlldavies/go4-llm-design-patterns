---
id: V20
title: Output / Schema Validation
type: pattern
category: Reliability
summary: "Treat every generated output as untrusted with respect to its declared shape, validate it against that shape, and recover from non-conformance with a bounded retry loop that carries the validation error back to the model — so downstream code never sees a malformed payload.."
when_to_use: Enforce output contracts; re-ask on validation failure
also_known_as: [Output Validation, Schema-Validated Generation, Validate-and-Repair, Reask Loop, Structured-Output Retry]
composes_with: [S6]
related: [V5, V15, S6]
mechanism_refs: [4, 7, 12]
canonical: patterns/V20-Schema-Validation.md
derived: true
---

## Description
Treat every generated output as untrusted with respect to its declared shape, validate it against that shape, and recover from non-conformance with a bounded retry loop that carries the validation error back to the model — so downstream code never sees a malformed payload. Composes with S6. This is a condensed digest; the canonical file (`patterns/V20-Schema-Validation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the output is consumed by code (parsed, persisted, sent to another API), or by a chained LLM call that depends on a stable shape;
- the schema includes semantic invariants beyond syntactic structure (enums, cross-field rules, domain ranges);
- the runtime cannot rely on schema-constrained decoding for every call (free-text S6, mixed structured + narrative, providers without strict JSON mode, local models without grammar-constrained decoders);
- malformed payloads must never reach the downstream system, even at the cost of an extra round-trip.

Related: [[S6-Output-Template]] · [[V5-Guardrail-Layering]] · [[V15-LLM-as-Judge]]
