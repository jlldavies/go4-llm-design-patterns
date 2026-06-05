# Summary

[Introduction](pdf-source/INTRO.md)
[The Pattern Catalog](pdf-source/TAXONOMY-DRAFT.md)

---

# Category I — Signal Patterns

- [Signal Overview](patterns/SIGNAL.md)
- [S1 Zero-Shot](patterns/S1-Zero-Shot.md)
- [S2 Few-Shot](patterns/S2-Few-Shot.md)
- [S3 Persona](patterns/S3-Persona.md)
- [S4 Instruction Decomposition](patterns/S4-Instruction-Decomposition.md)
- [S5 Constraint Framing](patterns/S5-Constraint-Framing.md)
- [S6 Output Template](patterns/S6-Output-Template.md)
- [S8 Meta-Prompt](patterns/S8-Meta-Prompt.md)
- [S9 Constitutional Framing](patterns/S9-Constitutional-Framing.md)
- [Decision Guide](patterns/SIGNAL-DECISION.md)

# Category II — Knowledge Patterns

- [Knowledge Overview](patterns/KNOWLEDGE.md)
- [K1 Vanilla RAG](patterns/K1-Vanilla-RAG.md)
- [K2 Query Transformation](patterns/K2-Query-Transformation.md)
- [K3 GraphRAG](patterns/K3-GraphRAG.md)
- [K4 RAPTOR](patterns/K4-RAPTOR.md)
- [K5 Adaptive RAG](patterns/K5-Adaptive-RAG.md)
- [K6 Context Compression](patterns/K6-Context-Compression.md)
- [K7 Context Pruning](patterns/K7-Context-Pruning.md)
- [K8 Working Memory](patterns/K8-Working-Memory.md)
- [K9 Long Context](patterns/K9-Long-Context.md)
- [K10 Long-Term Memory](patterns/K10-Long-Term-Memory.md)
- [K11 Observational Memory](patterns/K11-Observational-Memory.md)
- [K12 Karpathy Memory](patterns/K12-Karpathy-Memory.md)
- [K13 Retrieval Bundle](patterns/K13-Retrieval-Bundle.md)
- [Decision Guide](patterns/KNOWLEDGE-DECISION.md)

# Category III — Reasoning Patterns

- [Reasoning Overview](patterns/REASONING.md)
- [R1 Zero-Shot CoT](patterns/R1-Zero-Shot-CoT.md)
- [R2 Few-Shot CoT](patterns/R2-Few-Shot-CoT.md)
- [R3 Plan-and-Solve](patterns/R3-Plan-and-Solve.md)
- [R4 ReAct](patterns/R4-ReAct.md)
- [R5 ReWOO](patterns/R5-ReWOO.md)
- [R6 Self-Ask](patterns/R6-Self-Ask.md)
- [R7 Reflexion](patterns/R7-Reflexion.md)
- [R8 Self-Refine](patterns/R8-Self-Refine.md)
- [R9 Tree of Thoughts](patterns/R9-Tree-of-Thoughts.md)
- [R10 LATS](patterns/R10-LATS.md)
- [R11 Buffer of Thoughts](patterns/R11-Buffer-of-Thoughts.md)
- [R12 Skeleton-of-Thought](patterns/R12-Skeleton-of-Thought.md)
- [R13 CodeAct](patterns/R13-CodeAct.md)
- [R14 Program of Thoughts](patterns/R14-Program-of-Thoughts.md)
- [R16 Talker-Reasoner](patterns/R16-Talker-Reasoner.md)
- [R17 Self-Consistency](patterns/R17-Self-Consistency-Voting.md)
- [R18 Graph of Thoughts](patterns/R18-Graph-of-Thoughts.md)
- [R19 Step-Back Prompting](patterns/R19-Step-Back-Prompting.md)
- [R20 Chain of Verification](patterns/R20-Chain-of-Verification.md)
- [Decision Guide](patterns/REASONING-DECISION.md)

# Category IV — Orchestration Patterns

- [Orchestration Overview](patterns/ORCHESTRATION.md)
- [O1 Single Agent](patterns/O1-Single-Agent.md)
- [O2 Prompt Chaining](patterns/O2-Prompt-Chaining.md)
- [O3 Routing](patterns/O3-Routing.md)
- [O4 Parallelization](patterns/O4-Parallelization.md)
- [O5 Evaluator-Optimizer](patterns/O5-Evaluator-Optimizer.md)
- [O6 Orchestrator-Workers](patterns/O6-Orchestrator-Workers.md)
- [O7 Supervisor Hierarchy](patterns/O7-Supervisor-Hierarchy.md)
- [O8 Loop Agent](patterns/O8-Loop-Agent.md)
- [O9 Multi-Agent Reflection](patterns/O9-Multi-Agent-Reflection.md)
- [O10 Swarm](patterns/O10-Swarm.md)
- [O11 Blackboard](patterns/O11-Blackboard.md)
- [O12 Debate and Deliberation](patterns/O12-Debate-Deliberation.md)
- [O13 Negotiation](patterns/O13-Negotiation.md)
- [O14 SIE](patterns/O14-SIE.md)
- [O15 Agent Handoff](patterns/O15-Agent-Handoff.md)
- [O16 Hybrid Control Flow](patterns/O16-Hybrid-Control-Flow.md)
- [O17 Agent Isolation](patterns/O17-Agent-Isolation.md)
- [O18 Cache-Warmed Worker Pool](patterns/O18-Cache-Warmed-Worker-Pool.md)
- [Decision Guide](patterns/ORCHESTRATION-DECISION.md)

