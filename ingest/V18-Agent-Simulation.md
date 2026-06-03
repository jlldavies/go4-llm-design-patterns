---
id: V18
title: Agent Simulation
type: pattern
category: Reliability
summary: "Drive the agent through a complete task — with a simulated user, simulated tools, and a simulated environment — under happy-path, edge, adversarial, and load conditions, and score the full trajectory, not just the final answer, against safety and quality criteria — so trajectory-shaped failures invisible to flat eval surface before users see them.."
when_to_use: Simulated environment for pre-deployment stress testing
also_known_as: [Sandbox Testing, Agent Red-Teaming, End-to-End Simulation, Simulated-User Eval, Behavioural Audit]
mechanism_refs: [4, 10]
canonical: patterns/V18-Agent-Simulation.md
derived: true
---

## Description
Drive the agent through a complete task — with a simulated user, simulated tools, and a simulated environment — under happy-path, edge, adversarial, and load conditions, and score the full trajectory, not just the final answer, against safety and quality criteria — so trajectory-shaped failures invisible to flat eval surface before users see them. This is a condensed digest; the canonical file (`patterns/V18-Agent-Simulation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent's value is multi-turn — task completion across a dialogue, not a one-shot answer;
- the agent uses tools whose responses (errors, slowness, malformed payloads, injected content) materially change downstream behaviour;
- the deployment is high-stakes — customer service, financial assistance, security-sensitive domains — where adversarial users are realistic;
- the system is multi-agent (O6 Orchestrator-Workers, O7 Supervisor Hierarchy, O11 Blackboard) and emergent inter-agent dynamics cannot be captured case-by-case;
