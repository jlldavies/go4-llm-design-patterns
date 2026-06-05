# Conflicts — Reasoning

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Critical 1 — R4 $\oplus$ R5  {#critical-1}

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

## Critical 5 — R13 $\to$ V8  {#critical-5}

**Type:** Prerequisite Dependency

R13 (CodeAct) achieves its ~20pp accuracy advantage over JSON tool calls by executing arbitrary Python code. This is only safe inside a constrained execution environment. Without V8:

- LLM-generated code has full access to the host filesystem
- LLM-generated code can make arbitrary network requests
- A prompt injection (V6 concern) can generate and execute malicious code with the agent's full permissions
- A reasoning error can generate destructive code with no blast radius limit

**Resolution rule:** R13 without V8 is not a valid configuration in any production or shared environment. Treat this as a broken dependency, not a tradeoff.

**Implementation:** Docker containers (production), gVisor (high-security), or CodeSandbox/E2B (hosted sandbox) are the current implementation options.

---

## Connection C — R17 $\sim$ prefix cache  {#connection-c}

**Type:** Composability Tension ($\sim$)

When R17 (Self-Consistency Voting) wraps R2 (Few-Shot CoT) with a static exemplar block, the exemplar block qualifies as a cacheable prefix (mechanism 5). But if N samples are dispatched sequentially over time exceeding the provider TTL (~5 minutes), later samples lose the cache hit and re-pay full prefill.

**Resolution (O18 applies):** Fan out all N samples simultaneously in parallel (O4 Parallelization). Do not dispatch them sequentially. The first sample pays the cache write; all subsequent parallel samples hit the cache. This converts the token cost of N samples from N × full_prefill to 1 × cache_write + (N-1) × cache_read.

---

## Connection I — R7 $\sim$ R4  {#connection-i}

**Type:** Composability Tension ($\sim$)

Each R7 (Reflexion) retry is a full new R4 (ReAct) trajectory. The episodic memory buffer — containing N-1 prior critiques — is appended to each subsequent Actor call. Retry N's Actor call attends over a longer prefix than retry N-1 (mechanism 2: O(n²) attention cost). The retry cost is not N × per-task cost — it is strictly super-linear.

**Example:** For a base trajectory of 2,000 tokens and 3 critiques of 300 tokens each: Retry 1 pays O(2000²); Retry 2 pays O(2300²); Retry 3 pays O(2600²). Total: approximately 20–30% more than 3 × O(2000²).

**Resolution:** (1) Keep critiques compact — the Distiller pattern applied to critique outputs reduces the super-linear growth. (2) Cap retries aggressively — V9 Bounded Execution should account for the super-linear cost, not just count retries. (3) Clear the episodic buffer after convergence; do not carry it into the next independent task.

---

## Reasoning vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| R4 (ReAct) | $\oplus$ | R5 (ReWOO) | See CRITICAL 1. Mutually exclusive for the same task. |
| R7 (Reflexion) | $\leftrightarrow$ | R17 (Self-Consistency) | Both improve reliability through repetition but via different mechanisms. R17: parallel sampling + voting. R7: sequential iteration with memory of failures. R17 is parallel (immediate N× cost); R7 is sequential (cost scales only on failure). For tasks with automated feedback $\to$ R7. Without feedback $\to$ R17. |
| R9 (ToT) | $\leftrightarrow$ | R10 (LATS) | ToT uses heuristic tree search; LATS uses MCTS with full backtracking. LATS is strictly more powerful but can be 10× more expensive. Use ToT as default; upgrade to LATS only for the highest-stakes open-ended problems where LATS's backtracking provides decisive advantage. |
| R11 (Buffer of Thoughts) | $\leftrightarrow$ | R9 (ToT) | BoT achieves 12% of ToT's compute cost by reusing thought templates. BoT is appropriate when similar reasoning tasks recur; ToT is appropriate for novel problems where templates don't exist. |
| R13 (CodeAct) | $\to$ | V8 (Tool Sandboxing) | See CRITICAL 5. R13 requires V8; no exceptions. |

## Reasoning vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| R4 (ReAct) | $\sim$ | O6 (Orchestrator-Workers) | R4 is a reasoning loop within a single agent; O6 is delegation across agents. In O6 systems, each worker typically runs R4 internally. The conflict: if R4 loops are unbounded (A3), they prevent the orchestrator from receiving timely worker results. Always pair R4 with V9 (Bounded Execution) inside O6 workers. |
| R7 (Reflexion) | $\sim$ | O5 (Evaluator-Optimizer) | Reflexion is self-critique within a single agent; O5 uses a separate evaluator agent. They compose: R7 for intra-agent improvement; O5 for validated cross-agent quality gates. Don't run both simultaneously on the same task — the critique loops will conflict. |
| R12 (Skeleton-of-Thought) | $\sim$ | O4 (Parallelization) | SoT generates an outline then fills sections in parallel; O4 parallelises independent sub-tasks. They are essentially the same pattern at different levels of abstraction. If you implement SoT, you are implementing O4 at the section level. No conflict — but avoid implementing both independently for the same task. |
