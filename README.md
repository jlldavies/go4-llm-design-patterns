# GO4 — A Gang of Four for AI Engineering

**94 design patterns for LLM systems, grounded in the mechanical structure of transformers.**

In 1994, Gamma, Helm, Johnson, and Vlissides gave software engineers a shared vocabulary for object-oriented design. Before the Gang of Four, every team reinvented the Observer, the Factory, and the Strategy with different names. After it, engineers could say "use a Strategy here" and mean something exact.

AI engineering has the same problem today. Andrew Ng has "four agentic patterns." Anthropic has "five workflow patterns." Academic papers have chain-of-thought, ReAct, Reflexion, Tree of Thoughts. AWS, Google Cloud, and Azure all have their own guides. The techniques circulate as blog posts and GitHub repositories — each framed differently, none carrying the structural analysis that tells a practitioner *when* to use one, *why* it solves what it solves, or *what it trades away*.

This catalog applies the Gang of Four method to that body of knowledge.

---

## What makes this different

Most AI pattern catalogs state conclusions: *"use few-shot examples for format control"*, *"spawn subagents for complex tasks"*. This one derives them.

**Chapter 0** establishes a mechanical foundation — twelve principles derived from how transformers actually work at the tensor level, from the attention bilinear form to KV cache structure to prefix caching economics. Every pattern in the catalog cites the mechanism that explains why it works. When a pattern says *"(mechanism 2)"*, it means the O(n²) attention cost of sequence length; when it says *"(mechanism 7)"*, it means that token generation is stochastic and tools are deterministic. The rationale is derivable, not just observed.

Two patterns in this catalog — **K13 Retrieval Bundle** and **O18 Cache-Warmed Worker Pool** — were arrived at from first principles during the construction of the mechanical foundation, not sourced from prior literature. They address problems (the rediscovery problem, the shared-prefix caching opportunity) that follow directly from transformer mechanics.

---

## The Seven Categories

| # | Category | Patterns | Governs |
|---|---|---|---|
| I | **Signal** | S1–S9 | How instructions, personas, and examples are shaped before the model sees them |
| II | **Knowledge** | K1–K13 | What information and memory the model has access to — context engineering |
| III | **Reasoning** | R1–R20 | How a model structures its thinking: CoT, planning, tool use, search, reflection |
| IV | **Orchestration** | O1–O18 | How agents coordinate, delegate, and interoperate |
| V | **Reliability** | V1–V20 | Safety, cost, governance, observability |
| VI | **Integration** | I1–I6 | How agents connect to tools, services, and each other |
| VII | **Humanizers** | H1–H10 | How agents develop continuity, self-knowledge, and adaptive behaviour across sessions |

---

## The Catalog at a Glance

<details>
<summary><strong>Signal (S1–S9)</strong> — shaping the prompt</summary>

| Pattern | Intent |
|---|---|
| S1 Zero-Shot | Task with no examples; rely on model priors |
| S2 Few-Shot | Provide examples to demonstrate desired format or behaviour |
| S3 Persona | Assign the model an identity to frame knowledge and tone |
| S4 Instruction Decomposition | Break complex instructions into numbered sequential steps |
| S5 Constraint Framing | Define what the model must NOT do as prominently as what it should |
| S6 Output Template | Provide a skeleton of the expected output for the model to complete |
| S8 Meta-Prompt | Model generates or refines its own prompts |
| S9 Constitutional Framing | Embed principles the model applies to self-critique |

</details>

<details>
<summary><strong>Knowledge (K1–K13)</strong> — context engineering</summary>

| Pattern | Intent |
|---|---|
| K1 Vanilla RAG | Retrieve top-k similar chunks at query time |
| K2 Query Transformation | Rewrite the query before retrieval (HyDE, multi-query, step-back) |
| K3 GraphRAG | Index corpus as entity-relationship graph; multi-hop and global synthesis |
| K4 RAPTOR | Recursive summary tree; retrieve at the right abstraction level |
| K5 Adaptive RAG | Evaluate-and-control loop around retrieval |
| K6 Context Compression | Summarise context that no longer fits |
| K7 Context Pruning | Remove spent or irrelevant spans without summarising |
| K8 Working Memory | An explicit in-context scratchpad the model writes to |
| K9 Long Context | Hold the whole working set in a large window |
| K10 Long-Term Memory | External store of flat fact-shaped items, retrieved by similarity |
| K11 Observational Memory | Raw activity record as primary memory; cache-friendly |
| K12 Karpathy Memory | LLM curates structured, dense notes it reads back |
| **K13 Retrieval Bundle** | **Specify the exact operational context bundle a workflow type always needs before writing any retrieval code** |

