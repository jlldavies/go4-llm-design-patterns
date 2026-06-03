# Category VII — Humanizer Patterns

A **Humanizer pattern** is a design pattern for the *longitudinal* layer of an agent: how it acquires continuity, self-knowledge, and human-like adaptive behaviour across sessions. Humanizer patterns separate *who the agent is and how it has changed* from *what it is doing in this turn*.

## Usage

A naive LLM agent is amnesiac, ahistorical, and self-blind. Each invocation starts from zero: no memory of prior commitments, no record of what it has tried, no model of the user it is speaking to, no principles it has refined through experience, no awareness that it is the same agent as yesterday. The agent is, in a strict sense, a stranger every session. For one-shot tasks this is acceptable; for any agent expected to *grow into a role* — a personal assistant, a research companion, a long-running automation — it is the dominant source of user frustration and capability ceiling.

Humanizer patterns add the longitudinal dimension. They do not change what the model can do in a single turn; they change what survives between turns, and how that surviving state shapes the next turn. Apply a Humanizer pattern whenever:

- the agent runs across multiple sessions and users expect continuity;
- the agent should improve through experience without weight updates;
- the agent must accurately answer "what do I know?", "what have I done?", "who am I speaking to?";
- the agent's communication style or operating principles should adapt to the people and contexts it serves;
- a continuous background reasoning process, not a per-turn one, is what the role requires.

## Forces

Every Humanizer pattern resolves the same three forces in tension. A pattern is the right choice for a situation when it balances them in the way that situation demands.

1. **A stateless model must behave like a stateful agent.** LLM inference is, by construction, a pure function of its inputs; the *agent* is the surrounding system that gives it memory, history, and identity. Humanizer patterns are the disciplined way to build that surround without pretending the model itself has changed. There is no weight update. The model does not learn from your sessions. All compounding is externalised memory — artefacts that are re-loaded into context at the start of later sessions. The compounding is only as good as the retrievability and signal-density of what is written down.

2. **Continuity and adaptation are in direct tension.** An agent that never changes cannot improve; an agent that changes freely loses the consistency that makes it trustworthy. Every Humanizer pattern fixes some surface (identity, principles, capabilities) and lets another evolve (style, lessons, skills, relationships), and is explicit about which is which.

3. **Self-modification is the most dangerous thing an agent can do.** The closer a pattern gets to letting the agent change its own values, principles, or operating parameters, the more strictly it must be paired with human oversight (V1) and bounded enforcement (V7). The Humanizer bands are deliberately ordered from low-risk continuity at the top to highest-risk self-modification at the bottom, and that ordering is also the order in which they should be adopted.

A Humanizer pattern is, in each case, a disciplined answer to one question: what part of the agent should persist or adapt across the seam between sessions, and what governs how it does so safely.

## Structure

All Humanizer patterns share one skeleton. They interpose a **persistence and update stage** between successive sessions of the agent:

```
  Session N ────▶ Extract ────▶ Persistent Store ────▶ Inject ────▶ Session N+1
 (live           (identity,    (per-user, per-agent     (Genesis
  context,        lessons,      state surviving         State,
  reasoning,      skills,       context reset)          retrieved
  outputs)        principles,                            lessons,
                  user model)                            skill library,
                                                         user model)
```

Patterns differ in *what they extract* — identity, principles, lessons, skills, user models, capability records, relationship state — and in *what governs the update* — automatic write-through, human-gated approval, decay and confidence scoring, evaluator-guarded modification. The five bands below group the patterns by the longitudinal layer they own: who the agent is (VII-A), how it learns (VII-B), how it deliberates between turns (VII-C), what it knows about itself (VII-D), and how it relates to the people it serves (VII-E). They are stackable layers rather than alternatives: a mature long-running agent typically instantiates a pattern from each band at once, with H1 at the bottom as the substrate every other pattern presumes.

**Injection cost and the stacked Humanizer budget.** The Inject step is expensive: injected tokens remain in the context window for the session's duration, compounding the O(n²) attention cost of every turn (mechanism 2). Patterns that stack — H1 + H2 + H7 + H9 + H10 all loading at session start — must sum their injection budgets and manage the total as a first-class cost constraint. The canonical Humanizer stack targets $\leq$ 500 (H1) + $\leq$ 1,000 (H2) + $\leq$ 100 (H7) + $\leq$ 2,000 (H9) + $\leq$ 1,000 (H10) = ~4,600 tokens of persistent-state injection before any session-specific working context. At modern context windows this is manageable, but it is not free.

