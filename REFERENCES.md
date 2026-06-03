# GO4 — Master Reference List

*Consolidated bibliography for all patterns across all seven categories.*
*Organised by source type. Every citation used in any pattern file appears here.*
*Patterns that cite each source are listed in brackets.*

---

## Academic Papers

### Foundational LLM Papers

**Brown, T., Mann, B., Ryder, N., et al. (2020)**
"Language Models are Few-Shot Learners"
*NeurIPS 2020*
arXiv: 2005.14165
$\to$ Established in-context learning (few-shot). The empirical foundation for S2 (Few-Shot), I2 (Function Call).
*Cited by: S2, I2*

**Vaswani, A., Shazeer, N., Parmar, N., et al. (2017)**
"Attention Is All You Need"
*NeurIPS 2017*
arXiv: 1706.03762
$\to$ The transformer architecture underlying all patterns in this collection.
*Cited by: foundational context*

**Olsson, C., Elhage, N., Nanda, N., et al. (2022)**
"In-Context Learning and Induction Heads"
*Transformer Circuits Thread* (Anthropic)
transformer-circuits.pub/2022/in-context-learning/index.html
$\to$ Induction heads: a two-step attention circuit performing match-and-copy ([A][B]…[A]$\to$[B]); argued to be a major mechanism behind in-context learning. Mechanistic basis for why few-shot examples work.
*Cited by: S2*

**Liu, N. F., Lin, K., Hewitt, J., et al. (2024)**
"Lost in the Middle: How Language Models Use Long Contexts"
*TACL 2024*
arXiv: 2307.03172
$\to$ U-shaped recall over long context: strong at the start/end, materially weaker in the middle. Empirical foundation for the "clean the data room first" discipline.
*Cited by: K-series (Chapter 0 Mechanism 4)*

---

### Prompting and Reasoning Papers

**Wei, J., Wang, X., Schuurmans, D., et al. (2022)**
"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
*NeurIPS 2022*
arXiv: 2201.11903
$\to$ Established CoT as a prompting technique. Direct foundation for R1 (Zero-Shot CoT) and R2 (Few-Shot CoT).
*Cited by: R1, R2*

**Wang, X., Wei, J., Schuurmans, D., et al. (2022)**
"Self-Consistency Improves Chain of Thought Reasoning in Language Models"
*ICLR 2023*
arXiv: 2203.11171
$\to$ Established self-consistency voting. N=5-10 samples; majority vote outperforms greedy decoding on reasoning tasks.
*Cited by: R17, R-category conflict notes*

**Kojima, T., Gu, S. S., Reid, M., et al. (2022)**
"Large Language Models are Zero-Shot Reasoners"
*NeurIPS 2022*
arXiv: 2205.11916
$\to$ "Let's think step by step" zero-shot CoT. Foundation for R1.
*Cited by: R1*

**Wang, L., Xu, W., Lan, Y., et al. (2023)**
"Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models"
*ACL 2023*
arXiv: 2305.04091
$\to$ Establishes Plan-and-Solve as two-step: extract plan $\to$ execute. Foundation for R3.
*Cited by: R3*

**Yao, S., Zhao, J., Yu, D., et al. (2022)**
"ReAct: Synergizing Reasoning and Acting in Language Models"
*ICLR 2023*
arXiv: 2210.03629
$\to$ The foundational ReAct paper. Thought-Action-Observation loop. One of the most cited papers in this collection.
*Cited by: R4, R5-conflict*

**Xu, B., Peng, B., Li, B., et al. (2023)**
"ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models"
arXiv: 2305.18323
$\to$ Reasoning Without Observation. Plans all tool calls upfront. 5$\times$ token efficiency over ReAct.
*Cited by: R5*

**Press, O., Zhang, M., Min, S., et al. (2022)**
"Measuring and Narrowing the Compositionality Gap in Language Models"
arXiv: 2210.03350
$\to$ Self-Ask decomposition pattern. Compositional multi-hop question answering.
*Cited by: R6*

**Shinn, N., Cassano, F., Berman, E., et al. (2023)**
"Reflexion: Language Agents with Verbal Reinforcement Learning"
*NeurIPS 2023*
arXiv: 2303.11366
$\to$ GPT-4 HumanEval 80% $\to$ 91% via verbal self-critique. Foundation for R7, H2.
*Cited by: R7, H2*