</details>

<details>
<summary><strong>Reasoning (R1–R20)</strong> — structuring thought</summary>

| Pattern | Intent |
|---|---|
| R1 Zero-Shot CoT | "Let's think step by step" — elicit reasoning without examples |
| R2 Few-Shot CoT | Show worked reasoning examples before the target question |
| R3 Plan-and-Solve | Explicit two-phase: extract plan, then execute |
| R4 ReAct | Interleave Thought / Action / Observation in an adaptive loop |
| R5 ReWOO | Plan all tool calls upfront; execute without mid-run observation (5× token efficiency) |
| R6 Self-Ask | Decompose into sub-questions; answer each; combine |
| R7 Reflexion | Verbal self-critique across attempts; verbal reinforcement learning |
| R8 Self-Refine | Generate → critique → refine in a single session |
| R9 Tree of Thoughts | BFS/DFS over reasoning states |
| R10 LATS | MCTS + ReAct + Reflexion unified |
| R11 Buffer of Thoughts | Reusable thought templates distilled from prior reasoning |
| R12 Skeleton-of-Thought | Parallel section generation via outline |
| R13 CodeAct | Python execution as the agent action language (~20pp accuracy gain) |
| R14 Program of Thoughts | Delegate computation to a deterministic interpreter |
| R16 Talker-Reasoner | Fast Talker + slow Reasoner running concurrently against shared memory |
| R17 Self-Consistency | Sample N reasoning paths; majority vote |
| R18 Graph of Thoughts | Directed acyclic graph of reasoning operations |
| R19 Step-Back Prompting | Abstract to a higher-level principle before answering |
| R20 Chain of Verification | Generate answer, then verify each claim independently |

</details>

<details>
<summary><strong>Orchestration (O1–O18)</strong> — coordinating agents</summary>

| Pattern | Intent |
|---|---|
| O1 Single Agent | One agent, one loop; the baseline |
| O2 Prompt Chaining | Fixed-sequence pipeline; step N feeds step N+1 |
| O3 Routing | Classify input; dispatch to the right agent or prompt |
| O4 Parallelization | Run independent sub-tasks concurrently |
| O5 Evaluator-Optimizer | Generator + judge in a quality loop |
| O6 Orchestrator-Workers | Central orchestrator decomposes dynamically; workers execute in isolation |
| O7 Supervisor Hierarchy | O6 applied recursively; supervisor of supervisors |
| O8 Loop Agent | Open-ended loop with periodic triggers; handles long-running workflows |
| O9 Multi-Agent Reflection | Multiple independent reviewers on a single output |
| O10 Swarm | Emergent coordination via shared environment; no central controller |
| O11 Blackboard | Shared workspace; agents post and consume asynchronously |
| O12 Debate and Deliberation | Two agents argue opposing positions; synthesiser integrates |
| O13 Negotiation | Structured multi-round protocol to reach agreement under conflicting objectives |
| O14 SIE | Self-Improving Executor; agent edits its own tools |
| O15 Agent Handoff | Structured state transfer between agents mid-interaction |
| O16 Hybrid Control Flow | Stack multiple loop primitives |
| O17 Agent Isolation | Fresh, isolated context per sub-task; the mechanism behind O6's quality win |
| **O18 Cache-Warmed Worker Pool** | **Establish a cacheable shared prefix before dispatching parallel workers — ~85% cost reduction on shared context** |

</details>

<details>
<summary><strong>Reliability (V1–V20)</strong> — safety and production</summary>

| Pattern | Intent |
|---|---|
| V1 Human-in-the-Loop | Block until a human approves irreversible actions |
| V2 Human-on-the-Loop | Human monitors and can interrupt; agent proceeds by default |
| V3 Rule of Two | Require two independent confirmations for high-stakes actions |
| V4 Dual LLM | Quarantined Q-LLM handles untrusted content; privileged P-LLM acts |
| V5 Guardrail Layering | Input / pre-call / post-call / output guards at all four boundaries |
| V6 Prompt Injection Shield | Structural and positional defences against injection attacks |
| V7 AgentSpec | Declarative, out-of-prompt policy enforcement |
| V8 Tool Sandboxing | Confine code execution to a restricted environment |
| V9 Bounded Execution | Hard caps on steps, cost, time, depth |
| V10 Checkpointing | Persist replayable snapshots of agent state |
| V11 Error Compaction | Compress errors into compact structured signals |
| V12 Stateless Reducer | Reduce accumulated state to a deterministic summary |
| V13 Tool Budget | Limit schema tokens and active tool count |
| V14 Trajectory Logging | OTel-compatible trace of every call, action, and observation |
| V15 LLM-as-Judge | Use a second LLM to evaluate quality |
| V16 Offline Evaluation | Batch evaluation against a benchmark before deployment |
| V17 Online Evaluation | Real-time quality monitoring in production |
| V18 Agent Simulation | Synthetic environment for pre-deployment stress testing |
| V19 Fallback | Graceful degradation when the primary path fails |
| V20 Schema Validation | Enforce structured output contracts |

