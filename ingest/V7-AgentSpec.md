---
id: V7
title: AgentSpec / Declarative Governance
type: pattern
category: Reliability
summary: "Place the agent's hard rules in code outside the model, expressed in a declarative policy artefact, and have an independent runtime engine check every proposed action against that policy — so the rules survive prompt manipulation, produce an audit record, and can be changed without redeploying the model.."
when_to_use: "Declarative, out-of-prompt, deterministic policy enforcement"
also_known_as: [Policy-Driven Agent, Runtime Governance, Deontic Control, Declarative Policy Engine, Programmable Privilege Control]
related: [S9, H5, V4, V6, V8, V5, V15]
composes_with: [V5, V14, V4, V6, V8, V3, V16, V17]
mechanism_refs: [5, 7]
canonical: patterns/V7-AgentSpec.md
derived: true
---

## Description
Place the agent's hard rules in code outside the model, expressed in a declarative policy artefact, and have an independent runtime engine check every proposed action against that policy — so the rules survive prompt manipulation, produce an audit record, and can be changed without redeploying the model. Composes with V5, V14, V4, V6, V8, V3, V16, V17. This is a condensed digest; the canonical file (`patterns/V7-AgentSpec.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent operates in a regulated industry (healthcare, finance, legal, defense, critical infrastructure) and compliance must be *provable*, not "the prompt says so";
- the deployment is enterprise-scale and IT / security must control agent capability independent of any prompt the application team writes;
- the agent is multi-tenant or multi-role, and rules differ per tenant / per role in ways the prompt cannot reliably distinguish;
- a published audit trail of policy decisions is required by law or contract (EU AI Act Article 9 risk-management evidence; SOC 2; HIPAA);

Related: [[V5-Guardrail-Layering]] · [[V14-Trajectory-Logging]] · [[V4-Dual-LLM]] · [[V6-Prompt-Injection-Shield]] · [[V8-Tool-Sandboxing]] · [[V3-Rule-of-Two]] · [[V16-Offline-Eval]] · [[V17-Online-Eval]] · [[S9-Constitutional-Framing]] · [[H5-Constitutional-Self-Alignment]] · [[V15-LLM-as-Judge]]
