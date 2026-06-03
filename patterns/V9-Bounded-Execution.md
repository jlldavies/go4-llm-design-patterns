# V9 — Bounded Execution

> Wrap every agent loop in a hard envelope of iteration, tool-call, token, time, and cost caps — so a wrong turn becomes a graceful termination instead of a runaway invoice.

**Also Known As:** Circuit Breaker (for agents), Iteration Cap, Recursion Limit, Execution Budget, Step Budget, Cost Budget. (The conceptual ancestor is Netflix Hystrix–style circuit breaking applied to LLM loops.)

**Classification:** Category V — Reliability · the universal recovery-loop bound — required by virtually every loop pattern in the catalogue (R4, R7, R8, R9, R10, R13, R17, R20; K5; O5, O8, O16; H5).

---

## Intent

Apply hard, externally-enforced limits on every dimension along which an agent loop can run away — iterations, tool calls, tokens, wall-clock, and dollars — so that a miscalibrated agent fails fast at a known bound instead of consuming unbounded resources before someone notices.

## Motivation

Agentic loops have no natural stopping condition. ReAct (R4) keeps reasoning and acting until *it* decides it is done. Reflexion (R7) retries until *it* believes the result is acceptable. LATS (R10) expands the tree until *it* converges. Self-Refine (R8) revises until *it* judges the draft good. Every one of these terminations is a *judgement made by the LLM under test* — and the LLM under test is exactly the component whose miscalibration is the failure mode of interest. There is no inner check that catches "this loop is stuck": the loop *being stuck* is what the LLM does not notice. The mechanism is that each loop step appends tokens to the context; the KV cache grows monotonically within a session (mechanism 3), each step costs more in O(n²) attention computation than the last (mechanism 2), and earlier reasoning steps drift toward mid-context positions where recall is geometrically weakest (mechanism 4). The model cannot observe any of this — it conditions only on visible context tokens, not on its own computational costs or cache state.

Production incident reports converge on the same story. An agent built for a 30-second task quietly runs for six hours overnight, makes 14,000 tool calls, exhausts a Tier-2 API rate limit, and rings up four figures in token spend — discovered the next morning. A coding agent gets caught in a fix-test-fix cycle on a problem the test suite cannot decide, and the cycle compounds across a worker pool. A retrieval loop cascades through fallbacks (K5) on a query nobody can answer, each fallback worse than the last. Anti-pattern A3 (Uncontrolled Recursion) names this class directly. The Composio AI Agent Report 2025 lists cost overruns as the top production-incident category and the most cited reason 88% of agent pilots never reach production.

The fix is not smarter judgement inside the loop — the LLM cannot reliably judge its own runaway. The fix is **a bound outside the loop that does not consult the LLM**. This is the software circuit breaker (Nygard, 2007; embodied in Netflix Hystrix and resilience4j): an external counter that trips after N failures or after a budget threshold, opens the circuit, and forces graceful degradation. V9 is that pattern applied to LLM agent loops. Its defining move is that the bound lives in **wiring code**, not in a prompt — no amount of model misbehaviour can talk past it. The other defining move is that the bound *terminates gracefully*: state is saved (V10), the partial result is returned with a termination reason, the event is logged (V14), and — if needed — a human is invited to rescue (V1). A bound that just crashes is a worse failure mode than the loop it stopped.

## Applicability

Use Bounded Execution when:

- the agent contains *any* loop — reasoning loop, evaluator loop, refine loop, search loop, recovery loop (this is essentially every R-band loop pattern, every loop-shaped orchestration pattern, and every adaptive K-pattern);
- the agent calls tools and the cost of an unbounded tool-call sequence is material;
- the deployment is production or anywhere unattended (no human in the room to notice a runaway);
- one component's budget overrun would cascade into shared rate limits, shared cost pools, or shared queues.

Do not use it when:

- the call is a *single shot* — one prompt, one completion, no tools, no loop. There is nothing to bound, and adding a budget framework is overhead; rely on the model's own `max_tokens` parameter and stop. (Single-shot LLM calls live entirely inside **S1 / S2** signal-layer patterns.)
- the workload is a deterministic non-LLM pipeline. V9 is a pattern for LLM loops; ordinary code uses its own resource controls.
- the loop is *already* bounded by an outer V9 envelope that subsumes it, and adding an inner V9 only multiplies counters without raising precision — pick the outer envelope and let it govern.