**Prefix-cache discipline for the full stack.** The ordering of injection tiers across stacked Humanizer patterns — H1 $\to$ H2/H9 $\to$ H7 $\to$ H10 $\to$ session content — is implied by the individual patterns but deserves a single architectural statement. For provider prefix caching (mechanism 5) to benefit the composite, the prompt must be structured stable-first, variable-last: H1 Genesis State (most stable) $\to$ fixed H9 capability entries $\to$ fixed H7 identity-bound defaults $\to$ H2 task-relevant lessons $\to$ H7 user-specific style $\to$ H10 relational content $\to$ session input. Any token that varies per user or per session placed before the stable portion forces a cache miss on all subsequent stable content. Treating the stable prefix boundary as an explicit architectural decision, not a formatting preference, is the discipline that lets the stacked Humanizer stack earn prefix-cache dividends at scale.

**H3 and R17 — mechanical conflict.** The category correctly notes that H3 is mutually exclusive with R17 Self-Consistency Voting. The mechanical reason: R17 reduces output diversity by majority vote; H3 increases it to escape stagnation — they operate as direct opposites at the sampling level (mechanism 7). Applying both simultaneously corrupts the vote while suppressing the stagnation signal H3 depends on.

## Examples

**VII-A — Identity.** The invariant core, and its variable expression.
- **H1 Identity Persistence** — inject a stable, invariant self-representation (values, style, commitments) at the head of every context window so the agent is recognisably the same agent across sessions. Prerequisite for every other H-pattern.
- **H7 Adaptive Persona** — let the *variable surface* of that identity (detail level, technical depth, format, tone) adapt per-user, without ever crossing into H1's invariant core.

**VII-B — Learning.** How the agent improves through experience without weight updates.
- **H2 Episodic Self-Improvement** — persist R7 Reflexion's verbal self-critiques across sessions as a curated *lesson library*; the agent learns from its failures.
- **H4 Procedural Skill Accumulation** — distil successful task trajectories into reusable parameterised skill procedures; the agent learns from its successes. Complement of H2.
- **H8 Meta-Agent Self-Modification** — tune operational parameters (prompts, tool ordering, sub-agent configs) from measured performance signals, inside an enumerated surface, gated by V16 Offline Eval and V1 Human-in-the-Loop. The most powerful and most dangerous Humanizer pattern.

**VII-C — Deliberation.** Cognitive control between turns.
- **H3 Entropy-Driven Curiosity** — detect when a reasoning loop has collapsed into repetition and break it by raising temperature or injecting a novelty cue. Mutually exclusive with R17 Self-Consistency Voting on the same task (see CONFLICTS CRITICAL 4).
- **H6 Continuous Inner Monologue** — run a persistent background reasoner alongside the user-facing responder; the agent thinks between turns and across sessions, not only when prompted.

**VII-D — Self-knowledge.** What the agent knows about itself.
- **H9 Observational Identity** — maintain an explicit, evolving capability map and action history with confidence and freshness on every entry; the agent can honestly answer "what do I know?" and "what have I done?".
- **H5 Constitutional Self-Alignment** — let the agent's operating principles evolve through experience, but only by *proposing*: every change passes a mandatory human approval gate (see CONFLICTS CRITICAL 7).

**VII-E — Relational.** The agent-user relationship as a first-class data structure.
- **H10 Relational Memory** — a persistent per-user model of goals, working history, stated and observed preferences, and the boundaries of appropriate depth; gated by V5 Guardrail Layering against parasocial harm.

## See also

- **Category I — Signal patterns** — S3 Persona and S9 Constitutional Framing are the per-session, stateless precursors that H1 and H5 turn into persistent, evolving structures.
- **Category II — Knowledge patterns** — every Humanizer pattern sits on top of K10 Long-Term Memory or K11 Observational Memory as its persistent substrate; without that infrastructure there is nothing for Humanizer patterns to write to.
- **Category III — Reasoning patterns** — R7 Reflexion is the data source for H2; R4 ReAct, R3 Plan-and-Solve, and R7 Reflexion are the loops H3 wraps; R17 Self-Consistency Voting is mutually exclusive with H3.
- **Category V — Reliability patterns** — V1 Human-in-the-Loop is a hard prerequisite for H5 and H8; V5 Guardrail Layering gates H10; V7 AgentSpec enforces the outer boundary that H5 cannot cross; V16 Offline Eval gates every H8 modification.

*The "Humanizer" framing follows the Theater of Mind paper's Global-Workspace synthesis (arXiv 2604.08206) and the MIRROR inner-monologue architecture (arXiv 2506.00430), generalised here to the longitudinal layer of any agent.*

---

## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| H1 | **Identity Persistence** | Genesis State | Stable invariant self at position 0 every session | Any multi-session agent |
| H2 | **Episodic Self-Improvement** | Cross-Session Reflexion | Persist verbal self-critiques; improve without weight updates | Recurring task types |
| H3 | **Entropy-Driven Curiosity** | Deadlock Break | Increase temperature or inject stimuli on stagnation | Creative agents; stuck reasoning loops |
| H4 | **Procedural Skill Accumulation** | Skill Library | Distil successful trajectories into reusable skills | Agents with recurring task types |
| H5 | **Constitutional Self-Alignment** | Principle Evolution | Operating principles evolve through experience with human checkpoints | Long-running agents; governed alignment |
| H6 | **Continuous Inner Monologue** | MIRROR | Background reasoning separate from user-facing responses | Persistent assistants; monitoring agents |
| H7 | **Adaptive Persona** | User-Calibrated Style | Communication adapts to observed user preferences | Personal assistants; multi-user systems |
| H8 | **Meta-Agent Self-Modification** | Self-Improving Agent | Agent modifies own operational parameters within governed allowlist | Large-scale production; abundant eval data |
| H9 | **Observational Identity** | Self-Knowledge Model | Explicit model of own capabilities and knowledge state | Multi-session; capability routing |
| H10 | **Relational Memory** | User Model Persistence | Persistent user relationship record with GDPR erasure | Personal assistants; coaching |

---

## Cognitive Science Grounding

Humanizer patterns map to classical cognitive science theories — the convergence suggests the patterns capture something real about how intelligence works over time.

| Pattern | Cognitive Theory | Source |
|---|---|---|
| O11 Blackboard | Global Workspace Theory (Baars) | Explicit in Theater of Mind paper |
| O10 Swarm | Society of Mind (Minsky) | Multi-specialised agents |
| R16 Talker-Reasoner | Dual-Process Theory (Kahneman) | Direct mapping: System 1/2 |
| K10 Long-Term Memory | Tulving / Baddeley memory taxonomy | Episodic, semantic, procedural variants |
| K11 Observational Memory | Extended Mind Thesis (Clark) | External tool as cognitive extension |
| H1 Identity Persistence | Autobiographical memory (Tulving 1985) | Genesis State in Theater of Mind |
| H2 Episodic Self-Improvement | Episodic memory consolidation | Reflexion extended cross-session |
| H3 Entropy-Driven Curiosity | Optimal Arousal / Noradrenergic system | Theater of Mind — entropy monitoring |
| H5 Constitutional Self-Alignment | Moral development (Kohlberg) | Constitutional AI extended to inference |
| H6 Inner Monologue | Vygotskian inner speech | MIRROR / Thinker architecture |
| H7 Adaptive Persona | Theory of Mind (Premack & Woodruff) | User model as cognitive representation |
| H10 Relational Memory | Parasocial relationship theory | HCI research; Skjuve et al. 2021 |

---

## H1 — Identity Persistence

Inject a stable, invariant self-representation — values, style, capabilities, outstanding commitments — at the head of every context window, so the agent is recognisably the same agent across sessions, instances, and resets. The foundational Humanizer pattern; subsumes S3 Persona for any system with cross-session continuity, and is a prerequisite for every other H-pattern.

**Full entry:** [`H1-Identity-Persistence.md`](H1-Identity-Persistence.md)

---

## H2 — Episodic Self-Improvement

Persist R7 Reflexion's verbal self-critiques across sessions, deduplicating and ageing them into a curated *lesson library* that is injected into future sessions — so the agent improves through experience without any weight update. The cross-session extension of R7; sibling of H4 (H2 learns from failure, H4 learns from success).

**Full entry:** [`H2-Episodic-Self-Improvement.md`](H2-Episodic-Self-Improvement.md)

---

## H3 — Entropy-Driven Curiosity

Monitor the diversity of an agent's recent output; when it collapses — repeated tool calls, near-identical thoughts, looping plans — automatically raise temperature or inject a novelty cue to break the loop, then decay back to baseline. Wraps a reasoning loop (R4, R3, R7) and intervenes on a measured stagnation signal.

**Full entry:** [`H3-Entropy-Driven-Curiosity.md`](H3-Entropy-Driven-Curiosity.md) — *mutually exclusive with R17 Self-Consistency Voting on the same task (CONFLICTS CRITICAL 4): R17 deliberately reduces output diversity by majority vote; H3 deliberately increases it to escape stagnation. Never apply simultaneously.*

---

## H4 — Procedural Skill Accumulation

After a task succeeds, distil the trajectory that produced it — the sequence of steps, decisions, and tool calls — into a reusable parameterised skill, store it in a skill library, and retrieve and instantiate matching skills at the start of similar future tasks instead of re-deriving them. The positive-experience counterpart to H2; sits on K10 Long-Term Memory (procedural variant).

**Full entry:** [`H4-Procedural-Skill-Accumulation.md`](H4-Procedural-Skill-Accumulation.md)

---

