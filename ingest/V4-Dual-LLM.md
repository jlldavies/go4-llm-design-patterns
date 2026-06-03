---
id: V4
title: Dual LLM
type: pattern
category: Reliability
summary: "Make prompt-injection-driven exfiltration architecturally impossible by ensuring no single LLM session simultaneously possesses private data access, tool access, and exposure to untrusted content.."
when_to_use: Quarantine Q-LLM handles untrusted content; privileged P-LLM acts
also_known_as: [Privilege Separation, Privileged + Quarantined Split, P-LLM / Q-LLM, Two-Brain Pattern]
mechanism_refs: [1, 3, 8]
canonical: patterns/V4-Dual-LLM.md
derived: true
---

## Description
Make prompt-injection-driven exfiltration architecturally impossible by ensuring no single LLM session simultaneously possesses private data access, tool access, and exposure to untrusted content. This is a condensed digest; the canonical file (`patterns/V4-Dual-LLM.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- a V3 audit confirms the Lethal Trifecta (private data + untrusted content + external comms) in a single agent;
- the agent processes content from outside the trust boundary (emails, web pages, uploaded documents, third-party API responses);
- the cost of a successful exfiltration attack is catastrophic (PII leakage, financial transactions, irreversible communications);
- the agent has tool access that could be weaponised — outbound email, web requests, data export, code execution.