**Madaan, A., Tandon, N., Gupta, P., et al. (2023)**
"Self-Refine: Iterative Refinement with Self-Feedback"
*NeurIPS 2023*
arXiv: 2303.17651
$\to$ Generate-Critique-Refine loop without separate judge. Foundation for R8, O5.
*Cited by: R8*

**Yao, S., Yu, D., Zhao, J., et al. (2023)**
"Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
*NeurIPS 2023*
arXiv: 2305.10601
$\to$ BFS/DFS over reasoning states. Foundation for R9.
*Cited by: R9*

**Zhou, A., Yan, K., Shlapentokh-Rothman, M., et al. (2024)**
"Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models"
*ICML 2024*
arXiv: 2310.04406
$\to$ MCTS + ReAct + Reflexion unified. Foundation for R10.
*Cited by: R10*

**Yang, C., Wang, X., Lu, Y., et al. (2023)**
"Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models"
*NeurIPS 2024*
arXiv: 2406.04271
$\to$ Reusable thought templates. 12% of ToT/GoT compute cost. Foundation for R11.
*Cited by: R11*

**Ning, X., Lin, Z., Zhou, Z., et al. (2024)**
"Skeleton-of-Thought: Prompting LLMs for Efficient Parallel Generation"
*ICLR 2024*
arXiv: 2307.15337
$\to$ Parallel section generation via outline. Reduces latency for structured long-form output. Foundation for R12.
*Cited by: R12*

**Wang, Z., Mao, S., Wu, W., et al. (2024)**
"Executable Code Actions Elicit Better LLM Agents"
*ICML 2024*
arXiv: 2402.01030
$\to$ CodeAct: Python execution as agent action vs. JSON tool calls. ~20pp accuracy gain. Foundation for R13.
*Cited by: R13, V8*

**Chen, W., Ma, X., Wang, X., Cohen, W. W. (2022)**
"Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks"
arXiv: 2211.12588
$\to$ Delegates computation to Python interpreter. Foundation for R14.
*Cited by: R14*

**Adams, G., Fabbri, A., Ladhak, F., et al. (2023)**
"From Sparse to Dense: GPT-4 Summarization with Chain of Density Prompting"
arXiv: 2309.04269
$\to$ Iterative densification without length increase. Foundation for K6 Chain-of-Density variant.
*Cited by: K6*

---

### Memory and Knowledge Papers

**Packer, C., Fang, V., Patil, S. G., et al. (2023)**
"MemGPT: Towards LLMs as Operating Systems"
arXiv: 2310.08560
$\to$ OS-inspired memory hierarchy for LLMs. Main memory / external storage analogy. Foundation for K10, K11, H9.
*Cited by: K10, K11, H2, H9*

**Gao, L., Ma, X., Lin, J., Callan, J. (2023)**
"Precise Zero-Shot Dense Retrieval without Relevance Labels"
*ACL 2023*
arXiv: 2212.10496
$\to$ HyDE: hypothetical document embeddings improve sparse query retrieval. Foundation for K2.
*Cited by: K2*

**Edge, D., Trinh, H., Cheng, N., et al. (2024)**
"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"
arXiv: 2404.16130
$\to$ GraphRAG: entity-relationship graph for multi-hop retrieval. Foundation for K3.
*Cited by: K3*

**Sarthi, P., Abdullah, R., Tuli, A., et al. (2024)**
"RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval"
*ICLR 2024*
arXiv: 2401.18059
$\to$ Multi-level summary tree for hierarchical retrieval. Foundation for K4.
*Cited by: K4*

**Asai, A., Wu, Z., Wang, Y., et al. (2024)**
"Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
*ICLR 2024*
arXiv: 2310.11511
$\to$ Model decides when to retrieve; critiques own outputs. Foundation for K5.
*Cited by: K5*

**Yan, S., Gu, J., Zhu, Y., Ling, Z. (2024)**
"Corrective Retrieval Augmented Generation"
arXiv: 2401.15884
$\to$ Evaluates retrieval quality; triggers web search fallback. Foundation for K6.
*Cited by: K6*

---

### Agent Architecture Papers

**Wang, G., Xie, Y., Jiang, Y., et al. (2023)**
"Voyager: An Open-Ended Embodied Agent with Large Language Models"
arXiv: 2305.16291
$\to$ Autonomous Minecraft agent building a skill library. Foundation for H4.
*Cited by: H4*

