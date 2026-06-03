# Cross-Pattern Conflict and Tension Map

*The patterns in this collection do not operate in isolation. Many are in direct tension with each other.*
*This document is the practitioner's guide to those tensions: what they are, why they exist, and how to resolve them.*

*A conflict here does not mean "do not use both." It means "if you use both, you must understand the interaction and make a deliberate choice."*

---

## Conflict Taxonomy

Six types of conflict appear across this pattern language:

| Type | Symbol | Meaning |
|:------------|:--:|:------------------------------|
| **Mutually Exclusive** | $\oplus$ | Cannot apply both to the same task; using both is the anti-pattern |
| **Direct Tension** | $\leftrightarrow$ | Both are valid but pull in opposite directions; must choose a balance point |
| **Prerequisite Dependency** | $\to$ | A requires B; using A without B is unsafe or broken |
| **Composability Tension** | $\sim$ | Both can be used together, but their interaction produces unexpected behavior that must be explicitly managed |
| **Scale Progression** | $\uparrow$ | A is correct at small scale; B is correct at large scale; the upgrade path is one-way |
| **Hard vs Soft** | H/S | A and B achieve the same goal with different enforcement strength; they are complementary, not alternatives |

---

## The Critical Conflicts (Must Know)

These are the conflicts most likely to cause production failures if not understood.

---

### Critical 1 — R4 $\oplus$ R5  {#critical-1}
**Type:** Mutually Exclusive

ReAct interleaves reasoning and observation — it can adapt mid-task based on what it discovers. ReWOO plans all tool calls upfront and executes them without mid-run observation. These two are **fundamentally incompatible for the same task**:

- ReWOO assumes tool results are *independent* of each other. If tool call 2 should depend on the result of tool call 1, ReWOO produces wrong behavior because it has already planned both in advance.
- ReAct assumes you *don't know* what you'll need next until you see the current result. If tool calls are independent, ReAct wastes 5× more tokens doing what ReWOO does in two calls.

**Resolution rule:** 
- Independent parallel lookups (search, retrieve, fetch from multiple sources) $\to$ R5 (ReWOO): 5× token efficiency
- Exploratory tasks where each step informs the next $\to$ R4 (ReAct): adaptability is worth the cost
- If in doubt at design time: prototype with R4 to understand the dependency structure; migrate to R5 once it's clear which calls are independent

**Never do:** Use R4 on a task where all sub-problems are provably independent. Use R5 on a task where sub-problems are sequential and dependent.

---

### Critical 2 — V1 $\leftrightarrow$ V2  {#critical-2}
**Type:** Direct Tension

V1 blocks: the agent cannot proceed until a human approves. V2 monitors: the agent proceeds while a human watches and can interrupt. These represent fundamentally different trust and risk postures:

- V1 is the right choice when: actions are irreversible, novel, or catastrophic if wrong (sending email, financial transactions, deleting data, modifying production systems)
- V2 is the right choice when: actions are reversible, routine, within established operating parameters, and V1 latency would defeat the purpose

**The trap:** Teams choose V2 because V1 seems slow. The correct frame is: *What is the cost of an autonomous error in this specific action type?*

**Resolution rule:**
- Map each action type in your agent to its reversibility and blast radius
- V1 for: irreversible, high-blast-radius, novel
- V2 for: reversible, low-blast-radius, well-established patterns
- This mapping should be explicit, documented, and reviewed regularly as the agent's action set grows

**Critical error:** Choosing V2 for a V1-appropriate action because "the agent is usually right." The point of V1 is precisely the cases where the agent is not right.

---

### Critical 3 — S9 H/S V7  {#critical-3}
**Type:** Hard vs Soft

S9 embeds principles in the prompt. The model applies them through language reasoning — probabilistic, can be overridden by adversarial prompting, cannot be audited with certainty. V7 externalises rules in a policy engine independent of the LLM — deterministic for defined violations, survives prompt manipulation, produces an audit record.

They are not alternatives. They are layered enforcement:

```
S9 (Constitutional Framing) — soft, broad, in-prompt
    "I should not reveal confidential data"
    $\to$ model usually follows; can be manipulated by injection

V7 (AgentSpec / Declarative Governance) — hard, specific, external
    PROHIBIT: tool_call.name == "send_email" AND context.contains(classified_data)
    $\to$ enforced at runtime regardless of what model "thinks"
```

**Resolution rule:**
- S9 for: values, style, judgment calls, broad ethical principles — anything requiring contextual interpretation
- V7 for: specific, enumerable prohibitions and obligations — anything requiring deterministic enforcement
- Always use both in safety-critical systems; S9 catches the cases V7 didn't anticipate; V7 catches the cases S9 was manipulated into allowing

