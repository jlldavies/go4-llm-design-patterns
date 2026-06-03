---
id: O13
title: Negotiation
type: pattern
category: Orchestration
summary: "Coordinate agents whose objectives diverge by *structure*, not just *opinion* — give each agent a private utility function and a walk-away threshold, run them through a bargaining protocol that produces offers, counter-offers, and concessions, and terminate on a deal that all parties accept or a formally-declared no-deal.."
when_to_use: Structured protocol for conflicting objectives
also_known_as: [Multi-Party Consensus, Agent Bargaining, Goal-Mediated Resolution, Stakeholder Negotiation, Multi-Issue Bargaining]
mechanism_refs: [1, 3, 4, 7, 10, 12]
canonical: patterns/O13-Negotiation.md
derived: true
---

## Description
Coordinate agents whose objectives diverge by *structure*, not just *opinion* — give each agent a private utility function and a walk-away threshold, run them through a bargaining protocol that produces offers, counter-offers, and concessions, and terminate on a deal that all parties accept or a formally-declared no-deal. This is a condensed digest; the canonical file (`patterns/O13-Negotiation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- two or more agents represent stakeholders with **structurally different utility functions** (cost vs. quality vs. timeline; buyer vs. seller; competing teams);
- a **single mutually-acceptable outcome** is required as output (a plan, a contract, a resource allocation, a price) — not a synthesised view;
- the agents have **enough information about their own utility** to evaluate offers — i.e., they can score "is this acceptable to me?";
- it is acceptable for the system to return **no-deal** when the gap cannot be bridged; better that than a phoney consensus.