# Category V — Reliability Patterns

- [Reliability Overview](patterns/RELIABILITY.md)
- [V1 Human-in-the-Loop](patterns/V1-Human-in-the-Loop.md)
- [V2 Human-on-the-Loop](patterns/V2-Human-on-the-Loop.md)
- [V3 Rule of Two](patterns/V3-Rule-of-Two.md)
- [V4 Dual LLM](patterns/V4-Dual-LLM.md)
- [V5 Guardrail Layering](patterns/V5-Guardrail-Layering.md)
- [V6 Prompt Injection Shield](patterns/V6-Prompt-Injection-Shield.md)
- [V7 AgentSpec](patterns/V7-AgentSpec.md)
- [V8 Tool Sandboxing](patterns/V8-Tool-Sandboxing.md)
- [V9 Bounded Execution](patterns/V9-Bounded-Execution.md)
- [V10 Checkpointing](patterns/V10-Checkpointing.md)
- [V11 Error Compaction](patterns/V11-Error-Compaction.md)
- [V12 Stateless Reducer](patterns/V12-Stateless-Reducer.md)
- [V13 Tool Budget](patterns/V13-Tool-Budget.md)
- [V14 Trajectory Logging](patterns/V14-Trajectory-Logging.md)
- [V15 LLM-as-Judge](patterns/V15-LLM-as-Judge.md)
- [V16 Offline Eval](patterns/V16-Offline-Eval.md)
- [V17 Online Eval](patterns/V17-Online-Eval.md)
- [V18 Agent Simulation](patterns/V18-Agent-Simulation.md)
- [V19 Fallback](patterns/V19-Fallback.md)
- [V20 Schema Validation](patterns/V20-Schema-Validation.md)
- [Decision Guide](patterns/RELIABILITY-DECISION.md)

# Category VI — Integration Patterns

- [Integration Overview](patterns/INTEGRATION.md)
- [I1 Direct API](patterns/I1-Direct-API.md)
- [I2 Function / Tool Call](patterns/I2-Function-Call.md)
- [I3 MCP Server](patterns/I3-MCP-Server.md)
- [I4 CLI Invocation](patterns/I4-CLI-Invocation.md)
- [I5 Agent Card](patterns/I5-Agent-Card.md)
- [I6 A2A Delegation](patterns/I6-A2A-Delegation.md)
- [Decision Guide](patterns/INTEGRATION-DECISION.md)

# Category VII — Humanizer Patterns

- [Humanizer Overview](patterns/HUMANIZERS.md)
- [H1 Identity Persistence](patterns/H1-Identity-Persistence.md)
- [H2 Episodic Self-Improvement](patterns/H2-Episodic-Self-Improvement.md)
- [H3 Entropy-Driven Curiosity](patterns/H3-Entropy-Driven-Curiosity.md)
- [H4 Procedural Skill Accumulation](patterns/H4-Procedural-Skill-Accumulation.md)
- [H5 Constitutional Self-Alignment](patterns/H5-Constitutional-Self-Alignment.md)
- [H6 Continuous Inner Monologue](patterns/H6-Continuous-Inner-Monologue.md)
- [H7 Adaptive Persona](patterns/H7-Adaptive-Persona.md)
- [H8 Meta-Agent Self-Modification](patterns/H8-Meta-Agent-Self-Modification.md)
- [H9 Observational Identity](patterns/H9-Observational-Identity.md)
- [H10 Relational Memory](patterns/H10-Relational-Memory.md)
- [Decision Guide](patterns/HUMANIZERS-DECISION.md)

---

# The Mechanical Foundation

- [The Mechanical Foundation](pdf-source/CHAPTER-0.md)

---

# Appendices

- [Appendix A — Conflicts](patterns/CONFLICTS.md)
  - [Signal](patterns/conflicts/SIGNAL.md)
  - [Knowledge](patterns/conflicts/KNOWLEDGE.md)
  - [Reasoning](patterns/conflicts/REASONING.md)
  - [Orchestration](patterns/conflicts/ORCHESTRATION.md)
  - [Reliability](patterns/conflicts/RELIABILITY.md)
  - [Integration](patterns/conflicts/INTEGRATION.md)
  - [Humanizers](patterns/conflicts/HUMANIZERS.md)
- [Appendix B — References](pdf-source/REFERENCES.md)
- [Appendix C — Anti-Patterns & Composition Examples](pdf-source/APPENDIX-C.md)
