# GO4 — AI Engineering Design Patterns

### 94 patterns for building LLM systems that actually work in production — with the mechanical explanation of why each one works.

---

## 📖 Get the Book

**[⬇ Download GO4.pdf — 1,163 pages, free](https://github.com/jlldavies/go4-llm-design-patterns/raw/main/GO4.pdf)**

**[📖 Browse online](https://jlldavies.github.io/go4-llm-design-patterns)** — the full catalog, searchable, no download needed.

[![Deploy mdBook](https://github.com/jlldavies/go4-llm-design-patterns/actions/workflows/deploy-pages.yml/badge.svg)](https://jlldavies.github.io/go4-llm-design-patterns)

---

## 🧠 Ingest GO4 into your agent's memory

Beyond reading it, you can load the **whole catalog** into an agent. The
[`ingest/`](ingest/) folder is a generated, ingestible projection — one markdown
unit per pattern, mechanism, and decision guide, plus a machine manifest
(`ingest.json`) carrying the full relationship graph.

**Workflow:** clone the repo → point your personal memory system or coding agent at
the top-level `ingest/` folder → it absorbs all of it (patterns, the mechanical
foundation, the conflict graph, references). The labels are suggestions you can
relabel on ingest. See [`ingest/INGEST.md`](ingest/INGEST.md) for load recipes
(Karpathy wiki / agentmemory, Cognee, Obsidian, Claude Code).

---

## 🔌 Use GO4 from your own agent

**Install the skill (recommended)** — GO4 ships an Agent Skill that fires automatically
whenever Claude is designing or debugging an LLM system, and routes into the catalog
(category decision guide → pattern digests → conflict check) without loading all 94 patterns:

    git clone https://github.com/jlldavies/go4-llm-design-patterns.git ~/GO4
    mkdir -p ~/.claude/skills && ln -s ~/GO4/skills/go4 ~/.claude/skills/go4

The symlink means the skill tracks the catalog — `git pull` updates both. Works in any
project. See [`skills/go4/SKILL.md`](skills/go4/SKILL.md).

**Reference it** — add to your project's `AGENTS.md` / `CLAUDE.md`:
> For LLM/agent design decisions, consult GO4: clone `jlldavies/go4-llm-design-patterns`
> and read `ingest/INGEST.md` (decision guides + 94 pattern digests + the conflict graph).
> Pick a pattern via the matching `patterns/*-DECISION.md`; check `patterns/CONFLICTS.md`
> before combining patterns.

**Query it live** — run the MCP server (`mcp/README.md`): three pull-not-push tools
(`go4_find` / `go4_pattern` / `go4_decision`), no auto-fire, works in Claude Code, Cursor,
or any MCP client.

---

## Why this exists

**88% of AI agents never reach production** (Composio, 2025). The ones that fail aren't failing because the model isn't good enough — they're failing because the engineering around the model is wrong. Wrong retrieval pattern. Wrong context management. No bounds on the agent loop. Rediscovery eating 85% of compute. Token costs compounding quadratically on tasks engineers thought were linear.

The patterns exist. Practitioners at different companies are independently discovering that routing works better with a classifier in front of it, that long-running agents need checkpointing, that a second model judging the first catches errors the first cannot see. The techniques circulate as blog posts and GitHub repositories — each framed differently, none connected, none telling you *when* to use one, *why* it works, or *what it costs*.

This is the [Gang of Four](https://en.wikipedia.org/wiki/Design_Patterns) applied to AI engineering. 94 patterns across seven categories, each in full GoF format: Intent, Motivation, Applicability, Decision Criteria, Structure, Participants, Consequences, Implementation Sketch, Known Uses, Related Patterns.

**The differentiator:** every pattern derives its recommendation from how transformers actually work — attention cost scaling, KV cache structure, stochastic generation, prefix caching economics. Not folklore. Not "it worked in our tests." The reason.

---

## What this helps you do

**Reduce token costs** — the n² attention cost means longer contexts are not 2$\times$ more expensive than shorter ones; they're 4$\times$. Understanding this changes how you architect retrieval, memory, and multi-agent systems. Patterns like [K7 Context Pruning](patterns/K7-Context-Pruning.md), [K6 Context Compression](patterns/K6-Context-Compression.md), [O18 Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md), and the entire [Knowledge category](patterns/KNOWLEDGE.md) are explicitly about keeping contexts small and high-signal.

**Build agents that don't stall, loop, or hallucinate** — [V9 Bounded Execution](patterns/V9-Bounded-Execution.md), [V14 Trajectory Logging](patterns/V14-Trajectory-Logging.md), [V4 Dual LLM](patterns/V4-Dual-LLM.md), [V6 Prompt Injection Shield](patterns/V6-Prompt-Injection-Shield.md). Every production failure mode documented, with Decision Criteria that tell you when you're at risk.

**Choose the right retrieval architecture** — [K1 Vanilla RAG](patterns/K1-Vanilla-RAG.md) vs [K9 Long Context](patterns/K9-Long-Context.md) vs [K3 GraphRAG](patterns/K3-GraphRAG.md) vs [K4 RAPTOR](patterns/K4-RAPTOR.md) have different cost and quality profiles depending on corpus size, query type, and update frequency. The Decision Criteria tell you which threshold triggers which choice.

**Avoid the most expensive mistakes** — [CONFLICTS.md](patterns/CONFLICTS.md) documents 30+ cross-pattern tensions. R4 ReAct and R5 ReWOO are mutually exclusive for the same task. O6 Orchestrator-Workers without O17 Agent Isolation loses the quality win. V20 Schema Validation retry loops must be accounted for in V9 token caps or costs balloon silently.

**Use prefix caching correctly** — provider KV cache reuse (Anthropic: 5-minute TTL, ~10% of normal input cost on hits) changes the economics of multi-agent fan-out, few-shot prompting, and long-session agents. [O18 Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md) and [K11 Observational Memory](patterns/K11-Observational-Memory.md) both turn on getting this right.

---

## The Seven Categories

| Category | Patterns | What it governs |
|---|---|---|
| **I. Signal** | S1–S6, S8–S9 | Prompt shaping — zero-shot, few-shot, personas, constitutional framing |
| **II. Knowledge** | K1–K13 | Context engineering — RAG, retrieval, memory, compression |
| **III. Reasoning** | R1–R14, R16–R20 | Thinking structure — CoT, ReAct, Tree of Thoughts, self-consistency |
| **IV. Orchestration** | O1–O18 | Multi-agent coordination — pipelines, hierarchies, parallelisation |
| **V. Reliability** | V1–V20 | Production safety — bounds, logging, human oversight, evaluation |
| **VI. Integration** | I1–I6 | Tool use — function calling, MCP, A2A delegation |
| **VII. Humanizers** | H1–H10 | Cross-session continuity — identity, memory, self-improvement |

---

## Pattern Index

<details>
<summary><strong>Signal — shaping what you say to the model (S1–S6, S8–S9)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [S1 Zero-Shot](patterns/S1-Zero-Shot.md) | Direct Instruction | Simple, well-defined tasks within model priors |
| [S2 Few-Shot](patterns/S2-Few-Shot.md) | In-Context Learning | Format control, novel task types, style matching |
| [S3 Persona](patterns/S3-Persona.md) | Role Prompting | Domain expertise framing, tone alignment |
| [S4 Instruction Decomposition](patterns/S4-Instruction-Decomposition.md) | Step Prompting | Multi-step tasks where order matters |
| [S5 Constraint Framing](patterns/S5-Constraint-Framing.md) | Negative Prompting | Safety-sensitive tasks, known failure modes |
| [S6 Output Template](patterns/S6-Output-Template.md) | Template Filling | Structured data extraction, consistent formatting |
| [S8 Meta-Prompt](patterns/S8-Meta-Prompt.md) | Auto-Prompting | Self-optimising workflows, automated prompt tuning |
| [S9 Constitutional Framing](patterns/S9-Constitutional-Framing.md) | Constitutional AI | Alignment enforcement, principle-based self-critique |

</details>

<details>
<summary><strong>Knowledge — context engineering, RAG, memory (K1–K13)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [K1 Vanilla RAG](patterns/K1-Vanilla-RAG.md) | Naive RAG, Basic Retrieval | Q&A over external corpus; citations required |
| [K2 Query Transformation](patterns/K2-Query-Transformation.md) | HyDE, multi-query | Improve retrieval by rewriting the query first |
| [K3 GraphRAG](patterns/K3-GraphRAG.md) | Graph RAG | Multi-hop reasoning; entity relationships; global synthesis |
| [K4 RAPTOR](patterns/K4-RAPTOR.md) | Hierarchical RAG | Variable abstraction levels; document trees |
| [K5 Adaptive RAG](patterns/K5-Adaptive-RAG.md) | Self-RAG, Corrective RAG | Gate retrieval; self-critique retrieved results |
| [K6 Context Compression](patterns/K6-Context-Compression.md) | Summarisation, Chain of Density | Reduce context size; session history management |
| [K7 Context Pruning](patterns/K7-Context-Pruning.md) | Selective forgetting | Remove spent spans without lossy summarisation |
| [K8 Working Memory](patterns/K8-Working-Memory.md) | Scratchpad | Explicit in-context state the model writes to itself |
| [K9 Long Context](patterns/K9-Long-Context.md) | Full-context, needle-in-haystack | Whole corpus fits in window; repeated queries |
| [K10 Long-Term Memory](patterns/K10-Long-Term-Memory.md) | Persistent Memory, MemGPT | Cross-session fact storage; retrieved by similarity |
| [K11 Observational Memory](patterns/K11-Observational-Memory.md) | Agent-Centric Memory | Append-only activity log; exploits prefix caching |
| [K12 Karpathy Memory](patterns/K12-Karpathy-Memory.md) | Curated Memory, Agent Wiki | LLM curates dense structured notes; cheap reads |
| [K13 Retrieval Bundle](patterns/K13-Retrieval-Bundle.md) | Agent Operating Context | **Specify the exact context bundle a workflow always needs — solves the rediscovery problem** |

</details>

<details>
<summary><strong>Reasoning — chain-of-thought, agents, tool use (R1–R14, R16–R20)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [R1 Zero-Shot CoT](patterns/R1-Zero-Shot-CoT.md) | "Let's think step by step" | Elicit reasoning without examples |
| [R2 Few-Shot CoT](patterns/R2-Few-Shot-CoT.md) | Exemplar CoT | Show worked reasoning before the target question |
| [R3 Plan-and-Solve](patterns/R3-Plan-and-Solve.md) | Plan-then-Execute | Two-phase: explicit plan, then execute |
| [R4 ReAct](patterns/R4-ReAct.md) | Reason+Act, Agent Loop | Adaptive tool use; each action informs the next |
| [R5 ReWOO](patterns/R5-ReWOO.md) | Plan-then-Execute with tools | Independent tool calls; 5$\times$ token efficiency vs ReAct |
| [R6 Self-Ask](patterns/R6-Self-Ask.md) | Decompose-and-Answer | Multi-hop factual questions; sub-question chains |
| [R7 Reflexion](patterns/R7-Reflexion.md) | Verbal Reinforcement Learning | Verbal self-critique across retries |
| [R8 Self-Refine](patterns/R8-Self-Refine.md) | Generate-Critique-Refine | Iterative in-session quality improvement |
| [R9 Tree of Thoughts](patterns/R9-Tree-of-Thoughts.md) | ToT | BFS/DFS over reasoning states; complex planning |
| [R10 LATS](patterns/R10-LATS.md) | Language Agent Tree Search | MCTS + ReAct + Reflexion unified |
| [R11 Buffer of Thoughts](patterns/R11-Buffer-of-Thoughts.md) | Thought Templates | Reusable reasoning patterns distilled from prior runs |
| [R12 Skeleton-of-Thought](patterns/R12-Skeleton-of-Thought.md) | Parallel generation | Outline first; generate sections in parallel |
| [R13 CodeAct](patterns/R13-CodeAct.md) | Executable Code Actions | Python as action language; ~20pp accuracy gain over JSON tool calls |
| [R14 Program of Thoughts](patterns/R14-Program-of-Thoughts.md) | PoT | Delegate computation to a deterministic interpreter |
| [R16 Talker-Reasoner](patterns/R16-Talker-Reasoner.md) | System 1 / System 2 | Fast responder + slow deliberative reasoner in parallel |
| [R17 Self-Consistency](patterns/R17-Self-Consistency-Voting.md) | Majority Voting | Sample N reasoning paths; majority vote |
| [R18 Graph of Thoughts](patterns/R18-Graph-of-Thoughts.md) | GoT | DAG of reasoning operations; non-linear thought |
| [R19 Step-Back Prompting](patterns/R19-Step-Back-Prompting.md) | Abstraction Prompting | Abstract to principle before answering |
| [R20 Chain of Verification](patterns/R20-Chain-of-Verification.md) | CoVe | Generate answer; verify each claim independently |

</details>

<details>
<summary><strong>Orchestration — multi-agent systems, pipelines, coordination (O1–O18)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [O1 Single Agent](patterns/O1-Single-Agent.md) | Loop Agent | Baseline; one model, one loop |
| [O2 Prompt Chaining](patterns/O2-Prompt-Chaining.md) | Pipeline, Sequential | Fixed-sequence pipeline; output of step N feeds step N+1 |
| [O3 Routing](patterns/O3-Routing.md) | Classifier-then-Agent | Classify input; dispatch to specialist prompt or agent |
| [O4 Parallelization](patterns/O4-Parallelization.md) | Map-Reduce, Fan-Out | Independent sub-tasks run concurrently |
| [O5 Evaluator-Optimizer](patterns/O5-Evaluator-Optimizer.md) | Generator-Critic | Generator + judge in a quality improvement loop |
| [O6 Orchestrator-Workers](patterns/O6-Orchestrator-Workers.md) | Hub-and-Spoke, Manager-Workers | Dynamic task decomposition; workers run in isolation |
| [O7 Supervisor Hierarchy](patterns/O7-Supervisor-Hierarchy.md) | Hierarchical Multi-Agent | O6 applied recursively; supervisor of supervisors |
| [O8 Loop Agent](patterns/O8-Loop-Agent.md) | Periodic Agent, Cron Agent | Long-running workflows; periodic trigger |
| [O9 Multi-Agent Reflection](patterns/O9-Multi-Agent-Reflection.md) | Multi-Critic | Multiple independent reviewers on a single output |
| [O10 Swarm](patterns/O10-Swarm.md) | Emergent Multi-Agent | No central controller; shared environment coordination |
| [O11 Blackboard](patterns/O11-Blackboard.md) | Shared Workspace | Asynchronous shared state; agents post and consume |
| [O12 Debate and Deliberation](patterns/O12-Debate-Deliberation.md) | Socratic Agents | Two agents argue opposing positions; synthesiser integrates |
| [O13 Negotiation](patterns/O13-Negotiation.md) | Multi-Party Agent | Structured protocol for conflicting objectives |
| [O14 SIE](patterns/O14-SIE.md) | Self-Improving Executor | Agent edits its own tools |
| [O15 Agent Handoff](patterns/O15-Agent-Handoff.md) | Context Transfer | Structured state transfer between agents mid-task |
| [O16 Hybrid Control Flow](patterns/O16-Hybrid-Control-Flow.md) | Primitive Stack | Stack multiple loop primitives; most production agents are this |
| [O17 Agent Isolation](patterns/O17-Agent-Isolation.md) | Clean Context | Fresh isolated context per sub-task — **mandatory companion to O6** |
| [O18 Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md) | Primed Agent Pool | **Establish cacheable shared prefix before fan-out — ~85% cost reduction on shared context** |

</details>

<details>
<summary><strong>Reliability — safety, bounds, evaluation, production hardening (V1–V20)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [V1 Human-in-the-Loop](patterns/V1-Human-in-the-Loop.md) | HITL | Block on irreversible, novel, or high-blast-radius actions |
| [V2 Human-on-the-Loop](patterns/V2-Human-on-the-Loop.md) | HOTL | Monitor and interrupt; agent proceeds by default |
| [V3 Rule of Two](patterns/V3-Rule-of-Two.md) | Lethal Trifecta guard | Two independent confirmations for high-stakes actions |
| [V4 Dual LLM](patterns/V4-Dual-LLM.md) | Quarantined Agent | Quarantine Q-LLM handles untrusted content; privileged P-LLM acts |
| [V5 Guardrail Layering](patterns/V5-Guardrail-Layering.md) | Defense in Depth | Input / pre-call / post-call / output guards at all four boundaries |
| [V6 Prompt Injection Shield](patterns/V6-Prompt-Injection-Shield.md) | Injection Defense | Structural and positional defences against prompt injection |
| [V7 AgentSpec](patterns/V7-AgentSpec.md) | Policy as Code | Declarative, out-of-prompt, deterministic policy enforcement |
| [V8 Tool Sandboxing](patterns/V8-Tool-Sandboxing.md) | Code Sandbox | Confine LLM-generated code to a restricted execution environment |
| [V9 Bounded Execution](patterns/V9-Bounded-Execution.md) | Circuit Breaker | Hard caps on steps, cost, wall-time, depth — **required for every loop** |
| [V10 Checkpointing](patterns/V10-Checkpointing.md) | State Snapshot | Replayable agent state; recovery without restart |
| [V11 Error Compaction](patterns/V11-Error-Compaction.md) | Error Summarisation | Compress errors into compact structured signals |
| [V12 Stateless Reducer](patterns/V12-Stateless-Reducer.md) | Pure Function Agent | Reduce accumulated state to a deterministic, replayable summary |
| [V13 Tool Budget](patterns/V13-Tool-Budget.md) | Schema Budget | Limit active schema tokens — **every schema token costs n² attention** |
| [V14 Trajectory Logging](patterns/V14-Trajectory-Logging.md) | Agent Tracing, OTel | OTel-compatible trace of every call, action, and observation |
| [V15 LLM-as-Judge](patterns/V15-LLM-as-Judge.md) | AI Evaluator | Second model evaluates quality; catches errors the first cannot see |
| [V16 Offline Evaluation](patterns/V16-Offline-Eval.md) | Benchmark Evaluation | Batch evaluation against held-out test cases before deployment |
| [V17 Online Evaluation](patterns/V17-Online-Eval.md) | Production Monitoring | Real-time quality metrics in production |
| [V18 Agent Simulation](patterns/V18-Agent-Simulation.md) | Synthetic Testing | Simulated environment for pre-deployment stress testing |
| [V19 Fallback](patterns/V19-Fallback.md) | Graceful Degradation | Defined behaviour when primary path fails |
| [V20 Schema Validation](patterns/V20-Schema-Validation.md) | Structured Output | Enforce output contracts; re-ask on validation failure |

</details>

<details>
<summary><strong>Integration — tool calling, MCP, A2A (I1–I6)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [I1 Direct API](patterns/I1-Direct-API.md) | Deterministic Call | Call a deterministic service; no model decision needed |
| [I2 Function / Tool Call](patterns/I2-Function-Call.md) | Function Calling | Model selects and invokes a typed function |
| [I3 MCP Server](patterns/I3-MCP-Server.md) | Model Context Protocol | Standardised tool discovery; 5+ tools shared across agents |
| [I4 CLI Invocation](patterns/I4-CLI-Invocation.md) | Shell Tool | Wrap an existing CLI as an agent action |
| [I5 Agent Card](patterns/I5-Agent-Card.md) | Agent Discovery | Publish self-describing JSON for agent discovery |
| [I6 A2A Delegation](patterns/I6-A2A-Delegation.md) | Agent-to-Agent | Structured task delegation to another agent via A2A protocol |

</details>

<details>
<summary><strong>Humanizers — cross-session continuity, identity, adaptive memory (H1–H10)</strong></summary>

| Pattern | Also known as | When to use |
|---|---|---|
| [H1 Identity Persistence](patterns/H1-Identity-Persistence.md) | Genesis State | Stable persona loaded at position 0 every session |
| [H2 Episodic Self-Improvement](patterns/H2-Episodic-Self-Improvement.md) | Lesson Distillation | Distil session lessons into persistent improvement artefacts |
| [H3 Entropy-Driven Curiosity](patterns/H3-Entropy-Driven-Curiosity.md) | Curiosity Agent | Drive exploration by seeking to reduce uncertainty |
| [H4 Procedural Skill Accumulation](patterns/H4-Procedural-Skill-Accumulation.md) | Skill Library, Voyager | Generalise successful trajectories into reusable callable skills |
| [H5 Constitutional Self-Alignment](patterns/H5-Constitutional-Self-Alignment.md) | Self-Governed Agent | Agent proposes constitution updates; humans approve |
| [H6 Continuous Inner Monologue](patterns/H6-Continuous-Inner-Monologue.md) | Background Thinker, MIRROR | Background reasoning between turns; fast responder reads it |
| [H7 Adaptive Persona](patterns/H7-Adaptive-Persona.md) | Personalisation | Per-user style model; adapts communication to each person |
| [H8 Meta-Agent Self-Modification](patterns/H8-Meta-Agent-Self-Modification.md) | Self-Editing Agent | Agent edits own system prompt within a governed allowlist |
| [H9 Observational Identity](patterns/H9-Observational-Identity.md) | Self-Knowledge Model | Explicit model of own capabilities and knowledge state |
| [H10 Relational Memory](patterns/H10-Relational-Memory.md) | User Relationship Graph | Per-user relationship record with GDPR erasure support |

</details>

---

## The Mechanical Foundation

Most pattern guidance tells you *what to do*. This catalog tells you *why it works* — from transformer mechanics.

**The Mechanical Foundation** ([`build/content/CHAPTER-0.md`](build/content/CHAPTER-0.md)) derives twelve principles from how LLMs actually compute:

> **Why context length is expensive (not just "costs tokens"):** The attention computation is $O(n^2)$ in sequence length. Doubling your context doesn't double your cost — it quadruples the pairwise attention computation. This is why [K7 Context Pruning](patterns/K7-Context-Pruning.md), [K6 Context Compression](patterns/K6-Context-Compression.md), and context bounding via [O17 Agent Isolation](patterns/O17-Agent-Isolation.md) aren't just "best practices" — they're responses to a quadratic cost curve.

> **Why subagents aren't just organizational:** Each spawned agent has its own sequence length and its own $O(n^2)$ budget. [O6 Orchestrator-Workers](patterns/O6-Orchestrator-Workers.md) with [O17 Agent Isolation](patterns/O17-Agent-Isolation.md) isn't a design preference — it's how you prevent one agent's accumulated tool outputs from multiplying every subsequent call's cost.

> **Why prefix caching changes the economics of parallel agents:** The provider stores KV cache states for stable prompt prefixes (Anthropic: 5-minute TTL, ~10% cost on cache reads). [O18 Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md) turns this into an engineering pattern: design the shared worker prefix as a cacheable unit, warm it once, dispatch all workers within the TTL window. ~85% cost reduction on the shared portion.

> **Why "lost in the middle" is geometric, not random:** Attention weights follow a U-shaped distribution over sequence position — strong at the start and end, materially weaker in the middle (Liu et al. 2024). The model's learned projection matrices embed recency bias from training. This is why [V6 Prompt Injection Shield](patterns/V6-Prompt-Injection-Shield.md) re-anchors instructions at the end of context (geometrically closer to the query = stronger attention weight), and why [S3 Persona](patterns/S3-Persona.md) places identity at position 0.

> **Why tool calls are architecturally different from generation:** Token generation is stochastic — the same prompt produces different outputs on different runs. Code and tool execution is deterministic — same input, same output, no sampling variance. This is the mechanical basis of [R13 CodeAct](patterns/R13-CodeAct.md) (~20pp accuracy gain over JSON tool calls), [V8 Tool Sandboxing](patterns/V8-Tool-Sandboxing.md), and the "save the script" discipline in [H4 Procedural Skill Accumulation](patterns/H4-Procedural-Skill-Accumulation.md).

---

## Key Conflicts and Anti-Patterns

[`patterns/CONFLICTS.md`](patterns/CONFLICTS.md) — the patterns that cannot be used together, the dependencies that are non-negotiable, and the failure modes that look like model problems but are architecture problems.

Critical conflicts every production system must know:

- **R4 ReAct $\oplus$ R5 ReWOO** — mutually exclusive for the same task. ReAct adapts to observations; ReWOO plans upfront. Using ReAct when all tool calls are independent wastes ~5$\times$ tokens. Using ReWOO when calls are sequentially dependent produces wrong results.
- **O6 $\to$ O17** — O6 Orchestrator-Workers *requires* O17 Agent Isolation. Without it, workers share the orchestrator's context, defeating the n² cost bounding that produces O6's quality win.
- **V20 + V9** — Schema Validation retry loops grow context by ~2$\times$ the bad output per retry. V9 Bounded Execution token caps must account for worst-case V20 expansion or they're silently miscalibrated.
- **K6/K7 $\oplus$ K11** — Context Compression and Pruning rewrite or delete prior tokens, invalidating the provider prefix cache. K11 Observational Memory is append-only for a reason: any edit to a prior token position invalidates the KV state for that position and everything after it.
- **Dynamic S2 breaks the entire prefix cache chain** — Retrieval-augmented few-shot selection changes the prefix on every call, forfeiting not just S2's cache but the entire upstream stable prefix (S3 Persona, S5 Constraint Framing, S6 Output Template). The cost is materially larger than it appears.

---

## Two Patterns Derived from First Principles

Two patterns in this catalog don't appear in prior literature — they were derived from the mechanical analysis in Chapter 0:

**[K13 — Retrieval Bundle](patterns/K13-Retrieval-Bundle.md):** Before writing retrieval code, specify the exact operational context bundle a workflow type always needs — by field, by data shape (prose $\to$ vector search; structured document $\to$ hierarchical tree; governed tabular $\to$ semantic layer; relational $\to$ graph), by source authority, by freshness. The absence of this specification is the *rediscovery problem*: agents re-assembling the same context on every run, consuming up to 85% of compute on context construction rather than task execution.

**[O18 — Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md):** Establish a stable shared context as a provider-cached prefix before dispatching parallel workers. All workers dispatched within the provider TTL window (~5 minutes, Anthropic) hit the cache rather than independently re-paying prefill cost. At N=10 workers with a 3,000-token shared prefix, the saving is ~85% on the shared portion. This follows directly from the KV cache structure and prefix caching economics in Chapter 0.

---

## Repo Structure

```
├── GO4.pdf                   ← the typeset book (download)
├── README.md
├── patterns/                 ← the catalogue
│   ├── CONFLICTS.md          ← cross-pattern tensions (must-read for production)
│   ├── SIGNAL.md … HUMANIZERS.md   ← seven category overviews + decision guides
│   └── [94 pattern files]
├── research/
│   └── MECHANISMS.md         ← folk-claim → mechanism → evidence mapping
├── ingest/                   ← generated, ingestible projection of the catalog
│   ├── ingest.json           ← manifest: unit index + relationship graph + glossary
│   ├── INGEST.md             ← how to load it into agent memory
│   └── [pattern/mechanism/decision units]
└── build/                    ← everything that builds the PDF and the website
    ├── build_book.py         ← assembles content + pandoc → GO4.pdf
    ├── book.toml             ← mdBook config (the online edition)
    ├── prepare.py · validate.py · linkify.py   ← site build + cross-reference links
    ├── header.tex            ← LaTeX header for the PDF
    ├── content/              ← book-source markdown (intro, mechanical foundation, references)
    ├── src/SUMMARY.md        ← online navigation
    └── theme/head.hbs        ← MathJax config for the site
```

---

## Start Here

1. **[Download the PDF](https://github.com/jlldavies/go4-llm-design-patterns/raw/main/GO4.pdf)** — the fully typeset book
2. **[Read the Mechanical Foundation](build/content/CHAPTER-0.md)** — twelve mechanical principles that explain why patterns work
3. **[Browse the conflict map](patterns/CONFLICTS.md)** — the patterns you cannot combine, and why
4. **[Pick your category](patterns/)** — jump directly to the pattern you need
5. **[Ingest the whole catalog into your agent](ingest/INGEST.md)** — load every pattern, mechanism, and the conflict graph into your memory system

---

## Sources

60+ sources across academic papers, practitioner frameworks, and industry reports. Key references:

- Brown et al. (2020) — GPT-3 / in-context learning
- Yao et al. (2022) — ReAct
- Wei et al. (2022) — Chain-of-Thought
- Liu et al. (2024) — Lost in the Middle
- Shinn et al. (2023) — Reflexion
- Sarthi et al. (2024) — RAPTOR
- Edge et al. (2024) — GraphRAG
- Anthropic (2024–25) — Building Effective Agents, Context Engineering, Agent Skills, MCP, Prompt Caching
- White et al. (2023) — Prompt Pattern Catalog (PLoP)
- Composio (2025) — AI Agent Report (88% production failure rate)
- PineCone (2025) — Nexus / NoQL (rediscovery problem)
- 12-Factor Agents — Dex Horthy / HumanLayer
- Gamma, Helm, Johnson, Vlissides (1994) — Design Patterns (the original GoF)

Full bibliography: [`build/content/REFERENCES.md`](build/content/REFERENCES.md)

---

## Citation

```bibtex
@misc{davies2026go4,
  title        = {{GO4}: A Pattern Language for {LLM} Engineering},
  author       = {Davies, James},
  year         = {2026},
  howpublished = {\url{https://github.com/jlldavies/go4-llm-design-patterns}},
  note         = {94 design patterns for building LLM systems in production}
}
```

---

## License

[MIT](LICENSE) — free to use, adapt, and share.