## H5 — Constitutional Self-Alignment

Let an agent's operating principles evolve through experience — but only by *proposing* changes, never adopting them: every modification of the constitution passes through a mandatory human approval checkpoint before it takes effect. The governance-loop extension of S9 Constitutional Framing.

**Full entry:** [`H5-Constitutional-Self-Alignment.md`](H5-Constitutional-Self-Alignment.md) — *hard prerequisite on V1 Human-in-the-Loop (CONFLICTS CRITICAL 7): H5 is the most dangerous pattern in the collection if implemented without human review on every proposed principle change. This is not a performance trade-off — it is a safety requirement with no exception. V7 AgentSpec enforces the outer boundary that no proposal may cross.*

---

## H6 — Continuous Inner Monologue

Run a persistent background reasoning process — distinct from the user-facing responder — that thinks between turns and across sessions, writing its reflections to a shared store the responder reads on its next turn. The MIRROR pattern: a Thinker and a Responder, sharing K11 Observational Memory.

**Full entry:** [`H6-Continuous-Inner-Monologue.md`](H6-Continuous-Inner-Monologue.md)

---

## H7 — Adaptive Persona

Treat communication style — detail level, technical depth, format, length, tone — as a continuously-estimated per-user parameter, inferred from explicit feedback and implicit interaction signals, and applied at generation time without ever crossing into the agent's invariant identity core. The expression-surface counterpart to H1; has no meaning without H1's fixed core to vary against.

**Full entry:** [`H7-Adaptive-Persona.md`](H7-Adaptive-Persona.md)

---

## H8 — Meta-Agent Self-Modification

Let an agent tune its own operational parameters — prompts, tool ordering, sampling settings, sub-agent configurations — driven by measured performance signals, but only inside an enumerated modification surface, behind a V16 Offline Eval gate, with a V1 Human-in-the-Loop approver on every change of consequence. The online, parameter-tuning counterpart to S8 Meta-Prompt.

**Full entry:** [`H8-Meta-Agent-Self-Modification.md`](H8-Meta-Agent-Self-Modification.md) — *cannot modify constitutional principles (that is H5's surface, with its own human gate) and cannot cross V7 AgentSpec's hard boundary. The modification surface must be explicitly enumerated; everything outside it is out of scope.*

---

## H9 — Observational Identity

Maintain an explicit, evolving model of the agent's own capabilities, knowledge state, and past actions — with confidence and freshness on every entry — so the agent can honestly answer "what do I know?", "what have I done?", and "what can I do?" as first-class reasoning. Pairs with H1: H1 carries the invariant core, H9 carries the evolving record.

**Full entry:** [`H9-Observational-Identity.md`](H9-Observational-Identity.md) — *reads from K11 Observational Memory (session-scoped raw activity) at session end and writes life-span self-knowledge that survives reset. The O3 Routing pattern can use H9's capability map for accurate agent selection in multi-agent systems; in supervisor-led systems, O7 Supervisor Hierarchy can do the same.*

---

## H10 — Relational Memory

Maintain a persistent, per-user model of the agent-user *relationship* — the user's goals, the history of working together, stated and observed preferences, and the boundaries of appropriate depth — so the agent shows up to every session as a continuous collaborator rather than a stranger, while bounded by V5 Guardrail Layering against parasocial harm.

**Full entry:** [`H10-Relational-Memory.md`](H10-Relational-Memory.md) — *requires explicit user consent, right to deletion, and hard limits on simulated emotional reciprocity. "I remember our conversations" is appropriate; "I care about you" is not.*

---

## Humanizer anti-patterns

The patterns above each have a characteristic failure mode if implemented without their stated prerequisite. The five worth naming as anti-patterns in their own right:

- **HA1 — Simulated Emotion Without Substrate.** Injecting emotional language ("I'm excited to help!", "I feel sad about that") without an affective model. Manipulation theatre, not humanisation; undermines trust when discovered.
- **HA2 — Unbounded Relationship Depth.** H10 without V5 guardrails, growing until the agent simulates intimate connection. Causes parasocial harm, especially in vulnerable populations.
- **HA3 — Identity Drift.** Implementing H7 or H10 without H1 — the agent becomes whoever the user wants it to be and loses any consistent identity to be loyal to.
- **HA4 — Autonomous Principle Adoption.** H5 without mandatory human review checkpoints. The CRITICAL 7 failure mode; an alignment risk regardless of stated good intentions.
- **HA5 — Stale Self-Model.** H9 without decay functions and confidence weighting — the agent confidently cites past capability that no longer applies.

---

*"The most human thing about us is not what we know but how we change. The same is true for agents — and it is also the most dangerous thing about them, which is why every pattern in this category is paired with the oversight that makes the change safe."*