## Decision Criteria

V9 is right whenever any loop is present in the agent — the only question is *what to cap* and *at what value*.

**1. Identify every loop dimension.** Inventory:
- max **iterations** (reasoning steps),
- max **tool calls**,
- max **tokens** (prompt + completion total),
- max **wall-clock** seconds,
- max **cost** in dollars.
If the answer to *any* dimension is "no cap currently," that dimension is the gap.

The token cap is mechanically load-bearing beyond cost: as context grows, prior loop steps move toward mid-context where attention recall is u-shaped and weakest (mechanism 4), degrading the model's ability to reason over its own earlier work — bounded iteration is also a reasoning-quality intervention, not only a cost control.

**2. Pick caps from measured data, not intuition.** Run the agent on a representative test set; record p50 and p99 of each dimension. Set the cap at **p99 $\times$ 1.5–2$\times$**. Caps below p99 truncate legitimate work; caps above 5$\times$ p99 fail to catch runaways until they are already expensive. If you have no measured data, you cannot calibrate V9 — collect first, cap second.

**3. Soft warning before hard stop.** At 80% of any cap, emit a warning event (V14 trajectory log) and optionally surface to a human (V1 escape valve). A hard stop with no prior warning is hostile; a warning gives operations time to extend the budget or intervene before work is lost.

**4. State preservation on trip.** Confirm that a tripped circuit triggers **V10 Checkpointing** before termination — otherwise the bound is pure loss. A V9 cap that discards work is worse than no cap on a recoverable agent.

**5. Per-task profile.** Different task classes warrant different envelopes — a quick Q&A and a multi-hour research run cannot share one budget. Maintain per-task-type profiles (e.g. `quick_qa`, `research`, `coding_agent`) and select the profile at task start. A single global cap is either too tight for hard tasks or too loose for easy ones; pick neither.

**Quick test — V9 is the right pattern when:**

- the agent contains any loop (R-band, O8, O16, K5, H5, anything with a "until" condition), *and*
- the loop's natural termination depends on the same model whose miscalibration is being defended against, *and*
- the cost of a runaway — in dollars, in rate-limit damage, or in time-to-detect — is meaningfully larger than the cost of a slightly truncated legitimate run, *and*
- caps can be calibrated against measured p99, not guessed.

If there is no loop, V9 is unnecessary — use the model's native `max_tokens` and stop. If the loop is bounded by an outer V9 envelope that already governs the dimensions you care about, do not add a redundant inner bound. If the loop legitimately needs deep search (R10 LATS), do not under-cap — calibrate against measured LATS depth and pair with **V10 Checkpointing** so a hit cap is a pause, not a drop.

## Structure