</details>

<details>
<summary><strong>Integration (I1–I6)</strong> — connecting to the world</summary>

| Pattern | Intent |
|---|---|
| I1 Direct API | Call a deterministic external service; no model involved |
| I2 Function / Tool Call | Model selects and invokes a typed function from a schema |
| I3 MCP Server | Standardised tool discovery and invocation via Model Context Protocol |
| I4 CLI Invocation | Wrap an existing command-line tool as an agent action |
| I5 Agent Card | Publish a self-describing JSON document for discovery |
| I6 A2A Delegation | Delegate a task to another agent via the Agent-to-Agent protocol |

</details>

<details>
<summary><strong>Humanizers (H1–H10)</strong> — continuity across sessions</summary>

| Pattern | Intent |
|---|---|
| H1 Identity Persistence | Stable Genesis State loaded at position 0 every session |
| H2 Episodic Self-Improvement | Distil session experience into persistent improvement artefacts |
| H3 Entropy-Driven Curiosity | Drive exploration by seeking to reduce uncertainty |
| H4 Procedural Skill Accumulation | Generalise successful trajectories into a reusable skill library |
| H5 Constitutional Self-Alignment | Agent proposes constitution updates; humans approve |
| H6 Continuous Inner Monologue | Background Thinker runs between turns; Responder answers in real time |
| H7 Adaptive Persona | User-model that adapts communication style per person |
| H8 Meta-Agent Self-Modification | Agent edits its own system prompt within a governed allowlist |
| H9 Observational Identity | Explicit model of own capabilities, knowledge state, and past actions |
| H10 Relational Memory | Per-user relationship record with GDPR-compliant deletion |

</details>

---

## The Mechanical Foundation — Chapter 0

The twelve mechanisms that underpin all patterns:

| # | Mechanism | What it says |
|---|---|---|
| 1 | Attention as bilinear form | The attention score $Q_\alpha K^\alpha$ is a contraction under a learned non-symmetric $(0,2)$ tensor $g_{\mu\nu} = W_Q W_K^T$ — not Euclidean similarity |
| 2 | n² attention cost | $QK^T$ is $O(n^2)$ in sequence length. Doubling context quadruples prefill cost |
| 3 | KV cache structure | A 4D tensor $[\text{layers} \times n \times n_\text{kv} \times d_\text{head}]$, growing monotonically. ~300KB per token. Does not persist across API calls |
| 4 | Lost-in-the-middle | U-shaped recall over sequence position (Liu et al. 2024). Middle of context is geometrically under-attended |
| 5 | Prefix caching | Provider stores KV states for stable prefixes. Anthropic: 5-min TTL, 1024-token minimum, ~10% cost on cache reads |
| 6 | Context bounding | Each agent has its own $n$. Multi-agent decomposition bounds the $O(n^2)$ cost per agent |
| 7 | Stochastic generation | Token generation is sampling from a learned distribution. Autoregressive commitment: no revision, only elaboration |
| 8 | Model size matching | Large capacity for reasoning; small models for routing, classification, lookup |
| 9 | Storage hierarchy | In-context ($O(n^2)$) → prefix cache (TTL) → vector index → exact store → cold storage |
| 10 | No cross-session persistence | Weights don't change between calls. All "memory" is file retrieval |
| 11 | Context compaction | Lossy, non-deterministic $n$ reduction. Mandatory for long-running systems |
| 12 | RoPE | $s_{ij} = Q_i^T R((i-j)\theta) K_j$. Relative-only position; recency bias is geometric, not heuristic |

---

## Repository Structure

