---
id: V1
title: Human-in-the-Loop
type: pattern
category: Reliability
summary: "Make the agent halt at the boundary of any action whose cost-of-error exceeds the cost-of-delay, surface the planned action to a human in interpretable form, and resume only on an explicit verdict — so that irreversible, novel, or high-blast-radius actions never execute autonomously."
when_to_use: "Block on irreversible, novel, or high-blast-radius actions"
also_known_as: [HITL, Approval Gate, Human Checkpoint, Mandatory Review Gate]
related: [V2, H5, H8, H6, V17]
requires: [V10]
composes_with: [V14, V9, V7, S6, S5]
conflicts_with: [V2]
mechanism_refs: [7]
canonical: patterns/V1-Human-in-the-Loop.md
derived: true
---

## Description
Make the agent halt at the boundary of any action whose cost-of-error exceeds the cost-of-delay, surface the planned action to a human in interpretable form, and resume only on an explicit verdict — so that irreversible, novel, or high-blast-radius actions never execute autonomously. Requires V10. In tension with V2. Composes with V14, V9, V7, S6, S5. This is a condensed digest; the canonical file (`patterns/V1-Human-in-the-Loop.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the action is **irreversible** — sending external communications, financial transactions, deleting data, modifying production systems, publishing public content;
- the action is **novel** — outside the agent's evaluated operating envelope (V16 Offline Eval coverage gap);
- the **blast radius is high** — error affects systems, users, or counterparties beyond the agent's own scope;
- a regulatory regime mandates human oversight (EU AI Act Article 14, sector-specific compliance);

Related: [[V10-Checkpointing]] · [[V2-Human-on-the-Loop]] · [[V14-Trajectory-Logging]] · [[V9-Bounded-Execution]] · [[V7-AgentSpec]] · [[S6-Output-Template]] · [[S5-Constraint-Framing]] · [[H5-Constitutional-Self-Alignment]] · [[H8-Meta-Agent-Self-Modification]] · [[H6-Continuous-Inner-Monologue]] · [[V17-Online-Eval]]
