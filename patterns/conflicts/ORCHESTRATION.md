# Conflicts — Orchestration

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Connection F — O6 $\to$ O17  {#connection-f}

**Type:** Prerequisite Dependency $\to$

The O6 (Orchestrator-Workers) quality win — cited as ~90% accuracy improvement — depends mechanically on each worker having a bounded seq_len separate from the orchestrator (mechanism 6). O17 (Agent Isolation) is the pattern that enforces this. Without O17, workers share context with the orchestrator; n² cost grows as if it were a single agent and the lost-in-middle degradation (mechanism 4) applies to the combined context.

**Unsafe composition:** O6 without O17 provides orchestration structure but not the context bounding that produces the quality gain. It is O6 in name only.

**Required composition:** O6 + O17 is mandatory, not recommended. The production composition law (*O6 + O4 + O17 + V9 + V14*) treats O17 as load-bearing.

---

## Orchestration vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| O2 (Prompt Chaining) | $\uparrow$ | O6 (Orchestrator-Workers) | O2 uses a fixed, predetermined sequence; O6 uses dynamic task decomposition at runtime. Start with O2 — cheaper and more testable. Upgrade to O6 when the decomposition cannot be predetermined at design time. |
| O6 (Orchestrator-Workers) | $\leftrightarrow$ | O7 (Supervisor Hierarchy) | O6 is single-level delegation; O7 is multi-level. Use O6 as long as the orchestrator can maintain oversight of all workers. Add hierarchy (O7) when the number of workers exceeds what the orchestrator can coordinate effectively (~5-10 workers). |
| O9 (Multi-Agent Reflection) | $\leftrightarrow$ | R17 (Self-Consistency) | Both achieve reliability through multiple independent assessments. R17 samples the same model N times; O9 uses distinct agents with different personas or knowledge. O9 is more expensive but produces genuinely diverse perspectives when agents are well-differentiated. R17 if you have one model and need reliability; O9 if you have multiple specialist agents and need diverse critique. |
| O10 (Swarm/Mesh) | $\leftrightarrow$ | O7 (Supervisor Hierarchy) | Swarm is emergent, peer-to-peer, no central coordinator; hierarchy is structured, top-down, coordinated. Swarm has no production consensus (as of 2025); hierarchy is the validated path. Use O7; revisit O10 when swarm coordination protocols mature. |
| O11 (Blackboard) | $\sim$ | K10 (Long-Term Memory) | Blackboard is active shared state that triggers agent activation; K10 is passive shared memory that agents query. In a fully developed multi-agent system, both may coexist: K10 as the long-term knowledge substrate, O11 as the working session coordination mechanism. Avoid treating them as alternatives. |
| O15 (Agent Handoff) | $\leftrightarrow$ | I6 (A2A Delegation) | O15 is intra-system state transfer (same codebase, different agent contexts); I6 is inter-system task delegation (different codebases, different organisations). If agents are in the same system: O15. If agents are in different systems: I6. |
