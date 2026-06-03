---
id: H4
title: Procedural Skill Accumulation
type: pattern
category: Humanizers
summary: "Convert the agent's successful problem-solving work into reusable, parameterised procedures, so the next time a similar task arrives the agent retrieves and adapts a proven skill rather than re-deriving it from scratch — turning one solved task into a permanent capability.."
when_to_use: Generalise successful trajectories into reusable callable skills
also_known_as: [Skill Library, LEGO Memory, Memp, Trajectory Distillation, Workflow Memory, Voyager-Style Skill Acquisition]
related: [K10, H1, R11, S8]
siblings: [H2]
composes_with: [V15, V9, V14, K11, R3, S4, O6]
mechanism_refs: [2, 6, 7, 10]
canonical: patterns/H4-Procedural-Skill-Accumulation.md
derived: true
---

## Description
Convert the agent's successful problem-solving work into reusable, parameterised procedures, so the next time a similar task arrives the agent retrieves and adapts a proven skill rather than re-deriving it from scratch — turning one solved task into a permanent capability. Composes with V15, V9, V14, K11, R3, S4, O6. Sibling of H2. This is a condensed digest; the canonical file (`patterns/H4-Procedural-Skill-Accumulation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent performs **recurring task types** where the same shape of work shows up again — code reviews, data transformations, report generation, navigation flows, tool orchestration recipes;
- task-completion **trajectories are long and expensive** (many tool calls, much reasoning), so re-deriving each time is a real cost;
- the environment and the success criterion are **stable enough** that a skill captured today is still valid in N days;
- the task language has **parameterisable shape** — there is a clear "what is the topic / source / target / parameters" axis along which similar tasks vary.

Related: [[V15-LLM-as-Judge]] · [[V9-Bounded-Execution]] · [[V14-Trajectory-Logging]] · [[K11-Observational-Memory]] · [[R3-Plan-and-Solve]] · [[S4-Instruction-Decomposition]] · [[O6-Orchestrator-Workers]] · [[H2-Episodic-Self-Improvement]] · [[K10-Long-Term-Memory]] · [[H1-Identity-Persistence]] · [[R11-Buffer-of-Thoughts]] · [[S8-Meta-Prompt]]
