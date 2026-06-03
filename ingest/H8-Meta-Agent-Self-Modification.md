---
id: H8
title: Meta-Agent Self-Modification
type: pattern
category: Humanizers
summary: "Make the operational configuration of a production agent a continuously-improving artefact — tuned online against measured performance — while preventing the runaway, the reward-hack, and the unreviewed value-edit that unconstrained self-modification produces."
when_to_use: Agent edits own system prompt within a governed allowlist
also_known_as: [Self-Improving Agent, Online Self-Tuning, Online Prompt Evolution, Tool Self-Configuration, Recursive Self-Modification, Self-Referential Agent]
related: [S8, V1, V16, V7, H5]
composes_with: [V9, V10, V14, V15, H2, H4]
siblings: [R7, S8]
mechanism_refs: [7]
canonical: patterns/H8-Meta-Agent-Self-Modification.md
derived: true
---

## Description
Make the operational configuration of a production agent a continuously-improving artefact — tuned online against measured performance — while preventing the runaway, the reward-hack, and the unreviewed value-edit that unconstrained self-modification produces. Composes with V9, V10, V14, V15, H2, H4. Sibling of R7, S8. This is a condensed digest; the canonical file (`patterns/H8-Meta-Agent-Self-Modification.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the system is at **production scale** with abundant performance signal — thousands to millions of invocations per day, where manual tuning of dozens of sub-components is genuinely infeasible;
- a **V16 Offline Eval** suite exists, is maintained, and reflects the user-value the operator actually cares about (not a proxy that drifts from it);
- a **V1 Human-in-the-Loop** approver is real and resourced for consequential changes — not aspirational;
- the modification surface can be **enumerated, code-enforced, and audited** — not "trust the agent to stay in bounds" (the mechanical reason: a prompt-level scope instruction is an input to stochastic sampling — the model may or may not follow it depending on which token path is drawn. A code-level executor that refuses descriptors outside the allowlist is deterministic — same input, same rejection, regardless of what the model proposed (mechanism 7). This is not about distrust; it is about substituting reliable determinism for unreliable probabilistic instruction-following);

Related: [[V9-Bounded-Execution]] · [[V10-Checkpointing]] · [[V14-Trajectory-Logging]] · [[V15-LLM-as-Judge]] · [[H2-Episodic-Self-Improvement]] · [[H4-Procedural-Skill-Accumulation]] · [[R7-Reflexion]] · [[S8-Meta-Prompt]] · [[V1-Human-in-the-Loop]] · [[V16-Offline-Eval]] · [[V7-AgentSpec]] · [[H5-Constitutional-Self-Alignment]]
