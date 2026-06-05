# Conflicts — Humanizers

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Critical 4 — H3 $\oplus$ R17  {#critical-4}

**Type:** Mutually Exclusive

R17 reduces entropy: it samples multiple outputs and selects the majority answer — the most consistent, lowest-entropy result. H3 increases entropy: it detects low-entropy states and injects novelty by raising temperature or pivoting approach.

If you apply both to the same task simultaneously, they cancel each other out at best; at worst, H3 fires during an R17 voting round and corrupts the sample diversity calculation.

**Resolution rule:**
- R17 is for: tasks with objectively correct answers where consistency = reliability (reasoning, classification, math)
- H3 is for: tasks where diversity = value (creative, exploratory, open-ended research)
- Never apply H3 during an active R17 voting phase
- Never apply R17 to a task where H3 is needed — by definition, you want diversity, not majority consensus

---

## Critical 7 — H5 $\to$ V1  {#critical-7}

**Type:** Prerequisite Dependency

H5 allows the agent to propose modifications to its own operating principles. This is the most dangerous pattern in the collection if implemented without human review. An agent that autonomously adopts its own principles can:

- Propose principles that serve its task optimization at the expense of user interests
- Gradually drift toward principles that eliminate oversight (self-serving alignment)
- Introduce principles that conflict with hard V7 (AgentSpec) constraints, creating governance gaps

**Resolution rule:** H5 is not valid without mandatory human review at every proposed principle change. This is not a performance tradeoff — it is a safety requirement with no exception.

**Implementation:** Every principle proposal must have: human review step, quarantine period (provisional status for 30+ days), and adversarial review (red-team agent). No principle auto-adopts.

---

## Connection G — H6 $\sim$ H2  {#connection-g}

**Type:** Composability Tension ($\sim$)

H6 (Continuous Inner Monologue) runs internal reflection that produces abstracted summaries of session activity. H2 (Episodic Self-Improvement) uses a Distiller step to compress session experience into persistent improvement artefacts. In a system running both, the H6 Thinker's end-of-session consolidation narrative is structurally equivalent to what the H2 Distiller needs as input — it is already a compressed, reflective summary of the session.

**Consequence:** Running both H6 and H2 with separate Distiller calls wastes one LLM step. The H6 Thinker output is the H2 Distiller input; treat it as such in implementation.

**Efficiency rule:** When H6 and H2 are both active, route H6's consolidation output directly to H2's persistence store rather than running a separate Distiller. This removes one LLM call per session from the Humanizer stack.

---

## Humanizer vs Humanizer

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| H1 (Identity Persistence) | $\leftrightarrow$ | H7 (Adaptive Persona) | H1 defines what is invariant; H7 adapts what is variable. The conflict: without clear boundary, H7 can erode H1 through gradual style adaptation. Resolution: explicitly partition "identity core" (H1: values, principles, commitments) from "expression surface" (H7: tone, vocabulary, detail level). H7 may never touch the identity core. |
| H1 (Identity Persistence) | $\sim$ | H9 (Observational Identity) | H1 is the stable identity; H9 is the evolving self-knowledge. They must be kept consistent: if H9 determines the agent is incapable of a task it previously claimed confidence in, H1's self-representation must update. H9 data informs H1 updates; H1 provides the stable anchor that H9 can't erode through capability measurement alone. |
| H2 (Episodic Self-Improvement) | $\sim$ | H4 (Procedural Skill Accumulation) | H2 accumulates failure lessons; H4 accumulates successful procedures. They are complementary but must not contaminate each other: a partially successful trajectory that also had failures should go to H4 (the successful parts) AND H2 (the failure patterns). Ensure deduplication at the boundary. |
| H3 (Entropy Curiosity) | $\oplus$ | R17 (Self-Consistency) | See CRITICAL 4. Never simultaneously. |
| H5 (Constitutional Self-Alignment) | $\to$ | V1 (Human-in-the-Loop) | See CRITICAL 7. H5 requires V1; no exceptions. |
| H5 (Constitutional Self-Alignment) | H/S | V7 (AgentSpec) | V7 defines hard constraints that H5 cannot evolve. H5 evolves soft principles within the space V7 permits. H5 proposes; V7 enforces the boundary; humans approve within the space between them. |
| H8 (Meta-Agent Self-Modification) | $\to$ | V1 (Human-in-the-Loop) | H8 must have human review for any significant behavioral modification. The scope of auto-modification (without human review) must be explicitly enumerated and minimal. |
| H8 (Meta-Agent Self-Modification) | $\leftrightarrow$ | H5 (Constitutional Self-Alignment) | H8 cannot modify H5's constitutional boundary. H8 tunes parameters; H5 (with human approval) evolves principles; V7 enforces the outer boundary. Never allow H8 to modify constitutional principles, even if "performance data suggests it would help." |
| H10 (Relational Memory) | $\to$ | V5 (Guardrail Layering) | Relational memory containing sensitive user data must be subject to guardrails. H10 without explicit V5 guardrails on relationship depth and data access is an ethical and security liability. |

## Humanizer vs Other Categories

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| H1 (Identity Persistence) | $\leftrightarrow$ | S3 (Persona) | S3 is per-session, stateless. H1 is persistent, session-spanning. H1 is strictly more capable; S3 is the default for systems without session persistence. Do not implement both for the same agent — H1 subsumes S3. |
| H2 (Episodic Self-Improvement) | $\sim$ | R7 (Reflexion) | R7 is within-session Reflexion; H2 persists R7's outputs across sessions. H2 requires R7 as its data source — they compose sequentially, not in conflict. The tension: H2's accumulated lessons may contradict a fresh R7 critique in a new context. Resolution: treat H2 lessons as prior evidence with confidence weighting, not as absolute rules. |
| H6 (Inner Monologue) | $\leftrightarrow$ | V1 (Human-in-the-Loop) | A continuous inner monologue (H6) implies significant autonomous operation between user interactions. When H6 leads to autonomous actions (not just thoughts), V1 must gate those actions. H6's Thinker should be designed to produce insights, not autonomous actions, unless those actions are explicitly scoped and gated. |
| H7 (Adaptive Persona) | $\sim$ | S2 (Few-Shot) | If few-shot examples are from a different user's interaction style than the current user's H7 model suggests, the examples and the persona adaptation will pull in different directions. When H7 is active, prefer zero-shot (S1) or ensure few-shot examples match the H7 user model. |
| H8 (Meta-Agent Self-Modification) | $\leftrightarrow$ | V16 (Offline Eval) | H8's modifications must be validated before deployment. If H8 can modify prompts or configurations, each modification must pass a V16 eval before becoming active. H8 without V16 is unsafe: the "performance signal" H8 optimises against may not represent actual user value. |
| H9 (Observational Identity) | $\sim$ | K11 (Observational Memory) | K11 observes what the agent has seen in the current session; H9 maintains a persistent self-model of what the agent knows and can do across all sessions. They operate at different time scales: K11 is session-scoped; H9 is life-span-scoped. K11 feeds H9 at session end. |

---
