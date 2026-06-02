# GO4 Taxonomy — Draft v0.2

*A pattern language for AI engineering, structured analogously to the Gang of Four.*
*Updated after deep research sweep including arXiv papers, HN community discussions, developer practitioner blogs, and empirical studies.*

---

## The Seven Categories

The original GoF had three categories: Creational, Structural, Behavioural. AI engineering patterns span more distinct concerns:

| Category | Governs | Analogy to GoF |
|---|---|---|
| **I. Signal** | How you shape instructions, personas, and examples | Creational — what gets built from what |
| **II. Knowledge** | What information and memory the model has access to | Structural — how things are assembled and connected |
| **III. Reasoning** | How a model structures its thinking process | Behavioural (individual) |
| **IV. Orchestration** | How agents coordinate, delegate, and interoperate | Behavioural (collective) |
| **V. Reliability** | Safety, cost, governance, observability | Cross-cutting / NFR |
| **VI. Integration** | How agents connect to tools, services, and each other | Infrastructure / Connective tissue |
| **VII. Humanizers** | How agents develop continuity, identity, and adaptive evolution | Emergent / Longitudinal |

---

## Category I — Signal Patterns

*How you shape the instruction, persona, and examples given to the model.*
*These are the "prompt engineering" layer — framed as design decisions with known forces and tradeoffs.*

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| S1 | **Zero-Shot** | Direct Instruction | Task with no examples; rely on model priors | Simple, well-defined tasks where model knowledge is sufficient |
| S2 | **Few-Shot** | In-Context Learning | Provide examples to demonstrate desired format or behaviour | Format control, style matching, novel task types |
| S3 | **Persona / Role** | Role Prompting | Assign the model an identity to frame knowledge and tone | Expert framing, domain-specific tasks, tone alignment |
| S4 | **Instruction Decomposition** | Step Prompting | Break complex instruction into numbered sequential steps | Multi-step tasks with clear ordering |
| S5 | **Constraint Framing** | Negative Prompting | Define what model must NOT do as prominently as what it should | Safety-sensitive, compliance, avoiding known failure modes |
| S6 | **Output Template** | Template Filling | Provide skeleton of expected output for model to complete | Structured data extraction, consistent formatting |
| S8 | **Meta-Prompt** | Auto-Prompting | Model generates or refines its own prompt | Self-optimising workflows; experimental; cost intensive |
| S9 | **Constitutional Framing** | Constitutional AI | Embed a set of principles the model applies to self-critique | Alignment enforcement, safety-critical contexts |

*Former S7 Self-Consistency Voting relocated to **R17** (Reasoning, band III-C). Former S10 Chain of Density folded into **K6 Context Compression** as a named Variant. S7 and S10 are intentional gaps in the Signal numbering.*