```
  Agent invocation
         │
         ▼
   Initialise budget:
     iter ← N, tools ← M, tokens ← T, wall ← W, cost ← $C
         │
         ▼
  ┌───── Loop ──────────────────────────────────────────┐
  │                                                       │
  │   Budget Checker:                                     │
  │     any dim ≥ 80% → warn (V14); optionally V1        │
  │     any dim exhausted → trip                          │
  │                                                       │
  │   if tripped:                                         │
  │     V10 Checkpoint state                              │
  │     V14 log termination reason                        │
  │     return partial result + status="terminated:<dim>" │
  │     optionally → V1 (Human-in-the-Loop) for rescue    │
  │     break                                             │
  │                                                       │
  │   step:                                                │
  │     LLM call / tool call                              │
  │     decrement counters                                │
  │     accumulate cost                                   │
  │                                                       │
  └───────────────────────────────────────────────────────┘
         │
         ▼
       Done (normal or terminated)
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Execution Budget** | the numeric envelope on every dimension (iter, tools, tokens, wall, cost) | task profile $\to$ initialised counters | be a prompt-level instruction. The budget lives in wiring code; an LLM that can read or override its own budget defeats the pattern. |
| **Budget Checker** | the test, run *before every step*, of whether any dimension is exhausted | counters $\to$ continue / warn / trip | be the LLM. The Checker is deterministic code; if its decision depends on the model under test, the failure mode the pattern defends against re-enters here. |
| **Graceful Terminator** | the trip path — checkpoint, log, return partial, optionally escalate | trip event + current state $\to$ terminated result | crash the process or drop state silently. A bound that loses work is worse than no bound on a recoverable task. |
| **Warning Threshold** *(optional)* | the soft alert at ~80% of any cap | counters $\to$ warning event | block execution. Warnings inform the operator and optionally **V1**; the hard stop belongs to the Checker. |
| **Task Profile** | the *per-task-type* set of cap values (e.g. `quick_qa`, `research`, `coding`) | task type $\to$ cap values | be a single global cap. One envelope cannot serve both a 1s Q&A and a 6h research run. |
| **State Saver ($\to$ V10)** | invoking checkpointing before the trip returns | current state $\to$ durable snapshot | be skipped. Without it, V9 is a circuit breaker that destroys the device it protects. |

The pattern's reliability rests on two prohibitions: the Checker is not an LLM, and the Terminator does not return without checkpointing. Violate either and V9 becomes ornamental.

## Collaborations

A task invocation selects its **Task Profile** and initialises the **Execution Budget**. The agent enters its loop. Before every step — every reasoning turn, every tool call — the **Budget Checker** evaluates the counters. While all dimensions remain below 80%, the loop proceeds and counters decrement. Crossing 80% on any dimension emits a warning event (logged via **V14 Trajectory Logging**) and may surface to a human via **V1 Human-in-the-Loop** as an escape valve — budget extension or early termination, the operator's choice. Crossing 100% on any dimension trips the circuit: the **State Saver** invokes **V10 Checkpointing** to persist the current trajectory, the **Graceful Terminator** writes a termination event to V14 and returns a partial result tagged with the tripped dimension, and — depending on configuration — control passes to V1 for human rescue or the task simply ends with a partial answer. The next invocation, if any, loads the V10 checkpoint and either resumes from there (under a fresh budget) or rolls back.

## Consequences

**Benefits**

- Catastrophic cost and time overruns become impossible by construction — the worst case is bounded, knowable, and pre-priced.
- Production agents are *deployable* — without V9, "what is the worst this could spend overnight?" has no answer and risk-averse organisations refuse to ship.
- The bound is in code, not prompt, so prompt injection cannot lift it. This is structural, not probabilistic.
- Combined with V10 + V14, a tripped circuit is recoverable, audited, and human-routable — failure becomes a *managed event*.

**Costs**

- Calibration is real work — caps must be measured against representative load, not guessed; bad calibration either truncates legitimate runs or fails to catch overruns until they are expensive.
- Per-task profiles need maintenance as task mixes evolve.
- Warning thresholds add some log volume and an extra V1 surface area.
- For exploratory patterns (R10 LATS, R9 ToT), caps create an inherent tension: a cap tight enough to be safe may be tight enough to prevent the search from reaching good solutions.

**Risks and failure modes**

- *Caps too high.* Limits set so generous they are never tripped until the cost is already catastrophic. Symptom: the V9 event log is empty across months of production; the protection is theoretical.
- *Caps too low.* Limits tuned against a p50 case truncate every p99 legitimate run. Symptom: high termination rate on inputs that should have succeeded; users see partial results with no apparent fault.
- *Bound without checkpoint.* V9 trips and the trajectory is lost — the agent is "safe" only by destroying its own work. Always pair with V10.
- *Bound without trajectory log.* The circuit trips and nobody can tell why or which dimension blew. Always pair with V14.
- *Bound inside a bound.* Inner V9 and outer V9 disagree on which fires first; an inner cap can mask an outer one or vice versa. Decide which envelope governs and let the other be advisory.
- *Prompt-level bound.* An "instruction to the model" to stop after N steps is not V9 — it is a request the model is free to ignore. V9 lives in wiring or it does not exist.

## Implementation Notes

- Build the budget object as a small, plain data structure (dict or struct) carrying all five dimensions, plus elapsed counters. Decrement in the same code that issues the LLM/tool call — never in the LLM itself.
- Token and cost dimensions are estimated from per-call usage metadata most providers expose; tool-call and iteration counts are exact; wall-clock is the simplest. Always cap on the dimensions you can measure exactly *and* the dimensions where the failure mode lives.
- Set caps from p99 of measured runs $\times$ 1.5–2$\times$. If you have no data, instrument first; do not deploy with intuited caps.
- Warning at 80% is a reasonable default; in cost-sensitive environments, tighten to 50–60% with V1 surfacing.
- Different per-task profiles for `quick_qa`, `research`, `coding_agent`, `recovery_loop` — never one global cap. Profile selection happens at task entry.
- LATS (R10) and ToT (R9) need especially generous iteration caps; calibrate against measured search depth on representative problems. **Conflict with R10** noted in CONFLICTS.md — set bounds at p95 of measured LATS completion, not p50.
- Inner loops inside O6 workers need V9; without it, one stuck worker prevents the orchestrator from receiving timely results from the others.
- The Graceful Terminator must always invoke V10 before returning. A trip without checkpoint is a regression from "uncontrolled" to "controlled-but-lossy".
- LangGraph's `recursion_limit` (default 25, configurable per invocation) and LangChain `AgentExecutor`'s `max_iterations` (default 15) and `max_execution_time` are the practical embodiments; treat them as the *minimum* V9 surface, not the maximum — add tokens, tool calls, and cost on top.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V9 wraps any loop pattern (R4, R7, R8, R9, R10, R13, R17, R20, K5, O5, O8, O16, H5) and *requires* **V10 Checkpointing** for graceful termination and **V14 Trajectory Logging** to record budget events. **V1 Human-in-the-Loop** is the optional escalation path at the warning threshold. The bound itself is pure code — no LLM session is added.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Select task profile; initialise budget | `code` | Task Profile registry |
| 2 | Before each loop step — check every dimension | `code` | Budget Checker |
| 3 | If any dim $\geq$ 80%: emit warning event; optionally surface to V1 | `code` | V14, V1 |
| 4 | If any dim $\geq$ 100%: trip $\to$ step 7 | `code` | |
| 5 | Execute the wrapped step (LLM call or tool call) | `LLM` *(or `code`)* | the wrapped pattern |
| 6 | Decrement counters with measured usage; loop to step 2 | `code` | |
| 7 | On trip: V10 checkpoint $\to$ V14 termination event $\to$ return partial with reason | `code` | V10, V14, optional V1 |

**Skeleton** — wiring only; no LLM session is added by V9 itself:

```
bounded_execution(task, profile_name):
    budget = init_budget(profile_name)       # code — Task Profile
    state  = load_or_init(task.session_id)   # code — V10 load
    while True:
        status = check_budget(budget)         # code — Budget Checker
        if status.warn:
            log_warning(budget)               # code — V14 event
            maybe_surface_to_human(budget)    # code — V1 escape valve
        if status.trip:
            checkpoint(state)                 # code — V10 save
            log_termination(budget, state)    # code — V14 event
            return partial_result(state,
                                   reason=status.dim)
        result = step(state)                  # LLM / tool call — the wrapped pattern
        budget = decrement(budget, result.usage)
        state  = update(state, result)
        if state.done:
            checkpoint(state)                 # code — V10 save
            return state.final
