---
id: V6
title: Prompt Injection Shield
type: pattern
category: Reliability
summary: "Treat every byte of externally-sourced text as adversarial; sanitise it on entry, mark it as data not instruction, and bound what the agent can do with it — so that a prompt smuggled inside untrusted content cannot redirect the agent's behaviour.."
when_to_use: Structural and positional defences against prompt injection
also_known_as: [Input Sanitisation, Injection Defense, Anti-Hijacking, Spotlighting]
composes_with: [V17]
mechanism_refs: [3, 12]
canonical: patterns/V6-Prompt-Injection-Shield.md
derived: true
---

## Description
Treat every byte of externally-sourced text as adversarial; sanitise it on entry, mark it as data not instruction, and bound what the agent can do with it — so that a prompt smuggled inside untrusted content cannot redirect the agent's behaviour. Composes with V17. This is a condensed digest; the canonical file (`patterns/V6-Prompt-Injection-Shield.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent processes any externally-sourced text — web pages, emails, user uploads, RAG retrievals, external API responses, MCP-tool outputs;
- the agent has tools, especially any that produce side effects or external communication;
- the agent operates in a multi-agent system where one agent passes content to another (the A14 Trust Handoff anti-pattern);
- the threat model includes adversarial users *or* adversarial third parties whose content the user pulls in.

Related: [[V17-Online-Eval]]