**Salemi, A., Mysore, S., Bendersky, M., Zamani, H. (2023)**
"LaMP: When Large Language Models Meet Personalization"
arXiv: 2304.11406
$\to$ LLM personalisation: user-specific style adaptation. Foundation for H7.
*Cited by: H7*

---

### Cognitive Architecture Papers

**"Theater of Mind: A Global Workspace Framework for LLM Agent Architecture" (2025)**
arXiv: 2604.08206
$\to$ Global Workspace Theory applied to LLMs. Introduces: Genesis State, autobiographical directives, entropy monitoring for deadlock breaking, epistemic state tracking. Foundation for H1, H3, H9.
*Cited by: H1, H3, H6, H9*

**"MIRROR: Inner Monologue as a First-Class Architectural Component" (2025)**
arXiv: 2506.00430
$\to$ Background Thinker process, continuous inner monologue, LEGOMem skill accumulation. Foundation for H4, H6, R15.
*Cited by: H4, H6, R15*

**"Talker-Reasoner: Dual-Process Architecture for Conversational Agents" (2024)**
arXiv: 2410.08328
$\to$ System 1 (Talker: fast, reactive) + System 2 (Reasoner: slow, deliberative) dual architecture. Foundation for R16.
*Cited by: R16*

**"Agentic Communities: Patterns for Multi-Agent AI Systems" (2025)**
arXiv: 2601.03624
$\to$ 46-pattern catalog. ISO ODP-EL deontic governance tokens (PERMIT, PROHIBIT, OBLIGATE, WAIVE). Foundation for V7, O-category patterns, H5.
*Cited by: V7, H5, O9-O13*

**"Inside the Scaffold: Empirical Taxonomy of Coding Agent Architectures" (2025)**
arXiv: 2604.03515
$\to$ 13 coding agents, 12 dimensions, 5 loop primitives. Key finding: 11/13 use stacked primitives. Two fault lines: LLM-as-navigator vs scaffold-understands-code. Foundation for O16.
*Cited by: O16*

**"Blackboard Multi-Agent Systems for LLMs" (bMAS) (2024)**
arXiv: 2510.01285
$\to$ Shared blackboard architecture achieving SOTA reasoning at lower token cost than static pipelines. Foundation for O11.
*Cited by: O11*

---

### Evaluation Papers

**Zheng, L., Chiang, W., Sheng, Y., et al. (2023)**
"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
*NeurIPS 2023*
arXiv: 2306.05685
$\to$ LLM-as-Judge methodology, position/verbosity/self-similarity bias documentation. Foundation for V15.
*Cited by: V15*

---

### Safety and Security Papers

**Bai, Y., Jones, A., Ndousse, K., et al. (2022)**
"Constitutional AI: Harmlessness from AI Feedback"
*Anthropic*
arXiv: 2212.08073
$\to$ Constitutional AI: RLHF + self-critique against a set of principles. Foundation for S9, H5.
*Cited by: S9, H5*

**Perez, F., Ribeiro, I. (2022)**
"Ignore Previous Prompt: Attack Techniques for Language Models"
arXiv: 2211.09527
$\to$ First systematic study of prompt injection. Documents injection attack classes. Foundation for V6.
*Cited by: V6*

---

### Prompt Engineering Papers

**White, J., Fu, Q., Hays, S., et al. (2023)**
"A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT"
*PLoP 2023 (Vanderbilt University)*
arXiv: 2302.11382
$\to$ 16-pattern prompt pattern catalog in GoF format. The closest prior work to this entire project. Covers Signal patterns primarily.
*Cited by: S1-S10, meta-reference*

**"AutoPDL: Automated Prompt Design with Large Language Models" (2025)**
arXiv: 2504.04365
$\to$ Automated prompt design loop. Foundation for S8, H8.
*Cited by: S8, H8*

**"Meta Prompting: Enhancing Language Models with Task-Agnostic Scaffolding" (2023)**
arXiv: 2311.11482
$\to$ Meta-prompting: model generates candidate prompts; selects best. Foundation for S8.
*Cited by: S8*

---

## Books

**Gamma, E., Helm, R., Johnson, R., Vlissides, J. (1994)**
*Design Patterns: Elements of Reusable Object-Oriented Software*
Addison-Wesley
$\to$ The original Gang of Four. This entire project is an attempt to do for AI engineering what GoF did for OOP.
*Cited by: all files (foundational)*

