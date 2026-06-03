---
id: H2
title: Episodic Self-Improvement
type: pattern
category: Humanizers
summary: "Promote R7 Reflexion's ephemeral, within-task verbal critiques into a durable lesson library that survives session resets, is injected into future contexts as light-weight guidance, and accumulates compounding improvement over time — giving the agent the closest thing to *learning* available without fine-tuning."
when_to_use: Distil session lessons into persistent improvement artefacts
also_known_as: [Cross-Session Reflexion, Accumulative Critique, Persistent Lesson Library, Inference-Time Learning Loop]
related: [R7, H1, K10, K12, S8]
composes_with: [R7, H1, K10, K6, V6, V1, V14, H4, H9]
mechanism_refs: [2, 5, 9, 10]
canonical: patterns/H2-Episodic-Self-Improvement.md
derived: true
---

## Description
Promote R7 Reflexion's ephemeral, within-task verbal critiques into a durable lesson library that survives session resets, is injected into future contexts as light-weight guidance, and accumulates compounding improvement over time — giving the agent the closest thing to *learning* available without fine-tuning. Composes with R7, H1, K10, K6, V6, V1, V14, H4, H9. This is a condensed digest; the canonical file (`patterns/H2-Episodic-Self-Improvement.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent runs over **days, weeks, or months** and faces recurring task types where the *same* mistake can plausibly recur (coding agents on a codebase, customer-support agents on a domain, research agents on a topic);
- **R7 Reflexion is already in place** as the in-task engine — H2 has no critiques to persist without it;
- failures are diagnosable enough that a one-paragraph lesson can plausibly point at *what to do differently* next time, not merely "it was wrong";
- the deployment has a persistent store, a curation budget, and a governance path for reviewing new lessons before they steer behaviour;

Related: [[R7-Reflexion]] · [[H1-Identity-Persistence]] · [[K10-Long-Term-Memory]] · [[K6-Context-Compression]] · [[V6-Prompt-Injection-Shield]] · [[V1-Human-in-the-Loop]] · [[V14-Trajectory-Logging]] · [[H4-Procedural-Skill-Accumulation]] · [[H9-Observational-Identity]] · [[K12-Karpathy-Memory]] · [[S8-Meta-Prompt]]
