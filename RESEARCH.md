# GO4 Research — Raw Findings

*Collected: May 2026. Deep sweep: web, GitHub, arXiv, HackerNews, practitioner blogs, academic papers.*
*Second pass targets obscure and primary sources; popular summaries deprioritised.*

---

## 1. Historical Context — Three Eras of AI Engineering

| Era | Period | Core Question | Primary Metric | Failure Mode |
|---|---|---|---|---|
| **Prompt Engineering** | 2022–2024 | "What should I say?" | Response quality | Blind prompting; no structure |
| **Context Engineering** | 2025 | "What information do I provide?" | KV-cache hit rate | Context pollution; overflow |
| **Harness Engineering** | 2026+ | "What system do I build?" | Task completion rate | Orchestration bugs; runaway loops |

Key inflection points:
- **June 2025**: Tobi Lütke + Karpathy endorse "context engineering"; Gartner: "context engineering is in, prompt engineering is out"
- **Late 2025**: Karpathy coins "agentic engineering" as successor to "vibe coding"
- **December 2025**: Karpathy's inflection point — "can't remember the last time I corrected the model"
- **April 2026**: Karpathy's AutoResearch — 1 markdown prompt + 630 lines of training code $\to$ 700 experiments in 2 days, 20 improvements found

---

## 2. Canonical Frameworks (Primary Sources)