**Nygard, M. T. (2007)**
*Release It! Design and Deploy Production-Ready Software*
Pragmatic Bookshelf (2nd ed. 2018)
$\to$ Circuit breaker pattern. Stability patterns for production systems. Foundation for V9.
*Cited by: V9*

**Baddeley, A. D. (2000)**
*Working Memory, Thought, and Action*
Oxford University Press
(Original model: Baddeley & Hitch, 1974)
$\to$ Episodic buffer, central executive, visuospatial sketchpad, phonological loop. Grounds K10 Long-Term Memory (episodic, semantic, and procedural variants). Foundation for cognitive grounding of memory patterns.
*Cited by: K10, H9*

**Minsky, M. (1986)**
*The Society of Mind*
Simon & Schuster
$\to$ Society of mind as multi-agent architecture. Foundation for O10 (Swarm).
*Cited by: O10*

**Kahneman, D. (2011)**
*Thinking, Fast and Slow*
Farrar, Straus and Giroux
$\to$ System 1 (fast, intuitive) / System 2 (slow, deliberative) dual-process theory. Foundation for R16 (Talker-Reasoner).
*Cited by: R16*

---

## Specifications and Standards

**Anthropic Model Context Protocol (MCP) Specification (November 2024)**
modelcontextprotocol.io
$\to$ Standardised tool discovery, authentication, and invocation. Foundation for I3.
*Cited by: I3, V13, CONFLICTS*

**Google Agent-to-Agent (A2A) Protocol Specification (2024)**
github.com/google-a2a/A2A
$\to$ Structured cross-agent task delegation with streaming status. Foundation for I5, I6.
*Cited by: I5, I6*

**IBM/Red Hat Agent Communication Protocol (ACP) (2025)**
$\to$ RESTful, message-based agent communication. Alternative to A2A. Foundation for I6.
*Cited by: I6*

**Linux Foundation Agentic AI Interoperability Framework (AAIF) (2025)**
$\to$ Standards body for agent interoperability. Covers A2A, ACP, ANP. Foundation for I5, I6.
*Cited by: I5, I6*

**OpenTelemetry GenAI Semantic Conventions (CNCF, 2024-25)**
opentelemetry.io/docs/specs/semconv/gen-ai/
$\to$ Standard trace format for LLM operations. Foundation for V14.
*Cited by: V14*

**OWASP LLM Top 10 (2025 Edition)**
owasp.org/www-project-top-10-for-large-language-model-applications/
$\to$ LLM01 Prompt Injection, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Code Execution. Foundation for V3, V4, V6, V8.
*Cited by: V3, V4, V5, V6, V8*

**European Union AI Act (2024)**
eur-lex.europa.eu — Regulation (EU) 2024/1689
$\to$ Article 9 (Risk Management), Article 14 (Human Oversight), Article 52 (Transparency obligations). Foundation for V1, V7, H10.
*Cited by: V1, V7, H10*

**NIST AI Risk Management Framework (AI RMF 1.0) (2023)**
airc.nist.gov/technical-reports/ [direct PDF link stale — landing page confirmed live]
$\to$ Govern, Map, Measure, Manage framework. Foundation for V5, V7, V18.
*Cited by: V5, V7, V18*

**IETF RFC 8615 — Well-Known Uniform Resource Identifiers (2019)**
$\to$ `/.well-known/` standard. Foundation for I5 (Agent Card URL convention).
*Cited by: I5*

**ISO/IEC ODP Enterprise Language (ODP-EL)**
$\to$ Deontic modalities used in Agentic Communities paper for governance tokens. Foundation for V7.
*Cited by: V7*

---

## Practitioner Frameworks

**Andrew Ng (2024)**
"What's next for AI agentic workflows"
deeplearning.ai / Sequoia Capital interview
$\to$ Four agentic patterns: Reflection, Tool Use, Planning, Multi-Agent Collaboration.
*Cited by: all categories (foundational context)*

**Anthropic (2024-25)**
"Building Effective Agents"
anthropic.com/research/building-effective-agents
$\to$ Five workflow patterns: Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer. Primary source for O2-O6.
*Cited by: O2, O3, O4, O5, O6, V1, V14*

