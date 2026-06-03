---
id: I1
title: Direct API Call
type: pattern
category: Integration
summary: "Execute an external action from ordinary code, with parameters fixed by program logic rather than chosen by a language model, so the integration is deterministic, sub-10ms-latency-achievable, and auditable line-for-line.."
when_to_use: Call a deterministic service; no model decision needed
also_known_as: [Deterministic Integration, Synchronous HTTP, Traditional API Client, Hard-Coded Tool Call]
mechanism_refs: [2, 3, 7]
canonical: patterns/I1-Direct-API.md
derived: true
---

## Description
Execute an external action from ordinary code, with parameters fixed by program logic rather than chosen by a language model, so the integration is deterministic, sub-10ms-latency-achievable, and auditable line-for-line. This is a condensed digest; the canonical file (`patterns/I1-Direct-API.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the API to call and its parameters are determined by program logic, by typed variables, or by a structured extraction from prior LLM output — no fresh interpretation needed;
- the call is latency-critical (sub-10ms achievable; LLM routing cannot reach that floor);
- the call is high-frequency and per-call LLM cost would be material at scale;
- the action has compliance, audit, or financial semantics that demand reproducible behaviour for identical inputs;