### 2.1 Lilian Weng's Agent Framework (June 2023 — still canonical)
Source: [lilianweng.github.io/posts/2023-06-23-agent](https://lilianweng.github.io/posts/2023-06-23-agent/)

**Foundational equation**: `Agent = LLM + Memory + Planning + Tool Use`

Three component categories:

**Planning:**
- Task decomposition: CoT, Tree of Thoughts, LLM+P (outsourcing to classical PDDL planners)
- Self-reflection: ReAct, Reflexion, Chain of Hindsight (CoH), Algorithm Distillation (AD)

**Memory:**
- Sensory Memory — raw input embeddings
- Short-Term / Working Memory — in-context (finite, limited to context window)
- Long-Term Memory — external vector store with MIPS retrieval (LSH, ANNOY, HNSW, FAISS, ScaNN)

**Tool Use:**
- MRKL (Modular Reasoning Knowledge and Language) — routes to neural or symbolic expert modules
- TALM / Toolformer — fine-tuned to learn API usage
- HuggingGPT — Task planning $\to$ Model selection $\to$ Execution $\to$ Response
- API-Bank — three capability levels: call, retrieve, plan

Critical identified limitations: context window constraints, long-horizon planning brittleness, natural language interface reliability

---

### 2.2 Andrew Ng's Four Agentic Patterns (2024)
Source: X/@AndrewYNg, DeepLearning.AI

1. **Reflection** — model critiques and revises its own output; most stable pattern
2. **Tool Use** — autonomous external API/DB/code calls; distinguishes agents from chatbots
3. **Planning** — decomposes complex tasks into subtasks; most brittle pattern
4. **Multi-Agent Collaboration** — specialised agents with distinct roles; most embryonic/highest-potential

These four are the most widely cited canonical set.

---

### 2.3 Anthropic's Five Workflow Patterns (2024-25)
Source: anthropic.com/engineering/building-effective-agents

1. **Prompt Chaining** — fixed sequential pipeline; output feeds next input
2. **Routing** — classify input $\to$ specialised handler
3. **Parallelization** — simultaneous LLM calls; two sub-types: Sectioning (independent tasks) and Voting (consensus)
4. **Orchestrator-Workers** — central LLM dynamically delegates to worker LLMs
5. **Evaluator-Optimizer** — separate generator and judge agents

---

### 2.4 White et al. Prompt Pattern Catalog (2023, PLoP Conference)
Source: [arxiv.org/abs/2302.11382](https://arxiv.org/abs/2302.11382) | [PDF](https://www.dre.vanderbilt.edu/~schmidt/PDF/PLoP-patterns.pdf)

Authors: Jules White, Quchen Fu, Sam Hays, Michael Sandborn, Carlos Olea, Henry Gilbert, Ashraf Elnashar, Jesse Spencer-Smith, Douglas C. Schmidt (Vanderbilt)

**Published in Proceedings of the 30th Conference on Pattern Languages of Programs**

16 patterns across 5 categories (first formal GoF-style treatment of prompt patterns):

**Input Semantics:**
- Meta Language Creation — custom notation/symbolic systems

**Output Customization:**
- Output Automater, Persona, Visualization Generator, Recipe, Output Template

**Error Identification:**
- Fact Check List

**Prompt Improvement:**
- Alternative Approaches, Question Decomposition, Refusal Breaker, Question Refinement, Cognitive Verifier

**Interaction:**
- Flipped Interaction, Infinite Generation, Game Play, Ask for Input

---

### 2.5 Harness Architecture (Fowler/Böckeler, 2026)
2$\times$2 classification matrix:

|  | Feedforward | Feedback |
|---|---|---|
| **Deterministic** | Guides (AGENTS.md, .cursorrules, CLAUDE.md) | Computational (compilers, linters, tests) |
| **Non-deterministic** | System prompts (behavioural constraints) | Inferential (LLM-as-judge review) |

---

### 2.6 12-Factor Agents (Dex Horthy / HumanLayer, 2025)
Source: [github.com/humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)
Inspired by Heroku's 12-Factor App. Core premise: most successful production agents are "mostly well-engineered traditional software, with LLM capabilities carefully sprinkled in at key points."

**All 12 factors:**
1. Natural Language to Tool Calls
2. Own Your Prompts
3. Own Your Context Window
4. Tools are Just Structured Outputs
5. Unify Execution State and Business State
6. Launch/Pause/Resume with Simple APIs
7. Contact Humans with Tool Calls
8. Own Your Control Flow
9. Compact Errors into Context Window
10. Small, Focused Agents
11. Trigger from Anywhere, Meet Users Where They Are
12. Stateless Reducer (agents as pure functions of input $\to$ output, no hidden state)

Community insight (HN): "most 'AI Agents' that make it to production aren't actually that agentic — they're engineered systems with LLMs strategically positioned." 99% accuracy still fails critical operations requiring higher assurance.

---

### 2.7 Agentic Communities: 46 Patterns in 12 Categories (arxiv 2601.03624)
Source: [arxiv.org/pdf/2601.03624](https://arxiv.org/pdf/2601.03624)

Framework uses ISO Open Distributed Processing Enterprise Language (ODP-EL) formalism.

**Governance mechanism — Deontic Tokens:**
- Burden tokens = obligations
- Permit tokens = permissions
- Embargo tokens = prohibitions

**12 Categories, 46 Total Patterns:**

*Foundational Cognitive (12):*
ReAct, Memory-Augmented, Hierarchical Planning, Reflexion, Constitutional AI, Critic-Actor, Metacognitive, Hybrid Neuro-Symbolic, Tool-Using, Embodied, Decomposition, Plan-then-Execute

*Multi-Agent Coordination (9):*
Multi-Agent System, Orchestration, Negotiation, Ensemble, Blackboard, Debate/Deliberation, Inter-Agent Communication, Human-Agent Communication, Semantic Bridge

*Governance & Safety (5):*
Compliance/Governance, Access Control, Audit Trail, Composable DSLs, Federated Privacy

*Specialized Functional (20):*
Workflow Management (3), Quality & Validation (2), Data Processing (4), Performance Optimization (4), Specialized Functions (4), Adaptation & Learning (3)

**Three-Step Pattern Application:**
- Simple Automation: 3–5 patterns
- Departmental: 8–12 patterns
- Enterprise-Wide: 15–20 patterns

---

### 2.8 Inside the Scaffold: Source-Code Taxonomy (arXiv 2604.03515, April 2026)
Source: [arxiv.org/abs/2604.03515](https://arxiv.org/abs/2604.03515) — Benjamin Rombaut, Huawei Canada

*First empirical study classifying 13 open-source coding agents at the source code level (not by abstract capabilities).*

**Three Layers, 12 Dimensions:**

**Layer 1 — Control Architecture:**
1. Control Loop Strategy — 7/13 agents use sequential ReAct; others use fixed pipeline (Agentless) or MCTS (Moatless Tools)
2. Loop Driver — who controls sequencing: user (Aider), scaffold (Agentless), or LLM (9 agents)
3. Control Flow Implementation — while loops (8), recursion (Cline), graph-as-control-flow (Prometheus), exception-based signaling (mini-swe-agent)

**Layer 2 — Tool and Environment Interface:**
4. Tool Set Design — 0 to 37 tools; all LLM-driven agents converge on 4 categories: read, search, edit, execute
5. Edit/Patch Format — string replacement appears independently in 5 agents; Aider supports 13 model-specific formats
6. Tool Discovery — static (6), config-conditional (SWE-agent, OpenHands), per-turn dynamic (Codex CLI), MCP-pluggable (Gemini CLI, Cline, OpenCode)
7. Context Retrieval Paradigm — 8 agents delegate navigation to LLM; others use: repository maps (Aider), AST indexing (AutoCodeRover, Moatless Tools), knowledge graphs (Prometheus), spectrum-based fault localisation (AutoCodeRover)
8. Execution Isolation — no sandboxing, platform sandboxing, Docker containers, shadow git checkpoints (Cline), in-memory shadow mode (Moatless Tools)

**Layer 3 — Resource Management:**
9. State Management — flat message lists, typed event logs (OpenHands), immutable event stores
10. Context Compaction — hard truncation, sliding window, LLM summarisation, selective tool-result dropping, absent
11. Multi-Model Routing — single-model vs role-based routing (planning vs execution)
12. Persistent Memory — static project instructions, LLM-authored memory, cross-tool compatibility mechanisms

**Five Loop Primitives (stackable building blocks):**
1. ReAct loop
2. Generate-test-repair
3. Plan-execute
4. Multi-attempt retry
5. Tree search (MCTS)
11/13 agents layer multiple primitives, not just one.

**Critical architectural fault line:**
"LLM-as-navigator" (8 agents — general tools, LLM-driven search) vs "Scaffold-understands-code" (repository maps, AST indices, knowledge graphs). This choice cascades through loop driver, tool discovery, and context retrieval.

---

## 3. Reasoning Patterns — Detailed Taxonomy

### 3.1 The Four Single-Agent Reasoning Patterns Compared
Source: [theaiengineer.substack.com](https://theaiengineer.substack.com/p/the-4-single-agent-patterns)

| Pattern | LLM Calls | Token Efficiency | Mid-Run Adaptation | Best For |
|---|---|---|---|---|
| **ReAct** | N (per-step) | Baseline | High | Exploratory, unpredictable |
| **Plan-and-Execute** | 1-2 + replans | Good | Medium (replan only) | Well-defined multi-step |
| **ReWOO** | 2 total | **5$\times$ better than ReAct** | None | Multiple independent lookups |
| **Reflexion** | N $\times$ retries | Poor | Meta-level only | Clear pass/fail criteria |

### 3.2 ReWOO — Reasoning Without Observation
Source: [arxiv.org/abs/2305.18323](https://arxiv.org/abs/2305.18323)

Mechanism: Single planning phase with placeholder variables (#E1, #E2). All tools execute in parallel. Final synthesis phase. Only 2 LLM calls total.
- **5$\times$ token efficiency** over ReAct
- **4% accuracy improvement** on HotpotQA
- Fatal flaw: breaks if any tool returns unexpected results; zero mid-execution adaptation

### 3.3 Self-Ask (Ofir Press, 2022/EMNLP 2023)
Source: [arxiv.org/abs/2210.03350](https://arxiv.org/abs/2210.03350)

Model asks itself "Are there follow up questions?" then decomposes complex questions into sub-questions before answering. First formalised decomposition-before-answer pattern. Precursor to modern planning patterns.

### 3.4 LATS — Language Agent Tree Search (ICML 2024)
Source: [arxiv.org/abs/2310.04406](https://arxiv.org/abs/2310.04406)

Unifies ReAct + Tree of Thoughts + Reflexion via MCTS. LLM serves three roles simultaneously: action generator, value function estimator, and reflection mechanism. Enables "go wide" search before committing to a path. Expensive but highest-quality for hard problems.

### 3.5 CodeAct — Executable Code as Actions (ICML 2024)
Source: [arxiv.org/abs/2402.01030](https://arxiv.org/abs/2402.01030)

Replaces JSON tool calls with executable Python code blocks. Agent writes code that calls multiple tools, processes results, applies control flow, stores intermediate data in container variables.
- **~20 percentage points higher** success rate on complex M3 ToolEval tasks vs text/JSON baseline
- **~30% fewer steps** to task completion
- Structured error feedback enables self-debugging

### 3.6 Skeleton-of-Thought (ICLR 2024)
Source: [arxiv.org/abs/2307.15337](https://arxiv.org/abs/2307.15337)

Generate skeleton/outline $\to$ parallel expansion of each skeleton point $\to$ aggregate. Exploits parallelism to reduce latency. Speed improvements across 12 LLMs tested. Less about accuracy; more about structured parallel generation.

### 3.7 Buffer of Thoughts (2024)
Source: [arxiv.org/abs/2406.04271](https://arxiv.org/abs/2406.04271)

Meta-buffer stores reusable high-level thought-templates distilled from problem solutions. Buffer-manager retrieves relevant templates at query time. Achieves significant accuracy improvements at only 12% of cost of multi-query methods (ToT/GoT).

### 3.8 Program of Thoughts / PoT
Disentangles computation from reasoning. For numerical tasks: generate code that computes the answer rather than computing in natural language. Sidesteps arithmetic hallucination entirely by delegating computation to a deterministic executor.

### 3.9 Inner Monologue / MIRROR (2025)
Source: [arxiv.org/abs/2506.00430](https://arxiv.org/abs/2506.00430)

Dual-process architecture:
- **Talker** — immediate response generation
- **Thinker** — asynchronous inner monologue stream generating/updating persistent reflection
Agent maintains its own conversation history where it exclusively talks to itself, seeded with "continue thinking" instruction. Enables background reasoning that informs future turns without consuming user-facing context.

### 3.10 Global Workspace Theory / Theater of Mind (arXiv 2604.08206, April 2026)
Source: [arxiv.org/abs/2604.08206](https://arxiv.org/abs/2604.08206)

Five specialised agent archetypes coordinated through an event-driven central broadcast hub:
1. **Attention Node** — RAG-based context retrieval
2. **Generator Agent** — candidate thought production (dynamic temperature)
3. **Critic Agent** — deterministic scoring (−5 to +5)
4. **Meta Agent** — metacognitive arbitration (picks winning thought)
5. **Response Node** — translates internal reasoning to output

**Entropy-based deadlock-breaking:** when thought diversity (Shannon entropy) drops near zero, generation temperature automatically increases to force exploration of new reasoning paths.

**Dual-layer memory:** Epistemic embedding (to long-term vector DB) + Semantic summarization (dense STM compression) triggered when working memory exceeds token capacity.

**Novelty vs prior work:** Active event-driven broadcasting replaces passive polling; entropy intrinsic motivation replaces ad hoc steering; metacognitive arbitration replaces arg_max. Addresses cognitive stagnation (homogeneous deadlocks) in AutoGen/MetaGPT/CAMEL.

---

## 4. Memory Architecture — Deep Taxonomy

### 4.1 Memory Types and Applications by Domain

| Memory Type | Scope | Mechanism | Dominant Domain |
|---|---|---|---|
| **Sensory / Raw** | Current input | Raw embeddings | Universal |
| **Working / In-Context** | Current task | Conversation history, scratchpad | Universal |
| **Episodic** | Prior runs | Success/failure trajectory logs | Personal assistants, game agents |
| **Semantic** | Domain knowledge | Embeddings, RAG | Personal assistants, enterprise |
| **Procedural** | How-to | Verified code patterns, skill definitions | Software engineering agents |
| **Long-Term** | Cross-session | Vector DB + retrieval | Research agents |

Research finding: Software engineering agents lean heavily on procedural memory; personal assistants on semantic; game agents need tight episodic + procedural integration.

### 4.2 Memory Evolution Framework (three stages)
1. **Storage** — trajectory preservation
2. **Reflection** — trajectory refinement
3. **Experience** — trajectory abstraction (distilling episodes into reusable templates)

### 4.3 Key Systems
- **MemP**: distils trajectories into procedural abstractions
- **LEGOMem**: modular, role-aware procedural memories for multi-agent coordination
- **TiMem**: temporal-hierarchical memory tree
- **MIRIX**: Core + Episodic + Semantic + Procedural + Resource + Knowledge Vault
- **LIGHT**: long-term episodic + short-term working + scratchpad for salient facts

### 4.4 Long Context vs RAG vs Agent Memory (2025-26 Practitioner Consensus)

| Approach | When to Use | Key Tradeoff |
|---|---|---|
| **Long Context** | Affordable cost; accuracy-critical; corpus fits context | 2-3$\times$ more expensive; "lost in the middle" degradation |
| **RAG** | Large corpus; cost-sensitive; retrieval latency acceptable | Lossy; retrieval can miss relevant chunks |
| **Observational Memory** | Agentic sessions; what agent has *seen* matters most | Newer pattern; stable context enables aggressive caching (10$\times$ cost reduction) |

Multi-agent consistency risk: per-agent memory stores cause divergent "memories" across agents. Enterprise architectures need a shared context substrate.

---

## 5. Retrieval Patterns — RAG Variant Taxonomy

| Variant | Mechanism | Best For |
|---|---|---|
| **Vanilla RAG** | Query $\to$ embed $\to$ retrieve $\to$ inject | Simple Q&A, static corpora |
| **HyDE** | Generate hypothetical document $\to$ embed that $\to$ retrieve | Improved semantic matching |
| **RAPTOR** | Multi-level hierarchical summary tree | Query diversity, theme-level answers |
| **GraphRAG** (Microsoft) | Entity-relationship graph over corpus | Complex multi-hop, global structure |
| **Self-RAG** | Model decides when to retrieve; critiques own outputs | Factuality-critical tasks |
| **Corrective RAG (CRAG)** | Evaluate retrieval quality; trigger web search if poor | Dynamic, uncertain knowledge bases |
| **Agentic RAG** | Agent plans multiple retrieval steps, adapts mid-task | Complex, open-ended research |
| **Hierarchical RAG** | Corpus selection $\to$ chunk-level search | Large heterogeneous knowledge bases |

---

## 6. Orchestration Patterns — Extended Catalog

### 6.1 Blackboard System
Classical AI pattern (1980s) now being applied to LLM multi-agent systems (arXiv 2510.01285, 2025).

Architecture: central shared "blackboard" with public and private spaces. Agents write to and read from the blackboard. A control unit adaptively selects agents based on blackboard state, avoiding rigid workflow templates.

Research result: "Blackboard-based architectures achieve state-of-the-art reasoning performance with lower token costs than static pipelines."

### 6.2 Debate / Deliberation Pattern
Multiple agents argue opposing positions before a synthesiser produces a conclusion. Related to ensemble methods. Effective for decisions with genuine uncertainty; expensive.

### 6.3 Negotiation Pattern
Agents with different objectives negotiate to reach mutually acceptable outcomes. Relevant for multi-stakeholder tasks. Draws from multi-agent systems research predating LLMs.

### 6.4 Single Information Environment (SIE)
Data-centric design where agents specialise in unique datasets; a coordinator routes queries to the appropriate agent. Reduces context overload by partitioning knowledge ownership.

### 6.5 Human-in-the-Loop vs Human-on-the-Loop
- **Human-in-the-loop**: agent pauses and requires human approval to proceed
- **Human-on-the-loop**: agent acts autonomously; human monitors and can intervene

Empirical finding: "Human oversight proved non-negotiable across all domains" in production MAS studies.

### 6.6 Hybrid Control Flow
Most production agents use mixed control flows. The scaffold taxonomy found 11/13 studied agents layer multiple loop primitives (ReAct + plan-execute + retry, etc.). The pattern is *composition of primitives*, not selection of one.

---

## 7. Security Patterns — Extended

### 7.1 Simon Willison's Lethal Trifecta
Source: [simonw.substack.com](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents)

Three conditions that, when combined, create catastrophic prompt injection risk:
1. Access to private data (email, documents, databases)
2. Exposure to untrusted content (web pages, emails, documents an attacker can modify)
3. External communication ability (HTTP, email send, PRs, clickable links)

Any agent combining all three can be trivially compromised by an attacker embedding instructions in content the agent reads.

**Six defence patterns** (from academic survey):
1. **Action-Selector** — agents trigger tools but cannot see responses (breaks feedback loops)
2. **Plan-Then-Execute** — plan before exposure to untrusted content
3. **LLM Map-Reduce** — sub-agents handle tainted content independently
4. **Dual LLM** — Privileged LLM (sees user query only) + Quarantined LLM (processes untrusted data, no tool access)
5. **Code-Then-Execute** — generate sandboxed code specifying tool interactions
6. **Context-Minimization** — strip user prompts before returning database results

### 7.2 CaMeL (Google DeepMind, April 2025)
Custom Python interpreter that tracks the origin of data and instructions. Uses Dual LLM pattern. First proposed credible technical solution to prompt injection at the tool-execution layer.

### 7.3 AgentSpec (2025-26)
Declarative, externally-specified rules for runtime enforcement of LLM agent behaviour. Decouples governance from prompt engineering; enables transparent auditing of enforced constraints.

### 7.4 Deontic Governance (from ISO ODP-EL / Agentic Communities paper)
Formal governance using deontic tokens:
- Burden tokens = obligations (must do)
- Permit tokens = permissions (may do)
- Embargo tokens = prohibitions (must not do)

Creates traceable accountability chains across all agents and human participants. Enables regulated enterprise deployment.

---

## 8. Reliability Patterns — Extended

### 8.1 Tool Overload Problem (quantified)
Critical finding: performance degrades significantly with too many tools.
- Selection accuracy collapses: 43% $\to$ under 14% (3$\times$ degradation) at high tool counts
- AI accuracy drop: 87% $\to$ 54% with context overload
- Cursor enforces hard limit of 40 tools
- 4-5 MCP servers together can burn 60,000+ tokens on schema alone (30-50% of budget for frontier models)
- Mitigation: dynamic tool discovery, RAG-MCP (retrieve tool schemas), grouped tools, specialised agents with focused toolsets

### 8.2 12-Factor Reliability Principles (from Horthy)
Key reliability-specific factors:
- Factor 3 (Own Context Window): deliberate curation, not framework defaults
- Factor 9 (Compact Errors): efficient error representation within token budget
- Factor 12 (Stateless Reducer): pure function architecture; no hidden state

### 8.3 Speculative Execution in Agent Context
Draft-then-verify paradigm being extended to agent actions. Sherlock (arXiv 2511.00330) holistically explores cost/accuracy/latency tradeoffs by exploiting speculative execution with intelligent verifier selection. 2-3$\times$ speedup without accuracy loss on inference; agent-level benefits more limited (end-to-end latency dominated by tool execution time).

---

## 9. Interoperability — Emerging Standards

Four agent communication protocols now competing/converging (2025-26):

| Protocol | Source | Role |
|---|---|---|
| **MCP** (Model Context Protocol) | Anthropic | Agent $\leftrightarrow$ tools/services/data (97M+ downloads) |
| **A2A** (Agent-to-Agent) | Google Cloud | Agent $\leftrightarrow$ agent delegation and coordination |
| **ACP** (Agent Communication Protocol) | IBM | Agent-to-agent via REST |
| **ANP** (Agent Network Protocol) | Community | Decentralised agent discovery/marketplaces |

Both MCP and A2A now under Linux Foundation's Agentic AI Foundation (AAIF), launched December 2025 with OpenAI, Anthropic, Google, Microsoft, AWS, Block as co-founders.

Enterprise guidance: implement MCP for single-agent tool access; add A2A when multi-agent delegation is needed.

---

## 10. Policy-Driven vs Reactive Agents

New emerging distinction:
- **Reactive agents**: LLM decides next action at each step based on observation (ReAct model)
- **Policy-driven agents**: External declarative policy specification constrains agent action space; LLM operates within formally specified boundaries

Policy-driven approach (AgentSpec, PoAct) enables: auditing, guaranteed constraint satisfaction, multi-agent governance. Trade-off: less flexible; requires upfront specification of policies.

---

## 11. Cognitive Science Foundations

AI agent architectures increasingly grounded in cognitive science theories:
- **Global Workspace Theory** (Baars) $\to$ GWA, Theater of Mind architectures
- **Society of Mind** (Minsky) $\to$ Multi-agent specialisation patterns
- **Dual-Process Theory** (Kahneman) $\to$ Talker/Thinker (MIRROR), System 1/System 2 agent designs
- **Predictive Processing** (Friston) $\to$ anticipatory agent architectures
- **Baddeley's Working Memory Model** $\to$ working memory + episodic buffer + long-term stores mapping
- **Extended Mind Thesis** (Clark) $\to$ external tool use as cognitive extension

"Agentic Flow" framework explicitly maps five modules to these theories in a repeatable cognitive loop.

---

## 12. Empirical Research Findings

From "LLM-Enabled Multi-Agent Systems" (arXiv 2601.03328):
- Prototype to pilot: 2 weeks; pilot-ready: 1 month
- Customer service automation: 5 emails/min at £0.05 vs 3/min at £0.33 manually; 100% accuracy in pilot
- **Critical limit**: "Performance degrades when toolkit expands beyond 8–12 tools due to context-window overload and cognitive interference"
- **Dominant constraint**: "Variability in LLM behaviour that leads to challenges in transitioning from prototype to production maturity"
- Human oversight was non-negotiable in all production deployments

From scaffold taxonomy (arXiv 2604.03515):
- No consensus exists on: context compaction, state representation, or safety mechanisms for interactive agents
- Dimensions converge where external constraints dominate (tool capabilities, edit formats, sandboxing)
- Dimensions diverge where open questions remain (compaction, state representation, safety)

---

## 13. Hacker News Community Intelligence

Threads surfaced (relevance-ranked):

1. **"54 Agentic Tool Patterns"** (HN 46954615) — Drawing from Gregor Hohpe's Enterprise Integration Patterns (EIP book), applying patterns like Content-Based Router, Dead Letter Channel, Claim Check to AI tool design
2. **"12-Factor Agents"** (HN 43699271) — Strong practitioner consensus: "most 'AI agents' that make it to production aren't actually that agentic"
3. **"Patterns for building LLM-based systems"** (HN 36965993) — August 2023, foundational community discussion
4. **"Dual LLM pattern"** (HN 35925758) — Simon Willison's original post, spawned security pattern thinking
5. **"Prompt pattern catalog"** (HN 36196113) — White et al. paper discussion; good critical analysis of what the pattern formalism adds/doesn't

---

## 14. Key Papers Reference List

| Paper | Year | Key Contribution |
|---|---|---|
| White et al. — Prompt Pattern Catalog | 2023 | First GoF-style prompt patterns; 16 patterns; PLoP |
| Yao et al. — ReAct | 2022 | Interleaved reasoning and acting |
| Yao et al. — Tree of Thoughts | 2023 | Branching reasoning; BFS/DFS |
| Wei et al. — Chain-of-Thought | 2022 | Step-by-step reasoning elicitation |
| Press et al. — Self-Ask | 2022 | Decomposition via follow-up questions |
| Shinn et al. — Reflexion | 2023 | Verbal reinforcement via self-reflection |
| Xu et al. — ReWOO | 2023 | 5$\times$ token efficiency via decoupled reasoning |
| Zhou et al. — LATS | 2023/ICML 2024 | MCTS + ReAct + Reflexion unified |
| Wang et al. — CodeAct | 2024/ICML 2024 | Executable code as agent actions |
| Ning et al. — Skeleton-of-Thought | ICLR 2024 | Parallel generation via outline |
| Yang et al. — Buffer of Thoughts | 2024 | Meta-buffer of reusable thought templates |
| Rombaut — Inside the Scaffold | 2026 | Empirical scaffold taxonomy; 13 coding agents; 12 dimensions |
| Dao et al. — Agentic Design Patterns | 2026 | System-theoretic framework (arXiv 2601.19752) |
| Shang — Theater of Mind | 2026 | Global Workspace Theory applied to LLM agents |
| bMAS — Blackboard LLM MAS | 2025 | Blackboard system pattern for LLM multi-agents |
| MIRROR — Inner Monologue | 2025 | Talker/Thinker dual-process for persistent reflection |
| CaMeL — DeepMind prompt injection | 2025 | First credible technical prompt injection defence |
| AgentSpec | 2025-26 | Declarative runtime governance for LLM agents |

---

---

## 16. MCP vs API vs Function Calling — Full Decision Framework

Source: jamwithai.substack.com, bytebridge.medium.com, HN discussions

### Three Pattern Definitions

| Pattern | What It Is | Who Calls It |
|---|---|---|
| **Direct API Call** | HTTP request to external service | Your code, deterministically |
| **Function/Tool Calling** | Schema-wrapped API the LLM can invoke | LLM decides; your code executes |
| **MCP** | Standardisation layer over tool calling; dynamic discovery; credential isolation | LLM via client-server JSON-RPC |

### Decision Tree (from jamwithai.substack.com)

```
Does LLM reasoning determine the action?
  NO → Direct API call
  YES:
    How many integrations?
    1-5 tools → Function calling
    5-20 tools → MCP + function calling hybrid
    20+ tools → MCP servers with gateway

    Multiple agents sharing integrations?
    NO → Function calling suffices
    YES → Implement MCP

    CLI exists for this tool?
    YES → Try CLI first (git, docker, gh, cloud CLIs)

    Sub-10ms latency critical?
    YES → Direct API only
```

### MCP Context Overhead (critical production data)
- GitHub MCP alone: 40,000–55,000 tokens per request
- 4–5 MCP servers together: 60,000+ tokens on schemas (30–50% of frontier model budget)
- Tool selection accuracy collapses at high tool counts: 43% $\to$ under 14% (3$\times$)
- AWS Lambda cold start for MCP servers: ~5 seconds
- Best production system uses **all three patterns simultaneously**: direct API for determinism, function calling for app-specific routing, MCP for shared reusable integrations, CLIs for developer tools

### MCP Specific Tradeoffs (from ByteBridge analysis)

**MCP advantages:** Dynamic runtime tool discovery; write-once multi-client compatibility; credential isolation; stateful connections; audit trail support; OAuth now in spec

**MCP disadvantages:** Non-determinism (same input $\to$ different tool call); cascading failure modes (5+ failure points vs 1 for direct API); context window consumption; cold start latency; version management for tool schemas; testing automation harder; operational infrastructure (gateways, registries, credential management)

### Developer Community Position on MCP
"MCP is a fad" HN debate (HN 46552254):
- Pragmatist camp: "it's the LSP for AI tools; write once, support every client"
- Skeptic camp: "almost everything I might achieve with an MCP can be handled by a CLI tool"
- Both agree: poor naming, early security design flaws, no consensus on auth
- Emerging consensus: MCP for shared reusable integrations across clients; CLI or function calling for agent-specific tools

### Karpathy on CLIs
"CLIs are exciting precisely because they are a 'legacy' technology — AI agents can natively and easily use them." CLIs are the path of least resistance for agents that need to touch developer tooling.

---

## 17. Developer Community — Framework Debates

### The LangChain Backlash (HN 40739982 — "Why we no longer use LangChain")
Overwhelming negative sentiment. Key problems:
- "Death by abstraction" — 5 layers of abstraction to change one detail
- Accessing token usage metadata required diving into source code
- 80+ package dependencies; breaking changes in most updates
- "For many use cases, calling the model directly was simpler, faster, and more predictable"
- Cost: LangChain's complex agents make several thought calls; direct API calls give precise cost control

What developers use instead:
- Direct OpenAI/Anthropic API calls
- Simple custom loops (80–500 lines of code)
- Instructor (structured output without framework overhead)
- LangGraph (lower-level; graph-based control flow)
- OpenAI Agents SDK (lightweight, native function calling primitives)

Harrison Chase (LangChain CEO) acknowledged the framework abstracted too much initially.

**Principle emerging**: MCP (late 2024) substantially disrupted LangChain's value proposition by providing standardised tool connectivity without the monolithic framework overhead.

### The Anti-Framework Principle (Horthy / 12-Factor Agents)
"Most 'AI agents' that make it to production aren't actually that agentic — they're engineered systems with LLMs strategically positioned." 99% accuracy still fails critical operations. Own your prompts, own your control flow, own your context window.

### The CLI-First Contrarian View
Gaining traction in 2026: prefer CLIs over MCP for tools the model already knows. Karpathy endorsement. No context overhead; universal coverage; no auth complexity; agents can already use them.

---

## 18. Vibe Coding $\to$ Agentic Engineering Shift (Developer Experience)

What practically changed:
1. **From code generation to agent orchestration**: not writing code 99% of the time — directing agents and acting as oversight
2. **Structured workflow requirements**: design systems, constraints, feedback loops that enable AI to write code reliably
3. **Spec-driven development**: functional spec documents first; JetBrains and GitHub released Spec Kit to formalise this
4. **Production viability milestone**: late 2025, when Anthropic's Opus + OpenAI's Codex crossed reliability threshold
5. **Developer role transformation**: engineers at Anthropic review, direct, and govern agents that write code
6. **Quality gates became mandatory**: automated tests, human oversight at critical checkpoints

The failure mode of vibe coding: skipped design, review, and testing. Works for demos; collapses under real users, security requirements, and scale.

---

## 19. Production Failure Analysis — Why Agents Fail

### The Statistics
- 88% of AI agents never reach production (Composio AI Agent Report 2025)
- Only 12% of agent initiatives successfully reach production at scale
- 97% of executives report deploying AI agents over past year (same report)
- 70% of canceled AI projects: tool or API failures were root cause

### Root Cause Clusters
Failures cluster around **three areas** (not the model itself):
1. **Data fragmentation** — messy production data vs clean pilot sandbox
2. **Integration complexity** — 70% of cancellations trace to tool/API failures
3. **Governance gaps** — no documentation, escalation paths, monitoring

### The Pilot $\to$ Production Gap
Why pilots succeed: clean curated data, bounded sandbox, tightly scoped, simplified integrations.
Why production fails: messy unstructured data, concurrent users, unanticipated edge cases, strict compliance, real failure consequences.

### Five Context Debt Failure Modes
1. Inconsistent answers across agents (per-agent memory divergence)
2. Authoritative hallucination (confident wrong answers)
3. Tests pass while production breaks
4. Agents that cannot scale beyond one use case
5. Adoption stalls because nobody trusts untraced outputs

### Real Operator Experience (23 agents across 5 businesses)
"The model was almost never the problem — the ops layer caused failures repeatedly in preventable ways."
First major incident: agent stuck in loop, consuming API credits without useful output.
Solution: explicit circuit breakers, trajectory logging, error compaction.

### Agent Loop Failure Modes
- **Semantic drift**: model "forgets" system prompt constraints; hallucination of tool names; contradicting earlier instructions
- **Context overflow**: token limit hit mid-task; critical instructions lost
- **Tool call hallucination**: structurally plausible but functionally incorrect tool calls; wrong tool selection, malformed parameters, incorrect chaining
- **Probabilistic failure**: same input succeeds 9/10 times; fails catastrophically on 10th
- Modern observability tracks patterns: "tool call retry loop — context window overflow — 38 occurrences"

---

## 20. Evaluation Patterns

### Multi-Level Evaluation Framework
**Offline evals** (before production): validate against known scenarios, reference outputs, regression tests
**Online evals** (production monitoring): monitor live traces for quality regressions, drift, safety without ground truth

Full conversation thread is the relevant evaluation unit for agents (not individual responses).

### LLM-as-Judge Patterns
- Automated scorers assess output quality across: correctness, relevance, safety, helpfulness
- Score calibrated against human corrections
- "Agent-as-a-Judge" emerging pattern (arXiv 2508.02994, 2025)
- Risk: same system generating output and critique reinforces blind spots (Reflexion limitation)

### Evaluation Toolchain (2025-26)
CI/CD integration; simulation engines (test end-to-end reasoning before production); custom scoring functions; LangWatch, MLflow LLM Evaluation, Latitude, Augment Code tools

---

## 21. Agent Observability — Production Standard

### OpenTelemetry GenAI Semantic Conventions (emerging standard)
Vendor-neutral; defines span types for: LLM calls, agent invocations, tool executions
Attributes: token usage, model identity, agent metadata
Supported by: Datadog, Honeycomb, New Relic, and natively emitted by LangChain, CrewAI, AutoGen

### Multi-Agent Tracing Pattern
Each agent invocation = a span. Trace context passed whenever agent calls another agent. Root agent span $\to$ child spans for routing, planning, specialist agents, tool usage. Full execution trace navigable in one view.

### What to Trace
Full execution traces including: prompts, tool invocations, decision paths, context relevance, token usage, cost per step. Production agent failures diagnosable in minutes from trace instead of hours from log archaeology.

Non-deterministic execution paths (500ms to 3 minutes per agent run) require fundamentally different observability than traditional deterministic services.

---

## 22. System 1 / System 2 Agent Architecture (Talker-Reasoner)

Based on Kahneman's dual-process theory:
- **System 1**: fast, automatic, intuitive — "Talker" agent
- **System 2**: slow, deliberate, analytic — "Reasoner" agent

Source: [arxiv.org/abs/2410.08328](https://arxiv.org/abs/2410.08328)

Architecture: Talker handles immediate responses (fast); Reasoner handles multi-step reasoning and planning (slow, asynchronous). Inner Monologue / MIRROR extends this with the Thinker generating/updating a persistent reflection stream.

Inference-time reasoners (o1, o3, R1) effectively implement System 2 by trading speed for accuracy via test-time compute scaling.

---

## 23. Agent Identity and Interoperability

### Agent Card (A2A Protocol)
Standard JSON file at `/.well-known/agent.json` declaring:
- Identity (name, description, provider)
- Service endpoint URL
- Supported A2A capabilities (streaming, push notifications)
- Agent skills
- Security requirements

The Agent Card is the "digital business card" enabling agent discovery. Task object acts as a binding contract between client and remote agent. Led by Google; 50+ enterprise partners including Salesforce, Accenture, SAP.

### Four Protocol Landscape (2025-26)

| Protocol | Source | Layer | Status |
|---|---|---|---|
| MCP | Anthropic | Agent $\leftrightarrow$ tools/services | 97M+ downloads; AAIF |
| A2A | Google Cloud | Agent $\leftrightarrow$ agent | v1.0 early 2026; AAIF |
| ACP | IBM | Agent $\leftrightarrow$ agent via REST | Emerging |
| ANP | Community | Decentralised discovery | Experimental |

Linux Foundation AAIF (Dec 2025): OpenAI, Anthropic, Google, Microsoft, AWS, Block as co-founders.

---

## 24. Additional Patterns Not Previously Catalogued

### Self-Refine
Source: [github.com/madaan/self-refine](https://github.com/madaan/self-refine)
LLM generates output $\to$ generates feedback on its own output $\to$ refines based on feedback $\to$ repeats. Different from Reflexion (which uses explicit episodes) and O6 Evaluator-Optimizer (which uses separate judge). Self-Refine uses the same model instance throughout. Favoured over one-step generation across 7 diverse tasks.

### Chain of Density (CoD)
Iterative summarisation: identify 1-3 entities missing from previous summary $\to$ rewrite at same length incorporating them. Produces progressively denser, more information-rich summaries. Useful for context compression while preserving entity coverage.

### Constitutional AI (CAI, Anthropic 2022)
Training pattern: model generates responses $\to$ critiques them against an explicit "constitution" (set of principles) $\to$ revises. Generates preference pairs without human annotators. Result: simultaneously more helpful AND less harmful than RLHF baseline on Pareto frontier. Now used as an agent runtime pattern (not just training): agent carries a constitution it applies to self-critique at inference time.

### Agent Handoff Pattern
Structured state transfer between agents mid-interaction. Key challenge: context loss. Best practice:
- Pass structured summary (detected intent, extracted entities, sentiment, actions taken, stated goal) — not raw transcript
- Preserve provenance and tool state (citations, session state, trace IDs)
- Carry audit trail for compliance/replay
- Context loss is the #1 source of frustration in agent transfers

### Token Budget Management Patterns
- Hard token limits per agent invocation (Claude Code enforces these)
- Pre-execution budget checks before expensive operations
- Auto-compaction of conversation history before context fills
- Rate limits (requests/min, tokens/min) separate from budget limits (dollars/period)
- Weekly token volume: OpenRouter went from 0.4T $\to$ 27T tokens/week Dec 2024 $\to$ Mar 2026 (68$\times$ in 15 months)
- Context window is a "rival, excludable resource" contested by: system prompts, tool schemas, conversation history, retrieved docs, reasoning scratchpads

---

## 25. Real-World Agentic Use Cases (Production Evidence)

### Documented Production Deployments

**Customer Service:**
- Dutch insurer: ~90% of individual automotive claims automated
- Agents "running at scale" in call centers as of early 2025
- Customer service: 5 emails/min at £0.05 vs 3/min at £0.33 manually; 100% accuracy in pilot

**E-Commerce:**
- Global platform: 50M customers, personalized email/recommendations via agentic marketing workflows
- 45% decrease in marketing costs; 180% increase in conversion rates
- Fashion retail: 40% overstock reduction, improved inventory turnover

**Software Engineering:**
- AutoResearch (Karpathy): 700 experiments in 2 days; 20 training optimisations found
- Coding agents (Devin, SWE-agent, Claude Code): autonomous PR generation, bug fixing
- Code review, test generation, documentation

**Finance:**
- Supply chain agents $\to$ compliance agents $\to$ financial forecasting agents (fully autonomous chain)
- Claims automation, fraud detection, risk assessment

**Research:**
- AutoResearch patterns for scientific discovery
- Multi-hop Q&A, report generation

### Vertical Industry Patterns from arXiv Survey (2510.25445)
90 studies (2018-2025): healthcare, finance, robotics. Core finding: "application constraints dictate paradigm selection." The same architectural patterns appear across verticals but with domain-specific constraints driving choices:
- Healthcare: explainability + privacy $\to$ H-in-the-L + Dual LLM + Audit Trail
- Finance: consistency + compliance $\to$ Plan-and-Execute + AgentSpec + Audit Trail
- Education: adaptability $\to$ Reflexion + Episodic Memory + Persona

---

## 15. Web Sources

**Primary Research Papers:**
- [Lilian Weng — LLM Powered Autonomous Agents (2023)](https://lilianweng.github.io/posts/2023-06-23-agent/)
- [White et al. — Prompt Pattern Catalog PDF](https://www.dre.vanderbilt.edu/~schmidt/PDF/PLoP-patterns.pdf)
- [ReWOO — arXiv](https://arxiv.org/abs/2305.18323)
- [LATS — arXiv](https://arxiv.org/abs/2310.04406)
- [CodeAct — arXiv](https://arxiv.org/abs/2402.01030)
- [Inside the Scaffold — arXiv 2604.03515](https://arxiv.org/abs/2604.03515)
- [Agentic Communities Patterns — arXiv 2601.03624](https://arxiv.org/pdf/2601.03624)
- [Theater of Mind — arXiv 2604.08206](https://arxiv.org/abs/2604.08206)
- [Talker-Reasoner — arXiv 2410.08328](https://arxiv.org/abs/2410.08328)
- [MIRROR Inner Monologue — arXiv 2506.00430](https://arxiv.org/abs/2506.00430)
- [bMAS Blackboard — arXiv 2510.01285](https://arxiv.org/pdf/2510.01285v1)
- [LLM-Enabled MAS Empirical — arXiv 2601.03328](https://arxiv.org/html/2601.03328v1)
- [Agentic AI Comprehensive Survey — arXiv 2510.25445](https://arxiv.org/abs/2510.25445)
- [Agent Interoperability Protocols Survey — arXiv 2505.02279](https://arxiv.org/html/2505.02279v1)
- [Self-Refine — GitHub](https://github.com/madaan/self-refine)
- [Token Economics for LLM Agents — arXiv 2605.09104](https://arxiv.org/html/2605.09104v1)

**Practitioner Frameworks:**
- [Andrew Ng — Four Design Patterns (X)](https://x.com/AndrewYNg/status/1773393357022298617)
- [Anthropic — Building Effective AI Agents](https://resources.anthropic.com/building-effective-ai-agents)
- [12-Factor Agents — GitHub](https://github.com/humanlayer/12-factor-agents)
- [Simon Willison — Lethal Trifecta](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents)
- [The AI Engineer Substack — 4 Single-Agent Patterns](https://theaiengineer.substack.com/p/the-4-single-agent-patterns)
- [Augment Code — Agentic Design Patterns Catalog](https://www.augmentcode.com/guides/agentic-design-patterns)

**MCP vs API Analysis:**
- [ByteBridge — MCP vs Direct API in Production](https://bytebridge.medium.com/mcp-vs-traditional-api-calls-in-production-promises-pitfalls-and-proper-use-e0550c4b8065)
- [JamWithAI — MCP vs API vs Function Call Decision Framework](https://jamwithai.substack.com/p/when-to-use-mcp-vs-api-vs-functiontool)
- [Composio — API vs MCP Guide](https://composio.dev/content/api-vs-mcp-everything-you-need-to-know)

**HackerNews Community Discussions:**
- [HN: 12-Factor Agents](https://news.ycombinator.com/item?id=43699271)
- [HN: 54 Agentic Tool Patterns](https://news.ycombinator.com/item?id=46954615)
- [HN: Dual LLM Pattern](https://news.ycombinator.com/item?id=35925758)
- [HN: MCP is a fad](https://news.ycombinator.com/item?id=46552254)
- [HN: Why we no longer use LangChain](https://news.ycombinator.com/item?id=40739982)
- [HN: Prompt Pattern Catalog](https://news.ycombinator.com/item?id=36196113)

**Production & Observability:**
- [Jenova.ai — Tool Overload](https://www.jenova.ai/en/resources/mcp-tool-scalability-problem)
- [OpenTelemetry — AI Agent Observability Standards](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [Zylos Research — OpenTelemetry for AI Agents](https://zylos.ai/research/2026-02-28-opentelemetry-ai-agent-observability)
- [Zylos Research — Agent Protocol Convergence](https://zylos.ai/research/2026-03-26-agent-interoperability-protocols-mcp-a2a-acp-convergence)
- [Agent2Agent Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [Why 90% of AI Agents Fail](https://dev.to/nebulagg/why-90-of-ai-agent-projects-fail-and-the-patterns-that-fix-it-1dma)
- [88% Failure Analysis](https://www.digitalapplied.com/blog/88-percent-ai-agents-never-reach-production-failure-framework)

**RAG Variants:**
- [RAGFlow — RAG at the Crossroads (Mid-2025)](https://ragflow.io/blog/rag-at-the-crossroads-mid-2025-reflections-on-ai-evolution)
- [GraphRAG vs RAG — arXiv 2502.11371](https://arxiv.org/html/2502.11371v3)