**Anthropic (2025)**
"Effective Context Engineering for AI Agents"
anthropic.com/engineering/effective-context-engineering-for-ai-agents
$\to$ Canonical "context as finite resource" post. Verbatim: LLMs have an "attention budget"; transformer attention is n² in tokens; recall degrades as context grows; goal is "the smallest possible set of high-signal tokens." Primary mechanistic source for the K-series and the data-room workflow.
*Cited by: K-series (Chapter 0 Mechanisms 2, 5)*

**Anthropic (2025)**
"Equipping Agents for the Real World with Agent Skills"
anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
$\to$ Three-level progressive disclosure (metadata $\to$ SKILL.md $\to$ bundled files); bundled context "effectively unbounded." Mechanistic basis for skills-not-prompts.
*Cited by: I-series (Chapter 0 Mechanism 1)*

**Anthropic (2025)**
"Writing Effective Tools for AI Agents"
anthropic.com/engineering/writing-tools-for-agents
$\to$ Tools as a contract between deterministic systems and non-deterministic agents; bundle deterministic operations rather than have the model re-derive them.
*Cited by: I-series, V-series*

**Anthropic (2025)**
"Code Execution with MCP: Building More Efficient AI Agents"
anthropic.com/engineering/code-execution-with-mcp
$\to$ Treating tool calls as code keeps intermediate results out of context; reports ~98.7% token reduction (150k $\to$ 2k) in one case. Determinism-vs-sampling evidence.
*Cited by: I-series*

**Anthropic (2025-26)**
"Claude Code Memory" and "Memory Tool" (docs)
docs.anthropic.com/en/docs/claude-code/memory · platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
$\to$ Persistence is externalised memory (CLAUDE.md / MEMORY.md / /memory files re-loaded into context), not weight updates. Corrects the "skills compound" folk-claim.
*Cited by: H-series (Chapter 0 Mechanism 10)*

**Dex Horthy / HumanLayer (2025)**
"12-Factor Agents: Best Practices for Building AI Agents in Production"
github.com/humanlayer/12-factor-agents [original domain 12factor.agency has expired]
$\to$ All 12 factors: Natural Language to Structured Output; Own Your Prompts; Own Your Context Window; Own Your State, Separate from Session; Call LLM as a Pure Function; Human in the Loop; Small Focused Agents; Own Your Control Flow; Compact Errors; Trigger from Anywhere; Trust Nobody; Stateless by Default.
*Cited by: V1, V9, V10, V11, V12, V14*

**Lilian Weng (2023-25)**
"LLM-powered Autonomous Agents"
lilianweng.github.io/posts/2023-06-23-agent/
$\to$ Comprehensive survey covering planning, memory, tool use, multi-agent. One of the most-cited practitioner resources.
*Cited by: S2, S3, R17, R4, R7, K10, K11, H7, V15*

**Simon Willison (2023-25)**
"Prompt injection attacks against GPT-3" and subsequent posts
simonwillison.net
$\to$ Lethal Trifecta concept (3 conditions for catastrophic injection risk). 6 defense patterns. Dual LLM pattern.
*Cited by: V3, V4, V5, V6*

**Andrej Karpathy (2025)**
"Software Is Eating the World, AI Is Eating Software" and related talks
$\to$ "Harness engineering" era framing. Vibe coding $\to$ agentic engineering transition. Context engineering.
*Cited by: all categories (foundational context)*

**Martin Fowler and Birgitta Böckeler (2024)**
"Exploring Generative AI" series
martinfowler.com/articles/exploring-gen-ai.html
$\to$ Harness Architecture 2$\times$2 framework. Practical agent design patterns.
*Cited by: background context*

---

## Industry Reports

**Composio (2025)**
"AI Agent Report 2025"
composio.dev/blog/ai-agent-report [temporarily unavailable June 2026 due to security incident — report expected to return]
$\to$ Key findings: 88% of AI agents never reach production. Tool overload quantification: 43% $\to$ 14% selection accuracy. Production failure root cause analysis. Simulation as recommended mitigation.
*Cited by: V1, V9, V13, V16, V18*

