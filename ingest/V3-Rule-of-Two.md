---
id: V3
title: Rule of Two / Lethal Trifecta
type: pattern
category: Reliability
summary: "Make the Lethal Trifecta — the unique combination of capabilities that turns ordinary prompt injection into uncontrollable data exfiltration — visible at design time and continuously thereafter, so an agent that holds all three is *never* shipped without a named mitigation in place.."
when_to_use: Two independent confirmations for high-stakes actions
also_known_as: [Lethal Trifecta Check, Trifecta Audit, Willison's Rule, Dual-Access Prohibition]
related: [V4, V6, V8, V5]
composes_with: [V4, V14, V17]
mechanism_refs: [2, 4]
canonical: patterns/V3-Rule-of-Two.md
derived: true
---

## Description
Make the Lethal Trifecta — the unique combination of capabilities that turns ordinary prompt injection into uncontrollable data exfiltration — visible at design time and continuously thereafter, so an agent that holds all three is *never* shipped without a named mitigation in place. Composes with V4, V14, V17. This is a condensed digest; the canonical file (`patterns/V3-Rule-of-Two.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- you are designing or reviewing any agent that touches user data, third-party content, or outbound channels;
- you are about to add a new tool, MCP server, or data source to an existing agent;
- you are connecting two previously isolated agents (a handoff can compose the trifecta out of two safe halves);
- you are deploying to a regulated or high-stakes domain, where a single successful injection is an incident.

Related: [[V4-Dual-LLM]] · [[V14-Trajectory-Logging]] · [[V17-Online-Eval]] · [[V6-Prompt-Injection-Shield]] · [[V8-Tool-Sandboxing]] · [[V5-Guardrail-Layering]]