**Key distinctions:**
- S1–S4 are present in virtually every production system
- S5 is critically underused: "define what not to do" has asymmetric value in safety contexts
- S8 Meta-Prompt costs significantly more than S1–S6 / S9; measure before using
- S9 (Constitutional Framing) applies at both training time (Anthropic's CAI) and inference time (agent runtime constitution)

---

## Category II — Knowledge Patterns

*How you construct and curate what the model knows during a task.*
*The shift from "prompt engineering" to "context engineering" is the shift from Category I to Category II thinking.*

*Reviewed and rebuilt: 15 draft patterns reduced to 11 by the fundamentality test (a pattern that decomposes into other patterns plus an adaptor is not fundamental). Each pattern has a full 13-field GoF page at `patterns/Kn-*.md`.*

### II-A — Retrieval

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K1 | **Vanilla RAG** | Basic Retrieval, Naive RAG | Retrieve relevant chunks at query time; inject into context | Simple Q&A, static corpora, well-defined document sets |
| K2 | **Query Transformation** | Query Rewriting; HyDE, multi-query, step-back are *variants* | Transform the raw query into derived queries that retrieve better | Query/document mismatch, ambiguous or conversational or compound queries |
| K3 | **GraphRAG** | Graph Retrieval | Index the corpus as an entity-relationship graph | Multi-hop relational queries; global summary needs |
| K4 | **RAPTOR** | Hierarchical RAG | Index the corpus as a recursive summary tree | Query diversity; corpora with hierarchical structure |
| K5 | **Adaptive RAG** | Self-Reflective RAG; Self-RAG, Corrective RAG are *variants* | Wrap retrieval in an evaluate-and-control loop | Mixed query streams; factuality-critical; possibly stale corpora |

### II-B — Context-window management

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K6 | **Context Compression** | Summarisation, Compaction | Summarise context that no longer fits (lossy) | Long-running agents; context overflow prevention |
| K7 | **Context Pruning** | Selective Recall | Remove spent or irrelevant spans without summarising (lossless) | Spent tool outputs; finished sub-task context |
| K8 | **Working Memory / Scratchpad** | In-Context Scratch | An explicit in-context space the model writes to itself | Multi-step reasoning; intermediate state management |
| K9 | **Long Context** | Context Stuffing, No-RAG | Hold the whole working set in a large window instead of retrieving | Working set fits an affordable window; retrieval not justified |

### II-C — Memory

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K10 | **Long-Term Memory** | Persistent Memory; episodic, semantic, procedural are *variants* | An external store of flat fact-shaped items, retrieved by similarity | Agents expected to remember preferences, decisions, isolated facts across sessions |
| K11 | **Observational Memory** | Agent-Centric Memory, Seen-First Memory | The raw activity record as primary memory; cache-friendly (the Karpathy framing's raw-log branch) | Long-running agentic sessions; provider supports prompt caching; cost is the lever |
| K12 | **Karpathy Memory** | Curated Memory, Self-Edited Memory, Agent-Authored Wiki | The LLM curates structured, dense notes the agent reads (the Karpathy framing's curated-notes branch) | Read-frequency dominates write-frequency; structure worth preserving; editability matters |
| K13 | **Retrieval Bundle** | Agent Operating Context, Typed Memory Contract | Before writing retrieval code, specify the exact operational context bundle a workflow type always needs — by field, source, data shape, freshness, and authorization — then build assembly to deliver it reliably | Recurring agent workflows; rediscovery cost measurable (>30% of token budget on context assembly); multiple data shapes required |

**Key distinctions:**
- II-A (K1–K5, K13) is about retrieval strategy and specification; K13 is the design-time prerequisite for K1–K5 and the memory patterns. Selection depends on corpus structure and query type.
- II-B (K6–K9) is about the live context window; K9 Long Context is the architectural alternative to retrieval itself.
- II-C (K10–K12) is about persistence and curation: K10 cross-session flat facts, K11 in-session raw log, K12 LLM-curated structured notes. K11 and K12 are the *raw-log* and *curated-notes* branches of the Karpathy framing of agent memory; they typically run together.
- K1 vs K9 (retrieve vs long window) is the primary architectural decision of the category; benchmark both on your actual query workload at your corpus size — see the Decision Criteria in the K1 and K9 pattern entries.
- Four data shapes require different retrieval primitives: fuzzy prose → K1/K2; structured documents → K4; governed tabular data → semantic layer; relational knowledge → K3. K13 is where the shape-to-primitive mapping is specified.
- Reduced from 15: HyDE → variant of K2; Self-RAG + CRAG → merged as K5; episodic/semantic/procedural → merged as K10; Agent Isolation → moved to Orchestration (O17).

---

## Category III — Reasoning Patterns

*How a model or agent structures its thinking process to solve a problem.*
*These govern the shape of thought, not just its content. Each represents a different computational cost / quality / adaptability tradeoff.*

| # | Pattern Name | Also Known As | LLM Calls | Adaptation | Best For |
|---|---|---|---|---|---|
| R1 | **Zero-Shot CoT** | "Think step by step" | 1 | None | Quick reasoning improvement; no examples needed |
| R2 | **Few-Shot CoT** | Exemplar CoT | 1 | None | Consistent reasoning format with examples |
| R3 | **Plan-and-Solve** | Explicit Planning | 2 | Medium (replan) | Well-defined multi-step workflows; inspectable before execution |
| R4 | **ReAct** | Reason+Act Loop | N per-step | High | Exploratory tasks; open-ended; unpredictable paths |
| R5 | **ReWOO** | Reasoning Without Observation | 2 total | None | Independent parallel lookups; 5× token efficiency over ReAct |
| R6 | **Self-Ask** | Decomposition | 1+N follow-ups | Low | Compositional multi-hop questions |
| R7 | **Reflexion** | Verbal Reinforcement | N × retries | Meta-level | Clear pass/fail criteria; automated success measurement |
| R8 | **Self-Refine** | Generate-Critique-Refine | N iterations | Same model | General quality improvement; no separate judge needed |
| R9 | **Tree of Thoughts** | ToT | N (branching) | Via search | Hard open-ended problems; when path is unknown |
| R10 | **Language Agent Tree Search** | LATS / MCTS | N (tree search) | Full backtrack | Highest-quality reasoning; very expensive |
| R11 | **Buffer of Thoughts** | BoT | 1+template retrieval | Via templates | 12% cost of ToT/GoT; reusable thought-templates at meta-level |
| R12 | **Skeleton-of-Thought** | SoT | 1 outline + N parallel | None | Parallel generation; reduces latency; structured long-form output |
| R13 | **CodeAct** | Executable Code Actions | N (with execution) | High (self-debug) | Multi-tool tasks; 20pp higher accuracy than JSON tool calls; self-debugging |
| R14 | **Program of Thoughts** | PoT | 1+execution | None | Numerical/mathematical tasks; delegates computation to executor |
| R16 | **Talker-Reasoner** | System 1/System 2 | Dual async | Full | Real-time + deliberative combined; latency-sensitive with quality needs |

**Key decision guide:**
```
Need token efficiency? → ReWOO (R5) — 5× over ReAct
Need mid-run adaptation? → ReAct (R4)
Need guaranteed quality with retries? → Reflexion (R7)
Need search over solution space? → ToT (R9) or LATS (R10)
Need to call multiple tools efficiently? → CodeAct (R13)
Need parallel generation? → Skeleton-of-Thought (R12)
Need math/computation? → Program of Thoughts (R14)
```

**The "Something-of-Thought" family (Towards Data Science taxonomy):**
CoT → ToT → GoT → BoT → SoT — each adds structure or efficiency to the reasoning chain.

---

## Category IV — Orchestration Patterns

*How multiple agents, workflows, and tools are coordinated to accomplish complex tasks.*
*This is the systems design layer. Patterns here are composable with Category III reasoning patterns.*

### IV-A: Workflow Patterns (deterministic, lower complexity)

| # | Pattern Name | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O1 | **Single Agent** | Autonomous Agent | One LLM + tools + system prompt handles full task | Low |
| O2 | **Prompt Chaining** | Pipeline / Sequential | Output of one LLM call feeds the next in fixed order | Low |
| O3 | **Routing** | Classifier-Dispatcher | Classify input → direct to specialised handler | Medium |
| O4 | **Parallelization** | Fan-out Fan-in | Simultaneous LLM calls; outputs aggregated | Medium |

### IV-B: Agentic Patterns (dynamic, higher complexity)

| # | Pattern Name | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O5 | **Evaluator-Optimizer** | Generator-Critic | Separate generator and judge agents; iterative improvement | Medium |
| O6 | **Orchestrator-Workers** | Hub-and-Spoke | Central LLM dynamically delegates to worker LLMs | High |
| O7 | **Supervisor Hierarchy** | Hierarchical Agents | Multi-level tree: supervisor → sub-orchestrators → workers | High |
| O8 | **Loop Agent** | Agentic Loop | Sequence of agents repeats until termination condition met | Medium |
| O9 | **Multi-Agent Reflection** | Ensemble Critique | Multiple agents independently critique the same output | High |
| O10 | **Swarm / Mesh** | Peer-to-Peer Agents | Agents coordinate without central coordinator; emergent | Very High |

### IV-C: Specialised Coordination Patterns

| # | Pattern Name | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O11 | **Blackboard System** | Shared Memory Board | Central shared memory; agents read/write; dynamic agent activation | High |
| O12 | **Debate / Deliberation** | Devil's Advocate | Multiple agents argue opposing positions before synthesis | High |
| O13 | **Negotiation** | Multi-Party Consensus | Agents with different objectives negotiate mutually acceptable outcome | Very High |
| O14 | **Single Information Environment** | SIE | Agents own specific datasets; coordinator routes queries | Medium |
| O15 | **Agent Handoff** | Context Transfer | Structured state transfer between agents mid-interaction | Medium |
| O16 | **Hybrid Control Flow** | Primitive Stack | Stack multiple loop primitives (ReAct + plan-execute + retry) | Varies |
| O17 | **Agent Isolation** | Clean Context, Context Quarantine | Delegate a sub-task to a sub-agent with a fresh, isolated context | Context hygiene; parallel sub-tasks; preventing context pollution |
| O18 | **Cache-Warmed Worker Pool** | Primed Agent Pool, Prefix-Warm Fan-Out | Before dispatching parallel workers, establish a stable shared context as a provider-cached prefix so all workers hit the KV cache rather than independently re-paying prefill cost | Fan-out of N≥3 workers; shared prefix >1024 tokens; all workers dispatched within provider TTL (~5 min) |

**Key distinctions:**
- O1–O4 are deterministic; highly testable; prefer when task allows
- O2 (Prompt Chaining) vs O6 (Orchestrator-Workers): O2 is fixed decomposition; O6 is dynamic — use O2 when you can
- The scaffold taxonomy finding: 11/13 production agents use O16 (multiple stacked primitives), not a single pattern
- O11 (Blackboard): "achieves SOTA reasoning with lower token costs than static pipelines" — underused
- O10 (Swarm): experimental; no production consensus; most systems use O7 instead
- O4 (Parallelization) is the **most commonly missed optimisation** in production systems
- O18 (Cache-Warmed Worker Pool) is the **most commonly missed cost optimisation** in fan-out systems — identical shared prefixes across parallel workers should always be cached

**Composition law**: Most production systems are O6 + O4 + {R4 inside each worker} + {O17 for context isolation} + {O18 for cache efficiency on shared worker context}.

---

## Category V — Reliability Patterns

*How AI systems stay safe, bounded, cost-controlled, auditable, and recoverable.*
*These are cross-cutting — apply inside and across all other categories.*

### V-A: Safety and Security

| # | Pattern Name | Also Known As | Intent |
|---|---|---|---|
| V1 | **Human-in-the-Loop** | Approval Gate | Insert human checkpoints at defined decision boundaries |
| V2 | **Human-on-the-Loop** | Monitoring Mode | Agent acts autonomously; human monitors and can intervene |
| V3 | **Rule of Two** | Lethal Trifecta Prevention | Flag agents that simultaneously access private data + untrusted content + external comms |
| V4 | **Dual LLM** | Privilege Separation | Privileged LLM (clean data only) + Quarantined LLM (untrusted data, no tools) |
| V5 | **Guardrail Layering** | Multi-Point Safety | Safety checks at: user input, tool calls, tool responses, final output |
| V6 | **Prompt Injection Shield** | Input Sanitisation | Constrain action space; prevent adversarial inputs hijacking goals |
| V7 | **AgentSpec / Declarative Governance** | Policy-Driven Agent | External declarative rule specification enforced at runtime; deontic tokens |
| V8 | **Tool Sandboxing** | Isolated Execution | Isolated tool execution environment; constrain filesystem, network, clock |

### V-B: Operational Reliability

| # | Pattern Name | Also Known As | Intent |
|---|---|---|---|
| V9 | **Bounded Execution** | Circuit Breaker | Cap iterations, tool calls, cost, and time; prevent runaway loops |
| V10 | **Checkpointing** | State Snapshot | Save agent state at each step; enable rollback on failure |
| V11 | **Error Compaction** | Error Context | Represent errors efficiently in context window (not raw stack traces) |
| V12 | **Stateless Reducer** | Pure Agent | Agent as pure function of inputs → outputs; no hidden state |
| V13 | **Tool Budget** | Tool Scope Limit | Hard limit on number of tools per agent (<15 for most models; Cursor: 40 max) |
| V19 | **Fallback / Graceful Degradation** | Circuit-Breaker Fallback, Failover, Degraded-Mode Path | Declare a cheaper degraded path (smaller model, cache, rule, human escalation) for every primary-path failure mode |
| V20 | **Output / Schema Validation** | Validate-and-Repair, Reask Loop, Structured-Output Retry | Validate every model output against a declared schema; re-prompt with the validation error until conformance or retry budget is exhausted |

### V-C: Observability and Evaluation

| # | Pattern Name | Also Known As | Intent |
|---|---|---|---|
| V14 | **Trajectory Logging** | Agent Trace | Full trace of decisions, tool calls, intermediate outputs; OTel-compliant |
| V15 | **LLM-as-Judge** | Inferential Evaluation | Second LLM call evaluates output of first against defined rubrics |
| V16 | **Offline Eval** | Regression Testing | Validate against known scenarios and reference outputs before production |
| V17 | **Online Eval** | Production Monitoring | Monitor live traces for quality regressions, safety drift without ground truth |
| V18 | **Agent Simulation** | Sandbox Testing | Test end-to-end agent reasoning under realistic conditions before production |

**The Tool Overload quantification (critical empirical finding):**
- Selection accuracy: 43% → 14% at high tool counts (3× degradation)
- AI accuracy: 87% → 54% with context overload
- Hard limits: Cursor enforces 40 tools max
- 4–5 MCP servers = 60,000+ context tokens on schemas alone
- V13 (Tool Budget) should be a first-class constraint in every agent design

**The Lethal Trifecta (Simon Willison):**
Any agent combining all three creates catastrophic security risk: (1) private data access + (2) untrusted content exposure + (3) external communication. V3 is the detection pattern; V4, V6, V8 are mitigations.

---

## Category VI — Integration Patterns

*How agents connect to tools, services, and each other.*
*Added as a new category based on research depth in 2025-26 on MCP, APIs, and interoperability.*

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| I1 | **Direct API Call** | Deterministic Integration | Synchronous HTTP to external service; no LLM reasoning | Sub-10ms ops; consistency-critical; financial/compliance |
| I2 | **Function/Tool Call** | Schema-Wrapped API | LLM decides which function to invoke; code executes it | 1-5 tools; app-specific routing; simple agents |
| I3 | **MCP Server** | Model Context Protocol | Standardised tool discovery; credential isolation; multi-client | 5+ tools shared across agents/clients; reusable integrations |
| I4 | **CLI Invocation** | Shell Tool | Agent uses existing CLI tools directly | Tools that already have CLIs (git, docker, gh, cloud CLIs) |
| I5 | **Agent Card** | Agent Manifest | Self-describing `/.well-known/agent.json`; capability declaration for discovery | Multi-agent systems; A2A interoperability |
| I6 | **A2A Delegation** | Agent-to-Agent Protocol | Structured cross-agent task delegation; status updates; result return | Multi-vendor, multi-platform agent collaboration |

**Decision guide (from practitioner research):**
```
Does LLM reasoning determine the action?
  NO → I1 (Direct API Call)
  YES:
    1–5 tools, single agent → I2 (Function Call)
    5–20 tools → I2 + I3 hybrid
    20+ tools → I3 with gateway
    CLI exists? → I4 first (zero context overhead)
    Multiple agents need to coordinate? → I5 + I6
```

**Production cost reality:** GitHub MCP alone = 40,000–55,000 tokens per request. Every I3 server costs tokens. Design tool budgets before choosing integration patterns.

**Community consensus on frameworks:**
LangChain backlash is real and documented. 80+ package dependencies, "death by abstraction". Modern teams prefer: direct API + Instructor for structured output + custom 80–500 line loops. MCP disrupted LangChain's value proposition as of late 2024.

---

## Category VII — Humanizer Patterns

*How AI systems develop continuity, curiosity, self-improvement, and adaptive identity across time.*
*These are the "what the system becomes" layer — patterns that make agents evolve rather than merely execute.*
*The defining question of this category: does the agent get better at being itself over time?*

| # | Pattern Name | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| H1 | **Identity Persistence** | Genesis State, Core Self Injection | Inject stable invariant self-representation into every context | Any agent that runs across multiple sessions; long-term user relationships |
| H2 | **Episodic Self-Improvement** | Cross-Session Reflexion | Persist verbal self-critiques across sessions so agent improves without weight updates | Long-running agents performing recurring task types |
| H3 | **Entropy-Driven Curiosity** | Deadlock Break, Novelty Seeking | Auto-increase temperature or inject stimuli when agent detects its own stagnation | Creative agents; reasoning loops that get stuck; exploration tasks |
| H4 | **Procedural Skill Accumulation** | Skill Library, LEGO Memory | Distill successful task trajectories into reusable parameterised skill procedures | Agents with recurring task types; knowledge transfer across sessions |
| H5 | **Constitutional Self-Alignment** | Principle Evolution, Adaptive Ethics | Allow operating principles to evolve through experience, with human checkpoints | Long-running agents in evolving domains; alignment that must adapt |
| H6 | **Continuous Inner Monologue** | MIRROR, Thinker Agent | Background reasoning process separate from user-facing responses | Persistent assistant agents; monitoring agents; pre-computation |
| H7 | **Adaptive Persona** | User-Calibrated Style | Communication style adapts based on observed user preferences and history | Personal assistants; educational agents; multi-user systems |
| H8 | **Meta-Agent Self-Modification** | Self-Improving Agent | Agent modifies own operational parameters based on performance data | Large-scale production agents with abundant evaluation data; NOT for safety-critical |
| H9 | **Observational Identity** | Self-Knowledge Model | Explicit model of own capabilities, knowledge state, and past actions | Multi-session agents; capability routing; accurate self-representation |
| H10 | **Relational Memory** | User Model Persistence | Persistent model of the agent-user relationship including goals, history, tone | Personal assistant agents; coaching; any long-term user relationship |

**The Humanizer sequence (how to build up from nothing):**
```
Session 1: H1 (Identity Persistence) — establish who the agent is
After first failures: H2 (Episodic Self-Improvement) — learn from mistakes  
After first successes: H4 (Procedural Skill Accumulation) — remember what worked
As user model grows: H7 (Adaptive Persona) — communicate better
When loops stall: H3 (Entropy-Driven Curiosity) — break deadlocks autonomously
Advanced: H6 (Inner Monologue) — think between interactions
Advanced: H9 (Observational Identity) — accurate self-knowledge
With governance: H5 (Constitutional Self-Alignment) — evolving principles with oversight
```

**Key distinctions:**
- H1 is a prerequisite for all other Humanizer patterns — identity must be stable before it can evolve
- H2 and H4 are complementary: H2 learns from failure, H4 learns from success
- H5 is dangerous without mandatory human checkpoints — never implement autonomously
- H8 is the most powerful and most dangerous; scope modification surface carefully
- H10 requires explicit user consent and right-to-deletion
- All Humanizer patterns require K11 (Observational Memory) or K10 (Long-Term Memory) as infrastructure

**Humanizer Anti-Patterns (summary):**
- HA1 — Simulated Emotion: injecting emotional language without genuine affective model (manipulation theater)
- HA2 — Unbounded Relationship Depth: H10 without ethical guardrails → parasocial harm
- HA3 — Identity Drift: implementing H7/H10 without H1 → agent becomes whoever user wants it to be
- HA4 — Autonomous Principle Adoption: H5 without mandatory human review → alignment risk
- HA5 — Stale Self-Model: H9 without decay functions → overconfident outdated self-assessment

---

## Anti-Pattern Registry (Extended)

| # | Anti-Pattern | Description | Costs | Better Alternative |
|---|---|---|---|---|
| A1 | **God Prompt** | All instructions in one massive prompt | Attention dilution; maintenance nightmare | Decompose with O2/O6 |
| A2 | **Over-Agentification** | Agentic loops when deterministic code suffices | Cost; latency; brittleness | O2 (Prompt Chaining) or just write code |
| A3 | **Uncontrolled Recursion** | Reflection/planning loops with no exit condition | Runaway cost; stuck agents | V9 (Bounded Execution) |
| A4 | **Agent Sprawl** | Proliferating agents without ownership or governance | Inconsistency; undebuggable | V14 (Trajectory Logging) + V1 (H-in-the-L) |
| A5 | **Output-Only Guardrails** | Safety checks only on final output | Intermediate failures propagate | V5 (Guardrail Layering) at all 4 points |
| A6 | **Vibe-Checking as Testing** | Subjective assessment replacing eval frameworks | No regression detection | V15 (LLM-as-Judge) + V16 (Offline Eval) |
| A7 | **Context Hoarding** | Never pruning context; dumping everything in | Token waste; attention degradation; cost | K6/K7 (Compress/Prune) or O17 (Agent Isolation) |
| A8 | **Synchronous Everything** | Running independent sub-tasks sequentially | Unnecessary latency | O4 (Parallelization) |
| A9 | **Stateful Reducer** | Hidden agent state not reflected in business state | Bugs; replay failure; debugging hell | V12 (Stateless Reducer) + V10 (Checkpoint) |
| A10 | **Silent Failure** | Agent fails quietly; no error surfaced | Data loss; cascading failures | V1 + V14 + V10 |
| A11 | **Framework Lock-in** | Choosing LangChain/heavy framework first | Abstraction ceiling; debugging difficulty; cost opacity | Own your control flow (12-Factor Factor 8) |
| A12 | **Tool Proliferation** | Adding tools without tool budget management | Context overflow; selection accuracy collapse | V13 (Tool Budget) + I4 (CLI first) |
| A13 | **Pilot Simplification** | Clean data/sandbox in pilot; assume production is similar | 88% production failure rate | Data realism in pilots; governance from day 1 |
| A14 | **Trust Handoff** | Agent trusts instructions from other agents without verification | Prompt injection cascading | V3 (Rule of Two) + V4 (Dual LLM) |
| A15 | **Untraced Agent** | No observability; no audit trail | Debugging takes hours not minutes; no compliance | V14 (Trajectory Logging) from day 1 |

---

## Pattern Composition Examples

### Example 1: Standard Production Coding Agent (Claude Code, Devin)
`S3 (Persona) + S4 (Instruction Decomposition) + K1 (Vanilla RAG) + K8 (Working Memory) + R4 (ReAct) + O6 (Orchestrator-Workers) + O4 (Parallelization) + V1 (Human-in-the-Loop) + V9 (Bounded Execution) + V14 (Trajectory Logging) + I2/I3 (Function/MCP)`

### Example 2: Research Agent (Karpathy AutoResearch model)
`S4 (Instruction Decomposition) + K10 (Long-Term Memory) + R4 (ReAct) + O4 (Parallelization) + O8 (Loop Agent) + V9 (Bounded Execution) + V14 (Trajectory Logging)`

### Example 3: Safety-Critical Enterprise Agent
`S3 (Persona) + S9 (Constitutional Framing) + K1 (RAG) + R3 (Plan-and-Solve) + O6 (Orchestrator-Workers) + V1 (Human-in-the-Loop) + V3 (Rule of Two) + V4 (Dual LLM) + V5 (Guardrail Layering) + V7 (AgentSpec) + V8 (Tool Sandboxing) + V14 (Trajectory Logging) + I1 (Direct API for deterministic ops)`

### Example 4: Customer Support Router
`O3 (Routing) + O1 (Single Agent per route) + K1 (Vanilla RAG) + K11 (Observational Memory) + V1 (H-in-the-Loop for escalation) + V5 (Guardrail Layering) + V17 (Online Eval)`

### Example 5: Document Analysis Pipeline
`S2 (Few-Shot) + K6 (Context Compression) + O2 (Prompt Chaining) + O5 (Evaluator-Optimizer) + V5 (Guardrail Layering) + V16 (Offline Eval)`

### Example 6: Multi-Agent Research Network
`S3 (Persona per agent) + K10 (Long-Term Memory shared substrate) + R4 (ReAct per agent) + O7 (Supervisor Hierarchy) + O11 (Blackboard System) + I5 (Agent Card) + I6 (A2A Delegation) + V14 (OTel Trace)`

### Example 7: Long-Term Personal Research Assistant (Humanizer composition)
`H1 (Identity Persistence) + H2 (Episodic Self-Improvement) + H4 (Procedural Skill Accumulation) + H7 (Adaptive Persona) + H9 (Observational Identity) + H10 (Relational Memory) + K11 (Observational Memory) + R7 (Reflexion) + V1 (Human-in-the-Loop for H5 principle changes)`

### Example 8: Autonomous Creative Agent (Humanizer composition)
`H1 (Identity Persistence) + H3 (Entropy-Driven Curiosity) + H6 (Continuous Inner Monologue) + H7 (Adaptive Persona) + K10 (Long-Term Memory, episodic variant) + R4 (ReAct)`

### Example 9: Enterprise Process Automation Agent (Humanizer + Reliability)
`H2 (Episodic Self-Improvement) + H4 (Procedural Skill Accumulation) + H5 (Constitutional Self-Alignment, human-governed) + H9 (Observational Identity) + V1 (Human-in-the-Loop) + V7 (AgentSpec) + V14 (Trajectory Logging)`

---

## Decision Flowchart

### Primary Pattern Selection
```
Is the task solvable with a single LLM call + tools?
  YES → O1 (Single Agent) + appropriate Signal patterns → DONE
  NO:
    Does the task decompose into FIXED sequential steps?
      YES → O2 (Prompt Chaining)
      NO:
        Are there distinct input TYPES needing specialisation?
          YES → O3 (Routing)
          NO:
            Are sub-tasks INDEPENDENT (can run in parallel)?
              YES → O4 (Parallelization)
              NO → O6 (Orchestrator-Workers) + R4 (ReAct) inside workers

Does output quality matter AND can it be verified objectively?
  YES → Add O5 (Evaluator-Optimizer) or R7 (Reflexion)

Are there distinct specialised roles exceeding single context?
  YES → O7 (Supervisor Hierarchy)

Do agents need to share state across turns?
  YES → O11 (Blackboard) or K10 (Long-Term Memory shared substrate)
```

### Reasoning Pattern Selection
```
Token efficiency is critical → R5 (ReWOO): 5× reduction
Mid-run adaptation needed → R4 (ReAct)
Multi-tool task with self-debug → R13 (CodeAct)
Hard open-ended problem, quality trumps cost → R9 (ToT) or R10 (LATS)
Clear pass/fail criteria → R7 (Reflexion)
Math/numerical tasks → R14 (Program of Thoughts)
Parallel generation needed → R12 (Skeleton-of-Thought)
```

### Integration Pattern Selection
```
Does LLM reasoning decide the action?
  NO → I1 (Direct API)
  YES:
    1–5 tools, single agent → I2 (Function Call)
    CLI exists for this? → I4 first (zero overhead)
    5–20 tools shared across agents → I3 (MCP) + I2 hybrid
    20+ tools → I3 with gateway + dynamic tool discovery
    Agents from different vendors need to coordinate → I5 + I6
```

---

## Open Questions and Research Gaps

1. **Long-running agent session coherence**: No consensus on preventing context drift over hours/days
2. **Agent trust hierarchies**: How does Agent B verify that instructions from Agent A are legitimate? (V3 partially addresses; V4 for data; nothing for instruction provenance)
3. **Agent versioning and compatibility**: When a tool or sub-agent is updated, how do orchestrators handle the change?
4. **Cost-aware pattern selection**: Dynamic switching between R5 (ReWOO) and R4 (ReAct) based on runtime cost signals
5. **Cross-model composition**: No established patterns for mixing models from different providers in one pipeline
6. **O10 (Swarm) production viability**: No consensus on when peer-to-peer emerges, vs degrade to O7
7. **Multi-agent consistency**: Per-agent K10 stores create divergent memory; shared substrates are proposed but not standardised
8. **Prompt injection at orchestration layer**: V6 patterns are ad hoc; CaMeL is promising but not widely adopted
9. **Evaluation for long-horizon tasks**: V16/V17 evaluate per-interaction; no consensus on task-completion evals for multi-hour agent runs
10. **Should there be a Category 0**: "When not to use AI" — currently embedded in anti-patterns A2 and A13
11. **Humanizer identity continuity across model upgrades**: When the base model changes, does the agent's accumulated identity survive? No established pattern.
12. **Lesson library poisoning**: H2 (Episodic Self-Improvement) is vulnerable to adversarially-induced wrong lessons persisting across sessions — no defense pattern yet
13. **Constitutional evolution convergence**: Does H5 converge to a stable set of principles or continue drifting? What terminates the evolution?
14. **Authentic vs. simulated identity**: Philosophical question with practical implications — does H1 create genuine continuity or a performance of continuity? Matters for trust calibration.
15. **Cross-agent humanizer state**: If multiple agent instances run simultaneously, how do they share (or isolate) H1–H10 state without racing?

---

## Scaffold Architecture Dimensions (from empirical study, arXiv 2604.03515)

*Empirical finding: agents occupy positions on spectra, not discrete categories. 13 coding agents studied.*

**Five loop primitives (stackable):**
1. ReAct loop
2. Generate-test-repair
3. Plan-execute
4. Multi-attempt retry
5. Tree search (MCTS)

**The major architectural fault line:**
- **LLM-as-navigator** (8/13 agents): general tools; LLM decides navigation; simpler but less precise
- **Scaffold-understands-code** (5/13 agents): repository maps, AST indexing, knowledge graphs; more powerful but complex

**No consensus dimensions (active research frontier):**
- Context compaction strategy (7 different approaches found across 13 agents)
- State representation (flat list vs typed events vs immutable store)
- Safety mechanisms for interactive agents

---

## Cognitive Science Grounding

AI patterns increasingly map to classical cognitive science theories — this may be the right frame for understanding *why* they work:

| AI Pattern | Cognitive Theory | Source |
|---|---|---|
| O11 (Blackboard) | Global Workspace Theory (Baars) | Explicit in Theater of Mind paper |
| O10 (Swarm) | Society of Mind (Minsky) | Multi-specialised agents |
| R16 (Talker-Reasoner) | Dual-Process Theory (Kahneman) | Direct mapping: System 1/2 |
| K10 (Long-Term Memory) | Tulving / Baddeley memory taxonomy | Episodic, semantic, procedural variants |
| K11 (Observational Memory) | Extended Mind Thesis (Clark) | External tool as cognitive extension |
| H1 (Identity Persistence) | Autobiographical memory (Tulving 1985) | Genesis State in Theater of Mind |
| H2 (Episodic Self-Improvement) | Episodic memory consolidation | Reflexion extended cross-session |
| H3 (Entropy-Driven Curiosity) | Optimal Arousal / Noradrenergic system | Theater of Mind — entropy monitoring |
| H5 (Constitutional Self-Alignment) | Moral development (Kohlberg) | Constitutional AI extended to inference |
| H6 (Inner Monologue) | Vygotskian inner speech | MIRROR / Thinker architecture |
| H7 (Adaptive Persona) | Theory of Mind (Premack & Woodruff) | User model as cognitive representation |
| H10 (Relational Memory) | Parasocial relationship theory | HCI research; Skjuve et al. 2021 |

---

## Next Steps

- [x] Signal patterns complete (patterns/SIGNAL.md — S1–S10)
- [x] Knowledge patterns complete — full 13-field pages with Implementation Sketch + Decision Criteria, `patterns/K1–K12`; 15 draft patterns reduced to 11, then K12 Karpathy Memory added
- [x] Reasoning patterns complete (patterns/REASONING.md — R1–R16)
- [x] Orchestration patterns complete (patterns/ORCHESTRATION.md — O1–O16)
- [x] Humanizer patterns complete (patterns/HUMANIZERS.md — H1–H10)
- [x] Reliability patterns complete (patterns/RELIABILITY.md — V1–V20)
- [x] Integration patterns complete (patterns/INTEGRATION.md — I1–I6)
- [ ] Cross-pattern conflict and tension map (patterns/CONFLICTS.md)
- [ ] Build explicit relationship graph: what composes, what conflicts, what requires what
- [ ] Add code examples (Python + TypeScript) for key patterns
- [ ] Define formal "forces" for each pattern (pressures that make it the right choice)
- [ ] Consider POSA (Pattern-Oriented Software Architecture) format as alternative to GoF for non-OOP patterns
- [ ] Workshop "Category 0: When Not to Use AI" — currently only implicit in anti-patterns
- [ ] Map each pattern to SDLC phase (some patterns belong to specific development phases)
- [ ] Add: empirical evidence table (which patterns have quantified results vs. qualitative only)