**PineCone (2025)**
"Nexus: Agent Operating Context" and NoQL query language
pinecone.io/blog/nexus [link unavailable as of June 2026 — content may have moved within Pinecone docs]
$\to$ Explicit repositioning from vector similarity to agent operating context bundles. NoQL carries intent, filters, access policy, provenance, response shape, and confidence — not just similarity. Rediscovery quantification: up to 85% of agent compute consumed by context re-assembly rather than task execution. Conceptual and empirical foundation for K13 Retrieval Bundle.
*Cited by: K13*

**PageIndex (2025)**
Document tree retrieval — hierarchical indexing for structured documents
pageindex.ai
$\to$ Claim: many documents should never be chunked because document structure carries meaning that vector flattening destroys. Hierarchical tree approach (table of contents with per-node summaries; model reasons through tree to find section). Reports 98.7% accuracy on FinanceBench evaluation using tree retrieval vs. lower accuracy with embedding-based chunk retrieval. Foundation for the structured document shape in K13 and confirmation of K4 RAPTOR's core principle.
*Cited by: K13, K4*

**Chroma (2025)**
"Context Rot" research
trychroma.com
$\to$ Model performance degrades as context window fills with mixed-authority, mixed-freshness, and inferred-alongside-confirmed content — not because the correct answer is absent, but because it is not presented in a form the model uses reliably. Named failure mode: context rot. Distinct from lost-in-the-middle (mechanism 4): context rot is specifically about authority and freshness mixing, not positional under-attendance. Foundation for K13's per-field authority labeling requirement and K9's "appropriate context not maximum context" discipline.
*Cited by: K13, K9*

---

## Cognitive Science References

**Tulving, E. (1985)**
"Memory and Consciousness"
*Canadian Psychology*, 26(1), 1–12
$\to$ Episodic vs. semantic memory distinction. Foundation for K10/K11 split.
*Cited by: K10, K11, H1*

**Berlyne, D. E. (1966)**
"Curiosity and Exploration"
*Science*, 153(3731), 25–33
$\to$ Optimal arousal theory. Curiosity as entropy-seeking. Foundation for H3.
*Cited by: H3*

**Premack, D., Woodruff, G. (1978)**
"Does the chimpanzee have a theory of mind?"
*Behavioral and Brain Sciences*, 1(4), 515–526
$\to$ Theory of Mind. Foundation for H7 (Adaptive Persona as user model).
*Cited by: H7*

**Clark, A., Chalmers, D. (1998)**
"The Extended Mind"
*Analysis*, 58(1), 7–19
$\to$ External tools as cognitive extensions. Foundation for K11 (Observational Memory as extended mind).
*Cited by: K11*

**Saltzer, J. H., Schroeder, M. D. (1975)**
"The Protection of Information in Computer Systems"
*Proceedings of the IEEE*, 63(9)
$\to$ Principle of least privilege. Foundation for V4 (Dual LLM), V8 (Tool Sandboxing).
*Cited by: V4, V8*

**Baars, B. J. (1988)**
*A Cognitive Theory of Consciousness*
Cambridge University Press
$\to$ Global Workspace Theory. Conscious processing as broadcast to global workspace. Foundation for O11 (Blackboard System).
*Cited by: O11, H6, Theater of Mind paper*

**Vygotsky, L. S. (1934/1986)**
*Thought and Language*
MIT Press (Kozulin translation)
$\to$ Inner speech as internalized dialogue. Foundation for R15 (Inner Monologue), H6 (Continuous Inner Monologue).
*Cited by: R15, H6*

**Skjuve, M., Følstad, A., Fostervold, K. I., Brandtzaeg, P. B. (2021)**
"My Chatbot Companion — a Study of Human-Chatbot Relationships"
*Computers in Human Behavior*, 122, 106842
$\to$ Parasocial relationship formation with AI agents. Foundation for H10 (Relational Memory) ethical constraints.
*Cited by: H10*

---

## Community Sources

**Hacker News — MCP and Tool Overhead Discussion (2024-25)**
Multiple threads including: "Show HN: Model Context Protocol" discussion; "MCP is the npm of AI tools" thread
$\to$ Community quantification of token overhead. Practitioner backlash on schema costs. "Supply chain risk" framing.
*Cited by: I3*

**Hacker News — LangChain Backlash (2024)**
"Ask HN: Why are people moving away from LangChain?"
$\to$ 80+ package dependencies. Death by abstraction. MCP as disruption of LangChain value proposition.
*Cited by: I6*