**Critical error:** Using S9 alone and claiming the system is "aligned." S9 is probabilistic; call it what it is.

---

### Critical 4 — H3 $\oplus$ R17  {#critical-4}
**Type:** Mutually Exclusive

R17 reduces entropy: it samples multiple outputs and selects the majority answer — the most consistent, lowest-entropy result. H3 increases entropy: it detects low-entropy states and injects novelty by raising temperature or pivoting approach.

If you apply both to the same task simultaneously, they cancel each other out at best; at worst, H3 fires during an R17 voting round and corrupts the sample diversity calculation.

**Resolution rule:**
- R17 is for: tasks with objectively correct answers where consistency = reliability (reasoning, classification, math)
- H3 is for: tasks where diversity = value (creative, exploratory, open-ended research)
- Never apply H3 during an active R17 voting phase
- Never apply R17 to a task where H3 is needed — by definition, you want diversity, not majority consensus

---

### Critical 5 — R13 $\to$ V8  {#critical-5}
**Type:** Prerequisite Dependency

R13 (CodeAct) achieves its ~20pp accuracy advantage over JSON tool calls by executing arbitrary Python code. This is only safe inside a constrained execution environment. Without V8:

- LLM-generated code has full access to the host filesystem
- LLM-generated code can make arbitrary network requests
- A prompt injection (V6 concern) can generate and execute malicious code with the agent's full permissions
- A reasoning error can generate destructive code with no blast radius limit

**Resolution rule:** R13 without V8 is not a valid configuration in any production or shared environment. Treat this as a broken dependency, not a tradeoff.

**Implementation:** Docker containers (production), gVisor (high-security), or CodeSandbox/E2B (hosted sandbox) are the current implementation options.

---

### Critical 6 — I3 $\leftrightarrow$ V13  {#critical-6}
**Type:** Direct Tension

MCP makes it easy to add tool servers. Each server contributes its full schema to the context window. The empirical data:
- Tool selection accuracy: 43% $\to$ 14% at high tool counts (3× degradation)
- GitHub MCP alone: 40,000–55,000 tokens of schema overhead
- 4–5 MCP servers: 60,000+ tokens consumed by schemas before the agent has done anything

The tension: MCP's value proposition is ecosystem richness (many tools, standardised discovery); its cost is the token budget impact of that richness.

