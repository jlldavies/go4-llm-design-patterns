---
id: V5
title: Guardrail Layering
type: pattern
category: Reliability
summary: "Place the safety perimeter in code, not in the model."
when_to_use: Input / pre-call / post-call / output guards at all four boundaries
also_known_as: [Multi-Point Safety, Defense in Depth for LLMs, Input-Output Filtering, Four-Point Guardrails, I/O Guards]
mechanism_refs: [1, 2, 7]
canonical: patterns/V5-Guardrail-Layering.md
derived: true
---

## Description
Place the safety perimeter in code, not in the model. Intercept and validate at every boundary the agent crosses — input from the user, the parameters of each tool call, the response of each tool, and the final output to the user — so the system tolerates the model failing any single check. This is a condensed digest; the canonical file (`patterns/V5-Guardrail-Layering.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent invokes external tools (nearly all production agents qualify);
- the agent processes user-supplied or third-party text (web pages, emails, uploaded documents, API responses);
- the domain is safety-critical, regulated, or carries reputational tail risk (healthcare, finance, legal, public-facing brand);
- the agent crosses the V3 Lethal Trifecta surfaces — private data, untrusted content, external communication — in any combination;