**Hacker News — Production Agent Failures (2024-25)**
Various threads on agent reliability and production incidents
$\to$ Context for A1-A15 anti-patterns. Empirical grounding for reliability patterns.
*Cited by: V-category patterns*

---

## Reference Summary by Pattern Category

| Category | Key Primary Sources |
|---|---|
| **Signal (S)** | White et al. 2023 (PLoP), Brown et al. 2020, Bai et al. 2022, Adams et al. 2023, Wang et al. 2022 |
| **Knowledge (K)** | Packer et al. 2023, Gao et al. 2023, Edge et al. 2024, Sarthi et al. 2024, Asai et al. 2024, Clark & Chalmers 1998, PineCone 2025, PageIndex 2025, Chroma 2025 |
| **Reasoning (R)** | Wei et al. 2022, Yao et al. 2022 (ReAct), Xu et al. 2023 (ReWOO), Shinn et al. 2023, Yao et al. 2023 (ToT), Zhou et al. 2024 (LATS), Wang et al. 2024 (CodeAct) |
| **Orchestration (O)** | Anthropic 2024-25, Agentic Communities 2025, Scaffold Taxonomy 2025, bMAS 2024, Minsky 1986, Kahneman 2011 |
| **Reliability (V)** | OWASP LLM 2025, EU AI Act 2024, NIST AI RMF, Willison 2023-25, Nygard 2007, Bai et al. 2022, Zheng et al. 2023, Composio 2025, 12-Factor Agents |
| **Integration (I)** | Anthropic MCP 2024, Google A2A 2024, IBM ACP 2025, AAIF 2025, Brown et al. 2020 |
| **Humanizers (H)** | Theater of Mind 2025, MIRROR 2025, Talker-Reasoner 2024, Shinn et al. 2023, Voyager 2023, Salemi et al. 2023, Tulving 1985, Berlyne 1966, Skjuve et al. 2021 |

---

## Open Access Links

All arXiv papers are freely available at `arxiv.org/abs/[ID]`.

| Paper | arXiv ID |
|---|---|
| GPT-3 (Brown et al.) | 2005.14165 |
| Chain-of-Thought (Wei et al.) | 2201.11903 |
| Self-Consistency (Wang et al.) | 2203.11171 |
| Zero-Shot CoT (Kojima et al.) | 2205.11916 |
| Plan-and-Solve (Wang et al.) | 2305.04091 |
| ReAct (Yao et al.) | 2210.03629 |
| ReWOO (Xu et al.) | 2305.18323 |
| Self-Ask (Press et al.) | 2210.03350 |
| Reflexion (Shinn et al.) | 2303.11366 |
| Self-Refine (Madaan et al.) | 2303.17651 |
| Tree of Thoughts (Yao et al.) | 2305.10601 |
| LATS (Zhou et al.) | 2310.04406 |
| Buffer of Thoughts (Yang et al.) | 2406.04271 |
| Skeleton-of-Thought (Ning et al.) | 2307.15337 |
| CodeAct (Wang et al.) | 2402.01030 |
| Program of Thoughts (Chen et al.) | 2211.12588 |
| Chain of Density (Adams et al.) | 2309.04269 |
| MemGPT (Packer et al.) | 2310.08560 |
| HyDE (Gao et al.) | 2212.10496 |
| GraphRAG (Edge et al.) | 2404.16130 |
| RAPTOR (Sarthi et al.) | 2401.18059 |
| Self-RAG (Asai et al.) | 2310.11511 |
| Corrective RAG (Yan et al.) | 2401.15884 |
| Voyager (Wang et al.) | 2305.16291 |
| LAMP Personalisation (Salemi et al.) | 2304.11406 |
| LLM-as-Judge (Zheng et al.) | 2306.05685 |
| Constitutional AI (Bai et al.) | 2212.08073 |
| Prompt Injection (Perez & Ribeiro) | 2211.09527 |
| Prompt Pattern Catalog (White et al.) | 2302.11382 |
| AutoPDL | 2504.04365 |
| Meta Prompting | 2311.11482 |
| Theater of Mind | 2604.08206 |
| MIRROR Inner Monologue | 2506.00430 |
| Talker-Reasoner | 2410.08328 |
| Agentic Communities | 2601.03624 |
| Scaffold Taxonomy | 2604.03515 |
| Blackboard MAS (bMAS) | 2510.01285 |
