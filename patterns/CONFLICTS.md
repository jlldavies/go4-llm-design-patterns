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

## Conflict Index

These are the conflicts most likely to cause production failures if not understood.

<!-- BEGIN INDEX -->
### Signal
#### Critical 3 — S9 H/S V7  {#critical-3}
S9 embeds principles in the prompt. [full »](conflicts/SIGNAL.md#critical-3)

#### Connection B — S2 $\sim$ prefix cache  {#connection-b}
Dynamic S2 (Retrieval-Augmented Few-Shot variant) changes the token sequence of the few-shot block on every call. [full »](conflicts/SIGNAL.md#connection-b)

- **Signal vs Signal** — see [conflicts/SIGNAL.md](./conflicts/SIGNAL.md)
- **Signal vs Reasoning** — see [conflicts/SIGNAL.md](./conflicts/SIGNAL.md)

### Knowledge
#### Connection A — K6/K7 $\sim$ K11  {#connection-a}
K6 (Context Compression) rewrites earlier context spans; K7 (Context Pruning) deletes them. [full »](conflicts/KNOWLEDGE.md#connection-a)

#### Connection D — K1 $\leftrightarrow$ K9  {#connection-d}
K1 (Vanilla RAG) pays n² attention cost at retrieval time over a small context (retrieved chunks only). [full »](conflicts/KNOWLEDGE.md#connection-d)

- **Knowledge vs Knowledge** — see [conflicts/KNOWLEDGE.md](./conflicts/KNOWLEDGE.md)
- **Knowledge vs Reasoning** — see [conflicts/KNOWLEDGE.md](./conflicts/KNOWLEDGE.md)

### Reasoning
#### Critical 1 — R4 $\oplus$ R5  {#critical-1}
ReAct interleaves reasoning and observation — it can adapt mid-task based on what it discovers. [full »](conflicts/REASONING.md#critical-1)

#### Critical 5 — R13 $\to$ V8  {#critical-5}
R13 (CodeAct) achieves its ~20pp accuracy advantage over JSON tool calls by executing arbitrary Python code. [full »](conflicts/REASONING.md#critical-5)

#### Connection C — R17 $\sim$ prefix cache  {#connection-c}
When R17 (Self-Consistency Voting) wraps R2 (Few-Shot CoT) with a static exemplar block, the exemplar block qualifies as a cacheable prefix (mechanism 5). [full »](conflicts/REASONING.md#connection-c)

#### Connection I — R7 $\sim$ R4  {#connection-i}
Each R7 (Reflexion) retry is a full new R4 (ReAct) trajectory. [full »](conflicts/REASONING.md#connection-i)

- **Reasoning vs Reasoning** — see [conflicts/REASONING.md](./conflicts/REASONING.md)
- **Reasoning vs Orchestration** — see [conflicts/REASONING.md](./conflicts/REASONING.md)

### Orchestration
#### Connection F — O6 $\to$ O17  {#connection-f}
The O6 (Orchestrator-Workers) quality win — cited as ~90% accuracy improvement — depends mechanically on each worker having a bounded seq_len separate from the orchestrator (mechanism 6). [full »](conflicts/ORCHESTRATION.md#connection-f)

- **Orchestration vs Orchestration** — see [conflicts/ORCHESTRATION.md](./conflicts/ORCHESTRATION.md)

### Reliability
#### Critical 2 — V1 $\leftrightarrow$ V2  {#critical-2}
V1 blocks: the agent cannot proceed until a human approves. [full »](conflicts/RELIABILITY.md#critical-2)

#### Critical 8 — V12 $\sim$ V10  {#critical-8}
At first glance these conflict: V12 says agents should be pure functions with no internal state; V10 says agent state should be saved at each step. [full »](conflicts/RELIABILITY.md#critical-8)

#### Connection E — V4/V15/V6  {#connection-e}
V4 (Dual LLM) routes untrusted content through a quarantined Q-LLM before it reaches the privileged P-LLM. [full »](conflicts/RELIABILITY.md#connection-e)

#### Connection J — V20 $\to$ V9  {#connection-j}
Each V20 (Schema Validation) retry re-sends the original prompt + the bad output + an error message. [full »](conflicts/RELIABILITY.md#connection-j)

- **Reliability vs Signal/Reasoning** — see [conflicts/RELIABILITY.md](./conflicts/RELIABILITY.md)
- **Reliability vs Orchestration** — see [conflicts/RELIABILITY.md](./conflicts/RELIABILITY.md)

### Integration
#### Critical 6 — I3 $\leftrightarrow$ V13  {#critical-6}
MCP makes it easy to add tool servers. [full »](conflicts/INTEGRATION.md#critical-6)

#### Connection H — I3 $\sim$ I6  {#connection-h}
I3 (MCP Server) routes the main agent's tool-selection overhead to a search subagent with its own bounded context. [full »](conflicts/INTEGRATION.md#connection-h)

- **Integration vs Integration** — see [conflicts/INTEGRATION.md](./conflicts/INTEGRATION.md)

### Humanizers
#### Critical 4 — H3 $\oplus$ R17  {#critical-4}
R17 reduces entropy: it samples multiple outputs and selects the majority answer — the most consistent, lowest-entropy result. [full »](conflicts/HUMANIZERS.md#critical-4)

#### Critical 7 — H5 $\to$ V1  {#critical-7}
H5 allows the agent to propose modifications to its own operating principles. [full »](conflicts/HUMANIZERS.md#critical-7)

#### Connection G — H6 $\sim$ H2  {#connection-g}
H6 (Continuous Inner Monologue) runs internal reflection that produces abstracted summaries of session activity. [full »](conflicts/HUMANIZERS.md#connection-g)

- **Humanizer vs Humanizer** — see [conflicts/HUMANIZERS.md](./conflicts/HUMANIZERS.md)
- **Humanizer vs Other Categories** — see [conflicts/HUMANIZERS.md](./conflicts/HUMANIZERS.md)
<!-- END INDEX -->

*The following connections were identified through tensor-level mechanical analysis. Each describes a structural interaction between patterns that the mechanical understanding reveals.*

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