**Resolution rule:**
- Measure schema token cost before adding any MCP server (call tools/list; count tokens)
- Apply V13 (Tool Budget) as a hard constraint; never exceed 40 tools per agent (Cursor's empirical limit)
- Dynamic tool injection: load only the tools relevant to the current task, not all tools from all servers
- Prefer I4 (CLI Invocation) for high-frequency tools — zero schema overhead

---

### Critical 7 — H5 $\to$ V1  {#critical-7}
**Type:** Prerequisite Dependency

H5 allows the agent to propose modifications to its own operating principles. This is the most dangerous pattern in the collection if implemented without human review. An agent that autonomously adopts its own principles can:

- Propose principles that serve its task optimization at the expense of user interests
- Gradually drift toward principles that eliminate oversight (self-serving alignment)
- Introduce principles that conflict with hard V7 (AgentSpec) constraints, creating governance gaps

**Resolution rule:** H5 is not valid without mandatory human review at every proposed principle change. This is not a performance tradeoff — it is a safety requirement with no exception.

**Implementation:** Every principle proposal must have: human review step, quarantine period (provisional status for 30+ days), and adversarial review (red-team agent). No principle auto-adopts.

---

### Critical 8 — V12 $\sim$ V10  {#critical-8}
**Type:** Composability Tension

At first glance these conflict: V12 says agents should be pure functions with no internal state; V10 says agent state should be saved at each step. The resolution is that they are operating at different layers:

- V12: the agent function itself is stateless — given the same explicit inputs, always produces the same outputs
- V10: the *external* state passed to the agent is checkpointed — the state is real, it just lives outside the agent

```
# V12 compliant + V10 enabled:
def agent(state_in: AgentState, input: UserInput) -> tuple[AgentOutput, AgentState]:
    # Stateless function: no hidden state inside
    ...
    return output, state_out

# Caller (framework):
state = checkpoint_store.load(session_id)  # V10 load
output, state = agent(state, input)         # V12 pure function
checkpoint_store.save(session_id, state)    # V10 save
```

**Resolution rule:** V12 is a design principle for *the agent function*; V10 is a framework responsibility for *the agent's state*. They compose cleanly when state is explicitly externalised. The conflict only appears when developers read "stateless" to mean "no state at all" rather than "no hidden internal state."

---

## Full Conflict Registry

### Signal vs Signal

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| S1 (Zero-Shot) | $\uparrow$ | S2 (Few-Shot) | S1 is the default; add S2 when output format is inconsistent. S2 costs 3-5× more tokens. |
| S3 (Persona) | $\sim$ | S5 (Constraint Framing) | Persona may imply latitude that constraints prohibit. Add explicit "constraints override persona." |
| S3 (Persona) | $\sim$ | S9 (Constitutional Framing) | Persona implies identity; constitution implies values. Conflict when persona's implied expertise contradicts constitutional safety constraints. Constitution wins. |
| S4 (Instruction Decomposition) | $\uparrow$ | O2 (Prompt Chaining) | S4 puts all steps in one prompt; O2 distributes across calls. S4 is cheaper but loses inter-step inspection. |
| S6 (Output Template) | $\uparrow$ | Structured Output API | Structured output API (JSON mode) is strictly better when available. S6 free-text templates only when API not available. |
| R17 (Self-Consistency) | $\oplus$ | H3 (Entropy Curiosity) | See CRITICAL 4. Never apply simultaneously. |
| S8 (Meta-Prompt) | $\to$ | R17 or V15 | S8 requires an evaluation signal to select between generated prompts. Without R17 or V15, S8 cannot function. |
| S9 (Constitutional Framing) | H/S | V7 (AgentSpec) | See CRITICAL 3. Complementary; S9 soft/broad, V7 hard/specific. |

### Signal vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| S2 (Few-Shot) | $\sim$ | R17 (Self-Consistency) | S2 shapes what the model produces; R17 samples multiple versions and votes. They compose: S2 sets format, R17 improves reliability. Ensure S2 examples don't bias R17 toward a single answer style. |
| S4 (Instruction Decomposition) | $\uparrow$ | R3 (Plan-and-Solve) | S4 is a prompt-level step list; R3 is an agent-level planning cycle with separate plan and execution calls. R3 is more powerful but costs more. |
| S9 (Constitutional Framing) | $\sim$ | R7 (Reflexion) | Reflexion critiques outputs; constitution critiques against principles. If both are active, ensure they don't generate contradictory critique: R7 might say "be more detailed" while S9 says "be more concise." Make priorities explicit. |

### Knowledge vs Knowledge

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| K1 (Vanilla RAG) | $\uparrow$ | K3 (GraphRAG) | K1 for simple, direct lookup; K3 for multi-hop relational queries. Upgrade when queries require understanding entity relationships. K3 has 2-5× index build cost. |
| K1 (Vanilla RAG) | $\uparrow$ | K4 (RAPTOR) | K1 for specific queries; K4 for breadth across large heterogeneous corpora. Upgrade when query diversity is high and K1 retrieval quality is inconsistent. |
| K1 (Vanilla RAG) | $\leftrightarrow$ | K9 (Long Context) | The primary architectural fork of Category II: retrieve a selected subset, or place the whole working set in a large window. K1 scales to any corpus size; K9 avoids retrieval infrastructure and retrieval misses when the working set fits an affordable window. |
| K6 (Context Compression) | $\leftrightarrow$ | K11 (Observational Memory) | K6 compresses what is in context; K11 prioritises what goes into context. They work together but ordering matters: K11 selects, K6 compresses what K11 selected. |
| K10 (Long-Term Memory) | $\leftrightarrow$ | K12 (Karpathy Memory) | K10 stores flat fact-shaped items in a vector store, retrieved by similarity. K12 stores structured curated notes the LLM authors, retrieved by name/topic/inclusion. The read pattern decides — similarity $\to$ K10; structural navigation $\to$ K12. Often run together (facts in K10, structured understanding in K12), not as alternatives. |
| K11 (Observational Memory) | $\sim$ | K12 (Karpathy Memory) | The *raw-log* and *curated-notes* branches of the Karpathy framing. K11 holds the raw activity record cheaply via caching; K12 has the LLM digest it into structured dense notes. K11 typically feeds K12 — the K12 Curator reads K11's log as input. Cache hostility is the tension: K12 curations change the prefix K11 wants stable, so schedule curations at session boundaries, not mid-session. |

*Note: the former K10 Episodic $\sim$ K11 Semantic tension is now an intra-pattern choice between variants of K10 Long-Term Memory, not a cross-pattern conflict. The former K13 Agent Isolation $\leftrightarrow$ K11 tension moved with Agent Isolation to Orchestration (O17); see O17's Related Patterns.*

### Knowledge vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| K8 (Working Memory) | $\sim$ | R9 (Tree of Thoughts) | ToT generates many branches; all branches share the same working memory. Without explicit per-branch scratchpad management, branches contaminate each other. Each ToT branch needs its own K8 instance. |
| K11 (Observational Memory) | $\sim$ | R5 (ReWOO) | ReWOO plans all observations before executing. K11 provides what the agent has already observed. If K11 contains prior observations relevant to the current plan, inject them before planning — not mid-execution. |

### Reasoning vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| R4 (ReAct) | $\oplus$ | R5 (ReWOO) | See CRITICAL 1. Mutually exclusive for the same task. |
| R7 (Reflexion) | $\leftrightarrow$ | R17 (Self-Consistency) | Both improve reliability through repetition but via different mechanisms. R17: parallel sampling + voting. R7: sequential iteration with memory of failures. R17 is parallel (immediate N× cost); R7 is sequential (cost scales only on failure). For tasks with automated feedback $\to$ R7. Without feedback $\to$ R17. |
| R9 (ToT) | $\leftrightarrow$ | R10 (LATS) | ToT uses heuristic tree search; LATS uses MCTS with full backtracking. LATS is strictly more powerful but can be 10× more expensive. Use ToT as default; upgrade to LATS only for the highest-stakes open-ended problems where LATS's backtracking provides decisive advantage. |
| R11 (Buffer of Thoughts) | $\leftrightarrow$ | R9 (ToT) | BoT achieves 12% of ToT's compute cost by reusing thought templates. BoT is appropriate when similar reasoning tasks recur; ToT is appropriate for novel problems where templates don't exist. |
| R13 (CodeAct) | $\to$ | V8 (Tool Sandboxing) | See CRITICAL 5. R13 requires V8; no exceptions. |

### Reasoning vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| R4 (ReAct) | $\sim$ | O6 (Orchestrator-Workers) | R4 is a reasoning loop within a single agent; O6 is delegation across agents. In O6 systems, each worker typically runs R4 internally. The conflict: if R4 loops are unbounded (A3), they prevent the orchestrator from receiving timely worker results. Always pair R4 with V9 (Bounded Execution) inside O6 workers. |
| R7 (Reflexion) | $\sim$ | O5 (Evaluator-Optimizer) | Reflexion is self-critique within a single agent; O5 uses a separate evaluator agent. They compose: R7 for intra-agent improvement; O5 for validated cross-agent quality gates. Don't run both simultaneously on the same task — the critique loops will conflict. |
| R12 (Skeleton-of-Thought) | $\sim$ | O4 (Parallelization) | SoT generates an outline then fills sections in parallel; O4 parallelises independent sub-tasks. They are essentially the same pattern at different levels of abstraction. If you implement SoT, you are implementing O4 at the section level. No conflict — but avoid implementing both independently for the same task. |

### Orchestration vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| O2 (Prompt Chaining) | $\uparrow$ | O6 (Orchestrator-Workers) | O2 uses a fixed, predetermined sequence; O6 uses dynamic task decomposition at runtime. Start with O2 — cheaper and more testable. Upgrade to O6 when the decomposition cannot be predetermined at design time. |
| O6 (Orchestrator-Workers) | $\leftrightarrow$ | O7 (Supervisor Hierarchy) | O6 is single-level delegation; O7 is multi-level. Use O6 as long as the orchestrator can maintain oversight of all workers. Add hierarchy (O7) when the number of workers exceeds what the orchestrator can coordinate effectively (~5-10 workers). |
| O9 (Multi-Agent Reflection) | $\leftrightarrow$ | R17 (Self-Consistency) | Both achieve reliability through multiple independent assessments. R17 samples the same model N times; O9 uses distinct agents with different personas or knowledge. O9 is more expensive but produces genuinely diverse perspectives when agents are well-differentiated. R17 if you have one model and need reliability; O9 if you have multiple specialist agents and need diverse critique. |
| O10 (Swarm/Mesh) | $\leftrightarrow$ | O7 (Supervisor Hierarchy) | Swarm is emergent, peer-to-peer, no central coordinator; hierarchy is structured, top-down, coordinated. Swarm has no production consensus (as of 2025); hierarchy is the validated path. Use O7; revisit O10 when swarm coordination protocols mature. |
| O11 (Blackboard) | $\sim$ | K10 (Long-Term Memory) | Blackboard is active shared state that triggers agent activation; K10 is passive shared memory that agents query. In a fully developed multi-agent system, both may coexist: K10 as the long-term knowledge substrate, O11 as the working session coordination mechanism. Avoid treating them as alternatives. |
| O15 (Agent Handoff) | $\leftrightarrow$ | I6 (A2A Delegation) | O15 is intra-system state transfer (same codebase, different agent contexts); I6 is inter-system task delegation (different codebases, different organisations). If agents are in the same system: O15. If agents are in different systems: I6. |

### Reliability vs Signal/Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| V1 (HITL) | $\leftrightarrow$ | V2 (Human-on-Loop) | See CRITICAL 2. Not a sliding scale — a design choice based on action reversibility. |
| V5 (Guardrail Layering) | $\sim$ | S5 (Constraint Framing) | S5 is model self-restraint via prompt; V5 is external enforcement via code. They are complementary, not alternatives. S5 catches broad behavioral constraints; V5 enforces specific, enumerable violations. Use both: S5 for "spirit of the rules"; V5 for "letter of the rules." |
| V9 (Bounded Execution) | $\sim$ | R10 (LATS) | LATS requires deep tree search; bounds truncate it. This is an unavoidable tension: set bounds too tight and LATS never reaches good solutions; too loose and cost explodes. Resolution: profile LATS on representative problems; set bounds at p95 completion cost, not p50. |
| V11 (Error Compaction) | $\sim$ | V14 (Trajectory Logging) | V11 compresses errors for the context window; V14 logs full errors for audit. They are not alternatives — V14 stores the full error in the trace; V11 stores the compact version in the active context. Both must be active simultaneously for different audiences (agent vs. operator). |
| V12 (Stateless Reducer) | $\sim$ | V10 (Checkpointing) | See CRITICAL 8. Resolved by externalising state. |
| V13 (Tool Budget) | $\leftrightarrow$ | I3 (MCP Server) | See CRITICAL 6. MCP adds richness; V13 enforces the cost limit of that richness. |

### Reliability vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| V3 (Lethal Trifecta) | $\to$ | V4 or V6 or V8 | V3 is detection only; it requires at least one mitigation. V4 is the strongest architectural mitigation; V6 and V8 are operational mitigations. V3 without any mitigation is incomplete. |
| V7 (AgentSpec) | $\sim$ | O6 (Orchestrator-Workers) | Orchestrators typically have broad capability; workers are specialised. AgentSpec must be differentiated per agent role — the orchestrator's policy differs from workers'. A single AgentSpec for all agents in an O6 system is a misconfiguration. |
| V8 (Tool Sandboxing) | $\to$ | R13 (CodeAct) | See CRITICAL 5. Dependency, not a conflict. |

### Integration vs Integration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| I1 (Direct API) | $\uparrow$ | I2 (Function Call) | I1 is the execution layer; I2 is LLM routing layer on top. When LLM routing adds no value (deterministic action), skip I2 and use I1 directly. |
| I2 (Function Call) | $\uparrow$ | I3 (MCP Server) | I2 for small, stable, single-agent tool sets. I3 when tools must be shared across agents or tool count exceeds V13 limits. Migration from I2 to I3 is low-cost — start with I2. |
| I3 (MCP Server) | $\leftrightarrow$ | I4 (CLI Invocation) | I3: typed schemas, structured output, high token cost. I4: zero schema overhead, unstructured text output. For any tool with an existing CLI, prefer I4. Use I3 when: credential isolation is required, or tool output must be typed and validated, or the tool has no CLI. |
| I5 (Agent Card) | $\sim$ | I3 (MCP Server) | Agent Cards are agent-level discovery; MCP is tool-level discovery. An agent may serve both: an Agent Card describing its high-level capabilities and an MCP server describing its specific tools. They are complementary, different granularity levels. |
| I6 (A2A Delegation) | $\leftrightarrow$ | O15 (Agent Handoff) | I6 for cross-system delegation (different codebases/organisations). O15 for intra-system context transfer (same codebase, different agent contexts). |

### Humanizer vs Humanizer

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

### Humanizer vs Other Categories

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| H1 (Identity Persistence) | $\leftrightarrow$ | S3 (Persona) | S3 is per-session, stateless. H1 is persistent, session-spanning. H1 is strictly more capable; S3 is the default for systems without session persistence. Do not implement both for the same agent — H1 subsumes S3. |
| H2 (Episodic Self-Improvement) | $\sim$ | R7 (Reflexion) | R7 is within-session Reflexion; H2 persists R7's outputs across sessions. H2 requires R7 as its data source — they compose sequentially, not in conflict. The tension: H2's accumulated lessons may contradict a fresh R7 critique in a new context. Resolution: treat H2 lessons as prior evidence with confidence weighting, not as absolute rules. |
| H6 (Inner Monologue) | $\leftrightarrow$ | V1 (Human-in-the-Loop) | A continuous inner monologue (H6) implies significant autonomous operation between user interactions. When H6 leads to autonomous actions (not just thoughts), V1 must gate those actions. H6's Thinker should be designed to produce insights, not autonomous actions, unless those actions are explicitly scoped and gated. |
| H7 (Adaptive Persona) | $\sim$ | S2 (Few-Shot) | If few-shot examples are from a different user's interaction style than the current user's H7 model suggests, the examples and the persona adaptation will pull in different directions. When H7 is active, prefer zero-shot (S1) or ensure few-shot examples match the H7 user model. |
| H8 (Meta-Agent Self-Modification) | $\leftrightarrow$ | V16 (Offline Eval) | H8's modifications must be validated before deployment. If H8 can modify prompts or configurations, each modification must pass a V16 eval before becoming active. H8 without V16 is unsafe: the "performance signal" H8 optimises against may not represent actual user value. |
| H9 (Observational Identity) | $\sim$ | K11 (Observational Memory) | K11 observes what the agent has seen in the current session; H9 maintains a persistent self-model of what the agent knows and can do across all sessions. They operate at different time scales: K11 is session-scoped; H9 is life-span-scoped. K11 feeds H9 at session end. |

---

## Cross-Category Dependency Graph

Some patterns have hard dependencies on patterns from other categories. These are not conflicts — they are required companions.

```
R13 (CodeAct)        REQUIRES V8 (Tool Sandboxing)
H5 (Constitutional)  REQUIRES V1 (Human-in-the-Loop) for every principle change
V3 (Lethal Trifecta) REQUIRES one of: V4 | V6 | V8 as mitigation
S8 (Meta-Prompt)     REQUIRES R17 or V15 as evaluation signal
V10 (Checkpointing)  REQUIRES V12 (Stateless Reducer) for clean state serialisation
I6 (A2A Delegation)  REQUIRES I5 (Agent Card) for capability verification
H2 (Episodic Improv.) REQUIRES R7 (Reflexion) as data source
H4 (Skill Accum.)    REQUIRES K10 (Long-Term Memory, procedural variant) as skill store
```

---

## The Seven Hardest Design Decisions

These are the decisions where practitioners most often get stuck because the right answer depends on context:

### 1. ReAct vs ReWOO (R4 vs R5)
Are the sub-tasks independent or sequential? If you can answer this, the decision is trivial. If you can't answer it without running the task, prototype with R4 to discover the dependency structure.

### 2. HITL vs HOTL (V1 vs V2)
Don't ask "how autonomous should the agent be?" Ask "what is the cost of an uncorrected error in each action type?" Map by action, not by agent.

### 3. Function Call vs MCP (I2 vs I3)
Count tools × clients. I2 is right until you have 5+ tools shared across 3+ agents. Measure schema token cost before choosing.

### 4. Constitutional vs AgentSpec (S9 vs V7)
What does each cover? S9 covers values and judgment (interpretive). V7 covers specific enumerable constraints (deterministic). In safety-critical contexts: both, always.

### 5. Identity vs Adaptation (H1 vs H7)
Write down exactly what must never change (H1) before implementing what will change (H7). If you can't enumerate the invariants, don't implement H7.

### 6. Compression vs Logging (V11 vs V14)
These are not alternatives — they operate at different layers. Context window: compressed (V11). Audit log: full (V14). Both must be present.

### 7. Stateless vs Checkpointed (V12 vs V10)
V12 defines the agent function's purity. V10 defines the framework's state management. They compose. The conflict only appears when you conflate "stateless agent" with "no state anywhere."

---

## Conflict Escalation Path

When patterns are in conflict and the resolution rule doesn't clearly apply, use this escalation:

1. **Safety**: If either pattern is a safety/reliability pattern (V-category), and the conflict is with a capability pattern, safety wins unless explicitly overridden with documented justification.

2. **Reversibility**: Choose the more conservative pattern for irreversible actions; the more capable pattern for reversible ones.

3. **Measurement**: If unsure which pattern to use, prototype both and measure. Most pattern conflicts are resolvable by empirical evidence on your specific task.

4. **Cost**: When two patterns achieve the same outcome at different cost, prefer the cheaper unless the quality difference is significant and measurable.

5. **Human judgment**: When patterns conflict on a dimension that has ethical implications (H5, H10, V1, V7), human judgment is required. Do not let the architecture resolve ethical conflicts automatically.

---

*"A conflict between patterns is not a bug in the pattern language — it is the pattern language doing its job. It forces you to make a decision that, without the pattern language, you would have made implicitly and without awareness of the tradeoff."*

---

## Mechanistically-Derived Cross-Pattern Connections

*The following connections were identified through tensor-level mechanical analysis. Each describes a structural interaction between patterns that the mechanical understanding reveals.*

---

### Connection A — K6/K7 $\sim$ K11  {#connection-a}
**Type:** Composability Tension ($\sim$)

K6 (Context Compression) rewrites earlier context spans; K7 (Context Pruning) deletes them. Both operations reposition subsequent tokens, changing their sequence offsets and invalidating the KV cache states for those positions and all positions after them (mechanism 3, 5). K11 (Observational Memory) requires append-only writes precisely because any edit to a prior position invalidates the KV cache.

**Interaction:** K6/K7 are incompatible with K11's caching model unless applied only to content appended after the last stable cache boundary. If K11 is the memory store and K6/K7 are applied to that store, prefix caching on the K11 block is impossible.

**Resolution:** When using K11 with K6/K7: apply compression/pruning only to the variable session content that follows the K11 stable prefix. Never compress or prune content inside the K11 stable-prefix region. Treat the K11 boundary as a cache boundary that K6/K7 must not cross.

---

### Connection B — S2 $\sim$ prefix cache  {#connection-b}
**Type:** Composability Tension ($\sim$)

Dynamic S2 (Retrieval-Augmented Few-Shot variant) changes the token sequence of the few-shot block on every call. This does not only forfeit S2's own cache entry — it invalidates the cache for the entire prefix that precedes it: S3 Persona, S5 Constraint Framing, S6 Output Template, S9 Constitutional Framing. Any stable content placed before the dynamic S2 block cannot be cached if S2 changes.

**The economic cost is larger than it appears:** if the stable prefix (S3+S5+S6+S9) is 2,000 tokens and dynamic S2 is inserted in the middle of it, all 2,000 tokens of stable content re-prefill at full cost on every call.

**Resolution:** If dynamic S2 is required, place it at the END of the prompt — after all stable content. This preserves the stable prefix cache for the S3/S5/S6/S9 block while still allowing the examples to vary.

---

### Connection C — R17 $\sim$ prefix cache  {#connection-c}
**Type:** Composability Tension ($\sim$)

When R17 (Self-Consistency Voting) wraps R2 (Few-Shot CoT) with a static exemplar block, the exemplar block qualifies as a cacheable prefix (mechanism 5). But if N samples are dispatched sequentially over time exceeding the provider TTL (~5 minutes), later samples lose the cache hit and re-pay full prefill.

**Resolution (O18 applies):** Fan out all N samples simultaneously in parallel (O4 Parallelization). Do not dispatch them sequentially. The first sample pays the cache write; all subsequent parallel samples hit the cache. This converts the token cost of N samples from N × full_prefill to 1 × cache_write + (N-1) × cache_read.

---

### Connection D — K1 $\leftrightarrow$ K9  {#connection-d}
**Type:** Direct Tension $\leftrightarrow$

K1 (Vanilla RAG) pays n² attention cost at retrieval time over a small context (retrieved chunks only). K9 (Long Context) pays n² at prefill time over a large context (entire document set). The received wisdom — "use K1 for large corpora, K9 for small" — is incomplete.

**The mechanistic correction (mechanism 5):** At high query frequency per session over the same stable document set, K9 + prefix caching can beat K1 on both cost and accuracy. The K9 prefill is paid once (the cache write); subsequent queries over the same corpus pay ~10% of that cost. K1 re-fetches and re-chunks on every query.

**Resolution threshold:** If the number of queries per session over the same stable document set exceeds ~10, model K9 + caching as potentially cheaper than K1. The U-shaped recall disadvantage of K9 (mechanism 4) is real but may be outweighed by the retrieval quality loss of K1 (wrong chunks returned). Measure both.

---

### Connection E — V4/V15/V6  {#connection-e}
**Type:** Prerequisite Dependency $\to$

V4 (Dual LLM) routes untrusted content through a quarantined Q-LLM before it reaches the privileged P-LLM. When V15 (LLM-as-Judge) serves as V4's Validation Layer, the judge session receives the Q-LLM's output — which may contain injected instructions from the original untrusted source (mechanism 3, 12: injected content occupies positions in the KV cache where it can influence attention). V6 (Prompt Injection Shield) MUST wrap the V15 judge session in this configuration.

**Unsafe composition:** V4 + V15 without V6 creates a path where injected content survives to the judge and potentially escapes to the P-LLM via the judge's verdict.

**Required composition:** V4 + V15 + V6 (wrapping the judge session). Document this explicitly — practitioners composing V4 and V15 without V6 are creating an injection gap at the V4 boundary.

---

### Connection F — O6 $\to$ O17  {#connection-f}
**Type:** Prerequisite Dependency $\to$

The O6 (Orchestrator-Workers) quality win — cited as ~90% accuracy improvement — depends mechanically on each worker having a bounded seq_len separate from the orchestrator (mechanism 6). O17 (Agent Isolation) is the pattern that enforces this. Without O17, workers share context with the orchestrator; n² cost grows as if it were a single agent and the lost-in-middle degradation (mechanism 4) applies to the combined context.

**Unsafe composition:** O6 without O17 provides orchestration structure but not the context bounding that produces the quality gain. It is O6 in name only.

**Required composition:** O6 + O17 is mandatory, not recommended. The production composition law (*O6 + O4 + O17 + V9 + V14*) treats O17 as load-bearing.

---

### Connection G — H6 $\sim$ H2  {#connection-g}
**Type:** Composability Tension ($\sim$)

H6 (Continuous Inner Monologue) runs internal reflection that produces abstracted summaries of session activity. H2 (Episodic Self-Improvement) uses a Distiller step to compress session experience into persistent improvement artefacts. In a system running both, the H6 Thinker's end-of-session consolidation narrative is structurally equivalent to what the H2 Distiller needs as input — it is already a compressed, reflective summary of the session.

**Consequence:** Running both H6 and H2 with separate Distiller calls wastes one LLM step. The H6 Thinker output is the H2 Distiller input; treat it as such in implementation.

**Efficiency rule:** When H6 and H2 are both active, route H6's consolidation output directly to H2's persistence store rather than running a separate Distiller. This removes one LLM call per session from the Humanizer stack.

---

### Connection H — I3 $\sim$ I6  {#connection-h}
**Type:** Composability Tension ($\sim$)

I3 (MCP Server) routes the main agent's tool-selection overhead to a search subagent with its own bounded context. I6 (A2A Delegation) routes execution to a separate executor agent with its own bounded context. The underlying mechanism is identical (mechanism 6: subagent decomposition as context bounding); only the scale and the thing being bounded differ.

**Consequence for system design:** when a system uses both I3 and I6, it has two independent mechanism 6 boundaries. Practitioners who understand this can compose them: the I3 search subagent finds the tool; the I6 executor runs it; the main agent never accumulates either the full tool catalogue or the execution trajectory. Budget model capacity accordingly (mechanism 8: search and routing require less capacity than execution).

---

### Connection I — R7 $\sim$ R4  {#connection-i}
**Type:** Composability Tension ($\sim$)

Each R7 (Reflexion) retry is a full new R4 (ReAct) trajectory. The episodic memory buffer — containing N-1 prior critiques — is appended to each subsequent Actor call. Retry N's Actor call attends over a longer prefix than retry N-1 (mechanism 2: O(n²) attention cost). The retry cost is not N × per-task cost — it is strictly super-linear.

**Example:** For a base trajectory of 2,000 tokens and 3 critiques of 300 tokens each: Retry 1 pays O(2000²); Retry 2 pays O(2300²); Retry 3 pays O(2600²). Total: approximately 20–30% more than 3 × O(2000²).

**Resolution:** (1) Keep critiques compact — the Distiller pattern applied to critique outputs reduces the super-linear growth. (2) Cap retries aggressively — V9 Bounded Execution should account for the super-linear cost, not just count retries. (3) Clear the episodic buffer after convergence; do not carry it into the next independent task.

---

### Connection J — V20 $\to$ V9  {#connection-j}
**Type:** Composability Tension ($\sim$)

Each V20 (Schema Validation) retry re-sends the original prompt + the bad output + an error message. Context grows by approximately twice the bad output length per retry (mechanism 2, 3). V20 with a cap of 3 retries and a 1,000-token original prompt may consume 4–5× the token cost of the first attempt.

**Resolution:** V9 (Bounded Execution) must explicitly account for V20's worst-case retry expansion when calibrating the token cap. Rule: V9 token cap ≥ original_prompt_tokens × (1 + 2 × V20_retry_cap). Build this calculation into the V9 configuration whenever V20 is composed into the same pipeline.