```
GO4/
├── CHAPTER-0.md              # The mechanical foundation — read this first
├── INTRO.md                  # Book introduction
├── TAXONOMY-DRAFT.md         # Pattern catalog and decision flowcharts
├── REFERENCES.md             # Full bibliography (60+ sources)
├── RESEARCH.md               # Research notes and source analysis
├── PATTERN-BUILD-SPEC.md     # Pattern format specification
├── book.md                   # Full compiled book (single Markdown file)
├── GO4.pdf                   # Compiled PDF (1,163 pages)
├── build_book.py             # Assembles book.md and calls pandoc → PDF
├── header.tex                # LaTeX header for PDF build
├── patterns/
│   ├── SIGNAL.md             # Category II overview
│   ├── KNOWLEDGE.md          # Category II overview
│   ├── REASONING.md          # Category III overview
│   ├── ORCHESTRATION.md      # Category IV overview
│   ├── RELIABILITY.md        # Category V overview
│   ├── INTEGRATION.md        # Category VI overview
│   ├── HUMANIZERS.md         # Category VII overview
│   ├── CONFLICTS.md          # Cross-pattern conflict and tension map
│   ├── S1-Zero-Shot.md       # ┐
│   ├── ...                   # ├ One file per pattern (94 total)
│   └── H10-Relational-Memory.md  # ┘
└── research/
    └── MECHANISMS.md         # Folk-claim → mechanism → evidence mapping
```

---

## Reading the Book

**Start with `CHAPTER-0.md`** — it establishes the twelve mechanisms that all patterns reference. You can read patterns without it, but you'll encounter citations like "(mechanism 5)" without the derivation behind them.

**Then `TAXONOMY-DRAFT.md`** — the full pattern index with decision flowcharts for choosing between patterns.

**Or go straight to a pattern** — each is self-contained with Intent, Motivation, Applicability, Decision Criteria, Structure, Participants, Collaborations, Consequences, Implementation Notes, Implementation Sketch, Known Uses, and Related Patterns.

**`GO4.pdf`** — the fully typeset book, 1,163 pages.

**`book.md`** — the full book as a single Markdown file, useful for search and LLM context.

---

## Building the PDF

Requires [pandoc](https://pandoc.org/) and XeLaTeX with Charter and Avenir Next fonts.

```bash
python3 build_book.py
# writes book.md and GO4.pdf
```

---

## Pattern Format

Every entry follows the Gang of Four structure:

| Field | Content |
|---|---|
| **Intent** | One sentence — what it does |
| **Motivation** | The problem it solves and why naive approaches fail |
| **Applicability** | When to use it, with measurable criteria; when not to |
| **Decision Criteria** | Thresholds and tests that distinguish this from alternatives |
| **Structure** | ASCII diagram of component relationships |
| **Participants** | Each role: what it owns, what it must not do |
| **Collaborations** | How participants work together |
| **Consequences** | Benefits, costs, risks, failure modes |
| **Implementation Notes** | Practical guidance |
| **Implementation Sketch** | Which steps are code, which require an LLM session |
| **Known Uses** | Real systems using this pattern |
| **Related Patterns** | Dependencies, conflicts, upgrade paths |

The Participants table and Decision Criteria are where this catalog earns its keep. A pattern whose applicability cannot be stated in measurable terms is not yet understood well enough to be useful.

---

## Sources

The catalog draws on 60+ sources across academic papers, practitioner frameworks, industry reports, and cognitive science. Key foundations:

- **Brown et al. (2020)** — GPT-3, in-context learning
- **Yao et al. (2022)** — ReAct
- **Wei et al. (2022)** — Chain-of-Thought
- **Liu et al. (2024)** — Lost in the Middle
- **Anthropic (2024–25)** — Building Effective Agents, Context Engineering, Agent Skills, MCP
- **White et al. (2023)** — Prompt Pattern Catalog (PLoP)
- **Gamma et al. (1994)** — Design Patterns (the original GoF)

Full bibliography in [`REFERENCES.md`](REFERENCES.md).

---

## Conflicts and Tensions

[`patterns/CONFLICTS.md`](patterns/CONFLICTS.md) documents the cross-pattern tensions that require explicit design decisions — patterns that cannot run simultaneously, dependencies that are non-negotiable, and tradeoffs that cannot be resolved by convention. 20+ conflicts documented, including mechanistically-derived connections between patterns (e.g. why dynamic few-shot selection invalidates the entire upstream prefix cache chain, or why O6 + O17 is a mandatory composition not an optional one).

---

## Citation

```bibtex
@misc{davies2026go4,
  title  = {GO4: A Gang of Four for AI Engineering},
  author = {Davies, James},
  year   = {2026},
  url    = {https://github.com/jlldavies/go4-llm-design-patterns}
}
```

---

## License

[MIT](LICENSE)