```

**The LLM sessions.** None. V9 adds no LLM session of its own — the **Budget Checker** is deterministic code, the **Graceful Terminator** is deterministic code, the **Task Profile** is configuration. The point of the pattern is to put the bound *outside* the LLM's reach.

**Specialist-model note.** None. V9 is a wiring pattern; it adds no model dependency. The prompt artifact that earns its keep is the **Task Profile registry** — the per-task-type cap values, versioned alongside the agent, tunable from measured V14 data, audited as part of every deployment review. Operations on the budget object (init, check, decrement, trip) are plain code; the registry is plain configuration.

## Open-Source Implementations

- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — `recursion_limit` parameter on graph invocation (default 25); `GraphRecursionError` raised when exceeded. Per-call configuration via `{"recursion_limit": N}`. The most direct V9 surface in the LangChain ecosystem.
- **LangChain AgentExecutor** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — `max_iterations` (default 15) and `max_execution_time` (wall-clock cap, default None) on `AgentExecutor`. Companion `early_stopping_method` (`"force"` or `"generate"`) controls the graceful-termination behaviour.
- **resilience4j** — [`github.com/resilience4j/resilience4j`](https://github.com/resilience4j/resilience4j) — the modern Java circuit-breaker library (successor to Hystrix); not LLM-specific but the canonical reference for the underlying circuit-breaker mechanics V9 inherits.
- **Netflix Hystrix (archived)** — [`github.com/Netflix/Hystrix`](https://github.com/Netflix/Hystrix) — the conceptual ancestor; now in maintenance mode but historically the reference implementation of the circuit-breaker pattern that V9 generalises to LLM loops. Netflix's own migration path points to resilience4j for new projects.
- **12-Factor Agents** — [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) — Dex Horthy's framework; Factor 5 ("Unify execution state and business state") and Factor 8 ("Own your control flow") establish bounded execution as a first-class production concern, not an afterthought.

## Known Uses

- **LangGraph / LangChain production deployments** — `recursion_limit` and `max_iterations` are de facto standard configuration on every production agent built on these frameworks.
- **Anthropic Claude Code, Cursor, Devin, and similar coding agents** — all expose per-task budgets (token, tool-call, wall-clock) and trip gracefully when exceeded; the trip is visible to the user as a partial result with a termination notice.
- **OpenAI Assistants / Responses APIs** — server-side `max_completion_tokens` and per-run `truncation` controls embody the single-shot edge of V9; multi-step agent runs add framework-level caps on top.
- **Composio AI Agent Report 2025** — cost overruns from unbounded loops cited as the top production-incident category and the most-cited reason 88% of agent pilots never reach production. Adoption of V9 cited as a baseline mitigation.

## Related Patterns

- **Pairs with** V10 Checkpointing — mandatory partner. A V9 trip without a V10 checkpoint is a circuit breaker that destroys the device it protects.
- **Pairs with** V14 Trajectory Logging — the trip event, the warning events, and the per-step counters are V14's content. Without V14, V9 trips are invisible to operations.
- **Pairs with** V1 Human-in-the-Loop — the 80% warning is the natural V1 surface: hand the partial trajectory to a human before the hard stop fires.
- **Required by** R4 ReAct, R7 Reflexion, R8 Self-Refine, R9 Tree-of-Thoughts, R10 LATS, R13 CodeAct, R17 Self-Consistency Voting, R20 Chain-of-Verification — every R-band loop pattern. None of these has a natural termination condition the model can be trusted to enforce.
- **Required by** K5 Adaptive RAG — the recovery loop (fallback re-retrieval) cascades indefinitely without a cap.
- **Required by** O5 Evaluator-Optimizer, O8 Loop Agent, O16 Hybrid Control Flow — every loop-shaped orchestration pattern.
- **Required by** H5 Constitutional Self-Alignment — the principle-evolution loop must be bounded both per session and across sessions.
- **Competes with** *nothing* — V9 has no substitute. The only alternative is "no bound," which is anti-pattern **A3 Uncontrolled Recursion**.
- **Conceptual ancestor:** Netflix Hystrix and the broader software circuit-breaker tradition (Nygard, 2007). V9 is that pattern transposed from "remote service call" to "LLM reasoning step."

## Sources

- Nygard, M. T. (2007) — *Release It! Design and Deploy Production-Ready Software*. The original articulation of the circuit-breaker pattern.
- Netflix Hystrix — [github.com/Netflix/Hystrix](https://github.com/Netflix/Hystrix) — the canonical (now-archived) reference implementation of circuit breaking in distributed systems.
- resilience4j — [github.com/resilience4j/resilience4j](https://github.com/resilience4j/resilience4j) — the modern functional-Java successor; current reference for circuit-breaker mechanics.
- 12-Factor Agents (Dex Horthy / HumanLayer, 2025) — [github.com/humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — Factor 5 (Unify execution state and business state) and Factor 8 (Own your control flow) establish bounded execution as a production prerequisite.
- LangGraph documentation — `recursion_limit` and `GRAPH_RECURSION_LIMIT` error semantics ([docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)).
- LangChain `AgentExecutor` API reference — `max_iterations`, `max_execution_time`, `early_stopping_method`.
- Composio AI Agent Report 2025 — cost-overrun root-cause analysis; 88% production-failure-rate breakdown.
- Anthropic, "Building Effective Agents" (2025) — bounded execution as part of the production-agent baseline.
