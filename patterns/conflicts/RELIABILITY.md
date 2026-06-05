# Conflicts — Reliability

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Critical 2 — V1 $\leftrightarrow$ V2  {#critical-2}

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

## Critical 8 — V12 $\sim$ V10  {#critical-8}

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

## Connection E — V4/V15/V6  {#connection-e}

**Type:** Prerequisite Dependency $\to$

V4 (Dual LLM) routes untrusted content through a quarantined Q-LLM before it reaches the privileged P-LLM. When V15 (LLM-as-Judge) serves as V4's Validation Layer, the judge session receives the Q-LLM's output — which may contain injected instructions from the original untrusted source (mechanism 3, 12: injected content occupies positions in the KV cache where it can influence attention). V6 (Prompt Injection Shield) MUST wrap the V15 judge session in this configuration.

**Unsafe composition:** V4 + V15 without V6 creates a path where injected content survives to the judge and potentially escapes to the P-LLM via the judge's verdict.

**Required composition:** V4 + V15 + V6 (wrapping the judge session). Document this explicitly — practitioners composing V4 and V15 without V6 are creating an injection gap at the V4 boundary.

---

## Connection J — V20 $\to$ V9  {#connection-j}

**Type:** Composability Tension ($\sim$)

Each V20 (Schema Validation) retry re-sends the original prompt + the bad output + an error message. Context grows by approximately twice the bad output length per retry (mechanism 2, 3). V20 with a cap of 3 retries and a 1,000-token original prompt may consume 4–5× the token cost of the first attempt.

**Resolution:** V9 (Bounded Execution) must explicitly account for V20's worst-case retry expansion when calibrating the token cap. Rule: V9 token cap ≥ original_prompt_tokens × (1 + 2 × V20_retry_cap). Build this calculation into the V9 configuration whenever V20 is composed into the same pipeline.

## Reliability vs Signal/Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| V1 (HITL) | $\leftrightarrow$ | V2 (Human-on-Loop) | See CRITICAL 2. Not a sliding scale — a design choice based on action reversibility. |
| V5 (Guardrail Layering) | $\sim$ | S5 (Constraint Framing) | S5 is model self-restraint via prompt; V5 is external enforcement via code. They are complementary, not alternatives. S5 catches broad behavioral constraints; V5 enforces specific, enumerable violations. Use both: S5 for "spirit of the rules"; V5 for "letter of the rules." |
| V9 (Bounded Execution) | $\sim$ | R10 (LATS) | LATS requires deep tree search; bounds truncate it. This is an unavoidable tension: set bounds too tight and LATS never reaches good solutions; too loose and cost explodes. Resolution: profile LATS on representative problems; set bounds at p95 completion cost, not p50. |
| V11 (Error Compaction) | $\sim$ | V14 (Trajectory Logging) | V11 compresses errors for the context window; V14 logs full errors for audit. They are not alternatives — V14 stores the full error in the trace; V11 stores the compact version in the active context. Both must be active simultaneously for different audiences (agent vs. operator). |
| V12 (Stateless Reducer) | $\sim$ | V10 (Checkpointing) | See CRITICAL 8. Resolved by externalising state. |
| V13 (Tool Budget) | $\leftrightarrow$ | I3 (MCP Server) | See CRITICAL 6. MCP adds richness; V13 enforces the cost limit of that richness. |

## Reliability vs Orchestration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| V3 (Lethal Trifecta) | $\to$ | V4 or V6 or V8 | V3 is detection only; it requires at least one mitigation. V4 is the strongest architectural mitigation; V6 and V8 are operational mitigations. V3 without any mitigation is incomplete. |
| V7 (AgentSpec) | $\sim$ | O6 (Orchestrator-Workers) | Orchestrators typically have broad capability; workers are specialised. AgentSpec must be differentiated per agent role — the orchestrator's policy differs from workers'. A single AgentSpec for all agents in an O6 system is a misconfiguration. |
| V8 (Tool Sandboxing) | $\to$ | R13 (CodeAct) | See CRITICAL 5. Dependency, not a conflict. |
